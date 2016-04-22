GLClient.controller('WBFileUploadCtrl', ['$scope', '$q', '$timeout', 'gbcCipherLib', function($scope, $q, $timeout, gbcCipherLib)  {
  $scope.disabled = false;
 
  // handleFileEncryption encrypts the passed file with the keys of the 
  // current scope's receivers and returns a new encrypted file with '.pgp'
  // added as the extension.
  // { File -> File }
  function handleFileEncryption(file) {
    var deferred = $q.defer();

    createFileArray(file).then(function(fileArr) {
      // Get the public keys for each receiver
      var pubKeyStrs = $scope.receivers.map(function(rec) { return rec.pgp_key_public; });
      var pubKeys;
      try {
        pubKeys = gbcCipherLib.loadPublicKeys(pubKeyStrs);
      } catch(err) {
        deferred.reject(err);
        return;
      }
      return gbcCipherLib.encryptArray(fileArr, pubKeys);
    }).then(function(cipherTextArr) {
      var cipherBlob = new Blob([cipherTextArr.buffer]);
      var encFile = new File([cipherBlob], file.name+'.pgp');
      deferred.resolve(encFile);
    });
    
    // TODO delete the file buffer's as soon as possible
    return deferred.promise;
  }

  // createFileArray returns a promise for an array of the bytes in the passed file.
  // { File -> { Promise -> Uint8Array } }
  function createFileArray(file) {
    var deferred = $q.defer();
    var fileReader = new FileReader();
    fileReader.onload = function() {
      var arrayBufferNew = this.result;
      var uintFileArray = new Uint8Array(arrayBufferNew);
      deferred.resolve(uintFileArray);
    };
    fileReader.readAsArrayBuffer(file);
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
        console.log("Encountered fatal error encrypting file.", err);
        throw err;
      });
    }
  });
}])
.controller('ImageUploadCtrl', ['$scope', '$http', function($scope, $http) {
  $scope.get_auth_headers = $scope.$parent.get_auth_headers;
  $scope.imgDataUri = $scope.$parent.imgDataUri;
  $scope.imageUploadObj = {};

  $scope.deletePicture = function() {
    $http({
      method: 'DELETE',
      url: $scope.imageUploadUrl,
      headers: $scope.get_auth_headers()
    }).then(function successCallback() {
      $scope.imageUploadModel[$scope.imageUploadModelAttr] = '';
      $scope.imageUploadObj.flow.files = [];
    }, function errorCallback() { });
  };
}]);
