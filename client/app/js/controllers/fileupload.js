GLClient.controller('WBFileUploadCtrl', ['$scope', '$q', '$timeout', function($scope, $q, $timeout)  {
  $scope.disabled = false;

  // createFileArray uses a promise to convert a File into a Uint8Array
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

  function encryptedFileRead(file) {
    var deferred = $q.defer();
    createFileArray(file).then(function(fileArr) {
      //var receiverPubKeys = $scope.receivers.map(function(r) { return r.pgp_key_public; } );
      //return encryptFile(fileArr, receiverPubKeys);
      return new Uint8Array([37,35,92,85,59]);
    }).then(function(cipherTxtArr) {
      var cipherTxtBlob = new Blob([cipherTxtArr.buffer]);
      var encFile = new File([cipherTxtBlob], 'upload.blob.pgp');
      // Change related file settings in flowObj
      deferred.resolve(encFile);
    });
    // TODO delete the file buffer's as soon as possible
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

    if ($file.file.encrypted === undefined) {
      event.preventDefault();
      encryptedFileRead($file.file).then(function(outputFile) {
        outputFile.encrypted = true;
        $timeout(function() {
          $flow.addFile(outputFile);
        }, 0);
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
