GLClient.controller('OverviewCtrl', ['$scope', 'ReceiverOverview', 'TipOverview', 'FileOverview',
  function($scope, ReceiverOverview, TipOverview, FileOverview) {

      $scope.users = ReceiverOverview.query();
      $scope.tips = TipOverview.query();
      $scope.files = FileOverview.query();
}]);

GLClient.controller('StatisticsCtrl', ['$scope', 'Node', 'StatsCollection', 'AnomaliesCollection',
    function($scope, Node, StatsCollection, AnomaliesCollection) {

        Node.get(function(node) {

          $scope.anomaly_checks = node.anomaly_checks;

        });

        $scope.anomalies = AnomaliesCollection.query();
        $scope.stats = StatsCollection.query();
}]);
