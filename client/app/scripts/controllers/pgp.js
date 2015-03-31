GLClient.controller('PGPConfigCtrl', ['$scope', 'pgp', function($scope, pgp) {
  pgp.generate_key(function(keyPair, zipFile) {
    saveAs(content, file_name);
    if ($scope.receiver) {
      $scope.receiver.gpg_key_armor = keyPair.publicKeyArmored.trim();
      $scope.receiver.pgp_key_armor_priv = keyPair.privateKeyArmored.trim();
      $scope.$apply();
    } else if ($scope.preferences) {
      $scope.preferences.gpg_key_armor = keyPair.publicKeyArmored.trim();
      $scope.preferences.pgp_key_armor_priv = keyPair.privateKeyArmored.trim();
      $scope.$apply();
    }
  });
}]);
