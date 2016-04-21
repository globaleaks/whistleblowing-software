GLClient.controller('WBFileUploadCtrl', ['$scope', function($scope)  {
  $scope.disabled = false;

  $scope.$on('flow::fileAdded', function (event, flow, file) {
    $scope.error_msg = undefined;
    if (file.size > $scope.node.maximum_filesize * 1024 * 1024) {
      $scope.error_msg = "This file exceeds the maximum upload size for this server.";
      event.preventDefault();
    } else {
      // as soon as a file is loaded.
      $scope.disabled = true;
    }
  };
}])
// glFlowBtn is an adaptation of flow-btn from ng-flow. It specifically replaces
// the default behavior of flow-btn as it attaches the 'change' listener to the 
// attached input DOM element. This is done to add file encryption before the handoff
// of a file to the $flow object.
// Source: https://github.com/flowjs/ng-flow/blob/master/src/directives/btn.js
.directive('glFlowBtn', ['$q', function($q) {

  // customAssignBrowse is copied with some modification from FlowJs:
  // https://github.com/flowjs/flow.js/blob/master/src/flow.js#L370
  function customAssignBrowse(domNodes, isDirectory, singleFile, attributes){ 
    if (typeof domNodes.length === 'undefined') {
      domNodes = [domNodes];
    }

    Flow.each(domNodes, function (domNode) {
      var input;
      if (domNode.tagName === 'INPUT' && domNode.type === 'file') {
        input = domNode;
      } else {
        input = document.createElement('input');
        input.setAttribute('type', 'file');
        Flow.extend(input.style, {
          visibility: 'hidden',
          position: 'absolute',
          width: '1px',
          height: '1px'
        });
        domNode.appendChild(input);

        domNode.addEventListener('click', function() {
          input.click();
        }, false);
      }
      if (!this.opts.singleFile && !singleFile) {
        input.setAttribute('multiple', 'multiple');
      }
      if (isDirectory) {
        input.setAttribute('webkitdirectory', 'webkitdirectory');
      }
      Flow.each(attributes, function (value, key) {
        input.setAttribute(key, value);
      });
      
      var $ = this;
      // The change event is fired when a file (or files) is selected on the input.
      // This is when we want to modify the file blob.
      input.addEventListener('change', function (e) {
        if (e.target.value) {
          console.log("Adding custom file instead of: ", e.target.files);
          var inputFile = e.target.files.item(0);
          encryptedFileRead(inputFile).then(function(outputFile) {
            // NOTE output file is not implemented properly yet.
            $.addFiles([outputFile], e);
            e.target.value = '';
          });
        }
      }, false);
    }, this);
  }

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

  // encryptFile is a mock funciton that should encrypt the passed Uint8Array.
  function encryptFile(fileArr, receiverPubKeys) {
  // NOTE this function does not work.
    var deferred = $q.defer();
    var options = {
      data: fileArr,
      publicKeys: receiverPubKeys,
      armor: false,
      format: 'binary',
    };
    openpgp.encrypt(options).then(function(ciphertext) {
      deferred.resolve(ciphertext); 
    });
    return deferred.promise;
  }

  // encryptedFileRead takes a plaintext File as input and returns a ciphertext 
  // file as output. It is still a TODO.
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

  return {
    'restrict': 'A',
    'scope': false,
    'require': '^flowInit',
    'link': function(scope, element, attrs) {
      var isDirectory = attrs.hasOwnProperty('flowDirectory');
      var isSingleFile = attrs.hasOwnProperty('flowSingleFile');
      var inputAttrs = attrs.hasOwnProperty('flowAttrs') && scope.$eval(attrs.flowAttrs);
      scope.$flow.assignBrowse = customAssignBrowse;
      scope.$flow.assignBrowse(element, isDirectory, isSingleFile, inputAttrs);

      // Alternativo optione
      // --------------------------
      // Create a custom force encryption directive. 
      // Make sure linker is executed last.
        // must enforce flow-btn presence.
      // Detect if input exists. If not fail
      // Clone the html input element
      // Delete the old input.
      // Attach new listener to input with same logic as above
      // Perform encryption through service interface.
      // Call $flow.addFiles( )
      // Upload normally.
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
