GLClient.controller('PGPConfigCtrl', ['$scope', 'pgp', function($scope, pgp) {
  $scope.generate_key = function() {
    pgp.generate_key(function(keyPair, content) {
      saveAs(content, "globaleaks_key.zip");
      if ($scope.receiver) {
        $scope.receiver.pgp_key_public = keyPair.publicKeyArmored.trim();
        $scope.receiver.pgp_key_private = keyPair.privateKeyArmored.trim();
      } else if ($scope.preferences) {
        $scope.preferences.pgp_key_public = keyPair.publicKeyArmored.trim();
        $scope.preferences.pgp_key_private = keyPair.privateKeyArmored.trim();
      }
      $scope.$apply();
    });
  }
}]);
