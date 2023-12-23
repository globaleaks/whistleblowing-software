GL.
controller("AdminAuditLogCtrl", ["$scope", function($scope){
  $scope.tabs = [
    {
      title:"Audit log",
      template:"views/admin/auditlog/tab1.html"
    },
    {
      title:"Users",
      template:"views/admin/auditlog/tab2.html"
    },
    {
      title:"Reports",
      template:"views/admin/auditlog/tab3.html"
    },
    {
      title:"Scheduled jobs",
      template:"views/admin/auditlog/tab4.html"
    }
  ];

  $scope.itemsPerPage = 20;

  $scope.resourcesNames = ["auditlog", "tips", "users"];

  $scope.auditLog = {};

  for (var i=0; i< $scope.resourcesNames.length; i++) {
    $scope.auditLog[$scope.resourcesNames[i]] = {
      currentPage: 1,
      elems: angular.copy($scope.resources[$scope.resourcesNames[i]])
    };
  }
}]);
