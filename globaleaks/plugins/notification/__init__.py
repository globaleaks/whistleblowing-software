__all__ = [ 'MailNotification' ]

from . import mail_plugin

# now is included like a module, but would be exported by the plugins,
# checking the Receiver.notification_type name (that is configured by
# /receiver/<secret_$ID>/options)
