/*
 * GLClient
 *
 * author: Arturo "hellais" Filastò <art@fuffa.org>
 * license: see LICENSE
 *
 */

define([
  "jquery",
  "utils/latenza",
  "app/uiNetwork",
  "jquery.validate", // XXX do we always need this?
  "bootstrap",
  "datatables", // XXX fix this to be lazy loaded,
],

function($, latenza, uiNetwork) {
  console.log("In here dog");
  $(function () {
      require("app/routes")();
      // XXX move instantiation of this to main.js
      uiNetwork();
      $('#tor2web').hide();
  });

});
