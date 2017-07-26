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
  $scope.delete_tenant = function() {
    AdminTenantResource.delete({
      id: tenant.id
    }, function(){
      var idx = $scope.admin.tenants.indexOf(tenant);
      $scope.admin.tenants.splice(idx, 1);
    });
  };

  $scope.toggleActivation = function() {
    tenant.active = !tenant.active;
    tenant.$update();
  };
}]);
