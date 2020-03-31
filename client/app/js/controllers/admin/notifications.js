GLClient.
controller("AdminMailCtrl", ["$scope", "$http", "AdminNotificationResource",
  function($scope, $http, AdminNotificationResource) {

  $scope.text_templates = [
    "account_activation_mail_template",
    "account_activation_mail_title",
    "activation_mail_template",
    "activation_mail_title",
    "admin_anomaly_activities",
    "admin_anomaly_disk_high",
    "admin_anomaly_disk_low",
    "admin_anomaly_mail_template",
    "admin_anomaly_mail_title",
    "admin_pgp_alert_mail_template",
    "admin_pgp_alert_mail_title",
    "admin_signup_alert_mail_template",
    "admin_signup_alert_mail_title",
    "admin_test_mail_template",
    "admin_test_mail_title",
    "comment_mail_template",
    "comment_mail_title",
    "email_validation_mail_template",
    "email_validation_mail_title",
    "export_message_recipient",
    "export_message_whistleblower",
    "export_template",
    "file_mail_template",
    "file_mail_title",
    "https_certificate_expiration_mail_template",
    "https_certificate_expiration_mail_title",
    "https_certificate_renewal_failure_mail_template",
    "https_certificate_renewal_failure_mail_title",
    "identity_access_authorized_mail_template",
    "identity_access_authorized_mail_title",
    "identity_access_denied_mail_template",
    "identity_access_denied_mail_title",
    "identity_access_request_mail_template",
    "identity_access_request_mail_title",
    "identity_provided_mail_template",
    "identity_provided_mail_title",
    "message_mail_template",
    "message_mail_title",
    "password_reset_complete_mail_template",
    "password_reset_complete_mail_title",
    "password_reset_validation_mail_template",
    "password_reset_validation_mail_title",
    "pgp_alert_mail_template",
    "pgp_alert_mail_title",
    "signup_mail_template",
    "signup_mail_title",
    "software_update_available_mail_template",
    "software_update_available_mail_title",
    "tip_expiration_summary_mail_template",
    "tip_expiration_summary_mail_title",
    "tip_mail_template",
    "tip_mail_title",
    "user_credentials"
  ];

  $scope.tabs = [
    {
      title:"Main configuration",
      template:"views/admin/notifications/tab1.html"
    },
    {
      title:"Notification templates",
      template:"views/admin/notifications/tab2.html"
    }
  ];

  var sendTestMail = function() {
    var req = {
      "operation": "test_mail",
      "args": {}
    };

    return $http({method: "PUT", url: "admin/config", data: req});
  };

  $scope.resetSMTPConfiguration = function() {
    $scope.resources.notification.smtp_server = "mail.globaleaks.org";
    $scope.resources.notification.smtp_port = 9267;
    $scope.resources.notification.smtp_username = "globaleaks";
    $scope.resources.notification.smtp_password = "globaleaks";
    $scope.resources.notification.smtp_source_email = "notification@mail.globaleaks.org";
    $scope.resources.notification.smtp_security = "TLS";
    $scope.resources.notification.smtp_authentication = true;

    $scope.Utils.update($scope.resources.notification);
  };

  $scope.updateThenTestMail = function() {
    AdminNotificationResource.update($scope.resources.notification)
    .$promise.then(function() { return sendTestMail(); }, function() { });
  };
}]);
