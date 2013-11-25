GLClient.controller('StatusCtrl',
  ['$scope', '$rootScope', '$location', '$route', '$routeParams', '$http', 'Tip', 'Contexts', 'ReceiverPreferences',
  function($scope, $rootScope, $location, $route, $routeParams, $http, Tip, Contexts, ReceiverPreferences) {
    $scope.tip_id = $routeParams.tip_id;

    if ($.cookie('role') === 'wb') {
      $rootScope.whistleblower_tip_id = $.cookie('tip_id');

      var url = '/tip/' + $rootScope.whistleblower_tip_id + '/upload',
        headers = {};
      if ($.cookie('session_id')) {
        headers['X-Session'] = $.cookie('session_id');
      };

      if ($.cookie('XSRF-TOKEN')) {
        headers['X-XSRF-TOKEN'] = $.cookie('XSRF-TOKEN');
      }

      if ($.cookie('language')) {
        headers['GL-Language'] = $.cookie('language');
      };

      $scope.options = {
        url: url,
        multipart: false,
        headers: headers,
        autoUpload: true,
      };

      $scope.queue = [];

      $scope.$watch('queue', function(){
        $scope.uploading = false;
        if ($scope.queue) {
          $scope.queue.forEach(function(k){
            if (!k.id)
              $scope.uploading = true;
          });
        }
      }, true);

    }

    if ($.cookie('role') === 'receiver') {
      $scope.preferences = ReceiverPreferences.get();
    }
    
    var TipID = {tip_id: $scope.tip_id};
    new Tip(TipID, function(tip){

      Contexts.query(function(contexts){
        $scope.tip = tip;
        $scope.contexts = contexts;
        $scope.fieldFormat = {};

        angular.forEach(contexts, function(context, k){
          if (context.context_gus == $scope.tip.context_gus) {
            $scope.current_context = context;
          }
        });
        angular.forEach($scope.current_context.fields,
                        function(field){
          $scope.fieldFormat[field.key] = field; 
        });

      });
    });

    $scope.getField = function(field_name) {
      angular.forEach($scope.current_context.fields,
                      function(field){
        if ( field.key  == field_name ) {
          return field; 
        }
      });
    };

    $scope.newComment = function() {
      $scope.tip.comments.newComment($scope.newCommentContent);
      $scope.newCommentContent = '';
    };

    $scope.increaseDownloadCount = function(file) {
      file.downloads = parseInt(file.downloads) + 1;
    };

    $scope.download = function(url) {
       return $http.get(url);
    }

  }]);

GLClient.controller('FileDetailsCtrl', ['$scope', function($scope){
    $scope.securityCheckOpen = false;

    $scope.openSecurityCheck = function() {
      $scope.securityCheckOpen = true;
    };

    $scope.closeSecurityCheck = function() {
      $scope.securityCheckOpen = false;
    };

    $scope.securityCheckOptions = {
      backdropFade: true,
      dialogFade: true
    }
}]);
