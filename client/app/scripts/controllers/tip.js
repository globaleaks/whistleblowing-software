GLClient.controller('TipCtrl',
  ['$scope', '$rootScope', '$location', '$route', '$routeParams', '$modal', '$http', 'Authentication', 'RTip', 'WBTip', 'ReceiverPreferences',
  function($scope, $rootScope, $location, $route, $routeParams, $modal, $http, Authentication, RTip, WBTip, ReceiverPreferences) {
    $scope.tip_id = $routeParams.tip_id;
    $scope.session = Authentication.id;
    $scope.target_file = '#';

    $scope.uploads = {};
    $scope.hideUploadWhenFinished = true;

    $scope.showEditLabelInput = false;

    $scope.fieldsRoot = [];

    $scope.extractSpecialTipFields = function(tip) {
      console.log(tip);
      angular.forEach(tip.questionnaire, function(step) {
        var i = step.children.length;
        while (i--) {
          if (step.children[i]['key'] == 'whistleblower_identity') {
            alert(step.children[i]['key']);
            $scope.whistleblower_identity_field = step.children[i];
            step.children.splice(i, 1);
          }
        }
      });

      //$scope.fieldsRoot = $scope.whistleblower_identity_field.children;
    }

    $scope.getFields = function(field) {
      var ret;
      var fields;
      if (field === undefined) {
        ret = $scope.tip.fields;
      } else {
        ret = field.children;
      }

      console.log(ret);
      return ret;
    };

    $scope.hasMultipleEntries = function(field_answer) {
      if (field_answer !== undefined) {
        return field_answer.length > 1;
      }

      return false;
    };

    $scope.filterFields = function(field) {
      return field.type !== 'fileupload';
    };

    $scope.filterReceivers = function(receiver) {
      return receiver.configuration !== 'hidden';
    };

    if (Authentication.role === 'whistleblower') {
      $scope.fileupload_url = '/wbtip/upload';

      new WBTip(function(tip) {
        $scope.extractSpecialTipFields(tip);

        $scope.tip = tip;

        angular.forEach($scope.contexts, function(context, k){
          if (context.id === tip.context_id) {
            $scope.current_context = context;
          }
        });

        if (tip.receivers.length === 1 && tip.msg_receiver_selected === null) {
          tip.msg_receiver_selected = tip.msg_receivers_selector[0].key;
        }

        tip.updateMessages();

        $scope.$watch('tip.msg_receiver_selected', function (newVal, oldVal) {
          if (newVal && newVal !== oldVal) {
            if ($scope.tip) {
              $scope.tip.updateMessages();
            }
          }
        }, false);

      });

    } else if (Authentication.role === 'receiver') {
      $scope.preferences = ReceiverPreferences.get();
    
      new RTip({id: $scope.tip_id}, function(tip) {
        $scope.extractSpecialTipFields(tip);

        $scope.tip = tip;

        $scope.showEditLabelInput = $scope.tip.label === '';

        $scope.tip_unencrypted = false;
        angular.forEach(tip.receivers, function(receiver){
          if (receiver.pgp_key_status === 'disabled' && receiver.receiver_id !== tip.receiver_id) {
            $scope.tip_unencrypted = true;
          }
        });

        angular.forEach($scope.contexts, function(context, k){
          if (context.id === $scope.tip.context_id) {
            $scope.current_context = context;
          }
        });

      });
    } else {
      if($location.path() === '/status') {
        // whistleblower
        $location.path('/');
      } else {
        // receiver
        var search = 'src=' + $location.path();
        $location.path('/login');
        $location.search(search);
      }
    }

    $scope.editLabel = function() {
      $scope.showEditLabelInput = true;
    };

    $scope.updateLabel = function(label) {
      $scope.tip.updateLabel(label);
      $scope.showEditLabelInput = false;
    };

    $scope.newComment = function() {
      $scope.tip.newComment($scope.tip.newCommentContent);
      $scope.tip.newCommentContent = '';
    };

    $scope.newMessage = function() {
      $scope.tip.newMessage($scope.tip.newMessageContent);
      $scope.tip.newMessageContent = '';
    };

    $scope.tip_delete = function () {
      var modalInstance = $modal.open({
        templateUrl: 'views/partials/tip_operation_delete.html',
        controller: 'TipOperationsCtrl',
        resolve: {
          tip: function () {
            return $scope.tip;
          },
          operation: function () {
            return 'delete';
          }
        }
      });
    };

    $scope.tip_postpone = function () {
      var modalInstance = $modal.open({
        templateUrl: 'views/partials/tip_operation_postpone.html',
        controller: 'TipOperationsCtrl',
        resolve: {
          tip: function () {
            return $scope.tip;
          },
          operation: function () {
            return 'postpone';
          }
        }
      });
    };

    $scope.file_identity_access_request = function () {
      var modalInstance = $modal.open({
        templateUrl: 'views/partials/tip_operation_file_identity_access_request.html',
        controller: 'IdentityAccessRequestCtrl',
        resolve: {
          tip: function () {
            return $scope.tip;
          }
        }
      });
    };
}]);

GLClient.controller('TipOperationsCtrl',
  ['$scope', '$http', '$route', '$location', '$modalInstance', 'RTip', 'tip', 'operation',
   function ($scope, $http, $route, $location, $modalInstance, Tip, tip, operation) {
  $scope.tip = tip;
  $scope.operation = operation;

  $scope.cancel = function () {
    $modalInstance.close();
  };

  $scope.ok = function () {
    $modalInstance.close();

    if ($scope.operation === 'postpone') {
      $scope.tip.operation = $scope.operation
      $scope.tip.$update(function() {
        $route.reload();
      });
    } else if ($scope.operation === 'delete') {
      return $http({method: 'DELETE', url: '/rtip/' + $scope.tip.id, data:{}}).
        success(function(data, status, headers, config) {
          $location.url('/receiver/tips');
          $route.reload();
        });
    }
  };
}]);

GLClient.controller('IdentityAccessRequestCtrl', 
  ['$scope', '$http', '$route', '$modalInstance', 'tip',
   function ($scope, $http, $route, $modalInstance, tip) {
  $scope.tip = tip;

  $scope.cancel = function () {
    $modalInstance.close();
  };

  $scope.ok = function () {
    $modalInstance.close();

    return $http.post('/rtip/' + tip.id + '/identityaccessrequests', {'request_motivation': $scope.request_motivation}).
        success(function(data, status, headers, config){
          $route.reload();
        });
  };
}]);
