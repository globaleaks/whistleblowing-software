GLClient.controller('AdminCtrl',
    ['$scope', '$http', '$location', 'Admin',
function($scope, $http, $location, Admin) {

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

  // XXX find a more elegant solution
  // This is required for the step by step wizard.
  $scope.steps = [
    '1 Content settings',
    '2 Notification and Delivery',
    '3 Review your settings'
  ];

  $scope.update = function(model) {
    $scope.master = angular.copy(model);
    model.$update();
  };

  $scope.isUnchanged = function(model) {
    return angular.equals(model, $scope.master);
  };

}]);
