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

  $scope.admin = Admin;

  // We need to have a special function for updating the node since we need to add old_password and password attribute
  // if they are not present
  $scope.updateNode = function(node) {
    if (typeof(node.password) === "undefined")
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
