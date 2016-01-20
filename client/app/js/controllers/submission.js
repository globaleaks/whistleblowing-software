GLClient.controller('SubmissionCtrl',
    ['$scope', '$rootScope', '$filter', '$location', '$timeout', '$uibModal', '$anchorScroll', 'Submission',
      function ($scope, $rootScope, $filter, $location, $timeout, $uibModal, $anchorScroll, Submission) {
  $scope.invalidForm = true;

  $scope.uploads = {};

  $scope.context_id = $location.search().context || undefined;
  $scope.receivers_ids = $location.search().receivers || [];
  $scope.contexts_selectable = $location.search().contexts_selectable;
  $scope.receivers_selectable = $location.search().receivers_selectable;

  $scope.problemToBeSolved = false;
  $scope.problemModal = undefined;

  $scope.problemSolved = function() {
    $scope.problemModal = undefined;
    $scope.submission._token.$update(function(token) {
      $scope.submission._token = token;
      $scope.problemToBeSolved = $scope.submission._token.human_captcha !== false;
      if ($scope.problemToBeSolved) {
        $scope.openProblemDialog($scope.submission);
      }
    });
  };

  $scope.openProblemDialog = function(submission){
    if ($scope.problemModal) {
      $scope.problemModal.dismiss();
    }

    $scope.problemModal = $uibModal.open({
        templateUrl: 'views/partials/captchas.html',
        controller: 'ConfirmableDialogCtrl',
        backdrop: 'static',
        keyboard: false,
        resolve: {
          object: function () {
            return submission;
          },
          problemSolved: function() {
            return $scope.problemSolved;
          }
        }

    });

    $scope.problemModal.result.then(
       function(result) { $scope.problemSolved($scope.submission); },
       function(result) { }
    );

  };

  if ($scope.receivers_ids) {
    try {
      $scope.receivers_ids = JSON.parse($scope.receivers_ids);
    }
    catch(err) {
      $scope.receivers_ids = [];
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

  $scope.public_contexts = $filter('filter')($rootScope.contexts, {'show_context': true});
  $scope.public_contexts = $filter('orderBy')($scope.public_contexts, $scope.contextsOrderPredicate);

  var startCountdown = function() {
    $scope.submission.wait = true;
    $scope.submission.pow = false;

    $scope.submission.countdown = $scope.submission._token.start_validity_secs;

    var countDown = function () {
      $scope.submission.countdown -= 1;
      if ($scope.submission.countdown <= 0) {
        $scope.submission.wait = false;
      } else {
        $timeout(countDown, 1000);
      }
    };

    countDown();
  };

  $scope.selectable = function () {
    if ($scope.submission.context.maximum_selectable_receivers === 0) {
      return true;
    }

    return $scope.submission.count_selected_receivers() < $scope.submission.context.maximum_selectable_receivers;
  };

  $scope.switch_selection = function (receiver) {
    if (receiver.configuration !== 'default' || (!$scope.node.allow_unencrypted && receiver.pgp_key_status !== 'enabled')) {
      return;
    }

    if ($scope.submission.receivers_selected[receiver.id] || $scope.selectable()) {
      $scope.submission.receivers_selected[receiver.id] = !$scope.submission.receivers_selected[receiver.id];
    }
  };

  $scope.getCurrentStepIndex = function() {
    return $scope.selection;
  };

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

    return ($scope.selection > 0 && $scope.selected_context.allow_recipients_selection) || $scope.selection > 1 ;
  };

  $scope.incrementStep = function() {
    if ($scope.hasNextStep()) {
      $scope.selection++;
      $anchorScroll('top');
    }
  };

  $scope.decrementStep = function() {
    if ($scope.hasPreviousStep()) {
      $scope.selection--;
      $anchorScroll('top');
    }
  };

  $scope.fileupload_url = function() {
    if (!$scope.submission) {
      return;
    }

    return 'submission/' + $scope.submission._token.id + '/file';
  };

  $scope.prepare_field_answers_structure = function(field) {
    if (field.answers_structure === undefined) {
      field.answer_structure = {};
      if (field.type === 'fieldgroup') {
        angular.forEach(field.children, function(child) {
          field.answer_structure[child.id] = [$scope.prepare_field_answers_structure(child)];
        });
      }
    }

    return field.answer_structure;
  };

  $scope.prepareSubmission = function(context, receivers_ids) {
    $scope.answers = {};

    angular.forEach(context.steps, function(field) {
      angular.forEach(field.children, function(child) {
        $scope.answers[child.id] = [angular.copy($scope.prepare_field_answers_structure(child))];
      });
    });

    $scope.submission.create(context.id, receivers_ids, function () {
      startCountdown();

      $scope.problemToBeSolved = $scope.submission._token.human_captcha !== false;

      if ($scope.node.enable_proof_of_work) {
        if (typeof window.Worker === 'undefined') {
          $scope.browserNotCompatible();
          return;
        }

        var worker = new Worker('js/crypto/proof-of-work.worker.js');

        worker.onmessage = function(e) {
          $scope.submission._token.proof_of_work_answer = e.data;
          $scope.submission._token.$update(function(token) {
            $scope.submission._token = token;
            $scope.submission.pow = true;
          });

          worker.terminate();
        };

        worker.postMessage({
          pow: $scope.submission._token.proof_of_work
        });
      } else {
        $scope.submission.pow = true;
      }

      if ($scope.problemToBeSolved) {
        $scope.openProblemDialog($scope.submission);
      }

      if ($scope.submission.context.show_receivers_in_alphabetical_order) {
        $scope.receiversOrderPredicate = 'name';
      } else {
        $scope.receiversOrderPredicate = 'presentation_order';
      }

      if ((!$scope.receivers_selectable || !$scope.submission.context.allow_recipients_selection)) {
        $scope.skip_first_step = true;
        $scope.selection = 1;
      } else {
        $scope.skip_first_step = false;
        $scope.selection = 0;
      }
    });
  };

  $scope.completeSubmission = function() {
    $scope.submission._submission.answers = $scope.answers;
    $scope.submission.submit();
  };

  new Submission(function(submission) {
    $scope.submission = submission;

    var context = null;

    if ($scope.context_id) {
      context = $filter('filter')($scope.contexts,
                                  {"id": $scope.context_id})[0];
    } else if ($scope.public_contexts.length == 1) {
      context = $scope.public_contexts[0];
    }

    if (context) {
      $scope.selected_context = context;
    }

    // Watch for changes in certain variables
    $scope.$watch('selected_context', function (newVal, oldVal) {
      if ($scope.submission && $scope.selected_context) {
        $scope.prepareSubmission($scope.selected_context, []);
      }
    });

  });
}]).
controller('SubmissionStepCtrl', ['$scope', '$filter', 'fieldsUtilities',
  function($scope, $filter, fieldsUtilities) {
  $scope.fields = $scope.step.children;

  $scope.rows = fieldsUtilities.splitRows($scope.fields);

  $scope.status = {
    opened: false
  };
}]).
controller('SubmissionFieldCtrl', ['$scope', 'fieldsUtilities', function ($scope, fieldsUtilities) {
  $scope.getClass = function(field, row_length) {
    if (field.width !== 0) {
      return "col-md-" + field.width;
    }

    return "col-md-" + ((row_length > 12) ? 1 : (12 / row_length));
  };

  $scope.getAnswersEntries = function(entry) {
    if (entry === undefined) {
      return $scope.answers[$scope.field.id];
    }

    return entry[$scope.field.id];
  };

  $scope.addAnswerEntry = function(entries) {
    entries.push(angular.copy($scope.field.answer_structure));
  };

  $scope.fields = $scope.field.children;
  $scope.rows = fieldsUtilities.splitRows($scope.fields);
  $scope.entries = $scope.getAnswersEntries($scope.entry);

  $scope.status = {
    opened: false
  };

  $scope.open = function() {
    $scope.status.opened = true;
  };

  $scope.validateRequiredCheckbox = function(field, entry) {
    if (!field.required) {
      return true;
    }

    for (var i=0; i<field.options.length; i++) {
      if (entry[field.options[i].id] && entry[field.options[i].id] === true) {
        return true;
      }
    }

    return false;
  };
}]);
