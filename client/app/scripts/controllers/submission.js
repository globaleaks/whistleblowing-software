GLClient.controller('SubmissionCtrl',
    ['$scope', '$rootScope', '$location', '$modal', 'Authentication', 'Submission', 'Receivers', 'WhistleblowerTip',
      function ($scope, $rootScope, $location, $modal, Authentication, Submission, Receivers, WhistleblowerTip) {

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

  if (contexts_selectable == "false" && context_id) {
    $scope.contexts_selectable = false;
  } else {
    $scope.contexts_selectable = true;
  }

  if (receivers_selectable == "false" && receivers_ids) {
    $scope.receivers_selectable = false;
  } else {
    $scope.receivers_selectable = true;
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

    if ($scope.submission.current_context.maximum_selectable_receivers == 0) {
      return true;
    }

    return $scope.selected_receivers_count() < $scope.submission.current_context.maximum_selectable_receivers;
  };

  $scope.switch_selection = function (receiver) {
    if (receiver.configuration != 'default' || (!$scope.submission.allow_unencrypted && receiver.missing_pgp)) {
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
    if ($scope.uploading) {
      return;
    }

    $scope.selection = index;
  };

  $scope.hasNextStep = function(){
    if ($scope.submission.current_context == undefined)
      return false;

    return $scope.selection < $scope.submission.current_context.steps.length;
  };

  $scope.hasPreviousStep = function(){
    if ($scope.submission.current_context == undefined)
      return false;

    return $scope.selection > 0;
  };

  $scope.incrementStep = function() {
    if ($scope.uploading)
      return;

    if ($scope.hasNextStep()) {
      $scope.selection++;
    }
  };

  $scope.decrementStep = function() {
    if ($scope.uploading)
      return;

    if ($scope.hasPreviousStep()) {
      $scope.selection--;
    }
  };

  $scope.uploading = false;

  // Watch for changes in certain variables
  $scope.$watch('submission.current_context', function () {
    if ($scope.submission && $scope.submission.current_context) {
      $scope.submission.create(function () {

        if ((!receivers_selectable && !$scope.submission.current_context.show_receivers)) {
          $scope.skip_first_step = true;
          $scope.selection = 1;
        } else {
          $scope.skip_first_step = false;
          $scope.selection = 0;
        }

        $scope.fileupload_url = '/submission/' + $scope.submission.current_submission.id + '/file';
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
  $scope.queue = $scope.queue || [];
  $scope.files  = [];
  $scope.indexed_files_values = {};
}]).
controller('SubmissionFieldCtrl', ['$scope', '$rootScope', function ($scope, $rootScope) {
  if ($scope.field.type == 'fileupload') {
    $scope.field.value = [];
  }

  var update_uploads_status = function(e, data) {
    $scope.$parent.uploading = false;
    if ($scope.field.value === "") {
      $scope.field.value = [];
    }
    if ($scope.queue) {
      $scope.files.slice(0, $scope.files.length);
      $scope.queue.forEach(function (k) {
        if (!k.id) {
          $scope.$parent.uploading = true;
        } else {
          if ($scope.submission.current_submission.files.indexOf(k.id) === -1) {
            $scope.submission.current_submission.files.push(k.id);

            $scope.indexed_files_values[k.id] = {
              'id': k.id,
              'options': angular.copy($scope.field.options)
            }
          }

          $scope.field.value.push($scope.indexed_files_values[k.id]);
          k.value = $scope.indexed_files_values[k.id];
        }

        if ($scope.files.indexOf(k) === -1) {
          $scope.files.push(k);
        }
      });
    }
  };

  $scope.$on('fileuploadalways', update_uploads_status);

}]).
controller('ReceiptController', ['$scope', '$location', 'Authentication', 'WhistleblowerTip',
  function($scope, $location, Authentication, WhistleblowerTip) {

    function reverse_receipt(r){
      return r.split("").reverse().join("");
    }

  format_keycode = function(keycode, rtl) {
    if (keycode && keycode.length == 16) {
      ret =  keycode.substr(0, 4) + ' ' +
             keycode.substr(4, 4) + ' ' +
             keycode.substr(8, 4) + ' ' +
             keycode.substr(12, 4);
    } else {
      ret = keycode;
    }

    if (rtl) {
      ret = reverse_receipt(ret);
    }

    return ret;

  }

  $scope.keycode = format_keycode(Authentication.keycode);
  $scope.formatted_keycode = format_keycode($scope.keycode, $scope.rtl);
  $scope.formatted_keycode_ltr = format_keycode($scope.keycode, false);

  $scope.view_tip = function (keycode) {
    keycode = keycode.replace(/\D/g,'');
    WhistleblowerTip(keycode, function () {
      $location.path('/status/');
    });
  };
}]);
