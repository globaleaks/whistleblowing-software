# -*- encoding: utf-8 -*-

"""
  Changes

    Stats is removed and forget, the past results are throw away.
    WeekStats is add (and replace Stats table),
    Anomalies is add

"""

from storm.locals import Pickle, Int, Bool, Pickle, Unicode, DateTime
import sys
from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model
from globaleaks.db.datainit import opportunistic_appdata_init


class Replacer1415(TableReplacer):

    def migrate_Node(self):
        """
        Opportunity: we can split the /node section associated with the text
                and the /node composed by other information.
        """
        print "%s Node migration assistant: (checking that admin has email configured)" % self.std_fancy

        old_node = self.store_old.find(self.get_right_model("Node", 14)).one()
        new_node = self.get_right_model("Node", 15)()

        for k, v in new_node._storm_columns.iteritems():

            if v.name == 'email':
                old_email = getattr(old_node, v.name)
                if not old_email or len(old_email):
                    print "In the next release is mandatory have an email address associated"
                    print "The Node Admin will receive Alert email if anomalous activity are detected"
                    print "lest email empty abort DB migration"
                    print "\nPlease enter email address:",
                    newmail = sys.stdin.readline()
                    setattr(new_node, v.name, unicode(newmail) )

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)
        self.store_new.commit()

