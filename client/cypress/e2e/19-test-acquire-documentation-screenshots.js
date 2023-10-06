// Convert the Protractor test to Cypress test
describe("acquire screenshots necessary for user documentation", () => {
  beforeEach(() => {
    // Perform the login action before each test
    cy.login_admin();
  });

  it("should navigate through some admin sections to collect screenshots", () => {
    // Home section
    cy.contains("a", "Home").first().click();
    cy.takeScreenshot("admin/home");

    cy.contains("a", "Changelog").first().click();
    cy.takeScreenshot("admin/changelog");

    cy.contains("a", "License").first().click();
    cy.takeScreenshot("admin/license");

    cy.contains("a", "Settings").first().click();
    cy.takeScreenshot("admin/site_settings_main_configuration");
    cy.get('#Content').takeScreenshot('admin/site_settings_logo_detail', { capture: 'viewport' });

    cy.contains("a", "Files").first().click();
    cy.takeScreenshot("admin/site_settings_files");

    cy.contains("a", "Languages").first().click();
    cy.takeScreenshot("admin/site_settings_languages");
    cy.get('#Content').takeScreenshot('admin/site_settings_languages_detail', { capture: 'viewport' });

    cy.contains("a", "Text customization").first().click();
    cy.takeScreenshot("admin/site_settings_text_customization");

    cy.contains("a", "Advanced").first().click();
    cy.takeScreenshot("admin/advanced_settings");

    cy.contains("a", "Users").first().click();
    cy.takeScreenshot("admin/users");
    cy.contains("a", "Options").first().click();
    cy.takeScreenshot("admin/users_options");

    cy.contains("a", "Questionnaires").first().click();
    cy.takeScreenshot("admin/questionnaires");

    cy.contains("a", "Question templates").first().click();
    cy.takeScreenshot("admin/question_templates");

    cy.contains("a", "Case management").first().click();
    cy.takeScreenshot("admin/report_statuses");

    cy.contains("a", "Notifications").first().click();
    cy.takeScreenshot("admin/notification_settings");
    cy.get('#Content').takeScreenshot('admin/notification_settings_detail', { capture: 'viewport' });
    cy.contains("a", "Templates").first().click();
    cy.takeScreenshot("admin/notification_templates");

    cy.contains("a", "Network").first().click();
    cy.takeScreenshot("admin/tor");

    cy.contains("a", "HTTPS").first().click();
    cy.takeScreenshot("admin/https");

    cy.contains("a", "Tor").first().click();
    cy.takeScreenshot("admin/tor");

    cy.contains("a", "Access control").first().click();
    cy.takeScreenshot("admin/access_control");

    cy.contains("a", "URL redirects").first().click();
    cy.takeScreenshot("admin/url_redirects");

    cy.contains("a", "Audit log").first().click();
    cy.takeScreenshot("admin/audit_log");

    cy.contains('a.nav-link', 'Users').click();
    cy.takeScreenshot("admin/audit_log_users");

    cy.contains("a", "Reports").first().click();
    cy.takeScreenshot("admin/audit_log_reports");

    cy.contains("a", "Scheduled jobs").first().click();
    cy.takeScreenshot("admin/audit_log_scheduled_jobs");

    cy.logout();
  });
});
