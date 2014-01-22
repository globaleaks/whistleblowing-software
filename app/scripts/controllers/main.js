GLClient.controller('MainCtrl', ['$scope', '$rootScope', '$http', '$route', '$location', 'Node',
  function($scope, $rootScope, $http, $route, $location, Node) {
    $scope.started = true;

    $scope.custom_stylesheet = '/custom_stylesheet.css';
    $scope.logo = '/static/globaleaks_logo.png';

    $scope.update_node = function() {
      Node.get(function(node){
        $scope.node = node;
      });
    }

    $scope.randomFluff = function() {
      return Math.round(Math.random() * 1000000);
    }

    var refresh = function() {
      $scope.custom_stylesheet = '/custom_stylesheet.css?' + $scope.randomFluff();
      $scope.logo = '/static/globaleaks_logo.png?' + $scope.randomFluff();
    }

    $scope.$on("REFRESH", refresh);

    $scope.update_node();

    $scope.isHomepage = function () { 
      return ($location.path() == '/') ? true : false;
    }
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

