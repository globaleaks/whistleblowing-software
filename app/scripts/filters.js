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
  filter('partition', function() {
    var part = function(arr, size) {
      if ( 0 === arr.length ) return [];
      return [ arr.slice( 0, size ) ].concat( part( arr.slice( size ), size) );
    };
    return part;
});
