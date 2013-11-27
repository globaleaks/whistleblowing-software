GLClient.controller('MainCtrl', ['$scope', '$http', '$route',
    function($scope, $http, $route) {
  $scope.started = true;

  $scope.delete = function(url) {
    return $http.delete(url).success(function(response){
               $route.reload();
           });
  }

}]);

angular.module('GLClient.fileuploader', ['blueimp.fileupload'])
  .config(['$httpProvider', 'fileUploadProvider',
    function ($httpProvider, fileUploadProvider) {
      delete $httpProvider.defaults.headers.common['X-Requested-With'];
      angular.extend(fileUploadProvider.defaults, {
        multipart: false,
      });
    }
]);

