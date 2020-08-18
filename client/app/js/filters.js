angular.module("GLFilters", []).
  filter("weekNumber", function() {
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
  filter("anomalyToString", function() {
    return function (anomaly) {
      var anomalies = {
        "completed_submissions": "Completed submissions",
        "failed_logins": "Failed logins",
        "successful_logins": "Successful logins"
      };

      return anomalies[anomaly];
    };
  }).
  filter("split", function() {
    return function(input, splitChar, splitIndex) {
      return input.split(splitChar)[splitIndex];
    };
  });
