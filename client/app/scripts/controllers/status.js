GLClient.controller('StatusCtrl',
  ['$scope', '$rootScope', '$location', '$route', '$routeParams', '$http', 'Authentication', 'Tip', 'WBTip', 'Contexts', 'Fields', 'ReceiverPreferences',
  function($scope, $rootScope, $location, $route, $routeParams, $http, Authentication, Tip, WBTip, Contexts, Fields, ReceiverPreferences) {


    $scope.tip_id = $routeParams.tip_id;
    $scope.session = Authentication.id;
    $scope.xsrf_token = $.cookie('XSRF-TOKEN');
    $scope.target_file = '#';

    $scope.auth_landing_page = Authentication.auth_landing_page;

    $scope.getFields = function(field) {
      if (field === undefined) {
        return $scope.tip.fields;
      } else {
        return field.children; }
    }

    $scope.filterFields = function(field) {
      if(field.type != 'fileupload') {
        return true;
      } else {
        return false;
      }
    }

    if (Authentication.role === 'wb') {

      $scope.fileupload_url = '/wbtip/upload';

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

      $scope.tip = new WBTip(function(tip){

        Contexts.query(function(contexts){

          Fields.query(function (fields) {

            $scope.tip = tip;

            angular.forEach(contexts, function(context, k){
              if (context.id == tip.context_id) {
                $scope.current_context = context;
              }
            });

            $scope.indexed_fields = _.reduce(fields, function (o, item) {
              o[item.id] = item; return o
            }, {});


            $scope.$watch('tip.msg_receiver_selected', function(){
              if ($scope.tip) {
                $scope.tip.updateMessages();
              }
            }, true);

          });

        });
      });

    } else if (Authentication.role === 'receiver') {
      $scope.preferences = ReceiverPreferences.get();
    
      var TipID = {tip_id: $scope.tip_id};
      $scope.tip = new Tip(TipID, function(tip){

        Contexts.query(function(contexts){

          Fields.query(function (fields) {

            $scope.tip = tip;

            $scope.tip_unencrypted = false;
            angular.forEach(tip.receivers, function(receiver){
              if (receiver.gpg_key_status == 'Disabled' && receiver.receiver_id !== tip.receiver_id) {
                $scope.tip_unencrypted = true;
              };
            });


            $scope.indexed_fields = _.reduce(fields, function (o, item) {
              o[item.id] = item; return o
            }, {});

            angular.forEach(contexts, function(context, k){
              if (context.id == $scope.tip.context_id) {
                $scope.current_context = context;
              }
            });

            $scope.fields = [];
            angular.forEach(tip.fields,
                            function(field, k){
              $scope.fields.push({
                                  'key': k,
                                  'value': field.value
                                });
            });

            $scope.increaseDownloadCount = function(file) {
              if (file.downloads < $scope.tip.download_limit) {
                file.downloads = parseInt(file.downloads) + 1;
              }
            };

            $scope.increaseDownloadCounts = function () {
              for (file in $scope.tip.files) {
                if ($scope.tip.files[file].downloads < $scope.tip.download_limit) {
                  $scope.tip.files[file].downloads = parseInt($scope.tip.files[file].downloads) + 1;
                }
              }
            };
          
            $scope.download_all_enabled = function() {
              download_all = false;
      
              for (file in $scope.tip.files) { 
                if ($scope.tip.files[file].downloads < $scope.tip.download_limit) { 
                  download_all = true;
                } 
              }

              $scope.$watch('tip.msg_receiver_selected', function(){
                if ($scope.tip) {
                  $scope.tip.updateMessages();
                }
              }, true);

              return download_all;
            }
          });
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
