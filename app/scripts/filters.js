// In here go angular.js filters
// http://docs.angularjs.org/guide/dev_guide.templates.filters.creating_filters
//
angular.module('GLClientFilters', []).
  filter('required-filter', function() {
    return function(input) {
      if (input) {
        return 'required';
      } else {
        return '';
      }
    }
}).
  filter('field-type-filter', function() {
    return function(input) {
      if (input == "string") {
        return 'text';
      } else {
        return input;
      }
    }
}).
  filter('translate', ['Translations', function(Translations) {
    return function(input) {
      var hash = md5(input);
      if ( hash in Translations ){
        return Translations[hash][$.cookie('language')];
      } else {
        return input;
      }
    }
}]);
