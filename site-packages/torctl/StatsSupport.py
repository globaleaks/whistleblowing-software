#!/usr/bin/python
#StatsSupport.py - functions and classes useful for calculating stream/circuit statistics

"""

Support classes for statisics gathering

The StatsSupport package contains several classes that extend
PathSupport to gather continuous statistics on the Tor network.

The main entrypoint is to extend or create an instance of the
StatsHandler class. The StatsHandler extends from
TorCtl.PathSupport.PathBuilder, which is itself a TorCtl.EventHandler.
The StatsHandler listens to CIRC and STREAM events and gathers all
manner of statics on their creation and failure before passing the
events back up to the PathBuilder code, which manages the actual
construction and the attachment of streams to circuits.

The package also contains a number of support classes that help gather
additional statistics on the reliability and performance of routers.

For the purpose of accounting failures, the code tracks two main classes
of failure: 'actual' failure and 'suspected' failure. The general rule
is that an actual failure is attributed to the node that directly
handled the circuit or stream. For streams, this is considered to be the
exit node. For circuits, it is both the extender and the extendee.
'Suspected' failures, on the other hand, are attributed to every member
of the circuit up until the extendee for circuits, and all hops for
streams.

For bandwidth accounting, the average stream bandwidth and the average
ratio of stream bandwidth to advertised bandwidth are tracked, and when
the statistics are written, a Z-test is performed to calculate the
probabilities of these values assuming a normal distribution. Note,
however, that it has not been verified that this distribution is
actually normal. It is likely to be something else (pareto, perhaps?).

"""

import sys
import re
import random
import copy
import time
import math
import traceback

import TorUtil, PathSupport, TorCtl
from TorUtil import *
from PathSupport import *
from TorUtil import meta_port, meta_host, control_port, control_host

class ReasonRouterList:
  "Helper class to track which Routers have failed for a given reason"
  def __init__(self, reason):
    self.reason = reason
    self.rlist = {}

  def sort_list(self): raise NotImplemented()

  def write_list(self, f):
    "Write the list of failure counts for this reason 'f'"
    rlist = self.sort_list()
    for r in rlist:
      susp = 0
      tot_failed = r.circ_failed+r.strm_failed
      tot_susp = tot_failed+r.circ_suspected+r.strm_suspected
      f.write(r.idhex+" ("+r.nickname+") F=")
      if self.reason in r.reason_failed:
        susp = r.reason_failed[self.reason]
      f.write(str(susp)+"/"+str(tot_failed))
      f.write(" S=")
      if self.reason in r.reason_suspected:
        susp += r.reason_suspected[self.reason]
      f.write(str(susp)+"/"+str(tot_susp)+"\n")
    
  def add_r(self, r):
    "Add a router to the list for this reason"
    self.rlist[r] = 1

  def total_suspected(self):
    "Get a list of total suspected failures for this reason"
    # suspected is disjoint from failed. The failed table
    # may not have an entry
    def notlambda(x, y):
      if self.reason in y.reason_suspected:
        if self.reason in y.reason_failed:
          return (x + y.reason_suspected[self.reason]
               + y.reason_failed[self.reason])
        else:
          return (x + y.reason_suspected[self.reason])
      else:
        if self.reason in y.reason_failed:
          return (x + y.reason_failed[self.reason])
        else: return x
    return reduce(notlambda, self.rlist.iterkeys(), 0)

  def total_failed(self):
    "Get a list of total failures for this reason"
    def notlambda(x, y):
      if self.reason in y.reason_failed:
        return (x + y.reason_failed[self.reason])
      else: return x
    return reduce(notlambda, self.rlist.iterkeys(), 0)
 
class SuspectRouterList(ReasonRouterList):
  """Helper class to track all routers suspected of failing for a given
     reason. The main difference between this and the normal
     ReasonRouterList is the sort order and the verification."""
  def __init__(self, reason): ReasonRouterList.__init__(self,reason)
  
  def sort_list(self):
    rlist = self.rlist.keys()
    rlist.sort(lambda x, y: cmp(y.reason_suspected[self.reason],
                  x.reason_suspected[self.reason]))
    return rlist
   
  def _verify_suspected(self):
    return reduce(lambda x, y: x + y.reason_suspected[self.reason],
            self.rlist.iterkeys(), 0)

class FailedRouterList(ReasonRouterList):
  """Helper class to track all routers that failed for a given
     reason. The main difference between this and the normal
     ReasonRouterList is the sort order and the verification."""
  def __init__(self, reason): ReasonRouterList.__init__(self,reason)

  def sort_list(self):
    rlist = self.rlist.keys()
    rlist.sort(lambda x, y: cmp(y.reason_failed[self.reason],
                  x.reason_failed[self.reason]))
    return rlist

  def _verify_failed(self):
    return reduce(lambda x, y: x + y.reason_failed[self.reason],
            self.rlist.iterkeys(), 0)
