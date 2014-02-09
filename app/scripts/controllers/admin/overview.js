GLClient.controller('OverviewCtrl', ['$scope', 'ReceiverOverview', 'TipOverview', 'FileOverview',
  function($scope, ReceiverOverview, TipOverview, FileOverview) {
      $scope.users = ReceiverOverview.query();
      $scope.tips = TipOverview.query();
      $scope.files = FileOverview.query();
}]);

GLClient.controller('StatisticsCtrl', ['$scope', 'StatsCollection', 'AnomaliesCollection',
    function($scope, StatsCollection, AnomaliesCollection) {
        $scope.anomalies = AnomaliesCollection.query();
        $scope.stats = StatsCollection.query();
}]);
