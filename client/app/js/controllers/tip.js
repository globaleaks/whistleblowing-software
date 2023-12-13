GL.controller("TipCtrl",
  ["$scope", "$location", "$filter", "$http", "$interval", "$routeParams", "$uibModal", "Authentication", "RTip", "WBTip", "RTipExport", "RTipDownloadWBFile", "WBTipDownloadWBFile", "WBTipDownloadRFile", "RTipViewWBFile", "fieldUtilities",
  function($scope, $location, $filter, $http, $interval, $routeParams, $uibModal, Authentication, RTip, WBTip, RTipExport, RTipDownloadWBFile, WBTipDownloadWBFile, WBTipDownloadRFile, RTipViewWBFile, fieldUtilities) {
    $scope.fieldUtilities = fieldUtilities;
    $scope.tip_id = $routeParams.tip_id;

    $scope.itemsPerPage = 5;
    $scope.currentCommentsPage = 1;

    $scope.answers = {};
    $scope.uploads = {};

    $scope.showEditLabelInput = false;

    $scope.audioFiles = {};

    $scope.loadAudioFile = function(reference_id) {
      for (var i=0; i < $scope.tip.wbfiles.length; i++) {
        if ($scope.tip.wbfiles[i].reference_id === reference_id) {
          var id = $scope.tip.wbfiles[i].id;
          var xhr = new XMLHttpRequest();

          if ($scope.Authentication.session.role === "whistleblower") {
            xhr.open("GET", "api/whistleblower/wbfiles/" + id, true);
          } else {
            xhr.open("GET", "api/recipient/wbfiles/" + id, true);
          }

          xhr.setRequestHeader("x-session", $scope.Authentication.session.id);
          xhr.overrideMimeType("audio/webm");
          xhr.responseType = "blob";

          xhr.onload = function() {
            if (this.status === 200) {
              $scope.audioFiles[reference_id] = this.response;

              window.addEventListener("message", function(message) {
                const iframe = document.getElementById("audio-file-" + reference_id);

                if (message.source !== iframe.contentWindow) {
                  return;
                }

                var data = {
                  tag: "audio",
                  blob: $scope.audioFiles[reference_id]
                };

                iframe.contentWindow.postMessage(data, "*");
              });

              $scope.$apply();
            }
          };

          xhr.send();

          break;
        }
      }
    };

    $scope.tabs = [
      {
        title: "Everyone",
        key: "public"
      },
      {
        title: "Recipients only",
        key: "internal"
      },
      {
        title: "Me only",
        key: "personal"
      }
    ];
    $scope.activeTabKey = $scope.tabs[0].key;

    $scope.selectedTab = function (key){
      $scope.activeTabKey = key;
    };

    $scope.openTipTransferModal = function() {
      $http({
        method: "PUT", url: "api/user/operations", data: {
          "operation": "get_users_names",
          "args": {}
        }
      }).then(function (response) {
        var selectable_recipients = [];

        $scope.public.receivers.forEach(async (receiver) => {
          if (receiver.id !== $scope.Authentication.session.user_id && !$scope.tip.receivers_by_id[receiver.id]) {
            selectable_recipients.push(receiver);
          }
        });

        $uibModal.open({
          templateUrl: "views/modals/transfer_access.html",
          controller: "ConfirmableModalCtrl",
          resolve: {
            arg: {
              users_names: response.data,
              selectable_recipients: selectable_recipients
            },
            confirmFun: function () {
              return function (receiver_id) {
                var req = {
                  operation: "transfer",
                  args: {
                    receiver: receiver_id
                  },
                };
                return $http({ method: "PUT", url: "api/recipient/rtips/" + $scope.tip.id, data: req }).then(function () {
                  $location.path("recipient/reports");
                });
              };
            },
            cancelFun: null
          }
        });
      });
    };

    $scope.openGrantTipAccessModal = function () {
      $http({method: "PUT", url: "api/user/operations", data:{
        "operation": "get_users_names",
        "args": {}
      }}).then(function(response) {
        var selectable_recipients = [];

        $scope.public.receivers.forEach(async (receiver) => {
          if (receiver.id !== $scope.Authentication.session.user_id && !$scope.tip.receivers_by_id[receiver.id]) {
            selectable_recipients.push(receiver);
          }
        });

        $uibModal.open({
          templateUrl: "views/modals/grant_access.html",
          controller: "ConfirmableModalCtrl",
          resolve: {
            arg: {
              users_names: response.data,
              selectable_recipients: selectable_recipients
            },
            confirmFun: function() {
              return function(receiver_id) {
                var req = {
                  operation: "grant",
                  args: {
                    receiver: receiver_id
                  },
                };

                return $http({method: "PUT", url: "api/recipient/rtips/" + $scope.tip.id, data: req}).then(function () {
                  $scope.reload();
                });
              };
            },
            cancelFun: null
          }
        });
      });
    };

    $scope.openRevokeTipAccessModal = function () {
      $http({method: "PUT", url: "api/user/operations", data:{
        "operation": "get_users_names",
        "args": {}
      }}).then(function(response) {
        var selectable_recipients = [];

        $scope.public.receivers.forEach(async (receiver) => {
          if (receiver.id !== $scope.Authentication.session.user_id && $scope.tip.receivers_by_id[receiver.id]) {
            selectable_recipients.push(receiver);
          }
        });

        $uibModal.open({
          templateUrl: "views/modals/revoke_access.html",
          controller: "ConfirmableModalCtrl",
          resolve: {
            arg: {
              users_names: response.data,
              selectable_recipients: selectable_recipients
            },
            confirmFun: function() {
              return function(receiver_id) {
                var req = {
                  operation: "revoke",
                  args: {
                    receiver: receiver_id
                  }
                };

                return $http({method: "PUT", url: "api/recipient/rtips/" + $scope.tip.id, data: req}).then(function () {
                  $scope.reload();
                });
              };
            },
            cancelFun: null
          }
        });
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
      if (fieldUtilities.isFieldTriggered($scope, parent, field, answers, $scope.tip.score)) {
        for(i=0; i<field.children.length; i++) {
          filterNotTriggeredField(field, field.children[i], answers);
        }
      }
    };

    $scope.preprocessTipAnswers = function(tip) {
      var x, i, j, k, questionnaire, step;

      for (x=0; x<tip.questionnaires.length; x++) {
        questionnaire = tip.questionnaires[x];
        $scope.fieldUtilities.parseQuestionnaire(questionnaire, {});

        for (i=0; i<questionnaire.steps.length; i++) {
          step = questionnaire.steps[i];
          if (fieldUtilities.isFieldTriggered($scope, null, step, questionnaire.answers, $scope.tip.score)) {
            for (j=0; j<step.children.length; j++) {
              filterNotTriggeredField(step, step.children[j], questionnaire.answers);
            }
          }
        }

        for (i=0; i<questionnaire.steps.length; i++) {
          step = questionnaire.steps[i];
          j = step.children.length;
          while (j--) {
            if (step.children[j]["template_id"] === "whistleblower_identity" || step.children[j]["key"] === "whistleblower_identity") {
              $scope.whistleblower_identity_field = step.children[j];
              $scope.whistleblower_identity_field.enabled = true;
              step.children.splice(j, 1);
              $scope.questionnaire = {
                steps: [angular.copy($scope.whistleblower_identity_field)]
              };

              $scope.fields = $scope.questionnaire.steps[0].children;
              $scope.rows = fieldUtilities.splitRows($scope.fields);

              fieldUtilities.onAnswersUpdate($scope);

              for (k=0; k<$scope.whistleblower_identity_field.children.length; k++) {
                filterNotTriggeredField($scope.whistleblower_identity_field, $scope.whistleblower_identity_field.children[k], $scope.tip.data.whistleblower_identity);
              }
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
      $scope.fileupload_url = "api/whistleblower/wbtip/wbfiles";

      $scope.tip = new WBTip(function(tip) {
        $scope.tip = tip;
        $scope.tip.context = $scope.contexts_by_id[$scope.tip.context_id];
        $scope.tip.receivers_by_id = $scope.Utils.array_to_map($scope.tip.receivers);
        $scope.score = $scope.tip.score;

        $scope.ctx = "wbtip";
        $scope.preprocessTipAnswers(tip);

        $scope.downloadWBFile = WBTipDownloadWBFile;

        $scope.tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText($scope.tip.status, $scope.tip.substatus, $scope.submission_statuses);

        $scope.downloadRFile = function(file) {
          WBTipDownloadRFile(file);
        };

        $scope.downloadWBFile = function(file) {
          WBTipDownloadWBFile(file);
        };

        // FIXME: remove this variable that is now needed only to map wb_identity_field
        $scope.submission = {};
        $scope.submission._submission = tip;

        $scope.provideIdentityInformation = function(identity_field_id, identity_field_answers) {
          for (var key in $scope.uploads) {
            if ($scope.uploads[key]) {
              $scope.uploads[key].resume();
            }
          }

          $scope.interval = $interval(function() {
            for (var key in $scope.uploads) {
              if ($scope.uploads[key] &&
                  $scope.uploads[key].isUploading() &&
                  $scope.uploads[key].isUploading()) {
                return;
              }
            }

            $interval.cancel($scope.interval);

            return $http.post("api/whistleblower/wbtip/identity",
                              {"identity_field_id": identity_field_id, "identity_field_answers": identity_field_answers}).
                then(function(){
                  $scope.reload();
                });

          }, 1000);
        };

        if (tip.receivers.length === 1 && tip.msg_receiver_selected === null) {
          tip.msg_receiver_selected = tip.msg_receivers_selector[0].key;
        }
      });

    } else if ($scope.Authentication.session.role === "receiver") {
      $scope.tip = new RTip({id: $scope.tip_id}, function(tip) {
        $scope.tip = tip;
        $scope.tip.context = $scope.contexts_by_id[$scope.tip.context_id];
        $scope.tip.receivers_by_id = $scope.Utils.array_to_map($scope.tip.receivers);

        $scope.score = $scope.tip.score;
        $scope.ctx = "rtip";
        $scope.preprocessTipAnswers(tip);

        $scope.exportTip = RTipExport;
        $scope.downloadWBFile = RTipDownloadWBFile;
        $scope.viewWBFile = RTipViewWBFile;

        $scope.showEditLabelInput = $scope.tip.label === "";

        $scope.tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText($scope.tip.status, $scope.tip.substatus, $scope.submission_statuses);
        $scope.supportedViewTypes = ["application/pdf", "audio/mpeg", "image/gif", "image/jpeg", "image/png", "text/csv", "text/plain", "video/mp4"];
      });
    }

    $scope.editLabel = function() {
      $scope.showEditLabelInput = true;
    };

    $scope.markReportStatus = function (date) {
      var report_date = new Date(date);
      var current_date = new Date();
      return current_date > report_date;
    };

    $scope.updateLabel = function(label) {
      $scope.tip.operation("set", {"key": "label", "value": label}).then(function() {
        $scope.showEditLabelInput = false;
      });
    };

    $scope.updateSubmissionStatus = function() {
      $scope.tip.updateSubmissionStatus().then(function() {
        $scope.tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText($scope.tip.status, $scope.tip.substatus, $scope.submission_statuses);
      });
    };

    $scope.newComment = function() {
      $scope.tip.newComment($scope.tip.newCommentContent, $scope.activeTabKey);
      $scope.tip.newCommentContent = "";
    };

    $scope.tip_toggle_star = function() {
      return $scope.tip.operation("set", {"key": "important", "value": !$scope.tip.important}).then(function() {
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
        templateUrl: "views/modals/delete_confirmation.html",
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
        templateUrl: "views/modals/tip_operation_postpone.html",
        controller: "TipOperationsCtrl",
        resolve: {
          args: function() {
            return {
              tip: $scope.tip,
              operation: "postpone",
              contexts_by_id: $scope.contexts_by_id,
              date: $scope.Utils.getPostponeDate($scope.tip.expiration_date, $scope.contexts_by_id[$scope.tip.context_id].tip_timetolive),
              dateOptions: {
                minDate: $scope.Utils.getMinPostponeDate($scope.tip.expiration_date)
              },
              opened: false,
              Utils: $scope.Utils
            };
          }
        }
      });
    };

    $scope.set_reminder = function () {
      $uibModal.open({
        templateUrl: "views/modals/tip_operation_set_reminder.html",
        controller: "TipOperationsCtrl",
        resolve: {
          args: function() {
            return {
              tip: $scope.tip,
              operation: "set_reminder",
              contexts_by_id: $scope.contexts_by_id,
              date: $scope.Utils.getReminderDate($scope.contexts_by_id[$scope.tip.context_id].tip_reminder),
              dateOptions: {
                minDate: new Date($scope.tip.creation_date)
              },
              opened: false,
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
        templateUrl: "views/modals/tip_additional_questionnaire_form.html",
        controller: "AdditionalQuestionnaireCtrl",
        scope: $scope
      });
    };

    $scope.access_identity = function () {
      return $http.post("api/recipient/rtips/" + $scope.tip.id + "/iars", {"request_motivation": ""}).then(function(){
         $scope.reload();
      });
    };

    $scope.file_identity_access_request = function () {
      $uibModal.open({
        templateUrl: "views/modals/tip_operation_file_identity_access_request.html",
        controller: "IdentityAccessRequestCtrl",
        resolve: {
          tip: function () {
            return $scope.tip;
          }
        }
      });
    };

    $scope.score = 0;

    $scope.$watch("answers", function () {
      fieldUtilities.onAnswersUpdate($scope);
    }, true);

    $scope.$on("GL::uploadsUpdated", function () {
      fieldUtilities.onAnswersUpdate($scope);
    });
}]).
controller("TipOperationsCtrl",
  ["$scope", "$http", "$location", "$uibModalInstance", "args",
   function ($scope, $http, $location, $uibModalInstance, args) {
  $scope.args = args;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.disable_reminder = function () {
    $uibModalInstance.close();
    var req = {
      "operation": "set_reminder",
      "args": {
        "value": 32503680000000
      }
    };

    return $http({method: "PUT", url: "api/recipient/rtips/" + args.tip.id, data: req}).then(function () {
      $scope.reload();
    });
  };

  $scope.confirm = function () {
    $uibModalInstance.close();

    if ($scope.args.operation === "postpone" || $scope.args.operation === "set_reminder") {
      $scope.args.date.setUTCHours(0, 0, 0);
      if ($scope.args.operation === "postpone") {
        $scope.args.date.setDate($scope.args.date.getDate() + 1);
      }

      var req = {
        "operation": $scope.args.operation,
        "args": {
          "value": $scope.args.date.getTime()
        }
      };

      return $http({method: "PUT", url: "api/recipient/rtips/" + args.tip.id, data: req}).then(function () {
        $scope.reload();
      });
    }  else if (args.operation === "delete") {
      return $http({method: "DELETE", url: "api/recipient/rtips/" + args.tip.id, data:{}}).
        then(function() {
          $location.url("/recipient/reports");
          $scope.reload();
        });
    }
  };
}]).
controller("RTipRFileUploadCtrl", ["$scope", "Authentication", "RTipDownloadRFile", "RTipRFileResource", function($scope, Authentication, RTipDownloadRFile, RTipRFileResource) {
  var reloadUI = function (){ $scope.reload(); };

  $scope.downloadRFile = function(file) {
    RTipDownloadRFile(file);
  };

  $scope.deleteRFile = function(f) {
    RTipRFileResource.remove({"id":f.id}).$promise.finally(reloadUI);
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

    return $http.post("api/recipient/rtips/" + tip.id + "/iars", {"request_motivation": $scope.request_motivation}).
      then(function(){
        $scope.reload();
      });
  };
}]).
controller("WhistleblowerFilesCtrl", ["$scope", function ($scope) {
  $scope.uploads = {};
}]).
controller("WhistleblowerIdentityFormCtrl", ["$scope", function ($scope) {
  $scope.uploads = {};
}]);
