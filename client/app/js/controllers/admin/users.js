GLClient.controller('AdminUsersCtrl', ['$scope', '$rootScope', 'AdminUserResource',
  function($scope, $rootScope, AdminUserResource) {

  $scope.save_user = function(user) {
    if (user.pgp_key_remove) {
      user.pgp_key_public = '';
    }

    if (user.pgp_key_public !== undefined &&
        user.pgp_key_public !== '') {
      user.pgp_key_remove = false;
    }

    user.$update(function(){
      $rootScope.successes.push({message: 'Success!'});
    });
  };

  $scope.perform_delete = function(user) {
    AdminUserResource.delete({
      id: user.id
    }, function(){
      var idx = $scope.admin.users.indexOf(user);
      $scope.admin.users.splice(idx, 1);
    });
  };
}]).
controller('AdminUserEditorCtrl', ['$scope',
  function($scope) {

    $scope.editing = false;

    $scope.toggleEditing = function () {
      $scope.editing = $scope.editing ^ 1;
    };

    $scope.save = function() {
      $scope.save_user($scope.user);
    };

    $scope.updateUserImgUrl = function() {
      $scope.userImgUrl = '/admin/users/' + $scope.user.id + '/img#' + $scope.Utils.randomFluff();
    };

    $scope.updateUserImgUrl();

    $scope.loadPublicKeyFile = function(file) {
      $scope.Utils.readFileAsText(file).then(function(txt) {
        $scope.user.pgp_key_public = txt;
      }, $scope.Utils.displayErrorMsg);
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
