GLClient.controller('WBFileUploadCtrl', ['$scope', '$q', '$timeout', 'glbcCipherLib', function($scope, $q, $timeout, glbcCipherLib)  {
  $scope.disabled = false;

  // handleFileEncryption encrypts the passed file with the keys of the
  // current scope's receivers and returns a new encrypted file with '.pgp'
  // added as the extension.
  // { File -> File }
  function handleFileEncryption(file) {
    var deferred = $q.defer();

    glbcCipherLib.createArrayFromBlob(file).then(function(fileArr) {
      // Get the public keys for each receiver
      // TODO TODO TODO Remove temp public key
      var pubKeyStrs = $scope.receivers.map(function(rec) { return rec.ccrypto_key_public; });
      // TODO TODO TODO
      var pubKeys;
      try {
        pubKeys = glbcCipherLib.loadPublicKeys(pubKeyStrs);
      } catch(err) {
        deferred.reject(err);
        return;
      }
      return glbcCipherLib.encryptArray(fileArr, pubKeys);
    }).then(function(cipherTextArr) {
      var cipherBlob = new Blob([cipherTextArr.buffer]);
      var encFile = new File([cipherBlob], file.name+'.pgp');
      deferred.resolve(encFile);
    });

    return deferred.promise;
  }


  $scope.$on('flow::fileAdded', function (event, flow, file) {
    if (file.size > $scope.node.maximum_filesize * 1024 * 1024) {
      file.error = true;
      file.error_msg = "This file exceeds the maximum upload size for this server.";
      event.preventDefault();
    } else {
      if ($scope.field !== undefined && !$scope.field.multi_entry) {
        // if the field allows to load only one file disable the button
        // as soon as a file is loaded.
        $scope.disabled = true;
      }
    }

    if (file.file.encrypted === undefined) {
      event.preventDefault();
      handleFileEncryption(file.file).then(function(outputFile) {
        outputFile.encrypted = true;
        $timeout(function() {
          flow.addFile(outputFile);
        }, 0);
      }, function(err) {
        throw err;
      });
    }
  });
}]).
controller('ImageUploadCtrl', ['$scope', '$rootScope', '$http', function($scope, $rootScope, $http) {
  $scope.imageUploadObj = {};
  $scope.Authentication = $rootScope.Authentication;
  $scope.Utils = $rootScope.Utils;

  $scope.deletePicture = function() {
    $http({
      method: 'DELETE',
      url: $scope.imageUploadUrl,
      headers: $scope.Authentication.get_auth_headers()
    }).then(function successCallback() {
      $scope.imageUploadModel[$scope.imageUploadModelAttr] = '';
      $scope.imageUploadObj.flow.files = [];
    }, function errorCallback() { });
  };
}]);
