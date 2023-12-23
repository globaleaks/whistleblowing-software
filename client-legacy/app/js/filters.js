GL.filter("weekNumber", function() {
  return function (value) {
    var date = new Date(value);
    date.setHours(0, 0, 0, 0);
    // Thursday in current week decides the year.
    date.setDate(date.getDate() + 3 - (date.getDay() + 6) % 7);
    // January 4 is always in week 1.
    var week1 = new Date(date.getFullYear(), 0, 4);
    // Adjust to Thursday in week 1 and count number of weeks from date to week1.
    return 1 + Math.round(((date.getTime() - week1.getTime()) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
  };
}).
filter("expirationDate", function() {
  return function(date, ttl) {
    if (angular.isUndefined(date)) {
      return undefined;
    }

    var e = new Date(new Date(date).getTime());
    e.setUTCHours(0, 0, 0, 0);
    e.setDate(ttl + 1);
    return e;
  };
}).
filter("split", function() {
  return function(input, splitChar, splitIndex) {
    return input.split(splitChar)[splitIndex];
  };
}).
filter("highlightSafe", function() {
  function escapeHtml( text) {
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function escapeRegexp(queryToEscape) {
    return ("" + queryToEscape).replace(/([.?*+^$[\]\\(){}|-])/g, "\\$1");
  }

  return function(matchItem, query) {
    var matchHtml = escapeHtml("" + matchItem);
    return query && matchItem ? matchHtml.replace(new RegExp(escapeRegexp(query), "gi"), "<span class=\"ui-select-highlight\">$&</span>") : matchHtml;
  };
});
