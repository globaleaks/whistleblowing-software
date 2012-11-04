# -*- coding: UTF-8
#   backend
#   *******
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>
#            Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#

"""
Here is the logic for creating a twisted service. In this part of the code we
do all the necessary high level wiring to make everything work together.
Specifically we create the cyclone web.Application from the API specification,
we create a TCPServer for it and setup logging.

We also set to kill the threadpool (the one used by Storm) when the application
shuts down.
"""
from twisted.internet import reactor

from twisted.application.service import Application
from twisted.application import internet

from cyclone import web

from globaleaks import db_threadpool, scheduler_threadpool
from apscheduler.scheduler import Scheduler
from globaleaks.jobs import *
# notification_sched, statistics_sched, tip_sched, delivery_sched, cleaning_sched, welcome_sched, digest_sched
from globaleaks.rest import api

from globaleaks.utils import log

log.debug("[D] %s %s " % (__file__, __name__), "backend.py")

application = Application('GLBackend')

# Initialize the web API event listener, handling all the synchronous operations
GLBackendAPIFactory = web.Application(api.spec, debug=True)
GLBackendAPI = internet.TCPServer(8082, GLBackendAPIFactory)
GLBackendAPI.setServiceParent(application)

# Initialize the asynchronous operation, scheduled in the system
# https://github.com/globaleaks/GLBackend/wiki/Asynchronous-and-synchronous-operations

GLAsynchronous = Scheduler()

# When the application boot, maybe because has been restarted. then, execute all the
# periodic operation by hand.

StatsSched = statistics_sched.APSStatistics()
StatsSched.force_execution(GLAsynchronous, seconds=10)
GLAsynchronous.add_interval_job(StatsSched.operation, StatsSched.get_node_delta() )

WelcomSched = welcome_sched.APSWelcome()
WelcomSched.force_execution(GLAsynchronous, seconds=15)
GLAsynchronous.add_interval_job(WelcomSched.operation, minutes=5)

TipSched = tip_sched.APSTip()
TipSched.force_execution(GLAsynchronous, seconds=20)
GLAsynchronous.add_interval_job(TipSched.operation, minutes=1)

# TODO - InputFilter processing, before considering a Folder safe, need
#        to be scheduler and then would be 'data available' for delivery

DeliverSched = delivery_sched.APSDelivery()
DeliverSched.force_execution(GLAsynchronous, seconds=25)
GLAsynchronous.add_interval_job(DeliverSched.operation, minutes=2)

NotifSched = notification_sched.APSNotification()
NotifSched.force_execution(GLAsynchronous, seconds=30)
GLAsynchronous.add_interval_job(NotifSched.operation, minutes=3)

CleanSched = cleaning_sched.APSCleaning()
CleanSched.force_execution(GLAsynchronous, seconds=35)
GLAsynchronous.add_interval_job(CleanSched.operation, hours=6)
# TODO not hours=6 but CleanSched.get_contexts_policies()

DigestSched = digest_sched.APSDigest()
GLAsynchronous.add_interval_job(DigestSched.operation, minutes=10)
# TODO not minutes=10 but DigestSched.get_context_policies()

# start the scheduler
GLAsynchronous.start()


"""
Not used approach - but I've fuckin' tried!

tip_schedule = tip.TipOps()
work_manager.add(tip_schedule)

delivery_schedule = delivery.DeliveryOps()
work_manager.add(delivery_schedule)

cleaning_schedule = cleaning.CleaningOps()
work_manager.add(cleaning_schedule)

statistics_schedule = statistics.StatisticsOps()
work_manager.add(statistics_schedule)

notification_schedule = notification.NotificationOps()
work_manager.add(notification_schedule)

To be removed
"""

# define exit behaviour
reactor.addSystemEventTrigger('after', 'shutdown', db_threadpool.stop)
reactor.addSystemEventTrigger('after', 'shutdown', scheduler_threadpool.stop)
