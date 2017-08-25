GLClient.factory('uploadUtils', ['$filter', function($filter) {
  // Utils shared across file upload controllers and directives

  function endsWith(subjectString, searchString) {
    // endsWith polyfill adapted for use with IE from:
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/endsWith
    var position = subjectString.length - searchString.length;
    if (position < 0 ) { return false; }
    var lastIndex = subjectString.lastIndexOf(searchString, position);
    return lastIndex !== -1 && lastIndex === position;
  }

  return {
    'validFilename': function(filename, types) {
      for (var i = 0; i < types.length; i++) {
        var s = filename.toLowerCase();
        if (endsWith(s, types[i])) {
            return true;
        }
      }
      return false;
    },

    'translateInvalidSizeErr': function(filename, maxSize) {
      var strs = ['Error with file:', 'File size not accepted.', 'Maximum file size is:'];
      angular.forEach(strs, function(s, i) {
        strs[i] = $filter('translate')(s);
      });
      return strs[0] + ' ' + filename + ' - ' + strs[1] + ' ' + strs[2] + ' ' + $filter('byteFmt')(maxSize, 2);
    },

    'translateInvalidTypeErr': function(filename, validTypes) {
      var uppercaseTypes = [];
      for (var i=0; i<validTypes.length; i++) {
        uppercaseTypes.push(validTypes[i].toUpperCase());
      }
      var strs = ['Error with file:', 'File type not accepted.', 'Accepted file types are:'];
      angular.forEach(strs, function(s, i) {
        strs[i] = $filter('translate')(s);
      });
      return strs[0] + ' ' + filename + ' - ' + strs[1] + ' ' + strs[2] + ' ' + uppercaseTypes;
    },
  };
}]).
controller('RFileUploadCtrl', ['$scope', function($scope) {
  $scope.disabled = false;

  $scope.$on('flow::fileAdded', function () {
    $scope.file_error_msgs = [];

    if ($scope.field !== undefined && !$scope.field.multi_entry) {
      // if the field allows to load only one file disable the button
      // as soon as a file is loaded.
      $scope.disabled = true;
    }
  });
}]).
controller('WBFileUploadCtrl', ['$scope', function($scope) {
  $scope.file_upload_description = "";

  $scope.beginUpload = function($files, $event, $flow) {
    $scope.file_error_msgs = [];

    $flow.opts.query = {'description': $scope.file_upload_description};
    $flow.upload();
  };
}]).
controller('ImageUploadCtrl', ['$scope', '$rootScope', '$http', 'uploadUtils', function($scope, $rootScope, $http, uploadUtils) {
  $scope.imageUploadObj = {};
  $scope.Utils = $rootScope.Utils;

  $scope.$on('flow::fileAdded', function (event, $flow, flowFile) {
    $scope.file_error_msgs = [];
    var validSize = $rootScope.node.maximum_filesize * 1024 * 1024;
    if (flowFile.size > validSize) {
      var errMsg = uploadUtils.translateInvalidSizeErr(flowFile.name, validSize);
      $scope.file_error_msgs.push(errMsg);
    }
  });

  $scope.deletePicture = function() {
    $http({
      method: 'DELETE',
      url: $scope.imageUploadUrl,
    }).then(function() {
      $scope.imageUploadModel[$scope.imageUploadModelAttr] = '';
      $scope.imageUploadObj.flow.files = [];
    });
  };
}]);
