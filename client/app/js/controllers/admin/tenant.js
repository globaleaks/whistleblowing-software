angular.module('GLClient')
.controller('TenantCtrl', ['$scope', '$http', 'Utils', function($scope, $http, Utils) {
  $scope.newTenant = new $scope.admin_utils.new_tenant();

  $scope.showAddTenant = false;
  $scope.toggleAddTenant = function() {
    $scope.showAddTenant = !$scope.showAddTenant;
  };

  $scope.addTenant = function() {
    $scope.newTenant.$save(function(tenant){
      $scope.admin.tenants.push(tenant);
      $scope.newTenant = new $scope.admin_utils.new_tenant();
    });
  };

  $scope.importTenant = function(file) {
    $http({
      method: 'POST',
      url: 'admin/tenants/import',
      data: file,
    }).then(function() {
       $route.reload();
    }, Utils.displayErrorMsg);
  };

  $scope.currentPage = 1;
  $scope.itemsPerPage = 20;
}])
.controller('TenantEditorCtrl', ['$scope', '$rootScope', '$http', 'Utils', 'FileSaver', 'AdminTenantResource', function($scope, $rootScope, $http, Utils, FileSaver, AdminTenantResource) {
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

  $scope.exportTenant = function($event) {
    $event.stopPropagation();
    $http({
      method: 'GET',
      url: 'admin/tenants/' + tenant.id + '/export',
      responseType: 'blob',
    }).then(function (response) {
      FileSaver.saveAs(response.data, 'tenant_export_tid_' + tenant.id + '.tar.gz');
    });
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