class BandwidthStats:
  "Class that manages observed bandwidth through a Router"
  def __init__(self):
    self.byte_list = []
    self.duration_list = []
    self.min_bw = 1e10
    self.max_bw = 0
    self.mean = 0
    self.dev = 0

  def _exp(self): # Weighted avg
    "Expectation - weighted average of the bandwidth through this node"
    tot_bw = reduce(lambda x, y: x+y, self.byte_list, 0.0)
    EX = 0.0
    for i in xrange(len(self.byte_list)):
      EX += (self.byte_list[i]*self.byte_list[i])/self.duration_list[i]
    if tot_bw == 0.0: return 0.0
    EX /= tot_bw
    return EX

  def _exp2(self): # E[X^2]
    "Second moment of the bandwidth"
    tot_bw = reduce(lambda x, y: x+y, self.byte_list, 0.0)
    EX = 0.0
    for i in xrange(len(self.byte_list)):
      EX += (self.byte_list[i]**3)/(self.duration_list[i]**2)
    if tot_bw == 0.0: return 0.0
    EX /= tot_bw
    return EX
    
  def _dev(self): # Weighted dev
    "Standard deviation of bandwidth"
    EX = self.mean
    EX2 = self._exp2()
    arg = EX2 - (EX*EX)
    if arg < -0.05:
      plog("WARN", "Diff of "+str(EX2)+" and "+str(EX)+"^2 is "+str(arg))
    return math.sqrt(abs(arg))

  def add_bw(self, bytes, duration):
    "Add an observed transfer of 'bytes' for 'duration' seconds"
    if not bytes: plog("NOTICE", "No bytes for bandwidth")
    bytes /= 1024.
    self.byte_list.append(bytes)
    self.duration_list.append(duration)
    bw = bytes/duration
    plog("DEBUG", "Got bandwidth "+str(bw))
    if self.min_bw > bw: self.min_bw = bw
    if self.max_bw < bw: self.max_bw = bw
    self.mean = self._exp()
    self.dev = self._dev()


