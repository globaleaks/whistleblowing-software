
## Notification and Delivery modules specification

GLBackend supports extension in classes 'Notification' and 'Delivery', 
those classes are called in two time:

  * by the task handler, are executed for every receiver with a new Tip associated.

  * by the event handler, when a new module is enabled by the adminitrator,
    this operation may not be completed if the adminitrator does not provide
    right configuration to the module

Notification and Delivery behaviour is like abstract classes, they
required extension and implementation by overriding methods.

The methods requird to be implemented by modules are:

class NotificationImplementation(Notification):

    def notification_name():
        """
        This method return the notification name, need to be different
        for every implementation, and the name will be associated with
        receivers preferences and settings, therefore shall never be
        changed in a running node
        """

    def get_admin_opt():
        return ModuleAdminConfig
        """
        ModuleAdminConfig is described in REST-spec.md
        """
    def set_admin_opt(ModuleAdminConfig):
        """
        During the setup of the module, if the admin need fill options,
        in get_ is returned the field struct, and in set is verify and
        recorded.
        """

    def get_receiver_opt(ModuleDataStruct):
        """
        ModuleDataStruct is described in REST-spec.md
        """
    def set_receiver_opt():
        retur ModuleDataStruct
        """
        Same logic of admin_opt, but related for receiver specific 
        settings
        """

    def do_notify():
        """
        Called by the task handler, perform the notification
        """
    def get_log():
        """
        The log are collected in Notification superclass, and returned 
        to the called using this function. When returned are flushed 
        by memory, permitting a centralized handling of the log
        """

class DeliveryImplementation(Delivery):
    """
    Delivery superclass behaviour is equal to Notification
    """

    def delivery_name():

    def get_admin_opt():
        return ModuleAdminConfig
    def set_admin_opt(ModuleAdminConfig):

    def get_receiver_opt(ModuleDataStruct):
    def set_receiver_opt():
        retur ModuleDataStruct

    def do_delivery():
    def get_log():

## Storage modules specification

TODO
