GLClient.controller('AdminUsersCtrl', ['$scope', '$uibModal', 'AdminUserResource',
  function($scope, $uibModal, AdminUserResource) {

  $scope.save_user = function(user, cb) {
    if (user.pgp_key_remove === true) {
      user.pgp_key_public = '';
    }

    if (user.pgp_key_public !== undefined &&
        user.pgp_key_public !== '') {
      user.pgp_key_remove = false;
    }

    var updated_user = new AdminUserResource(user);

    return $scope.update(updated_user, cb);
  };

  $scope.perform_delete = function(user) {
    AdminUserResource['delete']({
      id: user.id
    }, function(){
      var idx = $scope.admin.users.indexOf(user);
      $scope.admin.users.splice(idx, 1);
    });
  };

  $scope.userDeleteDialog = function(user) {
    var modalInstance = $scope.openConfirmableModalDialog('views/partials/user_delete.html', user);

    modalInstance.result.then(
       function(result) { $scope.perform_delete(result); },
       function(result) { }
    );
  };
}]);

GLClient.controller('AdminUserEditorCtrl', ['$scope', 'CONSTANTS',
  function($scope, CONSTANTS) {

    $scope.editing = false;

    $scope.toggleEditing = function () {
      $scope.editing = $scope.editing ^ 1;
    };

    $scope.save = function() {
      $scope.save_user($scope.user, false);
    };

    $scope.timezones = CONSTANTS.timezones;

    $scope.updateUserImgUrl = function() {
      $scope.userImgUrl = '/admin/users/' + $scope.user.id + '/img#' + $scope.randomFluff();
    };

    $scope.updateUserImgUrl();
}]);

GLClient.controller('AdminUserAddCtrl', ['$scope',
  function($scope) {
    $scope.new_user = {};

    $scope.add_user = function() {
      var user = new $scope.admin.new_user();

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
