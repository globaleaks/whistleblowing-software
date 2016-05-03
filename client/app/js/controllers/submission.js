GLClient.controller('SubmissionCtrl',
    ['$scope', '$filter', '$location', '$timeout', '$uibModal', '$anchorScroll', 'tmhDynamicLocale', 'Submission', 'glbcProofOfWork', 'fieldUtilities',
      function ($scope, $filter, $location, $timeout, $uibModal, $anchorScroll, tmhDynamicLocale, Submission, glbcProofOfWork, fieldUtilities) {
  $scope.context_id = $location.search().context || undefined;
  $scope.receivers_ids = $location.search().receivers || [];

  $scope.problemToBeSolved = false;
  $scope.problemModal = undefined;

  $scope.total_score = 0;

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

    var args = {
      submission: submission,
      problemSolved: $scope.problemSolved
    };

    $scope.problemModal = $scope.openConfirmableModalDialog('views/partials/captchas.html', args);

    $scope.problemModal.result.then(
      function() { $scope.problemSolved($scope.submission); },
      function() { }
    );
  };

  $scope.selected_context = undefined;

  $scope.selectContext = function(context) {
    $scope.selected_context = context;
  };

  if ($scope.receivers_ids) {
    try {
      $scope.receivers_ids = angular.fromJson($scope.receivers_ids);
    }
    catch(err) {
      $scope.receivers_ids = [];
    }
  }

  if ($scope.node.show_contexts_in_alphabetical_order) {
    $scope.contextsOrderPredicate = 'name';
  } else {
    $scope.contextsOrderPredicate = 'presentation_order';
  }

  $scope.selectable_contexts = $filter('filter')($scope.contexts, {'show_context': true});
  $scope.selectable_contexts = $filter('orderBy')($scope.selectable_contexts, $scope.contextsOrderPredicate);

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

  $scope.firstStepIndex = function() {
    return $scope.receiver_selection_step ? -1 : 0;
  };

  $scope.lastStepIndex = function() {
    var last_enabled = 0;

    for (var i = 0; i < $scope.selected_context.questionnaire.steps.length; i++) {
      if ($scope.isStepTriggered($scope.selected_context.questionnaire.steps[i], $scope.answers, $scope.total_score)) {
        last_enabled = i;
      }
    }

    return last_enabled;
  };

  $scope.hasNextStep = function() {
    if ($scope.selected_context === undefined) {
      return false;
    }

    return $scope.selection < $scope.lastStepIndex();
  };

  $scope.hasPreviousStep = function() {
    if ($scope.selected_context === undefined) {
      return false;
    }

    return $scope.selection > $scope.firstStepIndex();
  };

  $scope.checkForInvalidFields = function() {
    // find the first invalid element
    var form = document.getElementById('step-' + $scope.selection);
    var firstInvalid = form.querySelector('.inputelem.ng-invalid');

    // if we find one, set focus
    if (firstInvalid) {
      firstInvalid.focus();
      return false;
    }

    return true;
  };

  $scope.incrementStep = function() {
    if ($scope.selection >=0 &&
        $scope.submission.context.questionnaire.steps_navigation_requires_completion &&
        !$scope.checkForInvalidFields()) {
      return;
    }

    if ($scope.hasNextStep()) {
      for (var i = $scope.selection + 1; i <= $scope.lastStepIndex(); i++) {
        if ($scope.isStepTriggered($scope.submission.context.questionnaire.steps[i], $scope.answers, $scope.total_score)) {
          $scope.selection = i;
          $anchorScroll('top');
          break;
        }
      }
    }
  };

  $scope.decrementStep = function() {
    if ($scope.hasPreviousStep()) {
      for (var i = $scope.selection - 1; i >= $scope.firstStepIndex(); i--) {
        if (i === -1 || $scope.isStepTriggered($scope.submission.context.questionnaire.steps[i], $scope.answers, $scope.total_score)) {
          $scope.selection = i;
          $anchorScroll('top');
          break;
        }
      }
    }
  };

  $scope.fileupload_url = function() {
    if (!$scope.submission) {
      return;
    }

    return 'submission/' + $scope.submission._token.id + '/file';
  };

  $scope.calculateScoreRecursively = function(field, entry) {
    var score = 0;
    var i;

    if (['selectbox', 'multichoice'].indexOf(field.type) !== -1) {
      for(i=0; i<field.options.length; i++) {
        if (entry['value'] === field.options[i].id) {
          score += field.options[i].score_points;
        }
      }
    }

    if (field.type === 'checkbox') {
      for(i=0; i<field.options.length; i++) {
        if (entry[field.options[i].id] === true) {
          score += field.options[i].score_points;
        }
      }
    }

    angular.forEach(field.children, function(child) {
      angular.forEach(entry[child.id], function(entry) {
        score += $scope.calculateScoreRecursively(child, entry);
      });
    });

    return score;
  };

  $scope.calculateScore = function() {
    if (!$scope.node.enable_experimental_features) {
      return 0;
    }

    var score = 0;

    angular.forEach($scope.submission.context.questionnaire.steps, function(step) {
      angular.forEach(step.children, function(field) {
        angular.forEach($scope.answers[field.id], function(entry) {
          score += $scope.calculateScoreRecursively(field, entry);
        });
      });
    });

    return score;
  };

  $scope.prepareSubmission = function(context, receivers_ids) {
    $scope.answers = {};
    $scope.uploads = {};

    // iterations over steps require the steps array to be ordered
    context.questionnaire.steps = $filter('orderBy')(context.questionnaire.steps, 'presentation_order');

    angular.forEach(context.questionnaire.steps, function(step) {
      angular.forEach(step.children, function(field) {
        $scope.answers[field.id] = [angular.copy(fieldUtilities.prepare_field_answers_structure(field))];
      });
    });

    $scope.$watch('answers', function() {
      $scope.total_score = $scope.calculateScore();
      $scope.submission._submission.total_score = $scope.total_score;
    }, true);

    $scope.submission.create(context.id, receivers_ids, function () {
      startCountdown();

      $scope.problemToBeSolved = $scope.submission._token.human_captcha !== false;

      if ($scope.node.enable_proof_of_work) {
        glbcProofOfWork.proofOfWork($scope.submission._token.proof_of_work).then(function(result) {
          $scope.submission._token.proof_of_work_answer = result;
          $scope.submission._token.$update(function(token) {
            $scope.submission._token = token;
            $scope.submission.pow = true;
          });
        });
      }

      if ($scope.problemToBeSolved) {
        $scope.openProblemDialog($scope.submission);
      }

      if ($scope.submission.context.show_receivers_in_alphabetical_order) {
        $scope.receiversOrderPredicate = 'name';
      } else {
        $scope.receiversOrderPredicate = 'presentation_order';
      }

      // --------------------------------------------------------------------------
      // fix steps numbering adding receiver selection step if neeeded
      $scope.receiver_selection_step = false;
      $scope.receiver_selection_step_index = -1;
      $scope.selection = 0;

      if ($scope.submission.context.allow_recipients_selection) {
        $scope.receiver_selection_step = true;
        $scope.selection = -1;
      }

      $scope.show_steps_navigation_bar = ($scope.submission.context.questionnaire.show_steps_navigation_bar &&
                                          ($scope.receiver_selection_step || $scope.submission.context.questionnaire.steps.length > 1));
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
    } else if ($scope.selectable_contexts.length === 1) {
      context = $scope.selectable_contexts[0];
    }

    if (context) {
      $scope.selected_context = context;
    }

    // Watch for changes in certain variables
    $scope.$watch('selected_context', function () {
      if ($scope.submission && $scope.selected_context) {
        $scope.prepareSubmission($scope.selected_context, $scope.receivers_ids);
      }
    });

  });
}]).
controller('SubmissionStepCtrl', ['$scope', '$filter', 'fieldUtilities',
  function($scope, $filter, fieldUtilities) {
  $scope.fields = $scope.step.children;

  $scope.rows = fieldUtilities.splitRows($scope.fields);

  $scope.status = {
    opened: false
  };
}]).
controller('SubmissionFieldCtrl', ['$scope', 'fieldUtilities', function ($scope, fieldUtilities) {
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
  $scope.rows = fieldUtilities.splitRows($scope.fields);
  $scope.entries = $scope.getAnswersEntries($scope.entry);

  // If the field is type 'date' attach an option configurator for the 
  // uib-datepicker modal.
  if ($scope.field.type === 'date') {
    var options = {
      showWeeks: false, // Just a sample option 
    };
    var max = $scope.field.attrs.max_date.value;
    var min = $scope.field.attrs.min_date.value;
    if (angular.isDefined(max)) {
      options.maxDate = new Date(max);
    }
    if (angular.isDefined(min)) {
      options.minDate = new Date(min);
    }
    $scope.dateOptions = options;
  }

  if ($scope.field.type === 'inputbox') {
    $scope.validator = fieldUtilities.getValidator($scope.field);
  }

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
