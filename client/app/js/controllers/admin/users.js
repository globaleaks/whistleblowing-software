GLClient.controller('AdminUsersCtrl', ['$scope',
  function($scope) {
    $scope.showAddUser = false;
    $scope.toggleAddUser = function() {
      $scope.showAddUser = !$scope.showAddUser;
    };
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
controller('AdminUserTenantAssociationAddCtrl', ['$scope', '$http',
function ($scope, $http) {
  $scope.presentation_order = $scope.newItemOrder($scope.submission_state.substates, 'presentation_order');

  $scope.addUserTenantAssociation = function () {
    /* IMPLEMENT ME */
  }
}]).
controller('AdminUserTenantAssociationEditorCtrl', ['$scope', '$rootScope', '$http', 'Utils', 'AdminSubmissionSubStateResource',
function ($scope, $rootScope, $http, Utils, AdminSubmissionSubStateResource) {
  // FIX AdminSubmissionSubStateResource - MUST BE CHANGED
  $scope.usertenant_association_editing = false;
  $scope.toggleUserTenantAssociationEditing = function () {
    $scope.usertenant_association_editing = !$scope.usertenant_association_editing;
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
