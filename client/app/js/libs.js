angular.module("GLLibs", [])
.factory("sha256", function() {
  return window.sha256;
})
.factory("topojson", function() {
  return window.topojson;
});
