GLClient.controller('AdminUsersCtrl', ['$scope',
  function($scope) {
    $scope.showAddUser = false;
    $scope.toggleAddUser = function() {
      $scope.showAddUser = !$scope.showAddUser;
    };

    $scope.tenants_by_id = $scope.Utils.array_to_map($scope.admin.tenants);
}]).controller('AdminUserEditorCtrl', ['$scope', '$rootScope', '$http', 'Utils', 'AdminUserResource',
  function($scope, $rootScope, $http, Utils, AdminUserResource) {
    $scope.deleteUser = function() {
      Utils.deleteDialog($scope.user).then(function() {
        return Utils.deleteResource(AdminUserResource, $scope.admin.users, $scope.user);
      });
    };

    $scope.editing = false;

    $scope.toggleEditing = function () {
      $scope.editing = $scope.editing ^ 1;
    };

    $scope.showAddUserTenantAssociation = false;
    $scope.toggleAddUserTenantAssociation = function () {
      $scope.showAddUserTenantAssociation = !$scope.showAddUserTenantAssociation;
    };

    $scope.saveUser = function() {
      var user = $scope.user;
      if (user.pgp_key_remove) {
        user.pgp_key_public = '';
      }

      if (user.pgp_key_public !== undefined && user.pgp_key_public !== '') {
        user.pgp_key_remove = false;
      }

      user.$update(function(){
        $rootScope.successes.push({message: 'Success!'});
      });
    };

    $scope.updateUserImgUrl = function() {
      $scope.userImgUrl = '/admin/users/' + $scope.user.id + '/img#' + Utils.randomFluff();
    };

    $scope.updateUserImgUrl();

    $scope.loadPublicKeyFile = function(file) {
      Utils.readFileAsText(file).then(function(txt) {
        $scope.user.pgp_key_public = txt;
      }, Utils.displayErrorMsg);
    }

    $scope.resetUserPassword = function() {
      $http.put(
        'admin/cmd', { 
          'operation': 'reset_user_password',
          'args': {
            'value': $scope.user.username
          }
      }).then(function() {
        $rootScope.successes.push({message: 'Success!'});
      })
    }  
}]).
controller('AdminUserTenantAssociationAddCtrl', ['$scope', '$http', '$filter',
function ($scope, $http, $filter) {
  $scope.refreshAvailableTenants = function(filter) {)
    var tenantList = [];

    /* Build a list of tenants that we can actually add */
    for (var i = 0; i < $scope.admin.tenants.length; i++) {
      var tenant = $scope.admin.tenants[i];

      /* If user.tid matches, it's not an elligable choice */
      if ($scope.user.tid === tenant.id) {
        continue;
      }

      /* Same if user is already associated */
      var already_associated = false;
      for (var j = 0; j < $scope.user.usertenant_assocations.length; j++) {
        var t_assoc = $scope.user.usertenant_assocations[j]
        if (t_assoc.tenant_id === tenant.id) {
          already_associated = true;
          break;
        }
      }

      if (already_associated === true) {
        continue;
      }

      // *phew*, we can add it to the list
      tenantList.push(tenant);
    }

    if (filter) {
      tenantList = $filter('filter')(tenantList, filter);
    }

    $scope.availableTenants = tenantList;
  }

  $scope.refreshAvailableTenants();

  $scope.addUserTenantAssociation = function (tenant) {
    var new_submission_substate = {
      'tenant_id':tenant.id
    }

    $http.post(
      '/admin/users/' + $scope.user.id + '/tenant_associations',
      new_submission_substate
    ).then(function (result) {
      $scope.user.usertenant_assocations.push(result.data);
    })
  }
}]).
controller('AdminUserTenantAssociationEditorCtrl', ['$scope', '$rootScope', '$http', 'Utils', 'AdminUserTenantAssociationResource',
function ($scope, $rootScope, $http, Utils, AdminUserTenantAssociationResource) {
  $scope.usertenant_association_editing = false;
  $scope.toggleUserTenantAssociationEditing = function () {
    $scope.usertenant_association_editing = !$scope.usertenant_association_editing;
  }

  $scope.deleteUserTenantAssociation = function() {
    Utils.deleteDialog($scope.association).then(function() {
      AdminUserTenantAssociationResource.delete({
        user_id: $scope.user.id,
        tenant_id: $scope.association.tenant_id
      }, function() {
        var index = $scope.user.usertenant_assocations.indexOf($scope.association);
        $scope.user.usertenant_assocations.splice(index, 1);
        $scope.refreshAvailableTenants();
      });
    });
  }

}]).
controller('AdminUserAddCtrl', ['$scope',
  function($scope) {
    $scope.new_user = {};

    $scope.add_user = function() {
      var user = new $scope.admin_utils.new_user();

      user.username = $scope.new_user.username !== undefined ? $scope.new_user.username : '';
      user.role = $scope.new_user.role;
      user.name = $scope.new_user.name;
      user.mail_address = $scope.new_user.email;
      user.can_edit_general_settings = false;
      user.presentation_order = $scope.newItemOrder($scope.admin.users, 'presentation_order');

      user.$save(function(new_user){
        $scope.admin.users.push(new_user);
        $scope.new_user = {};
      });
    };
}]);
