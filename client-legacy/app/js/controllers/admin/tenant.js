angular.module("GL")
.controller("TenantCtrl", ["$scope", function($scope) {
  $scope.tabs = [
    {
      title:"Sites",
      template:"views/admin/sites/tab1.html"
    },
    {
      title:"Options",
      template:"views/admin/sites/tab2.html"
    },
  ];

  $scope.search = undefined;
  $scope.currentPage = 1;
  $scope.itemsPerPage = 20;

  $scope.newTenant = new $scope.AdminUtils.new_tenant();

  $scope.$watch("search", function (value) {
    if (typeof value !== "undefined") {
      $scope.currentPage = 1;
    }
  });

  $scope.showAddTenant = false;
  $scope.toggleAddTenant = function() {
    $scope.showAddTenant = !$scope.showAddTenant;
  };

  $scope.addTenant = function() {
    $scope.newTenant.$save(function(tenant){
      $scope.resources.tenants.push(tenant);
      $scope.newTenant = new $scope.AdminUtils.new_tenant();
    });
  };
}])
.controller("TenantEditorCtrl", ["$scope", "$http", "$window", "AdminTenantResource",
  function($scope, $http, $window, AdminTenantResource) {
  $scope.toggleEditing = function($event) {
    $event.stopPropagation();
    $scope.editing = !$scope.editing;
  };

  $scope.isRemovableTenant = function() {
    return $scope.tenant.id !== 1;
  };

  $scope.isCurrentTenant = function() {
    return false;
  };

  $scope.toggleActivation = function($event) {
    $event.stopPropagation();
    $scope.tenant.active = !$scope.tenant.active;
    $scope.tenant.$update();
  };

  $scope.configureTenant = function($event, tid) {
    $event.stopPropagation();
    return $http.get("api/auth/tenantauthswitch/" + tid).then(function(x){
      return $window.open(x.data.redirect);
    });
  };

  $scope.saveTenant = function() {
    $scope.tenant.subdomain = angular.isDefined($scope.tenant.subdomain) ? $scope.tenant.subdomain : "";
    return $scope.tenant.$update();
  };

  $scope.deleteTenant = function($event) {
    $event.stopPropagation();
    $scope.Utils.deleteDialog().then(function() {
      return $scope.Utils.deleteResource(AdminTenantResource, $scope.resources.tenants, $scope.tenant);
    });
  };
}]);
