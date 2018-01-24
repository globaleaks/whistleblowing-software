GLClient
.controller('ForcedPasswordChangeCtrl', ['$scope', '$location', 'locationForce',
  function($scope, $location, locationForce) {
    $scope.save = function () {
      locationForce.clear();

      $scope.preferences.$update(function () {
        $location.path($scope.session.auth_landing_page);
      });
    };
}])
.factory('locationForce', ['$location', '$rootScope', function($location,  $rootScope) {
  var forcedLocation = null;
  var deregister = function() {};

  return {
    set: function(path) {
      forcedLocation = path;

      deregister = $rootScope.$on("$locationChangeStart", function(event, next) {
        next = next.substring($location.absUrl().length - $location.url().length);
        if (forcedLocation !== null && next !== forcedLocation) {
          event.preventDefault();
        }
      });

      $location.path(path);
    },

    clear: function() {
      forcedLocation = null;
      deregister();
    },
  };
}]);
