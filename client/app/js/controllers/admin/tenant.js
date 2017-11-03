angular.module('GLClient')
.controller('TenantCtrl', ['$scope', function($scope) {
  $scope.newTenant = new $scope.admin_utils.new_tenant();

  $scope.addTenant = function() {
    $scope.newTenant.$save(function(tenant){
      $scope.admin.tenants.push(tenant);
      $scope.newTenant = new $scope.admin_utils.new_tenant();
    });
  }
}])
.controller('TenantEditorCtrl', ['$scope', '$rootScope', 'Utils', 'AdminTenantResource', function($scope, $rootScope, Utils, AdminTenantResource) {
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

  $scope.saveTenant = function() {
    tenant.subdomain = angular.isDefined(tenant.subdomain) ? tenant.subdomain : '';
    tenant.$update().then(function() {
      $rootScope.successes.push({});
    });
  }

  $scope.deleteTenant = function($event) {
    $event.stopPropagation();
    Utils.deleteDialog(tenant).then(function() {
        return Utils.deleteResource(AdminTenantResource, $scope.admin.tenants, tenant);
    });
  };
}]);
