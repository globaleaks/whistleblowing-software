angular.module('GLClient')
.controller('TenantCtrl', ['$scope', function($scope) {
  $scope.new_tenant = {};

  $scope.add_tenant = function() {
    var new_tenant = new $scope.admin_utils.new_tenant();
    new_tenant.label = $scope.new_tenant.label;
    new_tenant.subdomain = '';

    new_tenant.$save(function(new_tenant){
      $scope.admin.tenants.push(new_tenant);
      $scope.new_tenant = {};
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
