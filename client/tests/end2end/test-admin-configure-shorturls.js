describe('configure short urls', function() {
  it('should should be able to configure short urls', function() {
    for (var i = 0; i < 3; i++) {
      element(by.cssContainingText("a", "URL shortener")).click();
      element(by.model('new_shorturl.shorturl')).sendKeys('shorturl');
      element(by.model('new_shorturl.longurl')).sendKeys('longurl');
      element(by.cssContainingText("button", "Add")).click();
      element(by.cssContainingText("button", "Delete")).click();
    }
  });
});
