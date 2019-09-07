describe("admin configure languages", function() {
  it("should configure languages", function() {
    // Enable german and italian and then test the language selector
    browser.setLocation("admin/content");
    element(by.cssContainingText("a", "Languages")).click();

    var enableLanguage = function(language) {
      var button = element(by.model("selected.value"));
      var input = button.element(by.css('.ui-select-search'));

      element(by.className("add-language-btn")).click();
      button.click();
      input.sendKeys(language);
      element.all(by.css('.ui-select-choices-row-inner span')).first().click();
    };

    enableLanguage("Deutsch");
    enableLanguage("Italiano");

    element.all(by.cssContainingText("button", "Save")).get(1).click();

    element(by.cssContainingText("a", "Languages")).click();

    element.all(by.cssContainingText("a", "Deutsch")).get(0).click();

    expect(browser.isElementPresent(element(by.cssContainingText("a", "Site settings")))).toBe(false);
    expect(browser.isElementPresent(element(by.cssContainingText("a", "Seiteneinstellungen")))).toBe(true);

    element.all(by.cssContainingText("a", "Italiano")).get(0).click();

    expect(browser.isElementPresent(element(by.cssContainingText("a", "Seiteneinstellungen")))).toBe(false);
    expect(browser.isElementPresent(element(by.cssContainingText("a", "Impostazioni sito")))).toBe(true);

    element.all(by.cssContainingText("a", "English")).get(0).click();

    expect(browser.isElementPresent(element(by.cssContainingText("a", "Impostazioni sito")))).toBe(false);
    expect(browser.isElementPresent(element(by.cssContainingText("a", "Site settings")))).toBe(true);
  });

  it("should configure default language", function() {
    // Set the default as german
    browser.setLocation("admin/content");
    element(by.cssContainingText("a", "Languages")).click();

    element.all(by.css(".non-default-language")).get(0).click();
    element.all(by.cssContainingText("button", "Save")).get(1).click();

    // Verify that the default is set to german
    browser.setLocation("admin/content");
    element(by.cssContainingText("a", "Languages")).click();
    expect(element(by.model("admin.node.default_language")).getAttribute("value")).toEqual("de");

    // Switch the default to english and disable german
    element.all(by.css(".non-default-language")).get(0).click();

    element.all(by.css(".remove-lang-btn")).get(0).click();

    element.all(by.cssContainingText("button", "Save")).get(1).click();

    // Verify that the new default is set again to english that is the first language among en/it
    browser.setLocation("admin/content");
    element(by.cssContainingText("a", "Languages")).click();
    expect(element(by.model("admin.node.default_language")).getAttribute("value")).toEqual("en");

    element.all(by.cssContainingText("button", "Save")).get(1).click();
  });
});
