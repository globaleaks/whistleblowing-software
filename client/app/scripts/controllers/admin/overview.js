GLClient.controller('OverviewCtrl', ['$scope', '$location', 'ReceiverOverview', 'TipOverview', 'FileOverview',
  function($scope, $location, ReceiverOverview, TipOverview, FileOverview, AdminStats) {

      $scope.users = ReceiverOverview.query();
      $scope.tips = TipOverview.query();
      $scope.files = FileOverview.query();

      var current_menu = $location.path().split('/').slice(-1);
      current_menu += "_overview";
      $scope.active = {};
      $scope.active[current_menu] = "active";
}]);

GLClient.controller('StatisticsCtrl', ['$scope', 'Node', 'StatsCollection', 'AnomaliesCollection',
    function($scope, Node, StatsCollection, AnomaliesCollection) {

        Node.get(function(node) {

          $scope.anomaly_checks = node.anomaly_checks;

        });

        $scope.anomalies = AnomaliesCollection.query();

        $scope.stats = StatsCollection.query();
        $scope.active = {
          stats_overview: "active"
        };
}]);
