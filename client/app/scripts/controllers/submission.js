GLClient.controller('SubmissionCtrl',
    ['$scope', '$rootScope', '$location', '$modal', 'Authentication', 'Submission',
      function ($scope, $rootScope, $location, $modal, Authentication, Submission) {

  $rootScope.invalidForm = true;

  var context_id = $location.search().context;
  var receivers_ids = $location.search().receivers;
  var contexts_selectable = $location.search().contexts_selectable;
  var receivers_selectable = $location.search().receivers_selectable;

  if (receivers_ids) {
    try {
      receivers_ids = JSON.parse(receivers_ids);
    }
    catch(err) {
      receivers_ids = undefined;
    }
  }

  if (contexts_selectable === "false" && context_id) {
    $scope.contexts_selectable = false;
  } else {
    $scope.contexts_selectable = true;
  }

  if (receivers_selectable === "false" && receivers_ids) {
    $scope.receivers_selectable = false;
  } else {
    $scope.receivers_selectable = true;
  }

  if ($scope.node.show_contexts_in_alphabetical_order) {
    $scope.contextsOrderPredicate = 'name';
  } else {
    $scope.contextsOrderPredicate = 'presentation_order';
  }

  new Submission(function (submission) {
    $scope.submission = submission;
    $scope.fields = submission.fields;
    $scope.indexed_fields = submission.indexed_fields;
    $scope.submit = $scope.submission.submit;
  }, context_id, receivers_ids);

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
    if ($scope.submission.current_context.maximum_selectable_receivers === 0) {
      return true;
    }

    return $scope.selected_receivers_count() < $scope.submission.current_context.maximum_selectable_receivers;
  };

  $scope.switch_selection = function (receiver) {
    if (receiver.configuration !== 'default' || (!$scope.submission.allow_unencrypted && receiver.missing_pgp)) {
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
    if ($scope.submission.current_context === undefined) {
      return false;
    }

    return $scope.selection < $scope.submission.current_context.steps.length;
  };

  $scope.hasPreviousStep = function(){
    if ($scope.submission.current_context === undefined) {
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

    return '/submission/' + $scope.submission.current_submission.id + '/file';
  };


  // Watch for changes in certain variables
  $scope.$watch('submission.current_context', function () {
    if ($scope.submission && $scope.submission.current_context) {
      $scope.submission.create(function () {

        if ($scope.submission.current_context.show_receivers_in_alphabetical_order) {
          $scope.receiversOrderPredicate = 'name';
        } else {
          $scope.receiversOrderPredicate = 'presentation_order';
        }

        if ((!receivers_selectable && !$scope.submission.current_context.show_receivers)) {
          $scope.skip_first_step = true;
          $scope.selection = 1;
        } else {
          $scope.skip_first_step = false;
          $scope.selection = 0;
        }

      });
      checkReceiverSelected();
     }
  });

  $scope.$watch('submission.receivers_selected', function () {
    if ($scope.submission) {
      checkReceiverSelected();
    }
  }, true);

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
