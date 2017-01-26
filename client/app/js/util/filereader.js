'use strict';

// MIT LICENSED by Matteo Suppo and modified by nskelsey

angular.module('ngFileReader', [])
  .factory('FileReader', ['$q', '$window', function ($q, $window) {

  // Wrap the onLoad event in the promise
  var onLoad = function(reader, deferred, scope) {
    return function () {
      scope.$apply(function () {
        deferred.resolve(reader.result);
      });
    };
  };

  // Wrap the onLoad event in the promise
  var onError = function (reader, deferred, scope) {
    return function () {
      scope.$apply(function () {
        deferred.reject(reader.result);
      });
    };
  };

  // Wrap the onProgress event by broadcasting an event
  var onProgress = function(reader, scope) {
    return function (event) {
      scope.$broadcast('fileProgress', {
        total: event.total,
        loaded: event.loaded
      });
    };
  };

  // Instantiate a new FileReader with the wrapped properties
  var getReader = function(deferred, scope) {
    var reader = new $window.FileReader();
    reader.onload = onLoad(reader, deferred, scope);
    reader.onerror = onError(reader, deferred, scope);
    reader.onprogress = onProgress(reader, scope);
    return reader;
  };

  var readAsDataURL = function(file, scope) {
    var deferred = $q.defer();

    var reader = getReader(deferred, scope);
    reader.readAsDataURL(file);

    return deferred.promise;
  };
  
  // Read a file as a text
  var readAsText = function(file, scope) {
    var deferred = $q.defer();

    var reader = getReader(deferred, scope);
    reader.readAsText(file);

    return deferred.promise;
  };

  return {
    readAsText: readAsText,
    readAsDataURL: readAsDataURL,
  };
}]);
