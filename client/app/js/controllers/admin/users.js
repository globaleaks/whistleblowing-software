GLClient.controller('AdminUsersCtrl', ['$scope',
  function($scope) {
    $scope.showAddUser = false;
    $scope.toggleAddUser = function() {
      $scope.showAddUser = !$scope.showAddUser;
    };
}]).controller('AdminUserEditorCtrl', ['$scope', '$rootScope', 'Utils', 'AdminUserResource',
  function($scope, $rootScope, Utils, AdminUserResource) {
    $scope.deleteUser = function() {
      Utils.deleteDialog($scope.user).then(function() {
        return Utils.deleteResource(AdminUserResource, $scope.admin.users, $scope.user);
      });
    };

    $scope.editing = false;

    $scope.toggleEditing = function () {
      $scope.editing = $scope.editing ^ 1;
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
      user.presentation_order = $scope.newItemOrder($scope.admin.users, 'presentation_order');

      user.$save(function(new_user){
        $scope.admin.users.push(new_user);
        $scope.new_user = {};
      });
    };
}]);