class StatsRouter(TorCtl.Router):
  "Extended Router to handle statistics markup"
  def __init__(self, router): # Promotion constructor :)
    """'Promotion Constructor' that converts a Router directly into a 
    StatsRouter without a copy."""
    # TODO: Use __bases__ to do this instead?
    self.__dict__ = router.__dict__
    self.reset()
    # StatsRouters should not be destroyed when Tor forgets about them
    # Give them an extra refcount:
    self.refcount += 1
    plog("DEBUG", "Stats refcount "+str(self.refcount)+" for "+self.idhex)

  def reset(self):
    "Reset all stats on this Router"
    self.circ_uncounted = 0
    self.circ_failed = 0
    self.circ_succeeded = 0 # disjoint from failed
    self.circ_suspected = 0
    self.circ_chosen = 0 # above 4 should add to this
    self.strm_failed = 0 # Only exits should have these
    self.strm_succeeded = 0
    self.strm_suspected = 0 # disjoint from failed
    self.strm_uncounted = 0
    self.strm_chosen = 0 # above 4 should add to this
    self.reason_suspected = {}
    self.reason_failed = {}
    self.first_seen = time.time()
    if "Running" in self.flags:
      self.became_active_at = self.first_seen
      self.hibernated_at = 0
    else:
      self.became_active_at = 0
      self.hibernated_at = self.first_seen
    self.total_hibernation_time = 0
    self.total_active_uptime = 0
    self.total_extend_time = 0
    self.total_extended = 0
    self.bwstats = BandwidthStats()
    self.z_ratio = 0
    self.prob_zr = 0
    self.z_bw = 0
    self.prob_zb = 0
    self.rank_history = []
    self.bw_history = []

  def was_used(self):
    """Return True if this router was used in this round"""
    return self.circ_chosen != 0

  def avg_extend_time(self):
    """Return the average amount of time it took for this router
     to extend a circuit one hop"""
    if self.total_extended:
      return self.total_extend_time/self.total_extended
    else: return 0

  def bw_ratio(self):
    """Return the ratio of the Router's advertised bandwidth to its 
     observed average stream bandwidth"""
    bw = self.bwstats.mean
    if bw == 0.0: return 0
    else: return self.bw/(1024.*bw)

  def adv_ratio(self): # XXX
    """Return the ratio of the Router's advertised bandwidth to 
       the overall average observed bandwith"""
    bw = StatsRouter.global_bw_mean
    if bw == 0.0: return 0
    else: return self.bw/bw

  def avg_rank(self):
    if not self.rank_history: return self.list_rank
    return (1.0*sum(self.rank_history))/len(self.rank_history)

  def bw_ratio_ratio(self):
    bwr = self.bw_ratio()
    if bwr == 0.0: return 0
    # (avg_reported_bw/our_reported_bw) *
    # (our_stream_capacity/avg_stream_capacity)
    return StatsRouter.global_ratio_mean/bwr 

  def strm_bw_ratio(self):
    """Return the ratio of the Router's stream capacity to the average
       stream capacity passed in as 'mean'"""
    bw = self.bwstats.mean
    if StatsRouter.global_strm_mean == 0.0: return 0
    else: return (1.0*bw)/StatsRouter.global_strm_mean

  def circ_fail_rate(self):
    if self.circ_chosen == 0: return 0
    return (1.0*self.circ_failed)/self.circ_chosen

  def strm_fail_rate(self):
    if self.strm_chosen == 0: return 0
    return (1.0*self.strm_failed)/self.strm_chosen

  def circ_suspect_rate(self):
    if self.circ_chosen == 0: return 1
    return (1.0*(self.circ_suspected+self.circ_failed))/self.circ_chosen

  def strm_suspect_rate(self):
    if self.strm_chosen == 0: return 1
    return (1.0*(self.strm_suspected+self.strm_failed))/self.strm_chosen

  def circ_suspect_ratio(self):
    if 1.0-StatsRouter.global_cs_mean <= 0.0: return 0
    return (1.0-self.circ_suspect_rate())/(1.0-StatsRouter.global_cs_mean)

  def strm_suspect_ratio(self):
    if 1.0-StatsRouter.global_ss_mean <= 0.0: return 0
    return (1.0-self.strm_suspect_rate())/(1.0-StatsRouter.global_ss_mean)

  def circ_fail_ratio(self):
    if 1.0-StatsRouter.global_cf_mean <= 0.0: return 0
    return (1.0-self.circ_fail_rate())/(1.0-StatsRouter.global_cf_mean)

  def strm_fail_ratio(self):
    if 1.0-StatsRouter.global_sf_mean <= 0.0: return 0
    return (1.0-self.strm_fail_rate())/(1.0-StatsRouter.global_sf_mean)

  def current_uptime(self):
    if self.became_active_at:
      ret = (self.total_active_uptime+(time.time()-self.became_active_at))
    else:
      ret = self.total_active_uptime
    if ret == 0: return 0.000005 # eh..
    else: return ret
        
  def failed_per_hour(self):
    """Return the number of circuit extend failures per hour for this 
     Router"""
    return (3600.*(self.circ_failed+self.strm_failed))/self.current_uptime()

  # XXX: Seperate suspected from failed in totals 
  def suspected_per_hour(self):
    """Return the number of circuits that failed with this router as an
     earlier hop"""
    return (3600.*(self.circ_suspected+self.strm_suspected
          +self.circ_failed+self.strm_failed))/self.current_uptime()

  # These four are for sanity checking
  def _suspected_per_hour(self):
    return (3600.*(self.circ_suspected+self.strm_suspected))/self.current_uptime()

  def _uncounted_per_hour(self):
    return (3600.*(self.circ_uncounted+self.strm_uncounted))/self.current_uptime()

  def _chosen_per_hour(self):
    return (3600.*(self.circ_chosen+self.strm_chosen))/self.current_uptime()

  def _succeeded_per_hour(self):
    return (3600.*(self.circ_succeeded+self.strm_succeeded))/self.current_uptime()
  
  key = """Metatroller Router Statistics:
  CC=Circuits Chosen   CF=Circuits Failed      CS=Circuit Suspected
  SC=Streams Chosen    SF=Streams Failed       SS=Streams Suspected
  FH=Failed per Hour   SH=Suspected per Hour   ET=avg circuit Extend Time (s)
  EB=mean BW (K)       BD=BW std Dev (K)       BR=Ratio of observed to avg BW
  ZB=BW z-test value   PB=Probability(z-bw)    ZR=Ratio z-test value
  PR=Prob(z-ratio)     SR=Global mean/mean BW  U=Uptime (h)\n"""

  global_strm_mean = 0.0
  global_strm_dev = 0.0
  global_ratio_mean = 0.0
  global_ratio_dev = 0.0
  global_bw_mean = 0.0
  global_cf_mean = 0.0
  global_sf_mean = 0.0
  global_cs_mean = 0.0
  global_ss_mean = 0.0

  def __str__(self):
    return (self.idhex+" ("+self.nickname+")\n"
    +"   CC="+str(self.circ_chosen)
      +" CF="+str(self.circ_failed)
      +" CS="+str(self.circ_suspected+self.circ_failed)
      +" SC="+str(self.strm_chosen)
      +" SF="+str(self.strm_failed)
      +" SS="+str(self.strm_suspected+self.strm_failed)
      +" FH="+str(round(self.failed_per_hour(),1))
      +" SH="+str(round(self.suspected_per_hour(),1))+"\n"
    +"   ET="+str(round(self.avg_extend_time(),1))
      +" EB="+str(round(self.bwstats.mean,1))
      +" BD="+str(round(self.bwstats.dev,1))
      +" ZB="+str(round(self.z_bw,1))
      +" PB="+(str(round(self.prob_zb,3))[1:])
      +" BR="+str(round(self.bw_ratio(),1))
      +" ZR="+str(round(self.z_ratio,1))
      +" PR="+(str(round(self.prob_zr,3))[1:])
      +" SR="+(str(round(self.strm_bw_ratio(),1)))
      +" U="+str(round(self.current_uptime()/3600, 1))+"\n")

  def sanity_check(self):
    "Makes sure all stats are self-consistent"
    if (self.circ_failed + self.circ_succeeded + self.circ_suspected
      + self.circ_uncounted != self.circ_chosen):
      plog("ERROR", self.nickname+" does not add up for circs")
    if (self.strm_failed + self.strm_succeeded + self.strm_suspected
      + self.strm_uncounted != self.strm_chosen):
      plog("ERROR", self.nickname+" does not add up for streams")
    def check_reasons(reasons, expected, which, rtype):
      count = 0
      for rs in reasons.iterkeys():
        if re.search(r"^"+which, rs): count += reasons[rs]
      if count != expected:
        plog("ERROR", "Mismatch "+which+" "+rtype+" for "+self.nickname)
    check_reasons(self.reason_suspected,self.strm_suspected,"STREAM","susp")
    check_reasons(self.reason_suspected,self.circ_suspected,"CIRC","susp")
    check_reasons(self.reason_failed,self.strm_failed,"STREAM","failed")
    check_reasons(self.reason_failed,self.circ_failed,"CIRC","failed")
    now = time.time()
    tot_hib_time = self.total_hibernation_time
    tot_uptime = self.total_active_uptime
    if self.hibernated_at: tot_hib_time += now - self.hibernated_at
    if self.became_active_at: tot_uptime += now - self.became_active_at
    if round(tot_hib_time+tot_uptime) != round(now-self.first_seen):
      plog("ERROR", "Mismatch of uptimes for "+self.nickname)
    
    per_hour_tot = round(self._uncounted_per_hour()+self.failed_per_hour()+
         self._suspected_per_hour()+self._succeeded_per_hour(), 2)
    chosen_tot = round(self._chosen_per_hour(), 2)
    if per_hour_tot != chosen_tot:
      plog("ERROR", self.nickname+" has mismatch of per hour counts: "
                    +str(per_hour_tot) +" vs "+str(chosen_tot))


