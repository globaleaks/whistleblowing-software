GLClient.controller('PGPConfigCtrl', ['$scope', 'pgp', function($scope, pgp) {
  pgp.generate_key(function(keyPair, zipFile) {
    saveAs(content, file_name);
    if ($scope.receiver) {
      $scope.receiver.pgp_key_public = keyPair.publicKeyArmored.trim();
      $scope.receiver.pgp_key_private = keyPair.privateKeyArmored.trim();
    } else if ($scope.preferences) {
      $scope.preferences.pgp_key_public = keyPair.publicKeyArmored.trim();
      $scope.preferences.pgp_key_private = keyPair.privateKeyArmored.trim();
    }
    $scope.$apply();
  });
}]);
