GLClient.controller('StatusCtrl',
  ['$scope', '$rootScope', '$location', '$route', '$routeParams', '$http', 'Tip', 'WBTip', 'Contexts', 'ReceiverPreferences',
  function($scope, $rootScope, $location, $route, $routeParams, $http, Tip, WBTip, Contexts, ReceiverPreferences) {
    $scope.tip_id = $routeParams.tip_id;

    if ($.cookie('role') === 'wb') {
      var url = '/wbtip/upload',
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

      new WBTip(function(tip){

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

      $scope.$watch('tip.msg_receiver_selected', function(){
        if ($scope.tip) {
          $scope.tip.updateMessages();
        }
      }, true);

    } else if ($.cookie('role') === 'receiver') {
      $scope.preferences = ReceiverPreferences.get();
    
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

          $scope.increaseDownloadCount = function(file) {
            file.downloads = parseInt(file.downloads) + 1;
          };

          $scope.increaseDownloadCounts = function() {
            for (file in $scope.tip.files) { 
              $scope.tip.files[file].downloads = parseInt($scope.tip.files[file].downloads) + 1;
            } 
          }

          $scope.show_download_all = function() {
            download_all = false;
      
            for (file in $scope.tip.files) { 
              if ($scope.tip.files[file].downloads < $scope.tip.download_limit) { 
                download_all = true;
              } 
            } 

            return download_all;
          }

        });
      });
    } else {
      $location.path('/');
    }

    $scope.newComment = function() {
      $scope.tip.newComment($scope.newCommentContent);
      $scope.newCommentContent = '';
    };

    $scope.newMessage = function() {
      $scope.tip.newMessage($scope.newMessageContent);
      $scope.newMessageContent = '';
    };


    $scope.getField = function(field_name) {
      angular.forEach($scope.current_context.fields,
                      function(field){
        if ( field.key  == field_name ) {
          return field; 
        }
      });
    };

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
