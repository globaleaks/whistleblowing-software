GLClient.controller('LoginCtrl', ['$scope', '$routeParams',
  function($scope, $routeParams) {
    var src = $routeParams.src;

    $scope.loginUsername = "";
    $scope.loginPassword = "";
    $scope.loginRole = "receiver";

    if (src && src.indexOf("/admin") != -1) {
      $scope.loginUsername = "admin";
      $scope.loginRole = "admin";
    }

    $scope.$watch("loginUsername", function(){
      if ($scope.loginUsername === "admin") {
        $scope.loginRole = "admin";
      } else if ($scope.loginUsername === "wb") {
        $scope.loginRole = "wb";
      } else {
        $scope.loginRole = "receiver";
      }
      $scope.loginPassword = "";
    });

}]);
