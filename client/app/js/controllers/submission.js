GLClient.controller('SubmissionCtrl',
    ['$scope', 'Utils', '$filter', '$location', '$interval', '$anchorScroll', 'tmhDynamicLocale', 'Submission', 'glbcProofOfWork', 'fieldUtilities',
      function ($scope, Utils, $filter, $location, $interval, $anchorScroll, tmhDynamicLocale, Submission, glbcProofOfWork, fieldUtilities) {
  $scope.vars = {};

  $scope.fieldUtilities = fieldUtilities;
  $scope.context_id = $location.search().context || undefined;
  $scope.receivers_ids = $location.search().receivers || [];

  $scope.navigation = -1;

  $scope.submitPressed = false;

  $scope.total_score = 0;

  function openProblemDialog() {
    var args = { token: $scope.submission._token };

    Utils.openConfirmableModalDialog('views/partials/captchas.html', args)
      .then(function() { return args.token.$update(); })
      .then(function(token) {
        // Always refresh the token after a submission
        $scope.submission._token = token;
        if (token.human_captcha) {
          // Reopen the captcha modal if the human_captcha is truthy which means
          // it is unresolved.
          openProblemDialog();
        }
      });
  }

  $scope.selected_context = undefined;

  $scope.selectContext = function(context) {
    $scope.selected_context = context;
  };

  $scope.singleStepForm = function() {
    return $scope.firstStepIndex() === $scope.lastStepIndex();
  };

  if ($scope.receivers_ids) {
    $scope.receivers_ids = angular.fromJson($scope.receivers_ids);
  }

  $scope.contextsOrderPredicate = $scope.node.show_contexts_in_alphabetical_order ? 'name' : 'presentation_order';

  $scope.selectable_contexts = $filter('filter')($scope.contexts, {'show_context': true});
  $scope.selectable_contexts = $filter('orderBy')($scope.selectable_contexts, $scope.contextsOrderPredicate);

  var startCountdown = function() {
    $scope.submission.wait = true;
    $scope.submission.pow = false;

    $scope.submission.countdown = 3; // aligned to backend submission_minimum_delay

    $scope.stop = $interval(function() {
      $scope.submission.countdown -= 1;
      if ($scope.submission.countdown < 0) {
        $scope.submission.wait = false;
        $interval.cancel($scope.stop);
      }
    }, 1000);
  };

  $scope.selectable = function () {
    if ($scope.submission.context.maximum_selectable_receivers === 0) {
      return true;
    }

    return $scope.submission.count_selected_receivers() < $scope.submission.context.maximum_selectable_receivers;
  };

  $scope.switch_selection = function (receiver) {
    if (receiver.configuration !== 'default' || (!$scope.node.allow_unencrypted && receiver.pgp_key_public === '')) {
      return;
    }

    if ($scope.submission.selected_receivers[receiver.id] || $scope.selectable()) {
      $scope.submission.selected_receivers[receiver.id] = !$scope.submission.selected_receivers[receiver.id];
    }
  };

  $scope.getCurrentStepIndex = function() {
    return $scope.selection;
  };

  $scope.getCurrentStep = function() {
    return $scope.submission.context.questionnaire.steps[$scope.selection];
  };

  $scope.goToStep = function(index, bypassErrors) {
    if (!bypassErrors && $scope.displayErrors()) {
      // if some errors are already triggered avoid navigation
      return;
    }

    $scope.selection = index;
    $anchorScroll('top');
  };

  $scope.firstStepIndex = function() {
    return $scope.receiver_selection_step ? -1 : 0;
  };

  $scope.lastStepIndex = function() {
    return $scope.selected_context.questionnaire.steps.length - 1;
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
    for(var i = 0; i <= $scope.selection; i++) {
      // find the first invalid element
      var form = document.getElementById('step-' + i);
      var firstInvalid = form.querySelector('.inputelem.ng-invalid');

      // if we find one, set focus
      if (firstInvalid) {
        $anchorScroll('top');
        return false;
      }
    }

    return true;
  };

  $scope.incrementStep = function() {
    if ($scope.hasNextStep()) {
      if ($scope.navigation < $scope.selection + 1) {
        $scope.navigation = $scope.selection + 1;
      }
    }

    if (!$scope.areReceiversSelected() && $scope.selection === $scope.receiver_selection_step_index) {
      $anchorScroll('top');
      return;
    }

    if ($scope.selection > -1 && !$scope.checkForInvalidFields()) {
      return;
    }

    if ($scope.hasNextStep()) {
      $scope.vars.submissionForm.$dirty = false;
      for (var i = $scope.selection + 1; i <= $scope.lastStepIndex(); i++) {
        $scope.selection = i;
        $anchorScroll('top');
        break;
      }
    }
  };

  $scope.decrementStep = function() {
    if ($scope.hasPreviousStep()) {
      $scope.vars.submissionForm.$dirty = false;
      for (var i = $scope.selection - 1; i >= $scope.firstStepIndex(); i--) {
        $scope.selection = i;
        $anchorScroll('top');
      }
    }
  };

  $scope.areReceiversSelected = function() {
    for (var rec_id in $scope.submission.selected_receivers) {
      if ($scope.submission.selected_receivers[rec_id]) {
        return true;
      }
    }

    return false;
  };

  $scope.submissionHasErrors = function() {
    if (angular.isDefined($scope.vars.submissionForm)) {
      return $scope.vars.submissionForm.$invalid ||
             Utils.isUploading($scope.uploads);
    }

    return false;
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
        if (entry[field.options[i].id]) {
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
    $scope.field_id_map = fieldUtilities.build_field_id_map(context);

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

      if ($scope.submission._token.proof_of_work) {
        glbcProofOfWork.proofOfWork($scope.submission._token.proof_of_work).then(function(result) {
          $scope.submission._token.proof_of_work_answer = result;
          $scope.submission._token.$update(function(token) {
            $scope.submission._token = token;
            $scope.submission.pow = true;
          });
        });
      } else {
        $scope.submission.pow = true;
      }

      if ($scope.submission._token.human_captcha) {
        openProblemDialog();
      }

      $scope.receiversOrderPredicate = $scope.submission.context.show_receivers_in_alphabetical_order ? 'name' : null;

      $scope.show_steps_navigation_bar = $scope.receiver_selection_step || $scope.submission.context.questionnaire.steps.length > 1;

      // --------------------------------------------------------------------------
      // fix steps numbering adding receiver selection step if neeeded
      $scope.receiver_selection_step = false;
      $scope.receiver_selection_step_index = -1;
      $scope.selection = 0;

      if ($scope.submission.context.allow_recipients_selection) {
        $scope.receiver_selection_step = true;
        $scope.selection = -1;
      }
    });
  };

  $scope.completeSubmission = function() {
    $scope.submitPressed = true;

    if (!$scope.areReceiversSelected() || !$scope.checkForInvalidFields()) {
      $anchorScroll('top');
      return;
    }

    $scope.submission._submission.answers = $scope.answers;
    $scope.submission.submit();
  };


  $scope.stepForm = function(index) {
    if (index !== -1) {
      return $scope.vars.submissionForm['step-' + index];
    }
  };

  $scope.displayStepErrors = function(index) {
    if (index !== -1) {
      return $scope.stepForm(index).$invalid;
    }
  };

  $scope.displayErrors = function() {
    if (!($scope.navigation > $scope.selection || $scope.submitPressed || $scope.submission.done)) {
      return false;
    }

    if (!($scope.hasPreviousStep() || !$scope.hasNextStep()) && !$scope.areReceiversSelected()) {
      return true;
    }

    if (!$scope.hasNextStep() && $scope.submissionHasErrors()) {
      return true;
    }

    if ($scope.displayStepErrors($scope.selection)) {
      return true;
    }

    return false;
  };

  $scope.evaluateAnonimityModalOpening();

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
      $scope.selectContext(context);
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
  $scope.stepId = 'step-' + $scope.$index;

  $scope.rows = fieldUtilities.splitRows($scope.fields);

  $scope.status = {
    opened: false,
  };
}]).
controller('SubmissionFieldErrKeyCtrl', ['$scope',
  function($scope) {
    var pre = 'fieldForm_';

    var f_id =  $scope.err.$name;
    f_id = f_id.substring(0, f_id.indexOf('$'));
    f_id = f_id.slice(pre.length).replace(new RegExp('_', 'g'), '-');
    $scope.field = $scope.field_id_map[f_id];

    $scope.goToQuestion = function() {
      var form = document.getElementById('step-' + $scope.selection);
      var s = 'div[data-ng-form="' + $scope.err.$name + '"] .ng-invalid';
      var formFieldSel = form.querySelector(s);
      formFieldSel.focus();
    };
}]).
controller('SubmissionFormFieldCtrl', ['$scope',
  function($scope) {
    $scope.f = $scope[$scope.fieldFormVarName];
}]).
controller('SubmissionFieldEntryCtrl', ['$scope',
  function($scope) {
    $scope.fieldEntry = $scope.fieldId + '-input-' + $scope.$index;
}]).
controller('SubmissionFieldCtrl', ['$scope', 'fieldUtilities', function ($scope, fieldUtilities) {
  $scope.fieldFormVarName = fieldUtilities.fieldFormName($scope.field.id + '$' + $scope.$index);

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
      if (entry[field.options[i].id] && entry[field.options[i].id]) {
        return true;
      }
    }

    return false;
  };

  $scope.fieldId = $scope.stepId + '-field-' + $scope.fieldRow + '-' + $scope.fieldCol;
}]);
