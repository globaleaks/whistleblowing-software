GLClient.controller('MainCtrl', ['$scope', '$http', '$route', 'StaticFiles',
  function($scope, $http, $route, StaticFiles) {
    $scope.started = true;
  }
]);

angular.module('GLClient.fileuploader', ['blueimp.fileupload'])
  .config(['$httpProvider', 'fileUploadProvider',
    function ($httpProvider, fileUploadProvider) {
      delete $httpProvider.defaults.headers.common['X-Requested-With'];
      angular.extend(fileUploadProvider.defaults, {
        multipart: false,
      });
    }
]);

