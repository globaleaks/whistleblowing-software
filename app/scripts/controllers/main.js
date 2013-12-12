GLClient.controller('MainCtrl', ['$scope', '$rootScope', '$http', '$route', 'Node',
  function($scope, $rootScope, $http, $route, Node) {
    $scope.started = true;

    $rootScope.update_node = function() {
      Node.get(function(node){
        $rootScope.node = node;
      });
    }

    $rootScope.update_node();

  }
]);

TabCtrl = ['$scope', function($scope) {
  /* Empty controller function used to implement TAB pages */
}];

angular.module('GLClient.fileuploader', ['blueimp.fileupload'])
  .config(['$httpProvider', 'fileUploadProvider',
    function ($httpProvider, fileUploadProvider) {
      delete $httpProvider.defaults.headers.common['X-Requested-With'];
      angular.extend(fileUploadProvider.defaults, {
        multipart: false,
      });
    }
]);

