GL.
controller("AdminAuditLogCtrl", ["$scope", function($scope){
  $scope.tabs = [
    {
      title:"Stats",
      template:"views/admin/auditlog/tab1.html"
    },
    {
      title:"Activities",
      template:"views/admin/auditlog/tab2.html"
    },
    {
      title:"Users",
      template:"views/admin/auditlog/tab3.html"
    },
    {
      title:"Reports",
      template:"views/admin/auditlog/tab4.html"
    },
    {
      title:"Anomalies",
      template:"views/admin/auditlog/tab5.html"
    },
    {
      title:"Scheduled jobs",
      template:"views/admin/auditlog/tab6.html"
    }
  ];

  $scope.itemsPerPage = 20;

  $scope.resourcesNames = ["activities", "anomalies", "tips", "users"];

  $scope.auditLog = {};

  for (var i=0; i< $scope.resourcesNames.length; i++) {
    $scope.auditLog[$scope.resourcesNames[i]] = {
      currentPage: 1,
      elems: angular.copy($scope.resources[$scope.resourcesNames[i]])
    };
  }
}]).
controller("StatisticsCtrl", ["$scope", "$filter", "StatsCollection",
  function($scope, $filter, StatsCollection) {
    $scope.week_delta = 0;
    $scope.blob = undefined;

    var margin = { top: 50, right: 0, bottom: 100, left: 30 },
      width = 960 - margin.left - margin.right,
      height = 430 - margin.top - margin.bottom,
      gridSize = Math.floor(width / 24),
      legendElementWidth = gridSize*2,
      buckets = 9,
      colors = ["#E8F4FB","#C4DDF8","#9FC7F1","#5794D5","#3777BC","#2863A2", "#204f82", "#1F4165","#103053"],
      days = ["1", "2", "3", "4", "5", "6", "7"],
      times = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24"];

    var show_data = function(data) {

      /*
      {
          "hour": 19,
          "day": 6,
          "summary": {
              "login_failure": 28
          },
          "valid": 0
      },
      valid is a status flag:
          0 means that data is meaningful
          -1 no stats available for this hour
      */

      data.forEach(function(d) {
          if (d.valid === 0) {
            d.summary.failed_logins = + d.summary.failed_logins ? d.summary.failed_logins : 0;
            d.summary.successful_logins = +d.summary.successful_logins ? d.summary.successful_logins : 0;
            d.summary.submissions = +d.summary.submissions ? d.summary.submissions : 0;

            d.value = 0;
            d.value += d.summary.failed_logins;
            d.value += d.summary.successful_logins;
            d.value += d.summary.submissions;
          }
      });

      var colorScale = d3.scaleQuantile()
          .domain([0, buckets - 1, d3.max(data, function (d) { return d.value; })])
          .range(colors);

      d3.selectAll("#chart > *").remove();

      var svg = d3.select("#chart").append("svg")
          .attr("width", width + margin.left + margin.right)
          .attr("height", height + margin.top + margin.bottom)
          .append("g")
          .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

      /* eslint-disable no-unused-vars */
      svg.selectAll(".dayLabel")
          .data(days)
          .enter().append("text")
            .text(function (d) { return d; })
            .attr("x", 0)
            .attr("y", function (d, i) { return i * gridSize; })
            .style("text-anchor", "end")
            .attr("transform", "translate(-6," + gridSize / 1.5 + ")")
            .attr("class", function (d, i) { return ((i >= 0 && i <= 4) ? "dayLabel mono axis axis-workweek" : "dayLabel mono axis"); });

      svg.selectAll(".timeLabel")
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
          .attr("x", function(d) { return (d.hour) * gridSize; })
          .attr("y", function(d) { return (d.day) * gridSize; })
          .attr("rx", 4)
          .attr("ry", 4)
          .attr("class", "hour bordered")
          .attr("width", gridSize)
          .attr("height", gridSize)
          .style("fill", function(d) {
              return colors[0];
          }).on("mouseenter", function(d) {
              if (d.valid === 0) {
                $scope.blob = d;
                $scope.$apply();
              }
          }).on("mouseleave", function(d) {
              $scope.blob = undefined;
              $scope.$apply();
          });
      /* eslint-enable no-unused-vars */

      heatMap.transition().duration(600)
          .style("fill", function(d) {
              if (d.valid === -1) {
                  return "white";
              }

              return colorScale(d.value);
          });

      heatMap.append("title").text(function(d) {
          if (d.valid === -1) {
              return "";
          } else {
              return $filter("translate")("Activities") + ": " + d.value;
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
      $scope.week = stats.week;
      $scope.complete = stats.complete;
    };

    $scope.update_week = function () {
        if (typeof $scope.week_delta === "undefined" || $scope.week_delta > 0) {
            $scope.week_delta = 0;
        }

        var delta = Math.abs($scope.week_delta);

        $scope.stats = StatsCollection.get({week_delta: delta}, $scope.show_stats);
    };

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
