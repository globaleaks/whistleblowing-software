GLClient.controller('StatusCtrl',
  ['$scope', '$rootScope', '$location', '$route', '$routeParams', '$http', 'Authentication', 'Tip', 'WBTip', 'Contexts', 'ReceiverPreferences',
  function($scope, $rootScope, $location, $route, $routeParams, $http, Authentication, Tip, WBTip, Contexts, ReceiverPreferences) {
    $scope.tip_id = $routeParams.tip_id;
    $scope.session = Authentication.id;
    $scope.xsrf_token = $.cookie('XSRF-TOKEN');
    $scope.target_file = '#';

    $scope.auth_landing_page = Authentication.auth_landing_page;

    if (Authentication.role === 'wb') {
      var url = '/wbtip/upload';

      $scope.options = {
        url: url,
        multipart: false,
        headers: Authentication.headers(),
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
          $scope.fields = [];

          angular.forEach(contexts, function(context, k){
            if (context.id == $scope.tip.context_id) {
              $scope.current_context = context;
            }
          });

          angular.forEach($scope.current_context.fields,
                          function(field){
            $scope.fieldFormat[field.key] = field;
          });

          angular.forEach(tip.fields,
                          function(field, k){
            $scope.fields.push({
                                'key': k,
                                'value': field.value,
                                'answer_order': field.answer_order
                              });
          });


        });
      });

      $scope.$watch('tip.msg_receiver_selected', function(){
        if ($scope.tip) {
          $scope.tip.updateMessages();
        }
      }, true);

    } else if (Authentication.role === 'receiver') {
      $scope.preferences = ReceiverPreferences.get();
    
      var TipID = {tip_id: $scope.tip_id};
      new Tip(TipID, function(tip){
        
        $scope.tip_unencrypted = false;
        angular.forEach(tip.receivers, function(receiver){
          if (receiver.gpg_key_status == 'Disabled' && receiver.receiver_id !== tip.receiver_id) {
            $scope.tip_unencrypted = true;
          };
        });

        Contexts.query(function(contexts){
          $scope.tip = tip;

          $scope.contexts = contexts;

          $scope.fieldFormat = {};
          $scope.fields = [];

          angular.forEach(contexts, function(context, k){
            if (context.id == $scope.tip.context_id) {
              $scope.current_context = context;
            }
          });
          angular.forEach($scope.current_context.fields,
                          function(field){
            $scope.fieldFormat[field.key] = field; 
          });

          angular.forEach(tip.fields,
                          function(field, k){
            $scope.fields.push({
                                'key': k,
                                'value': field.value,
                                'answer_order': field.answer_order
                              });
          });

          $scope.increaseDownloadCount = function(file) {
            file.downloads = parseInt(file.downloads) + 1;
          };

          $scope.increaseDownloadCounts = function () {
            for (file in $scope.tip.files) {
              $scope.tip.files[file].downloads = parseInt($scope.tip.files[file].downloads) + 1;
            }
          };
          
          $scope.download_all_enabled = function() {
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
      search = 'src=' + $location.path();
      $location.path('/login');
      $location.search(search);
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
