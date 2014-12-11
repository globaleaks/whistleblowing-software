GLClient.controller('StatisticsCtrl', ['$scope', 'Node', 'StatsCollection', 
  function($scope, Node, StatsCollection) {

    var margin = { top: 50, right: 0, bottom: 100, left: 30 },
      width = 960 - margin.left - margin.right,
      height = 430 - margin.top - margin.bottom,
      gridSize = Math.floor(width / 24),
      legendElementWidth = gridSize*2,
      buckets = 9,
      colors = ["#e5e5e5","#e5e5e5","e3e9f1", "1d88ca", "#d3e0f1","#aec7e5","#5d8fca","#3573bd","151a31"],
      days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
      times = ["1a", "2a", "3a", "4a", "5a", "6a", "7a", "8a", "9a", "10a", "11a", "12a", "1p", "2p", "3p", "4p", "5p", "6p", "7p", "8p", "9p", "10p", "11p", "12p"];

    /* 2014-11-09T13:38:22.707125Z  with [:-8] */
    var parseISODate = d3.time.format("%Y-%m-%dT%H:%M:%S").parse;

    var show_data = function(data) {

      /*
      {
      "day": 6,
      "freemegabytes": 5627,
      "hour": 19,
      "summary": {
      "login_failure": 28
      },
      "week": 46,
      "year": 2014
      },
      */

      data.forEach(function(d) {

          d.week =+d.week;
          d.year =+d.year;
          d.day =+ d.day;
          d.hour =+ d.hour;

          if(d.summary['submission_started']) { d.submission_started = +d.summary['submission_started']; } else { d.submission_started = 0 }
          d.value = d.submission_started;
          if(d.summary['submission_completed']) { d.submission_completed = +d.summary['submission_completed']; } else { d.submission_completed = 0 }
          d.value += d.submission_completed;
          if(d.summary['login_failure']) { d.login_failure = +d.summary['login_failure']; } else {d.login_failure = 0 }
          d.value += d.login_failure;
          if(d.summary['login_success']) { d.login_success= +d.summary['login_success']; } else { d.login_success= 0 }
          d.value += d.login_success;
          if(d.summary['wb_comment']) { d.wb_comment = +d.summary['wb_comment']; } else { d.wb_comment = 0 }
          d.value += d.wb_comment;
          if(d.summary['wb_message']) { d.wb_message= +d.summary['wb_message']; } else { d.wb_message= 0 }
          d.value += d.wb_message;
          if(d.summary['receiver_comment']) { d.receiver_comment = +d.summary['receiver_comment']; } else { d.receiver_comment = 0 }
          d.value += d.receiver_comment;
          if(d.summary['receiver_message']) { d.receiver_message = +d.summary['receiver_message']; } else { d.receiver_message = 0 }
          d.value += d.receiver_message;

      });

      var colorScale = d3.scale.quantile()
          .domain([0, buckets - 1, d3.max(data, function (d) {
          return d.value;
          })])
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
          .style("fill", colors[0]);

      heatMap.transition().duration(1000)
          .style("fill", function(d) {
              if (d.freemegabytes == -1) {
          return "#E5E5E5";
              } else {
          return colorScale(d.value);
              }
          });

      heatMap.append("title").text(function(d) {
          if (d.freemegabytes == -1) {
              return "Missing data for this hour";
          } else {
              return (
                "MBytes free: " + d.freemegabytes + "\n" +
                "#Failed Logins: " + d.login_failure + "\n" +
                "#Successful Logins: " + d.login_success + "\n" +
                "#WB Messages/Comments: " + d.wb_message +"/"+ d.wb_comment + "\n" +
                "#Started/Completed Submissions: " + d.submission_started + "/" + d.submission_completed + "\n" +
                "#Receiver Messages/Comments: " + d.receiver_message + "/" + d.receiver_comment + "\n"
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
          .style("fill", function(d, i) { return colors[i]; });

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
