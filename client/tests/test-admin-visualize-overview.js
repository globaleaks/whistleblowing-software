describe('verify navigation of admin overview sections', function() {
  it('should should navigate through overview sections', function() {
    browser.gl.utils.login_admin();

    element(by.cssContainingText("a", "System overview")).click();

    var pageContent = element(by.id("PageContent"));

    pageContent.element(by.cssContainingText("a", "Stats")).click();
    pageContent.element(by.cssContainingText("a", "Activities")).click();
    pageContent.element(by.cssContainingText("a", "Submissions")).click();
    pageContent.element(by.cssContainingText("a", "Users")).click();
    pageContent.element(by.cssContainingText("a", "Files")).click();
    pageContent.element(by.cssContainingText("a", "Anomalies")).click();
    pageContent.element(by.cssContainingText("a", "Scheduled jobs")).click();
  });
});
