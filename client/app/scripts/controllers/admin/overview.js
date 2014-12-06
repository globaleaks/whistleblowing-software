GLClient.controller('OverviewCtrl', ['$scope', 'ReceiverOverview', 'TipOverview', 'FileOverview',
  function($scope, ReceiverOverview, TipOverview, FileOverview) {

      $scope.users = ReceiverOverview.query();
      $scope.tips = TipOverview.query();
      $scope.files = FileOverview.query();
}]);

GLClient.controller('StatisticsCtrl', ['$scope', 'Node', 'StatsCollection', 
    function($scope, Node, StatsCollection) {

        $scope.stats = StatsCollection.query();
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
