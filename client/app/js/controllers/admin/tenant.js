angular.module("GLClient")
.controller("TenantCtrl", ["$scope", function($scope) {
  $scope.search = undefined;
  $scope.currentPage = 1;
  $scope.itemsPerPage = 20;

  $scope.newTenant = new $scope.AdminUtils.new_tenant();

  $scope.$watch("search", function (value) {
    if (value != undefined) {
      $scope.currentPage = 1;
    }
  });

  $scope.showAddTenant = false;
  $scope.toggleAddTenant = function() {
    $scope.showAddTenant = !$scope.showAddTenant;
  };

  $scope.addTenant = function() {
    $scope.newTenant.$save(function(tenant){
      $scope.admin.tenants.push(tenant);
      $scope.newTenant = new $scope.AdminUtils.new_tenant();
    });
  }
}])
.controller("TenantEditorCtrl", ["$scope", "$rootScope", "$http", "$window", "AdminTenantResource",
  function($scope, $rootScope, $http, $window, AdminTenantResource) {
  var tenant = $scope.tenant;

  $scope.toggleEditing = function($event) {
    $event.stopPropagation();
    $scope.editing = !$scope.editing;
  };

  $scope.isRemovableTenant = function() {
    return tenant.id != 1;
  };

  $scope.isCurrentTenant = function() {
    return false;
  };

  $scope.toggleActivation = function($event) {
    $event.stopPropagation();
    tenant.active = !tenant.active;
    tenant.$update();
  };

  $scope.configureTenant = function($event, tid) {
    $event.stopPropagation();
    return $http.get("/tenantauthswitch/" + tid).then(function(x){
      return $window.open(x.data.redirect);
    });
  };

  $scope.saveTenant = function() {
    tenant.subdomain = angular.isDefined(tenant.subdomain) ? tenant.subdomain : "";
    tenant.$update().then(function() {
      $rootScope.successes.push({});
    });
  }

  $scope.deleteTenant = function($event) {
    $event.stopPropagation();
    $scope.Utils.deleteDialog(tenant).then(function() {
      return $scope.Utils.deleteResource(AdminTenantResource, $scope.admin.tenants, tenant);
    });
  };
}]);
