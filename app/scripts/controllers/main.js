GLClient.controller('MainCtrl', ['$scope', '$http', '$route', '$location', 'Node',
  function($scope, $http, $route, $location, Node) {
    $scope.started = true;

    $scope.custom_stylesheet = '/custom_stylesheet.css';
    $scope.logo = '/static/globaleaks_logo.png';

    $scope.update_node = function () {
      Node.get(function (node) {
        $scope.node = node;
        if (!$scope.node.wizard_done) {
          $location.path('/wizard');
        }
      });
    };

    $scope.update = function(model) {
      var success = {};
      success.message = "Updated " + model;
      model.$update(function(){
        if (!$scope.successes) {
          $scope.successes = [];
        };
        $scope.successes.push(success);
      });
    };

    $scope.randomFluff = function () {
      return Math.round(Math.random() * 1000000);
    };

    var refresh = function () {
      $scope.custom_stylesheet = '/custom_stylesheet.css?' + $scope.randomFluff();
      $scope.logo = '/static/globaleaks_logo.png?' + $scope.randomFluff();
    };

    $scope.$on("REFRESH", refresh);

    $scope.$on('$routeChangeStart', function(next, current) {
      $scope.update_node();
    });

    $scope.update_node();

    $scope.isHomepage = function () {
      return ($location.path() == '/');
    };

    $scope.hasSubtitle = function() {
      return $scope.header_subtitle != '';
    }
  }
]);

GLClient.controller('ModalCtrl', ['$scope', 
  function($scope, $modalInstance, error) {
    $scope.error = error;
    $scope.seconds = error.arguments[0];
}]);

TabCtrl = ['$scope', function($scope) {
  /* Empty controller function used to implement TAB pages */
}];

GLClient.controller('DisableEncryptionCtrl', ['$scope', '$modalInstance', function($scope, $modalInstance){
    $scope.close = function() {
      $modalInstance.close(false);
    };

    $scope.no = function() {
      $modalInstance.close(false);
    };
    $scope.ok = function() {
      $modalInstance.close(true);
    };

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

