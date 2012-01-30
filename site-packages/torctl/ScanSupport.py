#!/usr/bin/python
# Copyright 2009-2010 Mike Perry. See LICENSE file.
import PathSupport
import threading
import copy
import time
import shutil
import TorCtl

from TorUtil import plog

SQLSupport = None

# Note: be careful writing functions for this class. Remember that
# the PathBuilder has its own thread that it recieves events on
# independent from your thread that calls into here.
class ScanHandler(PathSupport.PathBuilder):
  def set_pct_rstr(self, percent_skip, percent_fast):
    def notlambda(sm):
      sm.percent_fast=percent_fast
      sm.percent_skip=percent_skip
    self.schedule_selmgr(notlambda)

  def reset_stats(self):
    def notlambda(this):
      this.reset()
    self.schedule_low_prio(notlambda)

  def commit(self):
    plog("INFO", "Scanner committing jobs...")
    cond = threading.Condition()
    def notlambda2(this):
      cond.acquire()
      this.run_all_jobs = False
      plog("INFO", "Commit done.")
      cond.notify()
      cond.release()

    def notlambda1(this):
      plog("INFO", "Committing jobs...")
      this.run_all_jobs = True
      self.schedule_low_prio(notlambda2)

    cond.acquire()
    self.schedule_immediate(notlambda1)

    cond.wait()
    cond.release()
    plog("INFO", "Scanner commit done.")

  def close_circuits(self):
    cond = threading.Condition()
    def notlambda(this):
      cond.acquire()
      this.close_all_circuits()
      cond.notify()
      cond.release()
    cond.acquire()
    self.schedule_low_prio(notlambda)
    cond.wait()
    cond.release()

  def close_streams(self, reason):
    cond = threading.Condition()
    plog("NOTICE", "Wedged Tor stream. Closing all streams")
    def notlambda(this):
      cond.acquire()
      this.close_all_streams(reason)
      cond.notify()
      cond.release()
    cond.acquire()
    self.schedule_low_prio(notlambda)
    cond.wait()
    cond.release()

  def new_exit(self):
    cond = threading.Condition()
    def notlambda(this):
      cond.acquire()
      this.new_nym = True
      if this.selmgr.bad_restrictions:
        plog("NOTICE", "Clearing bad restrictions with reconfigure..")
        this.selmgr.reconfigure(this.current_consensus())
      lines = this.c.sendAndRecv("SIGNAL CLEARDNSCACHE\r\n")
      for _,msg,more in lines:
        plog("DEBUG", msg)
      cond.notify()
      cond.release()
    cond.acquire()
    self.schedule_low_prio(notlambda)
    cond.wait()
    cond.release()

  def idhex_to_r(self, idhex):
    cond = threading.Condition()
    def notlambda(this):
      cond.acquire()
      if idhex in self.routers:
        cond._result = self.routers[idhex]
      else:
        cond._result = None
      cond.notify()
      cond.release()
    cond.acquire()
    self.schedule_low_prio(notlambda)
    cond.wait()
    cond.release()
    return cond._result

  def name_to_idhex(self, nick):
    cond = threading.Condition()
    def notlambda(this):
      cond.acquire()
      if nick in self.name_to_key:
        cond._result = self.name_to_key[nick]
      else:
        cond._result = None
      cond.notify()
      cond.release()
    cond.acquire()
    self.schedule_low_prio(notlambda)
    cond.wait()
    cond.release()
    return cond._result

  def rank_to_percent(self, rank):
    cond = threading.Condition()
    def notlambda(this):
      cond.acquire()
      cond._pct = (100.0*rank)/len(this.sorted_r) # lol moar haxx
      cond.notify()
      cond.release()
    cond.acquire()
    self.schedule_low_prio(notlambda)
    cond.wait()
    cond.release()
    return cond._pct

  def percent_to_rank(self, pct):
    cond = threading.Condition()
    def notlambda(this):
      cond.acquire()
      cond._rank = int(round((pct*len(this.sorted_r))/100.0,0)) # lol moar haxx
      cond.notify()
      cond.release()
    cond.acquire()
    self.schedule_low_prio(notlambda)
    cond.wait()
    cond.release()
    return cond._rank

  def get_exit_node(self):
    ret = copy.copy(self.last_exit) # GIL FTW
    if ret:
      plog("DEBUG", "Got last exit of "+ret.idhex)
    else:
      plog("DEBUG", "No last exit.")
    return ret

  def set_exit_node(self, arg):
    cond = threading.Condition()
    exit_name = arg
    plog("DEBUG", "Got Setexit: "+exit_name)
    def notlambda(sm):
      plog("DEBUG", "Job for setexit: "+exit_name)
      cond.acquire()
      sm.set_exit(exit_name)
      cond.notify()
      cond.release()
    cond.acquire()
    self.schedule_selmgr(notlambda)
    cond.wait()
    cond.release()

