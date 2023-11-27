GL.controller("StatisticsCtrl", ["$scope", "$filter",
              function ($scope, $filter) {
  var returning_wb_labels = ["Returning", "Not returning"
    ].map($filter("translate"));
  var anonymity_wb_labels = ["Anonymous",
    "Subscribed", "Subscribed later"].map($filter("translate"));
  $scope.charts = [];
  var na = $scope.resources.stats.reports_with_no_access;
  var oa = $scope.resources.stats.reports_with_at_least_one_access;
  var totAcc = na + oa;
  na = Math.floor((na / totAcc)*100)
  oa = Math.floor((oa / totAcc)*100)
  
  var an = $scope.resources.stats.reports_anonymous;
  var sb = $scope.resources.stats.reports_subscribed;
  var sbl = $scope.resources.stats.reports_subscribed_later;
  var totId = an + sb + sbl;
  an = Math.floor((an / totId)*100)
  sb = Math.floor((sb / totId)*100)
  sbl = Math.floor((sbl / totId)*100)
  $scope.charts.push({
    title: "Returning whistleblowers",
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
            return data.labels[tooltipItem.index] + ' : ' + data.datasets[0].data[tooltipItem.index] + '%';
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
            return data.labels[tooltipItem.index] + ' : ' + data.datasets[0].data[tooltipItem.index] + '%';
          }
        }
      }
    }
  });
}]);
