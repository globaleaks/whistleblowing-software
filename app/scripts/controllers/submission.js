GLClient.controller('SubmissionCtrl',
    ['$scope', '$rootScope', '$location', 'Authentication', 'Node', 'Submission', 'Fields', 'Receivers', 'WhistleblowerTip',
      function ($scope, $rootScope, $location, Authentication, Node, Submission, Fields, Receivers, WhistleblowerTip) {

  $rootScope.invalidForm = true;
  $scope.receiptConfimation = "";

  Node.get(function (node) {
    $scope.node = node;

    new Submission(function (submission) {
      $scope.submission = submission;

      $scope.maximumFilesize = submission.maximum_filesize;

      $scope.current_context = submission.current_context;

      $scope.fields = submission.fields;
      $scope.indexed_fields = submission.indexed_fields;

      $scope.submission = submission;

      if ($scope.submission.contexts.length == 1 && !$scope.submission.current_context.show_receivers) {
        $scope.skip_first_step = true;
        $scope.selection = 1;
      } else {
        $scope.skip_first_step = false;
        $scope.selection = 0;
      }

      $scope.submit = $scope.submission.submit;

      checkReceiverSelected();
    });

  });

  var checkReceiverSelected = function () {
    $scope.receiver_selected = false;
    // Check if there is at least one selected receiver
    angular.forEach($scope.submission.receivers_selected, function (receiver) {
      $scope.receiver_selected = $scope.receiver_selected | receiver;
    });

  };

  $scope.selected_receivers_count = function () {
    var count = 0;

    if ($scope.submission) {
      angular.forEach($scope.submission.receivers_selected, function (selected) {
        if (selected) {
          count += 1;
        }
      });
    }

    return count;
  };

  $scope.selectable = function () {

    if ($scope.submission.current_context.maximum_selectable_receivers == 0) {
      return true;
    }

    return $scope.selected_receivers_count() < $scope.submission.current_context.maximum_selectable_receivers;
  };

  $scope.switch_selection = function (receiver) {
    if (receiver.disabled)
      return;
    if ($scope.submission.receivers_selected[receiver.id] || $scope.selectable()) {
      $scope.submission.receivers_selected[receiver.id] = !$scope.submission.receivers_selected[receiver.id];
    }
  };

  $scope.view_tip = function (receipt) {
    WhistleblowerTip(receipt, function () {
      $location.path('/status/');
    });
  };

  $scope.uploading = false;

  $scope.disclaimer = {accepted: false};

  // Watch for changes in certain variables
  $scope.$watch('submission.current_context', function () {
    if ($scope.current_context) {
      $scope.submission.create(function () {
        $scope.fileupload_url = '/submission/' + $scope.submission.current_submission.id + '/file';

      });
      checkReceiverSelected();

     }
  }, false);

  $scope.$watch('submission.receivers_selected', function () {
    if ($scope.submission) {
      checkReceiverSelected();
    }
  }, true);

  $rootScope.$watch('anonymous', function (newVal, oldVal) {
    if ($scope.node) {
      if (newVal == false && !$scope.node.tor2web_submission) {
        $location.path("/");
      }
    }
  });
}]).
controller('SubmissionFieldCtrl', ['$scope', '$rootScope', function ($scope, $rootScope) {
  $scope.queue = [];
  $scope.$watch('queue', function () {
    $scope.$parent.uploading = false;
    if ($scope.queue) {
      $scope.queue.forEach(function (k) {
        if (!k.id) {
          $scope.$parent.uploading = true;
        } else {
          $scope.submission.current_submission.files.push(k.id);
          if ($scope.submission.current_submission.wb_fields[$scope.field] == undefined) {
            $scope.submission.current_submission.wb_fields[$scope.field] = {};
          }
          $scope.submission.current_submission.wb_fields[$scope.field].value = k.id;
        }
      });
    }
  }, true);
}]).
controller('SubmissionFormController', ['$scope', '$rootScope', function ($scope, $rootScope) {
  $scope.$watch('submissionForm.$valid', function () {
    $rootScope.invalidForm = $scope.submissionForm.$invalid;
  }, true);
}]).
controller('SubmissionStepsCtrl', ['$scope', 'Fields', function($scope, Fields) {

  $scope.getCurrentStepIndex = function(){
    return $scope.selection;
  };

  // Go to a defined step index
  $scope.goToStep = function(index) {
    if ( $scope.uploading ) {
      return;
    }

    $scope.selection = index;
  };

  $scope.hasNextStep = function(){
    if ( $scope.current_context == undefined )
      return false;

    return $scope.selection < $scope.current_context.steps.length;
  };

  $scope.hasPreviousStep = function(){
    if ( $scope.current_context == undefined )
      return false;

    return $scope.selection > 0;
  };

  $scope.incrementStep = function() {
    if ( $scope.uploading )
      return;

    if ( $scope.hasNextStep() )
    {
      $scope.selection = $scope.selection + 1;
    }
  };

  $scope.decrementStep = function() {
    if ( $scope.uploading )
      return;

    if ( $scope.hasPreviousStep() )
    {
      $scope.selection = $scope.selection - 1;
    }
  };

}]);
