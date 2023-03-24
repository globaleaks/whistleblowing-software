describe("verify navigation of admin sections", function() {
  it("should should navigate through admin sections", async function() {
    await browser.gl.utils.login_admin();

    await element.all(by.cssContainingText("a", "Home")).first().click();
    await browser.gl.utils.takeScreenshot("admin/home.png");
    await element.all(by.cssContainingText("a", "Changelog")).first().click();
    await browser.gl.utils.takeScreenshot("admin/changelog.png");
    await element.all(by.cssContainingText("a", "License")).first().click();
    await browser.gl.utils.takeScreenshot("admin/license.png");

    await element.all(by.cssContainingText("a", "Settings")).first().click();
    await browser.gl.utils.takeScreenshot("admin/site_settings_main_configuration.png");
    await browser.gl.utils.takeScreenshot("admin/site_settings_logo_detail.png", element(by.id("Content")));
    await element.all(by.cssContainingText("a", "Theme customization")).first().click();
    await browser.gl.utils.takeScreenshot("admin/site_settings_theme_customization.png");
    await element.all(by.cssContainingText("a", "Languages")).first().click();
    await browser.gl.utils.takeScreenshot("admin/site_settings_languages.png");
    await browser.gl.utils.takeScreenshot("admin/site_settings_languages_detail.png", element(by.id("Content")));
    await element.all(by.cssContainingText("a", "Text customization")).first().click();
    await browser.gl.utils.takeScreenshot("admin/site_settings_text_customization.png");
    await element.all(by.cssContainingText("a", "Advanced")).first().click();
    await browser.gl.utils.takeScreenshot("admin/advanced_settings.png");

    await element.all(by.cssContainingText("a", "Users")).first().click();
    await browser.gl.utils.takeScreenshot("admin/users.png");

    await element.all(by.cssContainingText("a", "Questionnaires")).first().click();
    await browser.gl.utils.takeScreenshot("admin/questionnaires.png");

    await element.all(by.cssContainingText("a", "Question templates")).first().click();
    await browser.gl.utils.takeScreenshot("admin/question_templates.png");

    await element.all(by.cssContainingText("a", "Channels")).first().click();
    await browser.gl.utils.takeScreenshot("admin/contexts.png");

    await element.all(by.cssContainingText("a", "Case management")).first().click();
    await browser.gl.utils.takeScreenshot("admin/report_statuses.png");

    await element.all(by.cssContainingText("a", "Notifications")).first().click();
    await element.all(by.cssContainingText("a", "Settings")).last().click();
    await browser.gl.utils.takeScreenshot("admin/notification_settings.png");
    await browser.gl.utils.takeScreenshot("admin/notification_settings_detail.png", element(by.id("Content")));
    await element.all(by.cssContainingText("a", "Templates")).first().click();
    await browser.gl.utils.takeScreenshot("admin/notification_templates.png");

    await element.all(by.cssContainingText("a", "Network")).first().click();
    await element.all(by.cssContainingText("a", "Tor")).first().click();
    await browser.gl.utils.takeScreenshot("admin/tor.png");
    await element.all(by.cssContainingText("a", "HTTPS")).first().click();
    await browser.gl.utils.takeScreenshot("admin/https.png");
    await element.all(by.cssContainingText("a", "Access control")).first().click();
    await browser.gl.utils.takeScreenshot("admin/access_control.png");
    await element.all(by.cssContainingText("a", "URL redirects")).first().click();
    await browser.gl.utils.takeScreenshot("admin/url_redirects.png");

    await element.all(by.cssContainingText("a", "Audit log")).first().click();
    await browser.gl.utils.takeScreenshot("admin/audit_log.png");
    await element.all(by.cssContainingText("a", "Users")).get(1).click();
    await browser.gl.utils.takeScreenshot("admin/audit_log_users.png");
    await element.all(by.cssContainingText("a", "Reports")).first().click();
    await browser.gl.utils.takeScreenshot("admin/audit_log_reports.png");
    await element.all(by.cssContainingText("a", "Scheduled jobs")).first().click();
    await browser.gl.utils.takeScreenshot("admin/audit_log_scheduled_jobs.png");

    await browser.gl.utils.logout();
  });
});
