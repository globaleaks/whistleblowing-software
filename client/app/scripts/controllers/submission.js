GLClient.controller('SubmissionCtrl',
    ['$scope', '$rootScope', '$filter', '$location', '$timeout', '$modal', 'Authentication', 'Submission',
      function ($scope, $rootScope, $filter, $location, $timeout, $modal, Authentication, Submission) {

  $rootScope.invalidForm = true;

  $scope.context_id = $location.search().context;
  $scope.receivers_ids = $location.search().receivers;
  $scope.contexts_selectable = $location.search().contexts_selectable;
  $scope.receivers_selectable = $location.search().receivers_selectable;

  $scope.problemToBeSolved = false;

  $scope.captchaProblemSolved = function() {
    $scope.submission._submission.human_captcha = false;
    $scope.problemToBeSolved = false;
  }

  $scope.openProblemDialog = function(submission){
    var modalInstance = $modal.open({
        templateUrl:  'views/partials/captchas.html',
        controller: 'ConfirmableDialogCtrl',
        backdrop: 'static',
        keyboard: false,
        resolve: {
          object: function () {
            return submission;
          }
        }

    });

    modalInstance.result.then(
       function(result) { $scope.captchaProblemSolved($scope.submission); },
       function(result) { }
    );
  };

  if ($scope.receivers_ids) {
    try {
      $scope.receivers_ids = JSON.parse($scope.receivers_ids);
    }
    catch(err) {
      $scope.receivers_ids = undefined;
    }
  }

  if ($scope.contexts_selectable === "false" && $scope.context_id) {
    $scope.contexts_selectable = false;
  } else {
    $scope.contexts_selectable = true;
  }

  if ($scope.receivers_selectable === "false" && $scope.receivers_ids) {
    $scope.receivers_selectable = false;
  } else {
    $scope.receivers_selectable = true;
  }

  if ($scope.node.show_contexts_in_alphabetical_order) {
    $scope.contextsOrderPredicate = 'name';
  } else {
    $scope.contextsOrderPredicate = 'presentation_order';
  }

  var checkReceiverSelected = function () {
    $scope.receiver_selected = false;
    // Check if there is at least one selected receiver
    angular.forEach($scope.submission.receivers_selected, function (receiver) {
      $scope.receiver_selected = $scope.receiver_selected | receiver;
    });

  };

  var startCountdown = function() {
    $scope.submission.wait = true;

    $scope.submission.countdown = $scope.submission._submission.start_validity_secs;

    var countDown = function () {
      $scope.submission.countdown -= 1;
      if ($scope.submission.countdown <= 0) {
        $scope.submission.wait = false;
      } else {
        $timeout(countDown, 1000);
      }
    };

    countDown();
  }

  $scope.selectable = function () {
    if ($scope.submission.context.maximum_selectable_receivers === 0) {
      return true;
    }

    return $scope.selected_receivers_count() < $scope.submission.maximum_selectable_receivers;
  };

  $scope.switch_selection = function (receiver) {
    if (receiver.configuration !== 'default' || (!$scope.node.allow_unencrypted && receiver.missing_pgp)) {
      return;
    }
    if ($scope.submission.receivers_selected[receiver.id] || $scope.selectable()) {
      $scope.submission.receivers_selected[receiver.id] = !$scope.submission.receivers_selected[receiver.id];
    }
  };

  $scope.getCurrentStepIndex = function(){
    return $scope.selection;
  };

  // Go to a defined step index
  $scope.goToStep = function(index) {
    $scope.selection = index;
  };

  $scope.hasNextStep = function(){
    if ($scope.selected_context === undefined) {
      return false;
    }

    return $scope.selection < $scope.selected_context.steps.length;
  };

  $scope.hasPreviousStep = function(){
    if ($scope.selected_context === undefined) {
      return false;
    }

    return $scope.selection > 0;
  };

  $scope.incrementStep = function() {
    if ($scope.hasNextStep()) {
      $scope.selection++;
    }
  };

  $scope.decrementStep = function() {
    if ($scope.hasPreviousStep()) {
      $scope.selection--;
    }
  };

  $scope.fileupload_url = function() {
    if (!$scope.submission) {
      return;
    }

    return 'submission/' + $scope.submission._submission.id + '/file';
  };

  $scope.prepareSubmission = function(context, receivers_ids) {
    $scope.submission.create(context.id, receivers_ids, function () {
      startCountdown();

      $scope.problemToBeSolved = $scope.submission._submission.human_captcha !== false;

      if ($scope.problemToBeSolved) {
        $scope.openProblemDialog($scope.submission);
      }

      if ($scope.submission.context.show_receivers_in_alphabetical_order) {
        $scope.receiversOrderPredicate = 'name';
      } else {
        $scope.receiversOrderPredicate = 'presentation_order';
      }

      if ((!$scope.receivers_selectable || !$scope.submission.context.show_receivers)) {
        $scope.skip_first_step = true;
        $scope.selection = 1;
      } else {
        $scope.skip_first_step = false;
        $scope.selection = 0;
      }

      checkReceiverSelected();
    });
  }

  $scope.$watch('submission.receivers_selected', function () {
    if ($scope.submission) {
      checkReceiverSelected();
    }
  }, true);

  new Submission(function(submission) {
    $scope.submission = submission;

    var context = null;

    if ($scope.context_id) {
      context = $filter('filter')($rootScope.contexts,
                                  {"id": $scope.context_id})[0];
    } else if ($rootScope.contexts.length == 1) {
      context = $rootScope.contexts[0];
    }

    if (context) {
      $scope.selected_context = context;
      $scope.prepareSubmission(context, $scope.receivers_ids);
    }

    // Watch for changes in certain variables
    $scope.$watch('selected_context', function (newVal, oldVal) {
      if (newVal && newVal !== oldVal) {
        if ($scope.submission && $scope.selected_context) {
          $scope.prepareSubmission($scope.selected_context, []);
        }
      }
    });

  });

}]).
controller('SubmissionStepCtrl', ['$scope', function($scope) {
  $scope.uploads = [];
}]).
controller('SubmissionFieldCtrl', ['$scope', function ($scope) {
  if ($scope.field.type === 'fileupload') {
    $scope.field.value = {};
    $scope.upload_callbacks = [];

    var upload_callback = function(e, data) {
      var uploading = false;

      $scope.uploads.forEach(function (u) {
        if (!u.done) {
          uploading = true;
        }

        // TODO: https://github.com/globaleaks/GlobaLeaks/issues/1239

      });

      $scope.submission.uploading = uploading;

    };

    $scope.upload_callbacks.push(upload_callback);
  }

  $scope.getClass = function(stepIndex, fieldIndex, toplevel) {
    if (toplevel) {
      return "submission-step" + stepIndex + "-field" + fieldIndex;
    } else {
      return "";
    }
  };

  $scope.validateRequiredCheckbox = function(field) {
    if (!field.required) {
      return true;
    }

    var ret = false;
    angular.forEach(field.value, function (value) {
      if (value.value && value.value === true) {
        ret |= true;
      }
    });

    return ret;
  };

}]).
controller('ReceiptController', ['$scope', '$location', 'Authentication', 'WhistleblowerTip',
  function($scope, $location, Authentication, WhistleblowerTip) {
    var format_keycode = function(keycode) {
      var ret = keycode;
      if (keycode && keycode.length === 16) {
        ret =  keycode.substr(0, 4) + ' ' +
               keycode.substr(4, 4) + ' ' +
               keycode.substr(8, 4) + ' ' +
               keycode.substr(12, 4);
      }

      return ret;

    };

    $scope.keycode = format_keycode(Authentication.keycode);
    $scope.formatted_keycode = format_keycode($scope.keycode);
}]);
