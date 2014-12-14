GLClient.controller('StatusCtrl',
  ['$scope', '$rootScope', '$location', '$route', '$routeParams', '$http', 'Authentication', 'Tip', 'WBTip', 'Contexts', 'ReceiverPreferences',
  function($scope, $rootScope, $location, $route, $routeParams, $http, Authentication, Tip, WBTip, Contexts, ReceiverPreferences) {


    $scope.tip_id = $routeParams.tip_id;
    $scope.session = Authentication.id;
    $scope.xsrf_token = $.cookie('XSRF-TOKEN');
    $scope.target_file = '#';

    $scope.auth_landing_page = Authentication.auth_landing_page;

    $scope.getFields = function(field) {
      ret = [];
      if (field === undefined) {
        fields = $scope.tip.fields;
      } else {
        fields = field.children;
      }

      angular.forEach(fields, function(field, k) {
        ret.push(field);
      });

      return ret;
    }

    $scope.filterFields = function(field) {
      if(field.type != 'fileupload') {
        return true;
      } else {
        return false;
      }
    }

    if (Authentication.role === 'wb') {

      $scope.userrole = 'wb';

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

          $scope.tip = tip;

          angular.forEach(contexts, function(context, k){
            if (context.id == tip.context_id) {
              $scope.current_context = context;
            }
          });

          $scope.$watch('tip.msg_receiver_selected', function (newVal, oldVal) {
            if (newVal && newVal !== oldVal) {
              if ($scope.tip) {
                $scope.tip.updateMessages();
              }
            }
          }, false);

          if ($scope.tip.receivers.length == 1 && $scope.tip.msg_receiver_selected == null) {
            $scope.tip.msg_receiver_selected = $scope.tip.msg_receivers_selector[0]['key'];
          }

          $scope.tip.updateMessages();

        });
      });

    } else if (Authentication.role === 'receiver') {

      $scope.userrole = 'receiver';

      $scope.preferences = ReceiverPreferences.get();
    
      var TipID = {tip_id: $scope.tip_id};
      $scope.tip = new Tip(TipID, function(tip){

        Contexts.query(function(contexts){

          $scope.tip = tip;

          $scope.tip_unencrypted = false;
          angular.forEach(tip.receivers, function(receiver){
            if (receiver.gpg_key_status == 'Disabled' && receiver.receiver_id !== tip.receiver_id) {
              $scope.tip_unencrypted = true;
            };
          });


          angular.forEach(contexts, function(context, k){
            if (context.id == $scope.tip.context_id) {
              $scope.current_context = context;
            }
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
      $scope.tip.newComment($scope.tip.newCommentContent);
      $scope.tip.newCommentContent = '';
    };

    $scope.newMessage = function() {
      $scope.tip.newMessage($scope.tip.newMessageContent);
      $scope.tip.newMessageContent = '';
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
