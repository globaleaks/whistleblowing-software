// In here go angular.js filters
// http://docs.angularjs.org/guide/dev_guide.templates.filters.creating_filters
//
angular.module('GLClientFilters', [])
  .filter('range', function() {
    return function(val, range) {
      range = parseInt(range);
      for (var i=0; i<range; i++)
        val.push(i);
      return val;
    };
}).
  filter('trimTo', function() {
    return function (value, max, wordwise, tail) {
        if (!value) return '';

        max = parseInt(max, 10);
        if (!max) return value;
        if (value.length <= max) return value;

        value = value.substr(0, max);
        if (wordwise) {
            var lastspace = value.lastIndexOf(' ');
            if (lastspace != -1) {
                value = value.substr(0, lastspace);
            }
        }

        return value + (tail || ' …');
    };
}).
  filter('prettyBytes', function() {
    return function (bytes) {
        var ret;
        if      (bytes>=1000000000) {ret='' + Math.floor(bytes/1000000000) + 'GB';}
        else if (bytes>=1000000)    {ret='' + Math.floor(bytes/1000000) + 'MB';}
        else                        {ret='' + Math.floor(bytes/1000) + 'KB';}

        return ret;
    }
}).
  filter('weekNumber', function() {
    return function (value) {
      var date = new Date(value);
      date.setHours(0, 0, 0, 0);
      // Thursday in current week decides the year.
      date.setDate(date.getDate() + 3 - (date.getDay() + 6) % 7);
      // January 4 is always in week 1.
      var week1 = new Date(date.getFullYear(), 0, 4);
      // Adjust to Thursday in week 1 and count number of weeks from date to week1.
      return 1 + Math.round(((date.getTime() - week1.getTime()) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
    }
});
