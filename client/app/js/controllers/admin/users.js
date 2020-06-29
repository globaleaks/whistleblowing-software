GLClient.controller("AdminUsersCtrl", ["$scope", "AdminTenantResource",
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

    $scope.$watch("resources.users", function() {
      $scope.all_recipients_enabled = true;
      for (var i=0; i<$scope.resources.users.length; i++) {
        if ($scope.resources.users[i].role === "receiver" && !$scope.resources.users[i].encryption) {
          $scope.all_recipients_enabled = false;
        }
      }
    }, true);
}]).controller("AdminUserEditorCtrl", ["$scope", "$rootScope", "$http", "AdminUserResource",
  function($scope, $rootScope, $http, AdminUserResource) {
    $scope.deleteUser = function() {
      $scope.Utils.deleteDialog().then(function() {
        return $scope.Utils.deleteResource(AdminUserResource, $scope.resources.users, $scope.user);
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
        user.pgp_key_public = "";
      }

      if (user.pgp_key_public !== "") {
        user.pgp_key_remove = false;
      }

      user.$update(function(){
        $rootScope.successes.push({message: "Success!"});
      });
    };

    $scope.updateUserImgUrl = function() {
      $scope.userImgUrl = "/admin/users/" + $scope.user.id + "/img#" + $scope.Utils.randomFluff();
    };

    $scope.updateUserImgUrl();

    $scope.loadPublicKeyFile = function(file) {
      $scope.Utils.readFileAsText(file).then(function(txt) {
        $scope.user.pgp_key_public = txt;
      }, $scope.Utils.displayErrorMsg);
    };

    $scope.resetUserPassword = function() {
      $http.put(
        "api/admin/config", {
          "operation": "reset_user_password",
          "args": {
            "value": $scope.user.id
          }
      }).then(function() {
        $rootScope.successes.push({message: "Success!"});
      });
    };

    $scope.disable2FA = function() {
      $http.put(
        "api/admin/config", {
          "operation": "disable_2fa",
          "args": {
            "value": $scope.user.id
          }
      }).then(function() {
	$scope.user.two_factor_enable = false;
        $rootScope.successes.push({message: "Success!"});
      });
    };
}]).
controller("AdminUserAddCtrl", ["$scope",
  function($scope) {
    $scope.new_user = {"send_account_activation_link": true};

    $scope.add_user = function() {
      var user = new $scope.AdminUtils.new_user();

      user.username = typeof $scope.new_user.username !== "undefined" ? $scope.new_user.username : "";
      user.role = $scope.new_user.role;
      user.name = $scope.new_user.name;
      user.mail_address = $scope.new_user.email;
      user.send_account_activation_link = $scope.new_user.send_account_activation_link;

      user.$save(function(new_user){
        $scope.resources.users.push(new_user);
        $scope.new_user = {"send_account_activation_link": true};
      });
    };
}]);
