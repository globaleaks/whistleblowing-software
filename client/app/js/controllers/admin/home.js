GL.
controller("AdminCtrl",
    ["$scope", "$route", "$filter", "AdminNodeResource", "CONSTANTS",
    function($scope, $route, $filter, AdminNodeResource, CONSTANTS) {
  $scope.email_regexp = CONSTANTS.email_regexp;
  $scope.hostname_regexp = CONSTANTS.hostname_regexp;
  $scope.onionservice_regexp = CONSTANTS.onionservice_regexp;
  $scope.https_regexp = CONSTANTS.https_regexp;

  $scope.updateNode = function() {
    $scope.Utils.update($scope.resources.node, function() { $scope.$emit("REFRESH"); });
  };

  $scope.newItemOrder = function(objects, key) {
    if (objects.length === 0) {
      return 0;
    }

    var max = 0;
    angular.forEach(objects, function(object) {
      if (object[key] > max) {
        max = object[key];
      }
    });

    return max + 1;
  };

  $scope.$watch("resources.users", function() {
    $scope.all_recipients_enabled = false;

    if (!$scope.resources.users) {
      return;
    }

    for (var i=0; i<$scope.resources.users.length; i++) {
      if ($scope.resources.users[i].role === "receiver" && !$scope.resources.users[i].encryption) {
        break;
      }
    }

    $scope.all_recipients_enabled = true;
  }, true);
}]);