class SQLScanHandler(ScanHandler):
  def __init__(self, c, selmgr, RouterClass=TorCtl.Router,
               strm_selector=PathSupport.StreamSelector):
    # Only require sqlalchemy if we really need it.
    global SQLSupport
    if SQLSupport is None:
      import SQLSupport
    ScanHandler.__init__(self, c, selmgr, RouterClass, strm_selector)

  def attach_sql_listener(self, db_uri):
    plog("DEBUG", "Got sqlite: "+db_uri)
    SQLSupport.setup_db(db_uri, echo=False, drop=True)
    self.sql_consensus_listener = SQLSupport.ConsensusTrackerListener()
    self.add_event_listener(self.sql_consensus_listener)
    self.add_event_listener(SQLSupport.StreamListener())

  def write_sql_stats(self, rfilename=None, stats_filter=None):
    if not rfilename:
      rfilename="./data/stats/sql-"+time.strftime("20%y-%m-%d-%H:%M:%S")
    cond = threading.Condition()
    def notlambda(h):
      cond.acquire()
      SQLSupport.RouterStats.write_stats(file(rfilename, "w"),
                            0, 100, order_by=SQLSupport.RouterStats.sbw,
                            recompute=True, disp_clause=stats_filter)
      cond.notify()
      cond.release()
    cond.acquire()
    self.schedule_low_prio(notlambda)
    cond.wait()
    cond.release()

  def write_strm_bws(self, rfilename=None, slice_num=0, stats_filter=None):
    if not rfilename:
      rfilename="./data/stats/bws-"+time.strftime("20%y-%m-%d-%H:%M:%S")
    cond = threading.Condition()
    def notlambda(this):
      cond.acquire()
      f=file(rfilename, "w")
      f.write("slicenum="+str(slice_num)+"\n")
      SQLSupport.RouterStats.write_bws(f, 0, 100,
                            order_by=SQLSupport.RouterStats.sbw,
                            recompute=False, disp_clause=stats_filter)
      f.close()
      cond.notify()
      cond.release()
    cond.acquire()
    self.schedule_low_prio(notlambda)
    cond.wait()
    cond.release()

  def save_sql_file(self, sql_file, new_file):
    cond = threading.Condition()
    def notlambda(this):
      cond.acquire()
      SQLSupport.tc_session.close()
      try:
        shutil.copy(sql_file, new_file)
      except Exception,e:
        plog("WARN", "Error moving sql file: "+str(e))
      SQLSupport.reset_all()
      cond.notify()
      cond.release()
    cond.acquire()
    self.schedule_low_prio(notlambda)
    cond.wait()
    cond.release()

  def wait_for_consensus(self):
    cond = threading.Condition()
    def notlambda(this):
      if this.sql_consensus_listener.last_desc_at \
                 != SQLSupport.ConsensusTrackerListener.CONSENSUS_DONE:
        this.sql_consensus_listener.wait_for_signal = False
        plog("INFO", "Waiting on consensus result: "+str(this.run_all_jobs))
        this.schedule_low_prio(notlambda)
      else:
        cond.acquire()
        this.sql_consensus_listener.wait_for_signal = True
        cond.notify()
        cond.release()
    plog("DEBUG", "Checking for consensus")
    cond.acquire()
    self.schedule_low_prio(notlambda)
    cond.wait()
    cond.release()
    plog("INFO", "Consensus OK")