# TODO: Use __metaclass__ and type to make this inheritance flexible?
class StatsHandler(PathSupport.PathBuilder):
  """An extension of PathSupport.PathBuilder that keeps track of 
     router statistics for every circuit and stream"""
  def __init__(self, c, slmgr, RouterClass=StatsRouter, track_ranks=False):
    PathBuilder.__init__(self, c, slmgr, RouterClass)
    self.circ_count = 0
    self.strm_count = 0
    self.strm_failed = 0
    self.circ_failed = 0
    self.circ_succeeded = 0
    self.failed_reasons = {}
    self.suspect_reasons = {}
    self.track_ranks = track_ranks

  # XXX: Shit, all this stuff should be slice-based
  def run_zbtest(self): # Unweighted z-test
    """Run unweighted z-test to calculate the probabilities of a node
       having a given stream bandwidth based on the Normal distribution"""
    n = reduce(lambda x, y: x+(y.bwstats.mean > 0), self.sorted_r, 0)
    if n == 0: return (0, 0)
    avg = reduce(lambda x, y: x+y.bwstats.mean, self.sorted_r, 0)/float(n)
    def notlambda(x, y):
      if y.bwstats.mean <= 0: return x+0
      else: return x+(y.bwstats.mean-avg)*(y.bwstats.mean-avg)
    stddev = math.sqrt(reduce(notlambda, self.sorted_r, 0)/float(n))
    if not stddev: return (avg, stddev)
    for r in self.sorted_r:
      if r.bwstats.mean > 0:
        r.z_bw = abs((r.bwstats.mean-avg)/stddev)
        r.prob_zb = TorUtil.zprob(-r.z_bw)
    return (avg, stddev)

  def run_zrtest(self): # Unweighted z-test
    """Run unweighted z-test to calculate the probabilities of a node
       having a given ratio of stream bandwidth to advertised bandwidth
       based on the Normal distribution"""
    n = reduce(lambda x, y: x+(y.bw_ratio() > 0), self.sorted_r, 0)
    if n == 0: return (0, 0)
    avg = reduce(lambda x, y: x+y.bw_ratio(), self.sorted_r, 0)/float(n)
    def notlambda(x, y):
      if y.bw_ratio() <= 0: return x+0
      else: return x+(y.bw_ratio()-avg)*(y.bw_ratio()-avg)
    stddev = math.sqrt(reduce(notlambda, self.sorted_r, 0)/float(n))
    if not stddev: return (avg, stddev)
    for r in self.sorted_r:
      if r.bw_ratio() > 0:
        r.z_ratio = abs((r.bw_ratio()-avg)/stddev)
        r.prob_zr = TorUtil.zprob(-r.z_ratio)
    return (avg, stddev)

  def avg_adv_bw(self):
    n = reduce(lambda x, y: x+y.was_used(), self.sorted_r, 0)
    if n == 0: return (0, 0)
    avg = reduce(lambda x, y: x+y.bw, 
            filter(lambda r: r.was_used(), self.sorted_r), 0)/float(n)
    return avg 

  def avg_circ_failure(self):
    n = reduce(lambda x, y: x+y.was_used(), self.sorted_r, 0)
    if n == 0: return (0, 0)
    avg = reduce(lambda x, y: x+y.circ_fail_rate(), 
            filter(lambda r: r.was_used(), self.sorted_r), 0)/float(n)
    return avg 

  def avg_stream_failure(self):
    n = reduce(lambda x, y: x+y.was_used(), self.sorted_r, 0)
    if n == 0: return (0, 0)
    avg = reduce(lambda x, y: x+y.strm_fail_rate(), 
            filter(lambda r: r.was_used(), self.sorted_r), 0)/float(n)
    return avg 

  def avg_circ_suspects(self):
    n = reduce(lambda x, y: x+y.was_used(), self.sorted_r, 0)
    if n == 0: return (0, 0)
    avg = reduce(lambda x, y: x+y.circ_suspect_rate(), 
            filter(lambda r: r.was_used(), self.sorted_r), 0)/float(n)
    return avg 

  def avg_stream_suspects(self):
    n = reduce(lambda x, y: x+y.was_used(), self.sorted_r, 0)
    if n == 0: return (0, 0)
    avg = reduce(lambda x, y: x+y.strm_suspect_rate(), 
            filter(lambda r: r.was_used(), self.sorted_r), 0)/float(n)
    return avg 

  def write_reasons(self, f, reasons, name):
    "Write out all the failure reasons and statistics for all Routers"
    f.write("\n\n\t----------------- "+name+" -----------------\n")
    for rsn in reasons:
      f.write("\n"+rsn.reason+". Failed: "+str(rsn.total_failed())
          +", Suspected: "+str(rsn.total_suspected())+"\n")
      rsn.write_list(f)

  def write_routers(self, f, rlist, name):
    "Write out all the usage statistics for all Routers"
    f.write("\n\n\t----------------- "+name+" -----------------\n\n")
    for r in rlist:
      # only print it if we've used it.
      if r.circ_chosen+r.strm_chosen > 0: f.write(str(r))

  # FIXME: Maybe move this two up into StatsRouter too?
  ratio_key = """Metatroller Ratio Statistics:
  SR=Stream avg ratio     AR=Advertised bw ratio    BRR=Adv. bw avg ratio
  CSR=Circ suspect ratio  CFR=Circ Fail Ratio       SSR=Stream suspect ratio
  SFR=Stream fail ratio   CC=Circuit Count          SC=Stream Count
  P=Percentile Rank       U=Uptime (h)\n"""
  
  def write_ratios(self, filename):
    "Write out bandwith ratio stats StatsHandler has gathered"
    plog("DEBUG", "Writing ratios to "+filename)
    f = file(filename, "w")
    f.write(StatsHandler.ratio_key)

    (avg, dev) = self.run_zbtest()
    StatsRouter.global_strm_mean = avg
    StatsRouter.global_strm_dev = dev
    (avg, dev) = self.run_zrtest()
    StatsRouter.global_ratio_mean = avg
    StatsRouter.global_ratio_dev = dev

    StatsRouter.global_bw_mean = self.avg_adv_bw()

    StatsRouter.global_cf_mean = self.avg_circ_failure()
    StatsRouter.global_sf_mean = self.avg_stream_failure()
    
    StatsRouter.global_cs_mean = self.avg_circ_suspects()
    StatsRouter.global_ss_mean = self.avg_stream_suspects()

    strm_bw_ratio = copy.copy(self.sorted_r)
    strm_bw_ratio.sort(lambda x, y: cmp(x.strm_bw_ratio(), y.strm_bw_ratio()))
    for r in strm_bw_ratio:
      if r.circ_chosen == 0: continue
      f.write(r.idhex+"="+r.nickname+"\n  ")
      f.write("SR="+str(round(r.strm_bw_ratio(),4))+" AR="+str(round(r.adv_ratio(), 4))+" BRR="+str(round(r.bw_ratio_ratio(),4))+" CSR="+str(round(r.circ_suspect_ratio(),4))+" CFR="+str(round(r.circ_fail_ratio(),4))+" SSR="+str(round(r.strm_suspect_ratio(),4))+" SFR="+str(round(r.strm_fail_ratio(),4))+" CC="+str(r.circ_chosen)+" SC="+str(r.strm_chosen)+" U="+str(round(r.current_uptime()/3600,1))+" P="+str(round((100.0*r.avg_rank())/len(self.sorted_r),1))+"\n")
    f.close()
 
  def write_stats(self, filename):
    "Write out all the statistics the StatsHandler has gathered"
    # TODO: all this shit should be configurable. Some of it only makes
    # sense when scanning in certain modes.
    plog("DEBUG", "Writing stats to "+filename)
    # Sanity check routers
    for r in self.sorted_r: r.sanity_check()

    # Sanity check the router reason lists.
    for r in self.sorted_r:
      for rsn in r.reason_failed:
        if rsn not in self.failed_reasons:
          plog("ERROR", "Router "+r.idhex+" w/o reason "+rsn+" in fail table")
        elif r not in self.failed_reasons[rsn].rlist:
          plog("ERROR", "Router "+r.idhex+" missing from fail table")
      for rsn in r.reason_suspected:
        if rsn not in self.suspect_reasons:
          plog("ERROR", "Router "+r.idhex+" w/o reason "+rsn+" in fail table") 
        elif r not in self.suspect_reasons[rsn].rlist:
          plog("ERROR", "Router "+r.idhex+" missing from suspect table")

    # Sanity check the lists the other way
    for rsn in self.failed_reasons.itervalues(): rsn._verify_failed()
    for rsn in self.suspect_reasons.itervalues(): rsn._verify_suspected()

    f = file(filename, "w")
    f.write(StatsRouter.key)
    (avg, dev) = self.run_zbtest()
    StatsRouter.global_strm_mean = avg
    StatsRouter.global_strm_dev = dev
    f.write("\n\nBW stats: u="+str(round(avg,1))+" s="+str(round(dev,1))+"\n")

    (avg, dev) = self.run_zrtest()
    StatsRouter.global_ratio_mean = avg
    StatsRouter.global_ratio_dev = dev
    f.write("BW ratio stats: u="+str(round(avg,1))+" s="+str(round(dev,1))+"\n")


    # Circ, strm infoz
    f.write("Circ failure ratio: "+str(self.circ_failed)
            +"/"+str(self.circ_count)+"\n")

    f.write("Stream failure ratio: "+str(self.strm_failed)
            +"/"+str(self.strm_count)+"\n")

    # Extend times 
    n = 0.01+reduce(lambda x, y: x+(y.avg_extend_time() > 0), self.sorted_r, 0)
    avg_extend = reduce(lambda x, y: x+y.avg_extend_time(), self.sorted_r, 0)/n
    def notlambda(x, y):
      return x+(y.avg_extend_time()-avg_extend)*(y.avg_extend_time()-avg_extend) 
    dev_extend = math.sqrt(reduce(notlambda, self.sorted_r, 0)/float(n))

    f.write("Extend time: u="+str(round(avg_extend,1))
             +" s="+str(round(dev_extend,1)))
    
    # sort+print by bandwidth
    strm_bw_ratio = copy.copy(self.sorted_r)
    strm_bw_ratio.sort(lambda x, y: cmp(x.strm_bw_ratio(), y.strm_bw_ratio()))
    self.write_routers(f, strm_bw_ratio, "Stream Ratios")

    # sort+print by bandwidth
    bw_rate = copy.copy(self.sorted_r)
    bw_rate.sort(lambda x, y: cmp(y.bw_ratio(), x.bw_ratio()))
    self.write_routers(f, bw_rate, "Bandwidth Ratios")

    failed = copy.copy(self.sorted_r)
    failed.sort(lambda x, y:
          cmp(y.circ_failed+y.strm_failed,
            x.circ_failed+x.strm_failed))
    self.write_routers(f, failed, "Failed Counts")

    suspected = copy.copy(self.sorted_r)
    suspected.sort(lambda x, y: # Suspected includes failed
       cmp(y.circ_failed+y.strm_failed+y.circ_suspected+y.strm_suspected,
         x.circ_failed+x.strm_failed+x.circ_suspected+x.strm_suspected))
    self.write_routers(f, suspected, "Suspected Counts")

    fail_rate = copy.copy(failed)
    fail_rate.sort(lambda x, y: cmp(y.failed_per_hour(), x.failed_per_hour()))
    self.write_routers(f, fail_rate, "Fail Rates")

    suspect_rate = copy.copy(suspected)
    suspect_rate.sort(lambda x, y:
       cmp(y.suspected_per_hour(), x.suspected_per_hour()))
    self.write_routers(f, suspect_rate, "Suspect Rates")
    
    # TODO: Sort by failed/selected and suspect/selected ratios
    # if we ever want to do non-uniform scanning..

    # FIXME: Add failed in here somehow..
    susp_reasons = self.suspect_reasons.values()
    susp_reasons.sort(lambda x, y:
       cmp(y.total_suspected(), x.total_suspected()))
    self.write_reasons(f, susp_reasons, "Suspect Reasons")

    fail_reasons = self.failed_reasons.values()
    fail_reasons.sort(lambda x, y:
       cmp(y.total_failed(), x.total_failed()))
    self.write_reasons(f, fail_reasons, "Failed Reasons")
    f.close()

    # FIXME: sort+print by circ extend time

  def reset(self):
    PathSupport.PathBuilder.reset(self)
    self.reset_stats()

  def reset_stats(self):
    plog("DEBUG", "Resetting stats")
    self.circ_count = 0
    self.strm_count = 0
    self.strm_failed = 0
    self.circ_succeeded = 0
    self.circ_failed = 0
    self.suspect_reasons.clear()
    self.failed_reasons.clear()
    for r in self.routers.itervalues(): r.reset()

  def close_circuit(self, id):
    PathSupport.PathBuilder.close_circuit(self, id)
    # Shortcut so we don't have to wait for the CLOSE
    # events for stats update.
    self.circ_succeeded += 1
    for r in self.circuits[id].path:
      r.circ_chosen += 1
      r.circ_succeeded += 1

  def circ_status_event(self, c):
    if c.circ_id in self.circuits:
      # TODO: Hrmm, consider making this sane in TorCtl.
      if c.reason: lreason = c.reason
      else: lreason = "NONE"
      if c.remote_reason: rreason = c.remote_reason
      else: rreason = "NONE"
      reason = c.event_name+":"+c.status+":"+lreason+":"+rreason
      if c.status == "LAUNCHED":
        # Update circ_chosen count
        self.circ_count += 1
      elif c.status == "EXTENDED":
        delta = c.arrived_at - self.circuits[c.circ_id].last_extended_at
        r_ext = c.path[-1]
        try:
          if r_ext[0] != '$': r_ext = self.name_to_key[r_ext]
          self.routers[r_ext[1:]].total_extend_time += delta
          self.routers[r_ext[1:]].total_extended += 1
        except KeyError, e:
          traceback.print_exc()
          plog("WARN", "No key "+str(e)+" for "+r_ext+" in dict:"+str(self.name_to_key))
      elif c.status == "FAILED":
        for r in self.circuits[c.circ_id].path: r.circ_chosen += 1
        
        if len(c.path)-1 < 0: start_f = 0
        else: start_f = len(c.path)-1 

        # Count failed
        self.circ_failed += 1
        # XXX: Differentiate between extender and extendee
        for r in self.circuits[c.circ_id].path[start_f:len(c.path)+1]:
          r.circ_failed += 1
          if not reason in r.reason_failed:
            r.reason_failed[reason] = 1
          else: r.reason_failed[reason]+=1
          if reason not in self.failed_reasons:
             self.failed_reasons[reason] = FailedRouterList(reason)
          self.failed_reasons[reason].add_r(r)

        for r in self.circuits[c.circ_id].path[len(c.path)+1:]:
          r.circ_uncounted += 1

        # Don't count if failed was set this round, don't set 
        # suspected..
        for r in self.circuits[c.circ_id].path[:start_f]:
          r.circ_suspected += 1
          if not reason in r.reason_suspected:
            r.reason_suspected[reason] = 1
          else: r.reason_suspected[reason]+=1
          if reason not in self.suspect_reasons:
             self.suspect_reasons[reason] = SuspectRouterList(reason)
          self.suspect_reasons[reason].add_r(r)
      elif c.status == "CLOSED":
        # Since PathBuilder deletes the circuit on a failed, 
        # we only get this for a clean close that was not
        # requested by us.

        # Don't count circuits we requested closed from
        # pathbuilder, they are counted there instead.
        if not self.circuits[c.circ_id].requested_closed:
          self.circ_succeeded += 1
          for r in self.circuits[c.circ_id].path:
            r.circ_chosen += 1
            if lreason in ("REQUESTED", "FINISHED", "ORIGIN"):
              r.circ_succeeded += 1
            else:
              if not reason in r.reason_suspected:
                r.reason_suspected[reason] = 1
              else: r.reason_suspected[reason] += 1
              r.circ_suspected+= 1
              if reason not in self.suspect_reasons:
                self.suspect_reasons[reason] = SuspectRouterList(reason)
              self.suspect_reasons[reason].add_r(r)
    PathBuilder.circ_status_event(self, c)

  def count_stream_reason_failed(self, s, reason):
    "Count the routers involved in a failure"
    # Update failed count,reason_failed for exit
    r = self.circuits[s.circ_id].exit
    if not reason in r.reason_failed: r.reason_failed[reason] = 1
    else: r.reason_failed[reason]+=1
    r.strm_failed += 1
    if reason not in self.failed_reasons:
      self.failed_reasons[reason] = FailedRouterList(reason)
    self.failed_reasons[reason].add_r(r)

  def count_stream_suspects(self, s, lreason, reason):
    "Count the routers 'suspected' of being involved in a failure"
    if lreason in ("TIMEOUT", "INTERNAL", "TORPROTOCOL" "DESTROY"):
      for r in self.circuits[s.circ_id].path[:-1]:
        r.strm_suspected += 1
        if not reason in r.reason_suspected:
          r.reason_suspected[reason] = 1
        else: r.reason_suspected[reason]+=1
        if reason not in self.suspect_reasons:
          self.suspect_reasons[reason] = SuspectRouterList(reason)
        self.suspect_reasons[reason].add_r(r)
    else:
      for r in self.circuits[s.circ_id].path[:-1]:
        r.strm_uncounted += 1
  
  def stream_status_event(self, s):
    if s.strm_id in self.streams and not self.streams[s.strm_id].ignored:
      # TODO: Hrmm, consider making this sane in TorCtl.
      if s.reason: lreason = s.reason
      else: lreason = "NONE"
      if s.remote_reason: rreason = s.remote_reason
      else: rreason = "NONE"
      reason = s.event_name+":"+s.status+":"+lreason+":"+rreason+":"+self.streams[s.strm_id].kind
      circ = self.streams[s.strm_id].circ
      if not circ: circ = self.streams[s.strm_id].pending_circ
      if (s.status in ("DETACHED", "FAILED", "CLOSED", "SUCCEEDED")
          and not s.circ_id):
        # XXX: REMAPs can do this (normal). Also REASON=DESTROY (bug?)
        if circ:
          plog("INFO", "Stream "+s.status+" of "+str(s.strm_id)+" gave circ 0.  Resetting to stored circ id: "+str(circ.circ_id))
          s.circ_id = circ.circ_id
        #elif s.reason == "TIMEOUT" or s.reason == "EXITPOLICY":
        #  plog("NOTICE", "Stream "+str(s.strm_id)+" detached with "+s.reason)
        else:
          plog("WARN", "Stream "+str(s.strm_id)+" detached from no known circuit with reason: "+str(s.reason))
          PathBuilder.stream_status_event(self, s)
          return

      # Verify circ id matches stream.circ
      if s.status not in ("NEW", "NEWRESOLVE", "REMAP"):
        if s.circ_id and circ and circ.circ_id != s.circ_id:
          plog("WARN", str(s.strm_id) + " has mismatch of "
                +str(s.circ_id)+" v "+str(circ.circ_id))
        if s.circ_id and s.circ_id not in self.circuits:
          plog("NOTICE", "Unknown circuit "+str(s.circ_id)
                +" for stream "+str(s.strm_id))
          PathBuilder.stream_status_event(self, s)
          return
      
      if s.status == "DETACHED":
        if self.streams[s.strm_id].attached_at:
          plog("WARN", str(s.strm_id)+" detached after succeeded")
        # Update strm_chosen count
        self.strm_count += 1
        for r in self.circuits[s.circ_id].path: r.strm_chosen += 1
        self.strm_failed += 1
        self.count_stream_suspects(s, lreason, reason)
        self.count_stream_reason_failed(s, reason)
      elif s.status == "FAILED":
        # HACK. We get both failed and closed for the same stream,
        # with different reasons. Might as well record both, since they 
        # often differ.
        self.streams[s.strm_id].failed_reason = reason
      elif s.status == "CLOSED":
        # Always get both a closed and a failed.. 
        #   - Check if the circuit exists still
        # Update strm_chosen count
        self.strm_count += 1
        for r in self.circuits[s.circ_id].path: r.strm_chosen += 1

        if self.streams[s.strm_id].failed:
          reason = self.streams[s.strm_id].failed_reason+":"+lreason+":"+rreason

        self.count_stream_suspects(s, lreason, reason)
          
        r = self.circuits[s.circ_id].exit
        if (not self.streams[s.strm_id].failed
          and (lreason == "DONE" or (lreason == "END" and rreason == "DONE"))):
          r.strm_succeeded += 1

          # Update bw stats. XXX: Don't do this for resolve streams
          if self.streams[s.strm_id].attached_at:
            lifespan = self.streams[s.strm_id].lifespan(s.arrived_at)
            for r in self.streams[s.strm_id].circ.path:
              r.bwstats.add_bw(self.streams[s.strm_id].bytes_written+
                               self.streams[s.strm_id].bytes_read, lifespan)
  
        else:
          self.strm_failed += 1
          self.count_stream_reason_failed(s, reason)
    PathBuilder.stream_status_event(self, s)

  def _check_hibernation(self, r, now):
    if r.down:
      if not r.hibernated_at:
        r.hibernated_at = now
        r.total_active_uptime += now - r.became_active_at
      r.became_active_at = 0
    else:
      if not r.became_active_at:
        r.became_active_at = now
        r.total_hibernation_time += now - r.hibernated_at
      r.hibernated_at = 0

  def new_consensus_event(self, n):
    if self.track_ranks:
      # Record previous rank and history.
      for ns in n.nslist:
        if not ns.idhex in self.routers:
          continue
        r = self.routers[ns.idhex]
        r.bw_history.append(r.bw)
      for r in self.sorted_r:
        r.rank_history.append(r.list_rank)
    PathBuilder.new_consensus_event(self, n)
    now = n.arrived_at
    for ns in n.nslist:
      if not ns.idhex in self.routers: continue
      self._check_hibernation(self.routers[ns.idhex], now)

  def new_desc_event(self, d):
    if PathBuilder.new_desc_event(self, d):
      now = d.arrived_at
      for i in d.idlist:
        if not i in self.routers: continue
        self._check_hibernation(self.routers[i], now)
      
   
