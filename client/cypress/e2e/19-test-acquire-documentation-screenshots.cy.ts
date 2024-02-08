describe("acquire screenshots necessary for user documentation", () => {
  beforeEach(() => {
    cy.login_admin();
  });

  it("should navigate through some admin sections to collect screenshots", () => {
    // Home section
    cy.contains("a", "Home").first().click();
    cy.takeScreenshot("admin/home", 0);

    cy.contains("button", "Changelog").first().click();
    cy.takeScreenshot("admin/changelog");

    cy.contains("button", "License").first().click();
    cy.takeScreenshot("admin/license");

    cy.contains("a", "Settings").first().click();
    cy.takeScreenshot("admin/site_settings_main_configuration");
    cy.get('#Content').takeScreenshot('admin/site_settings_logo_detail', { capture: 'viewport' });

    cy.contains("button", "Files").first().click();
    cy.takeScreenshot("admin/site_settings_files");

    cy.contains("button", "Languages").first().click();
    cy.takeScreenshot("admin/site_settings_languages");
    cy.get('#Content').takeScreenshot('admin/site_settings_languages_detail', { capture: 'viewport' });

    cy.contains("button", "Text customization").first().click();
    cy.takeScreenshot("admin/site_settings_text_customization");

    cy.contains("button", "Advanced").first().click();
    cy.takeScreenshot("admin/advanced_settings");

    cy.contains("a", "Users").first().click();
    cy.takeScreenshot("admin/users");
    cy.contains("button", "Options").first().click();
    cy.takeScreenshot("admin/users_options");

    cy.contains("a", "Questionnaires").first().click();
    cy.takeScreenshot("admin/questionnaires");

    cy.contains("button", "Question templates").first().click();
    cy.takeScreenshot("admin/question_templates");

    cy.contains("a", "Case management").first().click();
    cy.takeScreenshot("admin/report_statuses");

    cy.contains("a", "Notifications").first().click();
    cy.takeScreenshot("admin/notification_settings");
    cy.get('#Content').takeScreenshot('admin/notification_settings_detail', { capture: 'viewport' });
    cy.contains("button", "Templates").first().click();
    cy.takeScreenshot("admin/notification_templates");

    cy.contains("a", "Network").first().click();
    cy.takeScreenshot("admin/tor");

    cy.contains("button", "HTTPS").first().click();
    cy.takeScreenshot("admin/https");

    cy.contains("button", "Tor").first().click();
    cy.takeScreenshot("admin/https");

    cy.contains("button", "Access control").first().click();
    cy.takeScreenshot("admin/access_control");

    cy.contains("button", "URL redirects").first().click();
    cy.takeScreenshot("admin/url_redirects");

    cy.contains("a", "Audit log").first().click();
    cy.takeScreenshot("admin/audit_log");

    cy.contains('button', 'Users').click();
    cy.takeScreenshot("admin/audit_log_users");

    cy.contains("button", "Reports").first().click();
    cy.takeScreenshot("admin/audit_log_reports");

    cy.contains("button", "Scheduled jobs").first().click();
    cy.takeScreenshot("admin/audit_log_scheduled_jobs");

    cy.logout();
  });
});
