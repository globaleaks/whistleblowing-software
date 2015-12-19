GLClient.controller('TipCtrl',
  ['$scope', '$rootScope', '$location', '$route', '$routeParams', '$uibModal', '$http', '$filter', 'Authentication', 'RTip', 'WBTip', 'ReceiverPreferences',
  function($scope, $rootScope, $location, $route, $routeParams, $uibModal, $http, $filter, Authentication, RTip, WBTip, ReceiverPreferences) {
    $scope.tip_id = $routeParams.tip_id;
    $scope.session = Authentication.id;
    $scope.target_file = '#';

    $scope.answers = {};
    $scope.uploads = {};

    $scope.showEditLabelInput = false;

     $scope.minY = function(arr) {
       return $filter('min')($filter('map')(arr, 'y'));
    };

    $scope.splitRows = function(fields) {
      var rows = $filter('groupBy')(fields, 'y');
      rows = $filter('toArray')(rows);
      rows = $filter('orderBy')(rows, $scope.minY);
      return rows;
    };

    $scope.extractSpecialTipFields = function(tip) {
      angular.forEach(tip.questionnaire, function(step) {
        var i = step.children.length;
        while (i--) {
          if (step.children[i]['key'] == 'whistleblower_identity') {
            $scope.whistleblower_identity_field = step.children[i];
            step.children.splice(i, 1);
            $scope.fields = $scope.whistleblower_identity_field.children;
            $scope.rows = $scope.splitRows($scope.fields);
          }
        }
      });
    };

    $scope.getFields = function(field) {
      if (field === undefined) {
        return $scope.tip.fields;
      } else {
        return field.children;
      }
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
      $scope.fileupload_url = $scope.getUploadUrl('/wbtip/upload');

      new WBTip(function(tip) {
        $scope.extractSpecialTipFields(tip);

        $scope.tip = tip;

        // FIXME: remove this variable that is now needed only to map wb_identity_field
        $scope.submission = tip;

        $scope.provideIdentityInformation = function(identity_field_id, identity_field_answers) {
          return $http.post('/wbtip/' + $scope.tip.id + '/provideidentityinformation',
                            {'identity_field_id': identity_field_id, 'identity_field_answers': identity_field_answers}).
              success(function(data, status, headers, config){
                $route.reload();
              });
        };

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

    $scope.allowWhistleblowerToComment = function() {
      return $scope.tip.setVar('enable_two_way_comments', true);
    };

    $scope.denyWhistleblowerToComment = function() {
      return $scope.tip.setVar('enable_two_way_comments', false);
    };

    $scope.allowWhistleblowerToMessage = function() {
      return $scope.tip.setVar('enable_two_way_messages', true);
    };

    $scope.denyWhistleblowerToMessage = function() {
      return $scope.tip.setVar('enable_two_way_messages', false);
    };

    $scope.allowWhistleblowerToAttachFiles = function() {
      return $scope.tip.setVar('enable_attachments', true);
    };

    $scope.denyWhistleblowerToAttachFiles = function() {
      return $scope.tip.setVar('enable_attachments', false);
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
      var modalInstance = $uibModal.open({
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
      var modalInstance = $uibModal.open({
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
      var modalInstance = $uibModal.open({
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
  ['$scope', '$http', '$route', '$location', '$uibModalInstance', 'RTip', 'tip', 'operation',
   function ($scope, $http, $route, $location, $uibModalInstance, Tip, tip, operation) {
  $scope.tip = tip;
  $scope.operation = operation;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.ok = function () {
    $uibModalInstance.close();

    if ($scope.operation === 'postpone') {
      var req = {
        'operation': 'postpone',
        'args': {}
      };

      return $http({method: 'PUT', url: '/rtip/' + tip.id, data: req}).success(function (response) {
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
  ['$scope', '$http', '$route', '$uibModalInstance', 'tip',
   function ($scope, $http, $route, $uibModalInstance, tip) {
  $scope.tip = tip;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.ok = function () {
    $uibModalInstance.close();

    return $http.post('/rtip/' + tip.id + '/identityaccessrequests', {'request_motivation': $scope.request_motivation}).
        success(function(data, status, headers, config){
          $route.reload();
        });
  };
}]);
