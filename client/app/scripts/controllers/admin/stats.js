GLClient.controller('StatisticsCtrl', ['$scope', '$filter', 'Node', 'StatsCollection',
  function($scope, $filter, Node, StatsCollection) {

    var margin = { top: 50, right: 0, bottom: 100, left: 30 },
      width = 960 - margin.left - margin.right,
      height = 430 - margin.top - margin.bottom,
      gridSize = Math.floor(width / 24),
      legendElementWidth = gridSize*2,
      buckets = 9,
      colors = ["#ffffd9","#edf8b1","#c7e9b4","#7fcdbb","#41b6c4","#1d91c0","#225ea8","#253494","#081d58"],
      days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
      times = ["1am", "2am", "3am", "4am", "5am", "6am", "7am", "8am", "9am", "10am", "11am", "12am", "1pm", "2pm", "3pm", "4pm", "5pm", "6pm", "7pm", "8pm", "9pm", "10pm", "11pm", "12pm"];

    /* 2014-11-09T13:38:22.707125Z  with [:-8] */
    var parseISODate = d3.time.format("%Y-%m-%dT%H:%M:%S").parse;

    var show_data = function(data) {

      /*
      {
          "hour": 19,
          "day": 6,
          "week": 46,
          "year": 2014
          "summary": {
              "login_failure": 28
          },
          "freemegabytes": 5627
          "valid": 0
      },
      valid is a status flag:
          A) 0 means that data is meaningful
          B) -1 missing result: node shut down
          C) -2 future hour, we can't have data
          D) -3 current hour
      */

      data.forEach(function(d) {

          d.week =+d.week;
          d.year =+d.year;
          d.day =+ d.day;
          d.hour =+ d.hour;

          if(d.summary['logins_failed']) { d.logins_failed = +d.summary['logins_failure']; } else {d.logins_failed = 0 }
          d.value += d.logins_failed;
          if(d.summary['logins_successful']) { d.logins_successful = +d.summary['logins_successful']; } else { d.logins_successful = 0 }
          d.value += d.logins_successful;
          if(d.summary['submissions_started']) { d.submissions_started = +d.summary['submissions_started']; } else { d.submissions_started = 0 }
          d.value = d.submissions_started;
          if(d.summary['submissions_completed']) { d.submissions_completed = +d.summary['submissions_completed']; } else { d.submissions_completed = 0 }
          d.value += d.submissions_completed;
          if(d.summary['uploaded_files']) { d.uploaded_files = +d.summary['uploaded_files']; } else { d.uploaded_files = 0 }
          d.value = d.uploaded_files;
          if(d.summary['wb_comments']) { d.wb_comments = +d.summary['wb_comments']; } else { d.wb_comments = 0 }
          d.value += d.wb_comments;
          if(d.summary['wb_messages']) { d.wb_messages = +d.summary['wb_messages']; } else { d.wb_messages = 0 }
          d.value += d.wb_messages;
          if(d.summary['receiver_comments']) { d.receiver_comments = +d.summary['receiver_comments']; } else { d.receiver_comments = 0 }
          d.value += d.receiver_comments;
          if(d.summary['receiver_messages']) { d.receiver_messages = +d.summary['receiver_messages']; } else { d.receiver_messages = 0 }
          d.value += d.receiver_messages;

      });

      var colorScale = d3.scale.quantile()
          .domain([0, buckets - 1, d3.max(data, function (d) { return d.value; })])
          .range(colors);

      d3.selectAll("#chart > *").remove();

      var svg = d3.select("#chart").append("svg")
          .attr("width", width + margin.left + margin.right)
          .attr("height", height + margin.top + margin.bottom)
          .append("g")
          .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

      var dayLabels = svg.selectAll(".dayLabel")
          .data(days)
          .enter().append("text")
          .text(function (d) { return d; })
          .attr("x", 0)
          .attr("y", function (d, i) { return i * gridSize; })
          .style("text-anchor", "end")
          .attr("transform", "translate(-6," + gridSize / 1.5 + ")")
          .attr("class", function (d, i) { return ((i >= 0 && i <= 4) ? "dayLabel mono axis axis-workweek" : "dayLabel mono axis"); });

      var timeLabels = svg.selectAll(".timeLabel")
          .data(times)
          .enter().append("text")
          .text(function(d) { return d; })
          .attr("x", function(d, i) { return i * gridSize; })
          .attr("y", 0)
          .style("text-anchor", "middle")
          .attr("transform", "translate(" + gridSize / 2 + ", -6)")
          .attr("class", function(d, i) { return ((i >= 7 && i <= 16) ? "timeLabel mono axis axis-worktime" : "timeLabel mono axis"); });

      var heatMap = svg.selectAll(".hour")
          .data(data)
          .enter().append("rect")
          .attr("x", function(d) { return (d.hour - 1) * gridSize; })
          .attr("y", function(d) { return (d.day - 1) * gridSize; })
          .attr("rx", 4)
          .attr("ry", 4)
          .attr("class", "hour bordered")
          .attr("width", gridSize)
          .attr("height", gridSize)
          .style("fill", function(d) {
              return colors[0]
          });

      heatMap.transition().duration(1000)
          .style("fill", function(d) {
              if (d.valid == -1) {
                  return '#FFF';
              }
              if (d.valid == -2) {
                  return '#000';
              }
              if (d.valid == -3) {
                  return 'red';
              }
              return colorScale(d.value);
          });

      heatMap.append("title").text(function(d) {
          // if strings are updated here remember to update client/translation.html to push them on transifex
          if (d.valid == -1) {
              return $filter('translate')('Missing data') + ':\n\t' + $filter('translate')('no stats available for the future.');
          } else if (d.valid == -2) {
              return $filter('translate')('Missing data') + ':\n\t' + $filter('translate')('in this hour the node was off.');
          } else if (d.valid == -3) {
              return $filter('translate')('Missing data') + ':\n\t' + $filter('translate')('no stats available for current hour; check activities page.');
          } else {
              return (
                $filter('translate')('Failed logins') + ': ' + d.logins_failed + '\n' +
                $filter('translate')('Successful logins') + ': ' + d.logins_successful + '\n' +
                $filter('translate')('Started submissions') + ' : ' + d.submissions_started + '\n' +
                $filter('translate')('Completed submissions') + ' : ' + d.submissions_completed + '\n' +
                $filter('translate')('Uploaded files') + ' : ' + d.uploaded_files + '\n' +
                $filter('translate')('Whistleblower Comments') + ': ' + d.wb_comments + '\n' +
                $filter('translate')('Whistleblower Message') + ': ' + d.wb_messages + '\n' +
                $filter('translate')('Receiver comments') + ': ' + d.receiver_comments + '\n' +
                $filter('translate')('Receiver messages') + ': ' + d.receiver_messages + '\n' +
                $filter('translate')('Free megabytes') + ': ' + d.freemegabytes + '\n'
              );
          }
      });

      var legend = svg.selectAll(".legend")
          .data([0].concat(colorScale.quantiles()), function(d) { return d; })
          .enter().append("g")
          .attr("class", "legend");

      legend.append("rect")
          .attr("x", function(d, i) { return legendElementWidth * i; })
          .attr("y", height)
          .attr("width", legendElementWidth)
          .attr("height", gridSize / 2)
          .style("fill", function(d, i) {
              return colors[i];
          });

      legend.append("text")
         .attr("class", "mono")
         .text(function(d) { return "≥ " + Math.round(d); })
         .attr("x", function(d, i) { return legendElementWidth * i; })
         .attr("y", height + gridSize);
    };

    $scope.stats = StatsCollection.query(function(stats) {
      show_data(stats);
    });

}]);

GLClient.controller('AnomaliesCtrl', ['$scope', 'Node', 'AnomaliesHistCollection',
  function($scope, Node, AnomaliesHistCollection) {

    $scope.showLevel = true;
    $scope.hanomalies = AnomaliesHistCollection.query();
}]);

GLClient.controller('ActivitiesCtrl', ['$scope', 'Node', 'ActivitiesCollection', 'AnomaliesCollection',
  function($scope, Node, ActivitiesCollection, AnomaliesCollection) {

    $scope.anomalies = AnomaliesCollection.query();
    $scope.activities = ActivitiesCollection.query();
}]);
