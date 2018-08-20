describe('whistleblower navigate home page', function() {
  it('should see page properly internationalize', function() {
    browser.get('/#/?lang=en');
    expect(browser.isElementPresent(element(by.cssContainingText("div", "TEXT1_IT")))).toBe(false);
    expect(browser.isElementPresent(element(by.cssContainingText("div", "TEXT2_IT")))).toBe(false);
    expect(browser.isElementPresent(element(by.cssContainingText("div", "TEXT1_EN")))).toBe(true);
    expect(browser.isElementPresent(element(by.cssContainingText("div", "TEXT2_EN")))).toBe(true);

    browser.get('/#/?lang=it');
    expect(browser.isElementPresent(element(by.cssContainingText("div", "TEXT1_IT")))).toBe(true);
    expect(browser.isElementPresent(element(by.cssContainingText("div", "TEXT2_IT")))).toBe(true);
    expect(browser.isElementPresent(element(by.cssContainingText("div", "TEXT1_EN")))).toBe(false);
    expect(browser.isElementPresent(element(by.cssContainingText("div", "TEXT2_EN")))).toBe(false);
  });
});
