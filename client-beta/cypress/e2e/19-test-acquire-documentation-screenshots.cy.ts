// Convert the Protractor test to Cypress test
describe("acquire screenshots necessary for user documentation", () => {
  beforeEach(() => {
    // Perform the login action before each test
    cy.login_admin();
  });

  it("should navigate through some admin sections to collect screenshots", () => {
    // Home section
    cy.contains("a", "Home").first().click();
    cy.takeScreenshot("admin/home", 500);

    cy.contains("button", "Changelog").first().click();
    cy.takeScreenshot("admin/changelog", 500);

    cy.contains("button", "License").first().click();
    cy.takeScreenshot("admin/license", 500);

    cy.contains("a", "Settings").first().click();
    cy.takeScreenshot("admin/site_settings_main_configuration", 500);
    cy.get('#Content').takeScreenshot('admin/site_settings_logo_detail', 500, { capture: 'viewport' });

    cy.contains("button", "Files").first().click();
    cy.takeScreenshot("admin/site_settings_files", 500);

    cy.contains("button", "Languages").first().click();
    cy.takeScreenshot("admin/site_settings_languages", 500);
    cy.get('#Content').takeScreenshot('admin/site_settings_languages_detail', 500, { capture: 'viewport' });

    cy.contains("button", "Text customization").first().click();
    cy.takeScreenshot("admin/site_settings_text_customization", 500);

    cy.contains("button", "Advanced").first().click();
    cy.takeScreenshot("admin/advanced_settings", 500);

    cy.contains("a", "Users").first().click();
    cy.takeScreenshot("admin/users", 500);
    cy.contains("button", "Options").first().click();
    cy.takeScreenshot("admin/users_options", 500);

    cy.contains("a", "Questionnaires").first().click();
    cy.takeScreenshot("admin/questionnaires", 500);

    cy.contains("button", "Question templates").first().click();
    cy.takeScreenshot("admin/question_templates", 500);

    cy.contains("a", "Case management").first().click();
    cy.takeScreenshot("admin/report_statuses", 500);

    cy.contains("a", "Notifications").first().click();
    cy.takeScreenshot("admin/notification_settings", 500);
    cy.get('#Content').takeScreenshot('admin/notification_settings_detail', 500, { capture: 'viewport' });
    cy.contains("button", "Templates").first().click();
    cy.takeScreenshot("admin/notification_templates", 500);

    cy.contains("a", "Network").first().click();
    cy.takeScreenshot("admin/tor", 500);

    cy.contains("button", "HTTPS").first().click();
    cy.takeScreenshot("admin/https", 500);

    cy.contains("button", "Tor").first().click();
    cy.takeScreenshot("admin/https", 500);

    cy.contains("button", "Access control").first().click();
    cy.takeScreenshot("admin/access_control", 500);

    cy.contains("button", "URL redirects").first().click();
    cy.takeScreenshot("admin/url_redirects", 500);

    cy.contains("a", "Audit log").first().click();
    cy.takeScreenshot("admin/audit_log", 500);

    cy.contains('button', 'Users').click();
    cy.takeScreenshot("admin/audit_log_users", 500);

    cy.contains("button", "Reports").first().click();
    cy.takeScreenshot("admin/audit_log_reports", 500);

    cy.contains("button", "Scheduled jobs").first().click();
    cy.takeScreenshot("admin/audit_log_scheduled_jobs", 500);

    cy.logout();
  });
});
