## Plugins directory 

https://github.com/globaleaks/GLBackend/wiki/Plugins

## Shared elements between plugins

    self.plugin_name
    self.plugin_description
    self.admin_fields
    self.receiver_fields

    def validate_admin_opt(self, pushed_af)
    def validate_receiver_opt(self, admin_fields, receiver_fields)


### Notification

    def digest_check(self, settings, stored_data, new_data)
    def do_notify(self, settings, stored_data)

