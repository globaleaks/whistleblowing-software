GL.controller("StatisticsCtrl", ["$scope", "$filter", function ($scope, $filter) {
  var reports_count = $scope.resources.stats.reports_count;

  // Percentages computing
  var a_1 = $scope.resources.stats.reports_with_no_access;
  var a_2 = reports_count - $scope.resources.stats.reports_with_no_access;
  var totAcc = a_1 + a_2;
  a_1 = ((a_1 / totAcc)*100).toFixed(1);
  a_2 = 100 - a_1;

  var b_1 = $scope.resources.stats.reports_anonymous;
  var b_2 = $scope.resources.stats.reports_subscribed;
  var b_3 = $scope.resources.stats.reports_initially_anonymous;
  var totId = b_1 + b_2 + b_3;
  b_1 = ((b_1 / totId)*100).toFixed(1);
  b_2 = ((b_2 / totId)*100).toFixed(1);
  b_3 = 100 - b_1 - b_2;

  var c_1 = $scope.resources.stats.reports_tor;
  var c_2 = reports_count - $scope.resources.stats.reports_tor;
  var totAcc = c_1 + c_2;
  c_1 = ((c_1 / totAcc)*100).toFixed(1);
  c_2 = 100 - c_1;

  var d_1 = reports_count - $scope.resources.stats.reports_mobile;
  var d_2 = $scope.resources.stats.reports_mobile;
  var totAcc = d_1 + d_2;
  d_1 = ((d_1 / totAcc)*100).toFixed(1);
  d_2 = 100 - d_1;

  // Label definition
  var returning_wb_labels = ["Yes", "No"].map($filter("translate"));
  var anonymity_wb_labels = ["Anonymous",
    "Subscribed", "Subscribed later"].map($filter("translate"));
  var tor_wb_labels = ["Yes", "No"].map($filter("translate"));
  var mobile_wb_labels = ["Computer", "Mobile"].map($filter("translate"));
  

  // Adding percentages to labels after translation
  returning_wb_labels[0] = `${returning_wb_labels[0]} ${a_1}% - (${reports_count - $scope.resources.stats.reports_with_no_access})`
  returning_wb_labels[1] = `${returning_wb_labels[1]} ${a_2}% - (${$scope.resources.stats.reports_with_no_access})`

  anonymity_wb_labels[0] = `${anonymity_wb_labels[0]} ${b_1}% - (${$scope.resources.stats.reports_anonymous})`
  anonymity_wb_labels[1] = `${anonymity_wb_labels[1]} ${b_2}% - (${$scope.resources.stats.reports_subscribed})`
  anonymity_wb_labels[2] = `${anonymity_wb_labels[2]} ${b_3}% - (${$scope.resources.stats.reports_initially_anonymous})`

  tor_wb_labels[0] = `${tor_wb_labels[0]} ${c_1}% - (${$scope.resources.stats.reports_tor})`
  tor_wb_labels[1] = `${tor_wb_labels[1]} ${c_2}% - (${reports_count - $scope.resources.stats.reports_tor})`

  mobile_wb_labels[0] = `${mobile_wb_labels[0]} ${d_1}% - (${reports_count - $scope.resources.stats.reports_mobile})`
  mobile_wb_labels[1] = `${mobile_wb_labels[1]} ${d_2}% - (${$scope.resources.stats.reports_mobile})`

  // Chart declaration
  $scope.charts = [];

  $scope.charts.push({
    title: $filter("translate")("Returning whistleblowers"),
    total: totAcc,
    labels: returning_wb_labels,
    values: [a_1, a_2],
    colors: ["rgb(96,186,255)", "rgb(0,127,224)"],
    options: {
      legend: {
        onClick: (e) => e.stopPropagation(),
        display: true,
        position: 'left',
        labels: {
          fontColor: '#333',
          fontSize: 12,
        }
      },
      tooltips: {
        callbacks: {
          label: function(tooltipItem, data) {
            return data.labels[tooltipItem.index];
          }
        }
      }
    }
  });

  $scope.charts.push({
    title: $filter("translate")("Anonymity"),
    labels: anonymity_wb_labels,
    values: [b_1, b_2, b_3],
    colors: ["rgb(96,186,255)", "rgb(0,127,224)", "rgb(0,46,82)"],
    options: {
      legend: {
        onClick: (e) => e.stopPropagation(),
        display: true,
        position: 'left',
        labels: {
          fontColor: '#333',
          fontSize: 12,
        }
      },
      tooltips: {
        callbacks: {
          label: function(tooltipItem, data) {
            return data.labels[tooltipItem.index];
          }
        }
      }
    }
  });

  $scope.charts.push({
    title: $filter("translate")("Tor"),
    total: totAcc,
    labels: tor_wb_labels,
    values: [c_1, c_2],
    colors: ["rgb(96,186,255)", "rgb(0,127,224)"],
    options: {
      legend: {
        onClick: (e) => e.stopPropagation(),
        display: true,
        position: 'left',
        labels: {
          fontColor: '#333',
          fontSize: 12,
        }
      },
      tooltips: {
        callbacks: {
          label: function(tooltipItem, data) {
            return data.labels[tooltipItem.index];
          }
        }
      }
    }
  });

  $scope.charts.push({
    title: $filter("translate")("Devices"),
    total: totAcc,
    labels: mobile_wb_labels,
    values: [d_1, d_2],
    colors: ["rgb(96,186,255)", "rgb(0,127,224)"],
    options: {
      legend: {
        onClick: (e) => e.stopPropagation(),
        display: true,
        position: 'left',
        labels: {
          fontColor: '#333',
          fontSize: 12,
        }
      },
      tooltips: {
        callbacks: {
          label: function(tooltipItem, data) {
            return data.labels[tooltipItem.index];
          }
        }
      }
    }
  });
}]);
