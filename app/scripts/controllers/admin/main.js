GLClient.controller('AdminCtrl',
    ['$rootScope', '$scope', '$http', '$location', 'Admin',
function($rootScope, $scope, $http, $location, Admin) {

  // XXX this should actually be defined per controller
  // otherwise every time you open a new page the button appears enabled
  // because such item is !=
  $scope.master = {};

  // XXX convert this to a directive
  // This is used for setting the current menu in the sidebar
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";

  $scope.admin = new Admin();

  // We need to have a special function for updating the node since we need to add old_password and password attribute
  // if they are not present
  $scope.updateNode = function(node) {

    console.log(node);

    if (typeof(node.password) === "undefined")
      node.password = "";
    if (typeof(node.check_password) === "undefined")
      node.password = "";
    if (typeof(node.old_password) === "undefined")
      node.old_password = "";
    $scope.update(node);
  }

  $scope.update = function(model) {
    var success = {};
    success.message = "Updated " + model;
    model.$update(function(){
      if (!$rootScope.successes) {
        $rootScope.successes = [];
      };
      $rootScope.successes.push(success);
    });
  };

}]);

GLClient.controller('AdminAdvancedCtrl', ['$scope', 'changePasswordWatcher',
                    function($scope, changePasswordWatcher) {
    changePasswordWatcher($scope, "admin.node.old_password",
        "admin.node.password", "admin.node.check_password");
}]);

GLClient.controller('ImageUploadCtrl', ['$scope', function($scope){
    $scope.uploadfile = false;

    // Used to keep track of weather or not the profile file has been changed
    // or not.
    $scope.fileSelected = false;
    $scope.changeProfile = function() {
      $scope.fileSelected = true;
    }

    $scope.closeProfile = function() {
      $scope.fileSelected = $scope.uploadfile = false;
    }

    $scope.openUploader = function() {
      $scope.uploadfile = true;
    }

    $scope.closeUploader = function() {
      $scope.uploadfile = false;
    }

}]);
