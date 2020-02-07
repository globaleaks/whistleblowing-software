GLClient.
controller("AdminAdvancedCtrl", ["$scope", "$http", function($scope, $http) {
  $scope.tabs = [
    {
      title:"Main configuration",
      template:"views/admin/advanced/tab1.html"
    }
  ];

  if ($scope.resources.node.root_tenant) {
    $scope.tabs.push({
      title:"Anomaly detection thresholds",
      template:"views/admin/advanced/tab2.html"
    });

    /*
    $scope.tabs.push({
      title: "Backups",
      template: "views/admin/advanced/tab3.html"
    });
    */
  }

  $scope.resetSubmissions = function() {
    $scope.Utils.deleteDialog().then(function() {
      var req = {
        "operation": "reset_submissions",
        "args": {}
      };

      return $http({method: "PUT", url: "admin/config", data: req});
    });
  };

  $scope.new_redirect = {};

  $scope.add_redirect = function() {
    var redirect = new $scope.AdminUtils.new_redirect();

    redirect.path1 = $scope.new_redirect.path1;
    redirect.path2 = $scope.new_redirect.path2;

    redirect.$save(function(new_redirect){
      $scope.resources.redirects.push(new_redirect);
      $scope.new_redirect = {};
    });
  };
}]);
