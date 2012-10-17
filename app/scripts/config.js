/*
 * GLClient
 *
 * author: Arturo "hellais" Filastò <art@fuffa.org>
 * license: see LICENSE
 *
 */

// For any third party dependencies, like jQuery, place them in the libs folder.

// Configure loading modules from the lib directory,
// except for 'app' ones, which are in a sibling
// directory.
requirejs.config({
  baseUrl: "scripts/libs",
  waitSeconds: 20,
  paths: {
      app: "../../scripts/",
      libs: "/scripts/libs",
      utils: "../../scripts/utils",
      templates: "../../templates",
      requests: "../../scripts/requests",
      handlers: "../../scripts/handlers",
      messages: "../../scripts/messages",
      dummy: "../../scripts/dummy"
  }
});

define([
  "jquery",
  "utils/latenza",
  "bootstrap",
  "jquery.validate",
  "datatables"
],

function($, latenza) {
  console.log("In here dog");
  /*
  require("jquery.validate"); // XXX do we always need this?
  require("datatables"); // XXX fix this to be lazy loaded,
  */
  $(function () {

      // XXX move instantiation of this to main.js
      require(["app/routes"], function(r){
        r();
        //require(["app/uiNetwork"], function(u){u();});
      });
      $('#tor2web').hide();
  });

});

