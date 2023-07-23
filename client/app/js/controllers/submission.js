GL.controller("SubmissionCtrl",
    ["$scope", "$filter", "$location", "$interval", "$timeout", "tmhDynamicLocale", "Submission", "fieldUtilities",
      function ($scope, $filter, $location, $interval, $timeout, tmhDynamicLocale, Submission, fieldUtilities) {
  $scope.vars = {};

  $scope.fieldUtilities = fieldUtilities;

  $scope.context_id = $location.search().context || "";

  $scope.context = undefined;

  $scope.navigation = -1;

  $scope.validate = {};

  $scope.score = 0;

  $scope.contextsOrderPredicate = $scope.public.node.show_contexts_in_alphabetical_order ? "name" : "order";

  $scope.selectable_contexts = $filter("filter")($scope.public.contexts, {"hidden": false});
  $scope.selectable_contexts = $filter("orderBy")($scope.selectable_contexts, $scope.contextsOrderPredicate);

  $scope.selectContext = function(context) {
    $scope.context = context;
  };

  $scope.selectable = function () {
    if ($scope.submission.context.maximum_selectable_receivers === 0) {
      return true;
    }

    return Object.keys($scope.submission.selected_receivers).length < $scope.submission.context.maximum_selectable_receivers;
  };

  $scope.switch_selection = function (receiver) {
    if (!$scope.submission.selected_receivers[receiver.id]) {
      delete $scope.submission.selected_receivers[receiver.id];
    } else if ($scope.selectable()) {
      $scope.submission.selected_receivers[receiver.id] = true;
    }
  };

  $scope.goToStep = function(index) {
    $scope.navigation = index;
    $scope.Utils.scrollTo("#SubmissionForm");
  };

  $scope.firstStepIndex = function() {
    return $scope.context.allow_recipients_selection ? -1 : 0;
  };

  $scope.lastStepIndex = function() {
    var last_enabled = 0;

    for (var i = 0; i < $scope.questionnaire.steps.length; i++) {
      if (fieldUtilities.isFieldTriggered($scope, null, $scope.questionnaire.steps[i], $scope.answers, $scope.score)) {
        last_enabled = i;
      }
    }

    return last_enabled;
  };

  $scope.hasNextStep = function() {
    if (typeof $scope.context === "undefined") {
      return false;
    }

    return $scope.navigation < $scope.lastStepIndex();
  };

  $scope.hasPreviousStep = function() {
    if (typeof $scope.context === "undefined") {
      return false;
    }

    return $scope.navigation > $scope.firstStepIndex();
  };

  $scope.checkForInvalidFields = function() {
    for(var i = 0; i <= $scope.navigation; i++) {
      if ($scope.questionnaire.steps[i].enabled) {
        // check presence of invalid elements
        if (document.querySelector("#step-" + i + " .inputelem.ng-invalid")) {
          $scope.navigation = i;
          $scope.Utils.scrollTo("#SubmissionErrors");
          return false;
        }
      }
    }

    return true;
  };

  $scope.runValidation = function() {
    for(var i = -1; i <= $scope.navigation; i++) {
      $scope.validate[i] = true;
    }

    if ($scope.context.allow_recipients_selection && !$scope.areReceiversSelected()) {
      $scope.navigation = -1;
      return false;
    }

    if (!$scope.checkForInvalidFields()) {
      return false;
    }

    return true;
  };

  $scope.incrementStep = function() {
    if (!$scope.runValidation()) {
      return;
    }

    if ($scope.hasNextStep()) {
      $scope.vars.submissionForm.$dirty = false;
      for (var i = $scope.navigation + 1; i <= $scope.lastStepIndex(); i++) {
        if (fieldUtilities.isFieldTriggered($scope, null, $scope.questionnaire.steps[i], $scope.answers, $scope.score)) {
          $scope.navigation = i;
          $scope.Utils.scrollTo("#step-" + i + " .inputelem");
          return;
        }
      }
    }
  };

  $scope.decrementStep = function() {
    if ($scope.hasPreviousStep()) {
      $scope.vars.submissionForm.$dirty = false;
      for (var i = $scope.navigation - 1; i >= $scope.firstStepIndex(); i--) {
        if (i === -1 || fieldUtilities.isFieldTriggered($scope, null, $scope.questionnaire.steps[i], $scope.answers, $scope.score)) {
          $scope.navigation = i;
          if (i === -1) {
            $scope.Utils.scrollTo("#SubmissionForm");
          } else {
            $scope.Utils.scrollTo("#step-" + i + " .inputelem");
          }
          return;
        }
      }
    }
  };

  $scope.areReceiversSelected = function() {
    return Object.keys($scope.submission.selected_receivers).length > 0;
  };

  $scope.submissionHasErrors = function() {
    if (angular.isDefined($scope.vars.submissionForm)) {
      return $scope.vars.submissionForm.$invalid ||
             $scope.Utils.isUploading($scope.uploads);
    }

    return false;
  };

  $scope.fileupload_url = function() {
    if (!$scope.submission) {
      return;
    }

    return "api/whistleblower/submission/attachment";
  };

  $scope.prepareSubmission = function(context) {
    $scope.done = false;
    $scope.answers = {};
    $scope.uploads = {};
    $scope.context = context;
    $scope.questionnaire = context.questionnaire;
    $scope.field_id_map = fieldUtilities.build_field_id_map($scope.questionnaire);

    $scope.submission.create(context.id);

    $scope.receiversOrderPredicate = $scope.submission.context.show_receivers_in_alphabetical_order ? "name" : null;
    $scope.show_steps_navigation_bar = $scope.context.allow_recipients_selection || $scope.questionnaire.steps.length > 1;

    $scope.navigation = $scope.firstStepIndex();
  };

  $scope.completeSubmission = function() {
    if (!$scope.runValidation()) {
      return;
    }

    $scope.done = true;

    $scope.submission._submission.answers = $scope.answers;

    $scope.Utils.resumeFileUploads($scope.uploads);

    $scope.interval = $interval(function() {
      for (var key in $scope.uploads) {
        if ($scope.uploads[key] &&
            $scope.uploads[key].isUploading() &&
            $scope.uploads[key].isUploading()) {
          return;
        }
      }

      $interval.cancel($scope.interval);

      return $scope.submission.submit();
    }, 1000);
  };

  $scope.stepForm = function(index) {
    if (index !== -1) {
      return $scope.vars.submissionForm["step-" + index];
    }
  };

  $scope.replaceReceivers = function(receivers) {
    for(var key in $scope.submission.selected_receivers) {
      if (receivers.indexOf(key) === -1) {
        delete $scope.submission.selected_receivers[key];
      }
    }

    for(var i=0; i<receivers.length; i++) {
      if (receivers[i] in $scope.receivers_by_id) {
        $scope.submission.selected_receivers[receivers[i]] = true;
      }
    }
  };

  $scope.displayErrors = function() {
    if (!($scope.validate[$scope.navigation] || $scope.submission.done)) {
      return false;
    }

    if (!($scope.hasPreviousStep() || !$scope.hasNextStep()) && !$scope.areReceiversSelected()) {
      return true;
    }

    if (!$scope.hasNextStep() && $scope.submissionHasErrors()) {
      return true;
    }

    if ($scope.navigation === -1) {
      if ($scope.context.allow_recipients_selection && !$scope.areReceiversSelected()) {
        return true;
      }
    } else {
      if ($scope.stepForm($scope.navigation).$invalid) {
        return true;
      }
    }

    return false;
  };

  $scope.setPage("submissionpage");

  $scope.submission = new Submission(function() {
    var context = null;

    if ($scope.context_id) {
      context = $filter("filter")($scope.public.contexts,
                                  {"id": $scope.context_id})[0];
    } else if ($scope.selectable_contexts.length === 1) {
      context = $scope.selectable_contexts[0];
    }

    if (context) {
      $scope.context = context;
    }

    // Watch for changes in certain variables
    $scope.$watch("context", function () {
      if ($scope.submission && $scope.context) {
        $scope.prepareSubmission($scope.context);
      }
    });

    $scope.$watch("answers", function () {
      fieldUtilities.onAnswersUpdate($scope);
    }, true);

    $scope.$watch("submission._submission.identity_provided", function() {
      fieldUtilities.onAnswersUpdate($scope);
    });

    $scope.$on("GL::uploadsUpdated", function () {
      fieldUtilities.onAnswersUpdate($scope);
    });
  });
}]).
controller("AdditionalQuestionnaireCtrl",
    ["$http", "$scope", "$uibModalInstance", "$filter", "$location", "$interval", "tmhDynamicLocale", "Submission", "glbcProofOfWork", "fieldUtilities",
      function ($http, $scope, $uibModalInstance, $filter, $location, $interval, tmhDynamicLocale, Submission, glbcProofOfWork, fieldUtilities) {
  $scope.vars = {};

  $scope.fieldUtilities = fieldUtilities;

  $scope.navigation = 0;

  $scope.validate = {};

  $scope.score = 0;

  $scope.goToStep = function(index) {
    $scope.navigation = index;
    $scope.Utils.scrollTo("#SubmissionForm");
  };

  $scope.lastStepIndex = function() {
    var last_enabled = 0;

    for (var i = 0; i < $scope.questionnaire.steps.length; i++) {
      if ($scope.questionnaire.steps[i].enabled) {
        last_enabled = i;
      }
    }

    return last_enabled;
  };

  $scope.hasNextStep = function() {
    return $scope.navigation < $scope.lastStepIndex();
  };

  $scope.hasPreviousStep = function() {
    return $scope.navigation > 0;
  };

  $scope.checkForInvalidFields = function() {
    for(var i = 0; i <= $scope.navigation; i++) {
      if ($scope.questionnaire.steps[i].enabled) {
        // check presence of invalid elements
        if (document.querySelector("#step-" + i + " .inputelem.ng-invalid")) {
          $scope.navigation = i;
          $scope.Utils.scrollTo("#SubmissionErrors");
          return false;
        }
      }
    }

    return true;
  };

  $scope.runValidation = function() {
    for(var i = -1; i <= $scope.navigation; i++) {
      $scope.validate[i] = true;
    }

    if ($scope.navigation > -1 && !$scope.checkForInvalidFields()) {
      return false;
    }

    return true;
  };

  $scope.incrementStep = function() {
    if (!$scope.runValidation()) {
      return;
    }

    if ($scope.hasNextStep()) {
      $scope.vars.submissionForm.$dirty = false;
      for (var i = $scope.navigation + 1; i <= $scope.lastStepIndex(); i++) {
        if (fieldUtilities.isFieldTriggered($scope, null, $scope.questionnaire.steps[i], $scope.answers, $scope.score)) {
          $scope.navigation = i;
          $scope.Utils.scrollTo("#step-" + i + " .inputelem");
          return;
        }
      }
    }
  };

  $scope.decrementStep = function() {
    if ($scope.hasPreviousStep()) {
      $scope.vars.submissionForm.$dirty = false;
      for (var i = $scope.navigation - 1; i >= 0; i--) {
        if (i === -1 || fieldUtilities.isFieldTriggered($scope, null, $scope.questionnaire.steps[i], $scope.answers, $scope.score)) {
          $scope.navigation = i;
          $scope.Utils.scrollTo("#step-" + i + " .inputelem");
          return;
        }
      }
    }
  };

  $scope.submissionHasErrors = function() {
    return false;
  };

  $scope.prepareSubmission = function() {
    $scope.done = false;
    $scope.answers = {};
    $scope.uploads = {};
    $scope.questionnaire = $scope.tip.additional_questionnaire;
    $scope.field_id_map = fieldUtilities.build_field_id_map($scope.questionnaire);
  };

  $scope.completeSubmission = function() {
    for(var i = -1; i <= $scope.navigation; i++) {
      $scope.validate[i] = true;
    }

    fieldUtilities.onAnswersUpdate($scope);

    if (!$scope.checkForInvalidFields()) {
      return;
    }

    $scope.done = true;

    for (var key in $scope.uploads) {
      if ($scope.uploads[key]) {
        $scope.uploads[key].resume();
      }
    }

    $scope.interval = $interval(function() {
      for (var key in $scope.uploads) {
        if ($scope.uploads[key] &&
            $scope.uploads[key].isUploading &&
            $scope.uploads[key].isUploading()) {
          return;
        }
      }

      $interval.cancel($scope.interval);

      return $http.post("api/whistleblower/wbtip/fillform",
                        {"cmd": "additional_questionnaire", "answers": $scope.answers}).
          then(function(){
            $scope.reload();
          });

    }, 1000);
  };

  $scope.stepForm = function(index) {
    if (index !== -1) {
      return $scope.vars.submissionForm["step-" + index];
    }
  };

  $scope.displayErrors = function() {
    if (!($scope.validate[$scope.navigation])) {
      return false;
    }

    if ($scope.navigation !== -1) {
      return $scope.stepForm($scope.navigation).$invalid;
    }

    return false;
  };

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  // Watch for changes in certain variables
  $scope.$watch("answers", function () {
    fieldUtilities.onAnswersUpdate($scope);
  }, true);

  $scope.$watch("submission._submission.identity_provided", function() {
    fieldUtilities.onAnswersUpdate($scope);
  });

  $scope.$on("GL::uploadsUpdated", function () {
    fieldUtilities.onAnswersUpdate($scope);
  });

  $scope.prepareSubmission();
  fieldUtilities.onAnswersUpdate($scope);
}]).
controller("SubmissionStepCtrl", ["$scope", "$filter", "fieldUtilities",
  function($scope, $filter, fieldUtilities) {
  $scope.fields = $scope.step.children;
  $scope.stepId = "step-" + $scope.$index;

  $scope.rows = fieldUtilities.splitRows($scope.fields);

  $scope.status = {
    opened: false,
  };
}]).
controller("SubmissionFieldErrKeyCtrl", ["$scope",
  function($scope) {
    var pre = "fieldForm_";

    var f_id =  $scope.err.$name;
    f_id = f_id.substring(0, f_id.indexOf("$"));
    f_id = f_id.slice(pre.length).replace(new RegExp("_", "g"), "-");
    $scope.field = $scope.field_id_map[f_id];

    $scope.goToQuestion = function() {
      var form = document.getElementById("step-" + $scope.navigation);
      var s = "div[data-ng-form=\"" + $scope.err.$name + "\"] .ng-invalid";
      var formFieldSel = form.querySelector(s);
      formFieldSel.focus();
    };
}]).
controller("SubmissionFormFieldCtrl", ["$scope", function($scope) {
    $scope.f = $scope[$scope.fieldFormVarName];
}]).
controller("SubmissionFieldEntryCtrl", ["$scope",
  function($scope) {
    $scope.fieldEntry = $scope.fieldId + "-input-" + $scope.entryIndex;
}]).
controller("SubmissionFieldCtrl", ["$scope", "fieldUtilities", function ($scope, fieldUtilities) {
  $scope.fieldFormVarName = fieldUtilities.fieldFormName($scope.field.id + "$" + $scope.$index);

  $scope.getAnswersEntries = function(entry) {
    if (typeof entry === "undefined") {
      return $scope.answers[$scope.field.id];
    }

    return entry[$scope.field.id];
  };

  $scope.addAnswerEntry = function(entries) {
    entries.push({});
  };

  $scope.fields = $scope.field.children;
  $scope.rows = fieldUtilities.splitRows($scope.fields);
  $scope.entries = $scope.getAnswersEntries($scope.entry);

  $scope.clear = function() {
    $scope.entries.length = 0;
    $scope.addAnswerEntry($scope.entries);
  };

  if ($scope.field.type === "inputbox") {
    $scope.validator = fieldUtilities.getValidator($scope.field);
  } else if ($scope.field.type === "date") {
    $scope.dateOptions = {};

    if (angular.isDefined($scope.field.attrs.min_date)) {
      $scope.dateOptions.minDate = new Date($scope.field.attrs.min_date.value);
    }

    if (angular.isDefined($scope.field.attrs.max_date)) {
      $scope.dateOptions.maxDate = new Date($scope.field.attrs.max_date.value);
    }

    $scope.status = {
      opened: false
    };

    $scope.open = function() {
      $scope.status.opened = true;
    };
  } else if ($scope.field.type === "daterange") {
    $scope.dateOptions1 = {};
    $scope.dateOptions2 = {};

    if (angular.isDefined($scope.field.attrs.min_date)) {
      $scope.dateOptions1.minDate = new Date($scope.field.attrs.min_date.value);
    }

    if (angular.isDefined($scope.field.attrs.max_date)) {
      $scope.dateOptions2 = new Date($scope.field.attrs.max_date.value);
    }

    $scope.clear = function() {
      $scope.daterange.start = "";
      $scope.daterange.end = "";
      $scope.entries.length = 0;
      $scope.addAnswerEntry($scope.entries);
    };

    $scope.daterange = {
      "start": "",
      "end": ""
    };

    $scope.$watch("daterange.start", function () {
      if ($scope.daterange.start) {
        $scope.dateOptions2.minDate = new Date($scope.daterange.start);
      }
    });

    $scope.$watch("daterange.end", function () {
      if ($scope.daterange.start && $scope.daterange.end) {
        $scope.entries[0].value = String(Number($scope.daterange.start)) + ":" + String(Number($scope.daterange.end));
      }
    });

    $scope.status = {
      openedStart: false,
      openedEnd: false
    };

    $scope.openStart = function() {
      $scope.status.openedStart = true;
      $scope.clear();
    };

    $scope.openEnd = function() {
      $scope.status.openedEnd = true;
    };
  }

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

  if ($scope.fieldEntry) {
    $scope.fieldId = $scope.fieldEntry + "-field-" + $scope.fieldRow + "-" + $scope.fieldCol;
  } else {
    $scope.fieldId = ($scope.stepId ? $scope.stepId + "-": "") + "field-" + $scope.fieldRow + "-" + $scope.fieldCol;
  }
}]);
