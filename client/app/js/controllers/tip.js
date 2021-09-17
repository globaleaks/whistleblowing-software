GL.controller("TipCtrl",
  ["$scope", "$location", "$filter", "$http", "$routeParams", "$uibModal", "Authentication", "RTip", "WBTip", "RTipExport", "RTipDownloadRFile", "WBTipDownloadFile", "fieldUtilities",
  function($scope, $location, $filter, $http, $routeParams, $uibModal, Authentication, RTip, WBTip, RTipExport, RTipDownloadRFile, WBTipDownloadFile, fieldUtilities) {
    $scope.fieldUtilities = fieldUtilities;
    $scope.tip_id = $routeParams.tip_id;

    $scope.itemsPerPage = 5;
    $scope.currentCommentsPage = 1;
    $scope.currentMessagesPage = 1;

    $scope.answers = {};
    $scope.uploads = {};

    $scope.showEditLabelInput = false;

    $scope.openGrantTipAccessModal = function () {
      $uibModal.open({
        templateUrl: "views/partials/modal_grant_access.html",
        controller: "ConfirmableModalCtrl",
        resolve: {
          arg: {},
          confirmFun: function() {
            return function(receiver_id) {
              var req = {
                operation: "grant",
                args: {
                  receiver: receiver_id
                },
              };

              return $http({method: "PUT", url: "api/rtips/" + $scope.tip.id, data: req}).then(function () {
                $scope.reload();
              });
            };
          },
          cancelFun: null
        }
      });
    };

    $scope.openRevokeTipAccessModal = function (receiver_id) {
      $uibModal.open({
        templateUrl: "views/partials/modal_revoke_access.html",
        controller: "ConfirmableModalCtrl",
        resolve: {
          arg: null,
          confirmFun: function() {
            return function(receiver_id) {
              var req = {
                operation: "revoke",
                args: {
                  receiver: receiver_id
                }
              };

              return $http({method: "PUT", url: "api/rtips/" + $scope.tip.id, data: req}).then(function () {
                $scope.reload();
              });
            };
          },
          cancelFun: null
        }
      });
    };

    $scope.getAnswersEntries = function(entry) {
      if (typeof entry === "undefined") {
        return $scope.answers[$scope.field.id];
      }

      return entry[$scope.field.id];
    };

    var filterNotTriggeredField = function(parent, field, answers) {
      var i;
      if (fieldUtilities.isFieldTriggered(parent, field, answers, $scope.tip.total_score)) {
        for(i=0; i<field.children.length; i++) {
          filterNotTriggeredField(field, field.children[i], answers);
        }
      }
    };

    $scope.preprocessTipAnswers = function(tip) {
      var x, i, j, questionnaire, step;

      for (x=0; x<tip.questionnaires.length; x++) {
        questionnaire = tip.questionnaires[x];
        $scope.fieldUtilities.parseQuestionnaire(questionnaire, {});

        for (i=0; i<questionnaire.steps.length; i++) {
          step = questionnaire.steps[i];
          if (fieldUtilities.isFieldTriggered(null, step, questionnaire.answers, $scope.tip.total_score)) {
            for (j=0; j<step.children.length; j++) {
              filterNotTriggeredField(step, step.children[j], questionnaire.answers);
            }
          }
        }

        for (i=0; i<questionnaire.steps.length; i++) {
          step = questionnaire.steps[i];
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

              fieldUtilities.onAnswersUpdate($scope);
            }
          }
        }
      }
    };

    $scope.hasMultipleEntries = function(field_answer) {
      return (typeof field_answer !== "undefined") && field_answer.length > 1;
    };

    $scope.filterFields = function(field) {
      return field.type !== "fileupload";
    };

    if ($scope.Authentication.session.role === "whistleblower") {
      $scope.fileupload_url = "api/wbtip/rfile";

      $scope.tip = new WBTip(function(tip) {
        $scope.tip = tip;
        $scope.tip.context = $scope.contexts_by_id[$scope.tip.context_id];
        $scope.total_score = $scope.tip.total_score;

        $scope.ctx = "wbtip";
        $scope.preprocessTipAnswers(tip);

        $scope.tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText($scope.tip.status, $scope.tip.substatus, $scope.submission_statuses);

        $scope.showWBFileWidget = function() {
          return $scope.tip.context.enable_rc_to_wb_files && (tip.wbfiles.length);
        };

        $scope.downloadWBFile = function(file) {
          WBTipDownloadFile(file);
        };

        // FIXME: remove this variable that is now needed only to map wb_identity_field
        $scope.submission = {};
        $scope.submission._submission = tip;

        $scope.provideIdentityInformation = function(identity_field_id, identity_field_answers) {
          return $http.post("api/wbtip/" + $scope.tip.id + "/provideidentityinformation",
                            {"identity_field_id": identity_field_id, "identity_field_answers": identity_field_answers}).
              then(function(){
                $scope.reload();
              });
        };

        if (tip.receivers.length === 1 && tip.msg_receiver_selected === null) {
          tip.msg_receiver_selected = tip.msg_receivers_selector[0].key;
        }
      });

    } else if ($scope.Authentication.session.role === "receiver") {
      $scope.tip = new RTip({id: $scope.tip_id}, function(tip) {
        $scope.tip = tip;
        $scope.tip.context = $scope.contexts_by_id[$scope.tip.context_id];

        $scope.total_score = $scope.tip.total_score;
        $scope.ctx = "rtip";
        $scope.preprocessTipAnswers(tip);

        $scope.exportTip = RTipExport;
        $scope.downloadRFile = RTipDownloadRFile;

        $scope.showEditLabelInput = $scope.tip.label === "";

        $scope.tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText($scope.tip.status, $scope.tip.substatus, $scope.submission_statuses);

        $scope.showWBFileUpload = function() {
          return $scope.tip.context.enable_rc_to_wb_files;
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
        $scope.tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText($scope.tip.status, $scope.tip.substatus, $scope.submission_statuses);
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

    $scope.tip_toggle_star = function() {
      return $scope.tip.operation("update_important", {"value": !$scope.tip.important}).then(function() {
        $scope.tip.important = !$scope.tip.important;
      });
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
              operation: "postpone",
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

      $uibModal.open({
        templateUrl: "views/partials/tip_additional_questionnaire_form.html",
        controller: "AdditionalQuestionnaireCtrl",
        scope: $scope
      });
    };

    $scope.access_identity = function () {
      return $http.post("api/rtips/" + $scope.tip.id + "/iars", {"request_motivation": ""}).then(function(){
         $scope.reload();
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
  ["$scope", "$http", "$location", "$uibModalInstance", "args",
   function ($scope, $http, $location, $uibModalInstance, args) {
  $scope.args = args;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.confirm = function () {
    $uibModalInstance.close();

    if ($scope.args.operation === "postpone") {
      var req = {
        "operation": "postpone",
        "args": {}
      };

      return $http({method: "PUT", url: "api/rtips/" + args.tip.id, data: req}).then(function () {
        $scope.reload();
      });
    } else if ($scope.args.operation === "delete") {
      return $http({method: "DELETE", url: "api/rtips/" + args.tip.id, data:{}}).
        then(function() {
          $location.url("/recipient/reports");
          $scope.reload();
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
  $scope.confirm = function() {
    $uibModalInstance.close();
    WBTipDownloadFile(file);
  };

  $scope.cancel = function () {
    $uibModalInstance.close();
  };
}]).
controller("IdentityAccessRequestCtrl",
  ["$scope", "$http", "$uibModalInstance", "tip",
   function ($scope, $http, $uibModalInstance, tip) {
  $scope.tip = tip;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.confirm = function () {
    $uibModalInstance.close();

    return $http.post("api/rtips/" + tip.id + "/iars", {"request_motivation": $scope.request_motivation}).
      then(function(){
        $scope.reload();
      });
  };
}]);
