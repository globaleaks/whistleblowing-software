GLClient.controller("TipCtrl",
  ["$scope", "$location", "$filter", "$route", "$routeParams", "$uibModal", "$http", "Authentication", "RTip", "WBTip", "ReceiverPreferences", "RTipExport", "RTipDownloadRFile", "WBTipDownloadFile", "fieldUtilities",
  function($scope, $location, $filter, $route, $routeParams, $uibModal, $http, Authentication, RTip, WBTip, ReceiverPreferences, RTipExport, RTipDownloadRFile, WBTipDownloadFile, fieldUtilities) {
    $scope.fieldUtilities = fieldUtilities;
    $scope.tip_id = $routeParams.tip_id;
    $scope.target_file = "#";

    $scope.answers = {};
    $scope.uploads = {};

    $scope.showEditLabelInput = false;

    $scope.getAnswersEntries = function(entry) {
      if (entry === undefined) {
        return $scope.answers[$scope.field.id];
      }

      return entry[$scope.field.id];
    };

    var filterNotTriggeredField = function(field, answers) {
      var i, j, f;
      for(i=field.children.length - 1; i>=0; i--) {
        f = field.children[i];
        if (!fieldUtilities.isFieldTriggered(field, f, answers[f.id], $scope.tip.total_score)) {
          field.enabled = false;
          field.children.splice(i, 1);
        } else {
          field.enabled = true;
          for (j=0; j<answers[f.id].length; j++) {
            filterNotTriggeredField(f, answers[f.id]);
          }
        }
      }
    };

    $scope.preprocessTipAnswers = function(tip) {
      var i, j, k, step, child;
      for (i=tip.questionnaires[0].steps.length - 1; i>=0; i--) {
        step = tip.questionnaires[0].steps[i];
        j = step.children.length;
        while (j--) {
          if (step.children[j]["template_id"] === "whistleblower_identity") {
            $scope.whistleblower_identity_field = step.children[j];
            step.children.splice(j, 1);
            $scope.questionnaire = {
              steps: [$scope.whistleblower_identity_field]
            };

            $scope.fields = $scope.questionnaire.steps[0].children;
            $scope.rows = fieldUtilities.splitRows($scope.fields);
            $scope.field = $scope.whistleblower_identity_field;

            for (k = 0; k < $scope.field.children.length; k++) {
              child = $scope.field.children[k];
              $scope.answers[child.id] = [angular.copy(fieldUtilities.prepare_field_answers_structure(child))];
            }
          }
        }

        if ($scope.node.enable_experimental_features) {
          if (!fieldUtilities.isFieldTriggered(null, step, $scope.tip.answers, $scope.tip.total_score)) {
            step.enabled = false;
            tip.questionnaires[0].steps.splice(i, 1);
          } else {
            step.enabled = true;
            for (j=0; j<step.children.length; j++) {
              child = step.children[i];
              for (k=0; k<$scope.tip.questionnaires[0].answers[child.id].length; k++) {
                filterNotTriggeredField(child, $scope.tip.questionnaires[0].answers[child.id][k]);
              }
            }
          }
        }
      }
    };

    $scope.hasMultipleEntries = function(field_answer) {
      if (field_answer !== undefined) {
        return field_answer.length > 1;
      }

      return false;
    };

    $scope.filterFields = function(field) {
      return field.type !== "fileupload";
    };

    if ($scope.session.role === "whistleblower") {
      $scope.fileupload_url = "wbtip/rfile";

      $scope.tip = new WBTip(function(tip) {
        $scope.tip = tip;
        $scope.context = $scope.tip.context;
        $scope.total_score = $scope.tip.total_score;

        $scope.ctx = "wbtip";
        $scope.preprocessTipAnswers(tip);

        $scope.Utils.evalSubmissionStatus($scope.tip, $scope.submission_statuses);

        $scope.showWBFileWidget = function() {
          return $scope.contexts_by_id[tip.context_id].enable_rc_to_wb_files && (tip.wbfiles.length > 0);
        };

        $scope.downloadWBFile = function(file) {
          WBTipDownloadFile(file);
        };

        // FIXME: remove this variable that is now needed only to map wb_identity_field
        $scope.submission = {};
        $scope.submission._submission = tip;

        $scope.provideIdentityInformation = function(identity_field_id, identity_field_answers) {
          return $http.post("wbtip/" + $scope.tip.id + "/provideidentityinformation",
                            {"identity_field_id": identity_field_id, "identity_field_answers": identity_field_answers}).
              then(function(){
                $route.reload();
              });
        };

        if (tip.receivers.length === 1 && tip.msg_receiver_selected === null) {
          tip.msg_receiver_selected = tip.msg_receivers_selector[0].key;
        }
      });

    } else if ($scope.session.role === "receiver") {
      $scope.preferences = ReceiverPreferences.get();

      $scope.tip = new RTip({id: $scope.tip_id}, function(tip) {
        $scope.tip = tip;
        $scope.context = $scope.tip.context;
        $scope.total_score = $scope.tip.total_score;
        $scope.ctx = "rtip";
        $scope.preprocessTipAnswers(tip);

        $scope.exportTip = RTipExport;
        $scope.downloadRFile = RTipDownloadRFile;

        $scope.showEditLabelInput = $scope.tip.label === "";

        $scope.Utils.evalSubmissionStatus($scope.tip, $scope.submission_statuses);

        $scope.showWBFileUpload = function() {
          return $scope.contexts_by_id[tip.context_id].enable_rc_to_wb_files;
        };
      });
    }

    $scope.editLabel = function() {
      $scope.showEditLabelInput = true;
    };

    $scope.updateLabel = function(label) {
      $scope.tip.updateLabel(label);
      $scope.showEditLabelInput = false;
    };

    $scope.updateSubmissionStatus = function() {
      $scope.tip.updateSubmissionStatus().then(function() {
        $scope.Utils.evalSubmissionStatus($scope.tip, $scope.submission_statuses);
      });
    };

    $scope.newComment = function() {
      $scope.tip.newComment($scope.tip.newCommentContent);
      $scope.tip.newCommentContent = "";
    };

    $scope.newMessage = function() {
      $scope.tip.newMessage($scope.tip.newMessageContent);
      $scope.tip.newMessageContent = "";
    };

    $scope.tip_notify = function(enable) {
      return $scope.tip.operation("set", {"key": "enable_notifications", "value": enable}).then(function() {
        $scope.tip.enable_notifications = enable;
      });
    };

    $scope.tip_delete = function () {
      $uibModal.open({
        templateUrl: "views/partials/tip_operation_delete.html",
        controller: "TipOperationsCtrl",
        resolve: {
          args: function () {
            return {
              tip: $scope.tip,
              operation: "delete"
            };
          }
        }
      });
    };

    $scope.tip_postpone = function () {
      $uibModal.open({
        templateUrl: "views/partials/tip_operation_postpone.html",
        controller: "TipOperationsCtrl",
        resolve: {
          args: function() {
            return {
              tip: $scope.tip,
              operation: "postpone_expiration",
              contexts_by_id: $scope.contexts_by_id,
              Utils: $scope.Utils
            };
          }
        }
      });
    };

    $scope.tip_open_additional_questionnaire = function () {
      $scope.answers = {};
      $scope.uploads = {};

      angular.forEach($scope.tip.additional_questionnaire.steps, function(step) {
        angular.forEach(step.children, function(field) {
          $scope.answers[field.id] = [angular.copy($scope.fieldUtilities.prepare_field_answers_structure(field))];
        });
      });

      $uibModal.open({
        templateUrl: "views/partials/tip_additional_questionnaire_form.html",
        controller: "AdditionalQuestionnaireCtrl",
        size: "lg",
        scope: $scope
      });
    };

    $scope.file_identity_access_request = function () {
      $uibModal.open({
        templateUrl: "views/partials/tip_operation_file_identity_access_request.html",
        controller: "IdentityAccessRequestCtrl",
        resolve: {
          tip: function () {
            return $scope.tip;
          }
        }
      });
    };

    $scope.total_score = 0;

    $scope.$watch("answers", function () {
      fieldUtilities.onAnswersUpdate($scope);
    }, true);
}]).
controller("TipOperationsCtrl",
  ["$scope", "$http", "$route", "$location", "$uibModalInstance", "args",
   function ($scope, $http, $route, $location, $uibModalInstance, args) {
  $scope.args = args;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.ok = function () {
    $uibModalInstance.close();

    if ($scope.args.operation === "postpone_expiration") {
      var req = {
        "operation": "postpone_expiration",
        "args": {}
      };

      return $http({method: "PUT", url: "rtip/" + args.tip.id, data: req}).then(function () {
        $route.reload();
      });
    } else if ($scope.args.operation === "delete") {
      return $http({method: "DELETE", url: "rtip/" + args.tip.id, data:{}}).
        then(function() {
          $location.url("/receiver/tips");
          $route.reload();
        });
    }
  };
}]).
controller("RTipWBFileUploadCtrl", ["$scope", "Authentication", "RTipDownloadWBFile", "RTipWBFileResource", function($scope, Authentication, RTipDownloadWBFile, RTipWBFileResource) {
  var reloadUI = function (){ $scope.reload(); };

  $scope.downloadWBFile = function(f) {
    RTipDownloadWBFile(f).finally(reloadUI);
  };

  $scope.showDeleteWBFile = function(f) {
    return Authentication.session.user_id === f.author;
  };

  $scope.deleteWBFile = function(f) {
    RTipWBFileResource.remove({"id":f.id}).$promise.finally(reloadUI);
  };
}]).
controller("WBTipFileDownloadCtrl", ["$scope", "$uibModalInstance", "WBTipDownloadFile", "file", "tip", function($scope, $uibModalInstance, WBTipDownloadFile, file, tip) {
  $scope.ctx = "download";
  $scope.file = file;
  $scope.tip = tip;
  $scope.ok = function() {
    $uibModalInstance.close();
    WBTipDownloadFile(file);
  };

  $scope.cancel = function () {
    $uibModalInstance.close();
  };
}]).
controller("IdentityAccessRequestCtrl",
  ["$scope", "$http", "$route", "$uibModalInstance", "tip",
   function ($scope, $http, $route, $uibModalInstance, tip) {
  $scope.tip = tip;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.ok = function () {
    $uibModalInstance.close();

    return $http.post("rtip/" + tip.id + "/identityaccessrequests", {"request_motivation": $scope.request_motivation}).
        then(function(){
          $route.reload();
        });
  };
}]);
