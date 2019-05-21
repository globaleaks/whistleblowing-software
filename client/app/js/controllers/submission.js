GLClient.controller("SubmissionCtrl",
    ["$scope", "$filter", "$location", "$interval", "$anchorScroll", "tmhDynamicLocale", "Submission", "glbcProofOfWork", "fieldUtilities",
      function ($scope, $filter, $location, $interval, $anchorScroll, tmhDynamicLocale, Submission, glbcProofOfWork, fieldUtilities) {
  $scope.vars = {};

  $scope.fieldUtilities = fieldUtilities;
  $scope.context_id = $location.search().context || undefined;
  $scope.context = undefined;

  $scope.navigation = -1;

  $scope.submitPressed = false;

  $scope.total_score = 0;

  $scope.singleStepForm = function() {
    return $scope.firstStepIndex() === $scope.lastStepIndex();
  };

  $scope.contextsOrderPredicate = $scope.node.show_contexts_in_alphabetical_order ? "name" : "presentation_order";

  $scope.selectable_contexts = $filter("filter")($scope.contexts, {"status": 1});
  $scope.selectable_contexts = $filter("orderBy")($scope.selectable_contexts, $scope.contextsOrderPredicate);

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

  $scope.selectContext = function(context) {
    $scope.context = context;
  };

  $scope.selectable = function () {
    if ($scope.submission.context.maximum_selectable_receivers === 0) {
      return true;
    }

    return $scope.submission.count_selected_receivers() < $scope.submission.context.maximum_selectable_receivers;
  };

  $scope.switch_selection = function (receiver) {
    if (receiver.recipient_configuration !== "default" || (!$scope.node.allow_unencrypted && receiver.pgp_key_public === "")) {
      return;
    }

    if ($scope.submission.selected_receivers[receiver.id] || $scope.selectable()) {
      $scope.submission.selected_receivers[receiver.id] = !$scope.submission.selected_receivers[receiver.id];
    }
  };

  $scope.getCurrentStepIndex = function() {
    return $scope.navigation;
  };

  $scope.getCurrentStep = function() {
    return $scope.questionnaire.steps[$scope.navigation];
  };

  $scope.goToStep = function(index, bypassErrors) {
    if (!bypassErrors && $scope.displayErrors()) {
      // if some errors are already triggered avoid navigation
      return;
    }

    $scope.navigation = index;
    $anchorScroll("top");
  };

  $scope.firstStepIndex = function() {
    return $scope.receiver_selection_step ? -1 : 0;
  };

  $scope.lastStepIndex = function() {
    var last_enabled = 0;

    for (var i = 0; i < $scope.questionnaire.steps.length; i++) {
      if (fieldUtilities.isFieldTriggered(null, $scope.questionnaire.steps[i], $scope.answers, $scope.total_score)) {
        last_enabled = i;
      }
    }

    return last_enabled;
  };

  $scope.hasNextStep = function() {
    if ($scope.context === undefined) {
      return false;
    }

    return $scope.navigation < $scope.lastStepIndex();
  };

  $scope.hasPreviousStep = function() {
    if ($scope.context === undefined) {
      return false;
    }

    return $scope.navigation > $scope.firstStepIndex();
  };

  $scope.checkForInvalidFields = function() {
    for(var i = 0; i <= $scope.navigation; i++) {
      if ($scope.questionnaire.steps[i].enabled) {
        // find the first invalid element
        var form = document.getElementById("step-" + i);
        var firstInvalid = form.querySelector(".inputelem.ng-invalid");

        // if we find one, set focus
        if (firstInvalid) {
          return false;
        }
      }
    }

    return true;
  };

  $scope.incrementStep = function() {
    if (!$scope.areReceiversSelected() && $scope.navigation === $scope.receiver_selection_step_index) {
      $anchorScroll("top");
      return;
    }

    if ($scope.navigation > -1 && !$scope.checkForInvalidFields()) {
      $anchorScroll("top");
      return;
    }

    if ($scope.hasNextStep()) {
      $scope.vars.submissionForm.$dirty = false;
      for (var i = $scope.navigation + 1; i <= $scope.lastStepIndex(); i++) {
        if (fieldUtilities.isFieldTriggered(null, $scope.questionnaire.steps[i], $scope.answers, $scope.total_score)) {
          $scope.navigation = i;
          $anchorScroll("top");
          return;
        }
      }
    }
  };

  $scope.decrementStep = function() {
    if ($scope.hasPreviousStep()) {
      $scope.vars.submissionForm.$dirty = false;
      for (var i = $scope.navigation - 1; i >= $scope.firstStepIndex(); i--) {
        if (i === -1 || fieldUtilities.isFieldTriggered(null, $scope.questionnaire.steps[i], $scope.answers, $scope.total_score)) {
          $scope.navigation = i;
          $anchorScroll("top");
          return;
        }
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
             $scope.Utils.isUploading($scope.uploads);
    }

    return false;
  };

  $scope.fileupload_url = function() {
    if (!$scope.submission) {
      return;
    }

    return "submission/" + $scope.submission._token.id + "/file";
  };

  $scope.prepareSubmission = function(context) {
    $scope.answers = {};
    $scope.uploads = {};
    $scope.context = context;
    $scope.questionnaire = context.questionnaire;
    $scope.field_id_map = fieldUtilities.build_field_id_map($scope.questionnaire);

    angular.forEach(context.questionnaire.steps, function(step) {
      angular.forEach(step.children, function(field) {
        $scope.answers[field.id] = [angular.copy(fieldUtilities.prepare_field_answers_structure(field))];
      });
    });

    $scope.submission.create(context.id, function () {
      startCountdown();

      if ($scope.submission._token.question) {
        glbcProofOfWork.proofOfWork($scope.submission._token.question).then(function(result) {
          $scope.submission._token.answer = result;
          $scope.submission._token.$update(function(token) {
            $scope.submission._token = token;
            $scope.submission.pow = true;
          });
        });
      } else {
        $scope.submission.pow = true;
      }

      $scope.receiversOrderPredicate = $scope.submission.context.show_receivers_in_alphabetical_order ? "name" : null;

      // --------------------------------------------------------------------------
      // fix steps numbering adding receiver selection step if neeeded
      $scope.receiver_selection_step = false;
      $scope.receiver_selection_step_index = -1;
      $scope.navigation = 0;

      if ($scope.submission.context.allow_recipients_selection) {
        $scope.receiver_selection_step = true;
        $scope.navigation = -1;
      }

      $scope.show_steps_navigation_bar = $scope.receiver_selection_step || $scope.questionnaire.steps.length > 1;
    });
  };

  $scope.completeSubmission = function() {
    $scope.submitPressed = true;

    if (!$scope.areReceiversSelected() || !$scope.checkForInvalidFields()) {
      $anchorScroll("top");
      return;
    }

    $scope.submission._submission.answers = $scope.answers;
    $scope.submission.submit();
  };


  $scope.stepForm = function(index) {
    if (index !== -1) {
      return $scope.vars.submissionForm["step-" + index];
    }
  };

  $scope.displayStepErrors = function(index) {
    if (index !== -1) {
      return $scope.stepForm(index).$invalid;
    }
  };

  $scope.replaceReceivers = function(receivers) {
    $scope.submission.selected_receivers = {};
    for(var i=0; i<receivers.length; i++) {
      $scope.submission.selected_receivers[receivers[i]] = true;
    }
  };

  $scope.displayErrors = function() {
    if (!($scope.submitPressed || $scope.submission.done)) {
      return false;
    }

    if (!($scope.hasPreviousStep() || !$scope.hasNextStep()) && !$scope.areReceiversSelected()) {
      return true;
    }

    if (!$scope.hasNextStep() && $scope.submissionHasErrors()) {
      return true;
    }

    if ($scope.displayStepErrors($scope.navigation)) {
      return true;
    }

    return false;
  };

  $scope.evaluateDisclaimerModalOpening();

  $scope.submission = new Submission(function(submission) {
    $scope.submission = submission;

    var context = null;

    if ($scope.context_id) {
      context = $filter("filter")($scope.contexts,
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
  });
}]).
controller("AdditionalQuestionnaireCtrl",
    ["$http", "$route", "$scope", "$uibModalInstance", "$filter", "$location", "$interval", "$anchorScroll", "tmhDynamicLocale", "Submission", "glbcProofOfWork", "fieldUtilities",
      function ($http, $route, $scope, $uibModalInstance, $filter, $location, $interval, $anchorScroll, tmhDynamicLocale, Submission, glbcProofOfWork, fieldUtilities) {
  $scope.vars = {};

  $scope.fieldUtilities = fieldUtilities;

  $scope.navigation = 0;

  $scope.submitPressed = false;

  $scope.total_score = 0;

  $scope.singleStepForm = function() {
    return $scope.firstStepIndex() === $scope.lastStepIndex();
  };

  $scope.getCurrentStepIndex = function() {
    return $scope.navigation;
  };

  $scope.getCurrentStep = function() {
    return $scope.questionnaire.steps[$scope.navigation];
  };

  $scope.goToStep = function(index) {
    $scope.navigation = index;
    $anchorScroll("top");
  };

  $scope.firstStepIndex = function() {
    return 0;
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
    return $scope.navigation > $scope.firstStepIndex();
  };

  $scope.checkForInvalidFields = function() {
    for(var i = 0; i <= $scope.navigation; i++) {
      if ($scope.questionnaire.steps[i].enabled) {
        // find the first invalid element
        var form = document.getElementById("step-" + i);
        var firstInvalid = form.querySelector(".inputelem.ng-invalid");

        // if we find one, set focus
        if (firstInvalid) {
          return false;
        }
      }
    }

    return true;
  };

  $scope.incrementStep = function() {
    if ($scope.navigation > -1 && !$scope.checkForInvalidFields()) {
      $anchorScroll("top");
      return;
    }

    if ($scope.hasNextStep()) {
      $scope.vars.submissionForm.$dirty = false;
      for (var i = $scope.navigation + 1; i <= $scope.lastStepIndex(); i++) {
        if (fieldUtilities.isFieldTriggered(null, $scope.questionnaire.steps[i], $scope.answers, $scope.total_score)) {
          $scope.navigation = i;
          $anchorScroll("top");
          return;
        }
      }
    }
  };

  $scope.decrementStep = function() {
    if ($scope.hasPreviousStep()) {
      $scope.vars.submissionForm.$dirty = false;
      for (var i = $scope.navigation - 1; i >= $scope.firstStepIndex(); i--) {
        if (i === -1 || fieldUtilities.isFieldTriggered(null, $scope.questionnaire.steps[i], $scope.answers, $scope.total_score)) {
          $scope.navigation = i;
          $anchorScroll("top");
          return;
        }
      }
    }
  };

  $scope.areReceiversSelected = function() {
    return true;
  };

  $scope.submissionHasErrors = function() {
    return false;
  };

  $scope.prepareSubmission = function() {
    $scope.answers = {};
    $scope.uploads = {};
    $scope.questionnaire = $scope.tip.additional_questionnaire;
    $scope.field_id_map = fieldUtilities.build_field_id_map($scope.questionnaire);

    angular.forEach($scope.questionnaire.steps, function(step) {
      angular.forEach(step.children, function(field) {
        $scope.answers[field.id] = [angular.copy(fieldUtilities.prepare_field_answers_structure(field))];
      });
    });
  };

  $scope.completeSubmission = function() {
    $scope.submitPressed = true;

    if (!$scope.checkForInvalidFields()) {
      $anchorScroll("top");
      return;
    }

    return $http.post("wbtip/" + $scope.tip.id + "/update",
                      {"cmd": "additional_questionnaire", "answers": $scope.answers}).
        then(function(){
          $route.reload();
        });
  };

  $scope.stepForm = function(index) {
    if (index !== -1) {
      return $scope.vars.submissionForm["step-" + index];
    }
  };

  $scope.displayStepErrors = function(index) {
    if (index !== -1) {
      return $scope.stepForm(index).$invalid;
    }
  };

  $scope.displayErrors = function() {
    return false;
  };

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  // Watch for changes in certain variables
  $scope.$watch("answers", function () {
    fieldUtilities.onAnswersUpdate($scope);
  }, true);

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
controller("SubmissionFormFieldCtrl", ["$scope", "fieldUtilities",
  function($scope, fieldUtilities) {
    $scope.f = $scope[$scope.fieldFormVarName];

    if ($scope.field.type === "map" && $scope.field.attrs.topojson.value) {
      var width = 384,
          height = 240;

      $scope.clicked = null;

      $scope.field.attrs.topojson.reset = function() {
        $scope.fieldEntry["value"] = "";
        $scope.clicked = null;

        for(var i=0; i<$scope.field.attrs.topojson.paths.length; i++) {
          d3.select($scope.field.attrs.topojson.paths[i]).attr("r", 5.5).style("fill", "#DDD");
        }
      };

      $scope.field.attrs.topojson.set = function(id) {
        $scope.clicked = null;
        for(var i=0; i<$scope.field.attrs.topojson.paths.length; i++) {
          var path = $scope.field.attrs.topojson.paths[i];
          if(path.__data__.id === id) {
           $scope.clicked = path;
           d3.select(path).attr("r", 10).style("fill", "red");
          } else {
           d3.select(path).attr("r", 5.5).style("fill", "#DDD");
          }
        }
      };

      d3.json($scope.field.attrs.topojson.value).then(function(topojson) {
        var projection = d3.geoMercator();
        var path = d3.geoPath();

        path.projection(projection);

        var svg = d3.select("#" + $scope.fieldEntry).select(".map").append("svg").attr("width", width).attr("height", height);

        var tooltip = d3.select("body").append("div").attr("class", "tooltip").style("opacity", 0);

        projection.scale(1).translate([0, 0]);

        var b = path.bounds($scope.field.attrs.topojson.geojson),
            s = .95 / Math.max((b[1][0] - b[0][0]) / width, (b[1][1] - b[0][1]) / height),
            t = [(width - s * (b[1][0] + b[0][0])) / 2, (height - s * (b[1][1] + b[0][1])) / 2];

        projection.scale(s).translate(t);

        svg.selectAll("svg")
           .data($scope.field.attrs.topojson.geojson.features)
           .enter()
           .append("path")
           .call(function(d){ $scope.field.attrs.topojson.paths = d._groups[0]; })
           .attr("class", "mapoutline")
           .attr("d", path)
           .on("mouseover", function(d) {
             tooltip.transition()
                    .duration(200)
                    .style("opacity", .9);

             tooltip.html(d.properties.name)
                    .style("left", (d3.event.pageX) + "px")
                    .style("top", (d3.event.pageY - 28) + "px");

             if ($scope.clicked !== this) {
               d3.select(this).attr("r", 5.5).style("fill", "orange");
             }

             $scope.$apply();
           })
           .on("mouseout", function() {
             tooltip.transition()
                    .duration(500)
                    .style("opacity", 0);

             if ($scope.clicked !== this) {
               d3.select(this).attr("r", 5.5).style("fill", "#DDD");
             }

             $scope.$apply();
           })
           .on("click", function(d) {
             if ($scope.answers[$scope.field.id][0]["value"] !== d.id) {
               if ($scope.clicked !== null) {
                 d3.select($scope.clicked).attr("r", 5.5).style("fill", "#DDD");
               }
               $scope.clicked = this;
               d3.select(this).attr("r", 10).style("fill", "red");
               $scope.answers[$scope.field.id][0]["value"] = d.id;
             } else {
               d3.select(this).attr("r", 5.5).style("fill", "#DDD");
               $scope.answers[$scope.field.id][0]["value"] = "";
             }
             $scope.$apply();
           });
      });
    }
}]).
controller("SubmissionFieldEntryCtrl", ["$scope",
  function($scope) {
    $scope.fieldEntry = $scope.fieldId + "-input-" + $scope.$index;
}]).
controller("SubmissionFieldCtrl", ["$scope", "fieldUtilities", function ($scope, fieldUtilities) {
  $scope.fieldFormVarName = fieldUtilities.fieldFormName($scope.field.id + "$" + $scope.$index);

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

  $scope.clear = function() {
    $scope.entries.length = 0;
    $scope.addAnswerEntry($scope.entries);
  };

  if ($scope.field.type === "inputbox") {
    $scope.validator = fieldUtilities.getValidator($scope.field);
  } else if ($scope.field.type === "date") {
    $scope.dateOptions = {showWeeks: false};

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
    $scope.dateOptions1 = {showWeeks: false};
    $scope.dateOptions2 = {showWeeks: false};

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
        $scope.entries[0]["value"] = String(Number($scope.daterange.start)) + ":" + String(Number($scope.daterange.end));
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

  $scope.fieldId = $scope.stepId + "-field-" + $scope.fieldRow + "-" + $scope.fieldCol;
}]);
