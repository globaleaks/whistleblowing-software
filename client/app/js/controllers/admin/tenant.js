angular.module('GLClient')
.controller('TenantCtrl', ['$scope', function($scope) {
  $scope.new_tenant = {};

  $scope.add_tenant = function() {
    var new_tenant = new $scope.admin_utils.new_tenant();
    new_tenant.label = $scope.new_tenant.label;

    new_tenant.$save(function(new_tenant){
      $scope.admin.tenants.push(new_tenant);
      $scope.new_tenant = {};
    });
  }
}])
.controller('TenantEditorCtrl', ['$scope', 'AdminTenantResource', function($scope, AdminTenantResource) {
  var tenant = $scope.tenant;
  $scope.perform_delete = function(tenant) {
    return $scope.Utils.deleteResource(AdminTenantResource, $scope.admin.tenants, tenant);
  };

  $scope.toggleActivation = function() {
    tenant.active = !tenant.active;
    tenant.$update();
  };
}]);
