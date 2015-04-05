GLClient.controller('StatisticsCtrl', ['$scope', '$filter', 'Node', 'StatsCollection',
  function($scope, $filter, Node, StatsCollection) {

    $scope.week_delta = 0;
    $scope.blob = {};

    var margin = { top: 50, right: 0, bottom: 100, left: 30 },
      width = 960 - margin.left - margin.right,
      height = 430 - margin.top - margin.bottom,
      gridSize = Math.floor(width / 24),
      legendElementWidth = gridSize*2,
      buckets = 9,
      colors = ["#ffffd9","#edf8b1","#c7e9b4","#7fcdbb","#41b6c4","#1d91c0","#225ea8","#253494","#081d58"],
      days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
      times = ["1am", "2am", "3am", "4am", "5am", "6am", "7am", "8am", "9am", "10am", "11am", "12am",
               "1pm", "2pm", "3pm", "4pm", "5pm", "6pm", "7pm", "8pm", "9pm", "10pm", "11pm", "12pm"];

    var show_data = function(data) {

      /*
      {
          "hour": 19,
          "day": 6,
          "summary": {
              "login_failure": 28
          },
          "free_disk_space": 5627
          "valid": 0
      },
      valid is a status flag:
          A) 0 means that data is meaningful
          B) -1 missing result: node shut down
          C) -2 future hour, we can't have data
          D) -3 current hour
      */

      data.forEach(function(d) {
          if (d.valid == 0) {
            d.summary.failed_logins = + d.summary.failed_logins ? d.summary.failed_logins : 0;
            d.summary.successful_logins = +d.summary.successful_logins ? d.summary.successful_logins : 0;
            d.summary.started_submissions = +d.summary.started_submissions ? d.summary.started_submissions : 0;
            d.summary.completed_submissions = +d.summary.completed_submissions ? d.summary.completed_submissions : 0;
            d.summary.uploaded_files =  +d.summary.uploaded_files ?  d.summary.uploaded_files : 0;
            d.summary.appended_files = +d.summary.appended_files ? d.summary.appended_files : 0;
            d.summary.wb_comments = +d.summary.wb_comments ? d.summary.wb_comments : 0;
            d.summary.wb_messages = +d.summary.wb_messages ? d.summary.wb_messages : 0;
            d.summary.receiver_comments = +d.summary.receiver_comments ? d.summary.receiver_comments : 0;
            d.summary.receiver_messages = +d.summary.receiver_messages ? d.summary.receiver_messages : 0;
            /* d.summary.homepage_access = +d.summary.homepage_access ? d.summary.homepage_access : 0; 
             * -- remind: disabled, not recorded in the d.value below */

            d.value = 0;
            d.value += d.summary.failed_logins;
            d.value += d.summary.successful_logins;
            d.value += d.summary.started_submissions;
            d.value += d.summary.completed_submissions;
            d.value += d.summary.uploaded_files;
            d.value += d.summary.appended_files;
            d.value += d.summary.wb_comments;
            d.value += d.summary.wb_messages;
            d.value += d.summary.receiver_comments;
            d.value += d.summary.receiver_messages;
          }
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
          .attr("class", "dayLabel mono axis");

      var timeLabels = svg.selectAll(".timeLabel")
          .data(times)
          .enter().append("text")
          .text(function(d) { return d; })
          .attr("x", function(d, i) { return i * gridSize; })
          .attr("y", 0)
          .style("text-anchor", "middle")
          .attr("transform", "translate(" + gridSize / 2 + ", -6)")
          .attr("class", "timeLabel mono axis" );

      var heatMap = svg.selectAll(".hour")
          .data(data)
          .enter().append("rect")
          .attr("x", function(d) { return (d.hour) * gridSize; })
          .attr("y", function(d) { return (d.day) * gridSize; })
          .attr("rx", 4)
          .attr("ry", 4)
          .attr("class", "hour bordered")
          .attr("width", gridSize)
          .attr("height", gridSize)
          .style("fill", function(d) {
              return colors[0]
          }).on("mouseenter", function(d) {
              if (d.valid == 0) {
                $scope.blob = d;
                $scope.$apply();
              }
          }).on("mouseleave", function(d) {
              $scope.blob = undefined;
              $scope.$apply();
          });

      heatMap.transition().duration(600)
          .style("fill", function(d) {
              if (d.valid == -1) {
                  return 'white';
              }
              if (d.valid == -2) {
                  return 'yellow';
              }
              if (d.valid == -3) {
                  return 'red';
              }
              return colorScale(d.value);
          });

      heatMap.append("title").text(function(d) {
          // if strings are updated here remember to update client/translation.html to push them on transifex
          if (d.valid == -1) {
              return $filter('translate')('Missing data') + ':\n\t' + $filter('translate')('in this hour the node was off.');
          } else if (d.valid == -2) {
              return $filter('translate')('Missing data') + ':\n\t' + $filter('translate')('no stats available for the future.');
          } else if (d.valid == -3) {
              return $filter('translate')('Missing data') + ':\n\t' + $filter('translate')('no stats available for current hour; check activities page.');
          } else {
              return $filter('translate')('Activities') + ': ' + d.value;
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

    $scope.show_stats = function(stats) {
      show_data(stats.heatmap);
      $scope.when = stats.associated_date;
      $scope.complete = stats.complete;
    };

    $scope.update_week = function () {
        if ($scope.week_delta == undefined || $scope.week_delta > 0) {
            $scope.week_delta = 0;
        }

        var delta = Math.abs($scope.week_delta);

        $scope.stats = StatsCollection.get({week_delta: delta}, $scope.show_stats);
    }

    $scope.increment_week = function() {
      if ($scope.week_delta < 0) {
        $scope.week_delta += 1;
        $scope.update_week();
      }
    };

    $scope.decrement_week = function() {
      $scope.week_delta -= 1;
      $scope.update_week();
    };

    $scope.update_week();

}]);

GLClient.controller('AnomaliesCtrl', ['$scope', 'Node', 'AnomaliesHistCollection',
  function($scope, Node, AnomaliesHistCollection) {

    $scope.showLevel = true;
    $scope.anomalies = AnomaliesHistCollection.query();
}]);

GLClient.controller('ActivitiesCtrl', ['$scope', 'Node', 'ActivitiesCollection',
  function($scope, Node, ActivitiesCollection) {

    $scope.activities = ActivitiesCollection.query();
}]);
