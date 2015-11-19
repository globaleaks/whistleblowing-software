exports.waitUntilReady = function (elm) {
   browser.wait(function () {
      return elm.isPresent();
   }, 1000);
   browser.wait(function () {
      return elm.isDisplayed();
   }, 1000);
};
