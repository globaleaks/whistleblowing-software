GL.controller("StatisticsCtrl", ["$scope", "$filter", function ($scope, $filter) {

  // Percentages computing
  let na = $scope.resources.stats.reports_with_no_access;
  let oa = $scope.resources.stats.reports_with_at_least_one_access;
  let totAcc = na + oa;
  na = ((na / totAcc)*100).toFixed(1);
  oa = ((oa / totAcc)*100).toFixed(1);

  let an = $scope.resources.stats.reports_anonymous;
  let sb = $scope.resources.stats.reports_subscribed;
  let sbl = $scope.resources.stats.reports_subscribed_later;
  let totId = an + sb + sbl;
  an = ((an / totId)*100).toFixed(1);
  sb = ((sb / totId)*100).toFixed(1);
  sbl = ((sbl / totId)*100).toFixed(1);

  // Label definition
  let returning_wb_labels = ["Not returning", "Returning"
    ].map($filter("translate"));
  let anonymity_wb_labels = ["Anonymous",
    "Subscribed", "Subscribed later"].map($filter("translate"));

  // Adding percentages to labels after translation
  returning_wb_labels[0] = `${returning_wb_labels[0]} ${na}% - (${$scope.resources.stats.reports_with_no_access})`
  returning_wb_labels[1] = `${returning_wb_labels[1]} ${oa}% - (${$scope.resources.stats.reports_with_at_least_one_access})`

  anonymity_wb_labels[0] = `${anonymity_wb_labels[0]} ${an}% - (${$scope.resources.stats.reports_anonymous})`
  anonymity_wb_labels[1] = `${anonymity_wb_labels[1]} ${sb}% - (${$scope.resources.stats.reports_subscribed})`
  anonymity_wb_labels[2] = `${anonymity_wb_labels[2]} ${sbl}% - (${$scope.resources.stats.reports_subscribed_later})`

  // Chart declaration
  $scope.charts = [];
  $scope.charts.push({
    title: "Returning whistleblowers",
    total: totAcc,
    //labels: ["Accessi senza ricevuta", "Accessi tramite ricevuta"],
    labels: returning_wb_labels,
    values: [na, oa],
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
    title: "Anonimity",
    //labels: ["Non fornita", "Fornita", "Fornita in un secondo momento"],
    labels: anonymity_wb_labels,
    values: [an, sb, sbl],
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
}]);
