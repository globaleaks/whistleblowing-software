from globaleaks.plugins.notification.password import data

# after hours throw in the cesspool in trying - in vain - how to do a Twister SMTPS client:
import smtplib

def GLBMailService(tip_gus, receiver_addr):

    x = smtplib.SMTP( data['host'], data['port'] )
    x.set_debuglevel(True)
    x.starttls()
    # x.login( data['username'], data['password'] ) # google do not support that ?
    x.ehlo()

    fromAddr = data['from']
    fromName = 'Debra Morgan'
    toName = 'Special Agent Landi'
    # ignored receiver_addr ATM
    toAddr = 'vecna@apps.globaleaks.org'

    subject = "new tip for you"
    body = "I'm Debra Morgan, Miami Omicide Tenent, and I approve this message\n\r%s" % tip_gus

    msg = ("From: <%s> %s\r\nTo: <%s> %s\r\n" % (fromName, fromAddr, toName, toAddr) )
    msg = msg + ("Subject: %s" % subject) + "\r\n\r\n" + body + "\r\n"

    x.sendmail(fromAddr, [ toAddr ] , msg)
    x.quit()


# class email(Notification)
# 
# plugin_type = "notification"
# plugin_name = "Twitter PM notification"
# plugin_description = $(localized pointer)
# 
# def get_admin_opt():
#   return pluginAdminDict

#
# def set_admin_opt(pluginAdminDict):
#
# def get_receiver_opt(pluginDataDict):

# def set_receiver_opt():
#   return pluginDataDict
#
# def do_notify():
#
# def get_log():
