GL.controller("AdminUserTabCtrl", ["$scope",
  function($scope) {
    $scope.tabs = [
      {
        title:"Users",
        template:"views/admin/users/tab1.html"
      },
      {
        title:"Options",
        template:"views/admin/users/tab2.html"
      }
    ];
}]).controller("AdminUsersCtrl", ["$scope", "AdminTenantResource",
  function($scope, AdminTenantResource) {
    $scope.showAddUser = false;
    $scope.toggleAddUser = function() {
      $scope.showAddUser = !$scope.showAddUser;
    };

    if ($scope.public.node.root_tenant) {
      AdminTenantResource.query(function(result) {
        $scope.resources.tenants = result;
        $scope.tenants_by_id = $scope.Utils.array_to_map($scope.resources.tenants);
      });
    }
}]).controller("AdminUserEditorCtrl", ["$scope", "$http", "AdminUserResource",
  function($scope, $http, AdminUserResource) {
    $scope.deleteUser = function() {
      $scope.Utils.deleteDialog().then(function() {
        return $scope.Utils.deleteResource(AdminUserResource, $scope.resources.users, $scope.user);
      });
    };

    $scope.editing = false;

    $scope.setPasswordArgs = {
      "user_id": $scope.user.id
    };

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
        user.pgp_key_public = "";
      }

      if (user.pgp_key_public !== "") {
        user.pgp_key_remove = false;
      }

      return user.$update();
    };

    $scope.loadPublicKeyFile = function(file) {
      $scope.Utils.readFileAsText(file).then(function(txt) {
        $scope.user.pgp_key_public = txt;
      }, $scope.Utils.displayErrorMsg);
    };

    $scope.setPassword = function() {
      $scope.Utils.runAdminOperation("set_user_password", $scope.setPasswordArgs).then(function() {
        $scope.user.newpassword = false;
        $scope.setPasswordArgs.password = "";
      });
    };

    $scope.resetUserPassword = function() {
      $scope.Utils.runAdminOperation("send_password_reset_email", {"value": $scope.user.id});
    };

    $scope.disable2FA = function() {
      $scope.Utils.runAdminOperation("disable_2fa", {"value": $scope.user.id}, true);
    };

    $scope.toggleUserEscrow = function() {
      // do not toggle till confirmation;
      $scope.user.escrow = !$scope.user.escrow;

      $scope.Utils.runAdminOperation("toggle_user_escrow", {"value": $scope.user.id}, true);
    };
}]).
controller("AdminUserAddCtrl", ["$scope",
  function($scope) {
    $scope.new_user = {};

    $scope.add_user = function() {
      var user = new $scope.AdminUtils.new_user();

      user.username = typeof $scope.new_user.username !== "undefined" ? $scope.new_user.username : "";
      user.role = $scope.new_user.role;
      user.name = $scope.new_user.name;
      user.mail_address = $scope.new_user.email;
      user.language = $scope.resources.node.default_language;

      user.$save(function(new_user){
        $scope.resources.users.push(new_user);
        $scope.new_user = {};
      });
    };
}]);
