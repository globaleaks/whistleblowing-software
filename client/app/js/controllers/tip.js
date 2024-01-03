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
            xhr.open("GET", "api/whistleblower/wbtip/wbfiles/" + id, true);
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

    $scope.redactMode = false;
    $scope.redactOperationTitle = $filter("translate")("Mask") + " / " + $filter("translate")("Redact");

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

    $scope.openModalReopen = function() {
      $uibModal.open({
        templateUrl: "views/modals/reopen_submission.html",
        controller: "ConfirmableModalCtrl",
        resolve: {
          arg: {
            motivation: "",
          },
          confirmFun: function () {
            return function (motivation) {
              $scope.tip.status = "opened";
              $scope.tip.substatus = null;
              $scope.tip.motivation = motivation;
              $scope.updateSubmissionStatus();
            };
          },
          cancelFun: null
        }
      });
    };

    $scope.openModalChangeState = function(){
      $uibModal.open({
        templateUrl: "views/modals/change_submission_status.html",
        controller: "ConfirmableModalCtrl",
        resolve: {
          arg: {
            tip: angular.copy($scope.tip),
            submission_statuses: function() {
              var sub_copy = angular.copy($scope.submission_statuses);
              var output = [];
              for (var x of sub_copy) {
                if (x.substatuses.length) {
                  for (var y of x.substatuses) {
                    output.push({
                      id: x.id + ":" + y.id,
                      label: $filter("translate")(x.label ) + " \u2013 " + y.label,
                      status: x.id,
                      substatus: y.id,
                      order: output.length
                    });
                  }
                } else {
                  x.status = x.id;
                  x.substatus = '';
                  x.order = output.length;
                  output.push(x);
                }
              }
              return output;
            }()
          },
          confirmFun: function () {
            return function (arg) {
              $scope.tip.status = arg.status.status;
              $scope.tip.substatus = arg.status.substatus;
              $scope.tip.motivation = arg.motivation;
              $scope.updateSubmissionStatus();
            };
          },
          cancelFun: null
        }
      });
    }

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

        var reloadUI = function() {
          $scope.reload();
        };

        $scope.redactFileOperation = function(operation, content_type, file) {
          var redactionData = {
            reference_id: file.ifile_id,
            internaltip_id: $scope.tip.id,
            entry: '0',
            operation: operation,
            content_type: content_type,
            temporary_redaction: [],
            permanent_redaction: []
          }

          if (operation === 'full-mask') {
            redactionData.temporary_redaction = [{'start': '-inf', 'end': 'inf'}];
          }

          let redaction = $scope.getRedaction(file.ifile_id, '0');

          if (redaction) {
            redactionData.id = redaction.id;
            $scope.tip.updateRedaction(redactionData);
          } else {
            $scope.tip.newRedaction(redactionData);
          }
        };

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

    function refineContent(content, ranges, code) {
      var maskedText = content.split("");

      ranges.forEach(function (range) {
        if (range.start >= 0 && range.start <= maskedText.length && range.end >= 0) {
          for (var i = range.start; i <= range.end; i++) {
            maskedText.splice(i, 1, String.fromCharCode(code));
          }
        }
      });

      return maskedText.join("");
    }

    $scope.maskContent = function(id, index, value) {
      let redaction = $scope.getRedaction(id, index);

      let masked_value = value;

      if (redaction) {
        if (redaction.temporary_redaction.length > 0) {
          var temporaryRedactionArray = Object.values(redaction.temporary_redaction);
          temporaryRedactionArray.sort(function(a, b) {
            return a.start - b.start;
          });

          masked_value = refineContent(masked_value, temporaryRedactionArray, 0x2591);
        }

        if (redaction.permanent_redaction.length > 0) {
          var permanentRedactionArray = Object.values(redaction.permanent_redaction);
          permanentRedactionArray.sort(function(a, b) {
            return a.start - b.start;
          });

          masked_value = refineContent(masked_value, permanentRedactionArray, 0x2588);
        }
      }

      return masked_value;
    }

    $scope.getRedaction = function(id, entry) {
      var redactionObjects = $scope.tip.redactions.filter(function(redaction) {
        return redaction.reference_id === id && redaction.entry === entry;
      });

      return redactionObjects.length > 0 ? redactionObjects[0] : null;
    }

    $scope.isMasked = function(id) {
      return $scope.getRedaction(id, '0') !== null;
    }

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

    $scope.toggleRedactMode = function() {
      $scope.redactMode = !$scope.redactMode;
    }

    $scope.redactInformation = function(type, id, entry, content) {
      $uibModal.open({
        templateUrl: "views/modals/redact_information.html",
        controller: "TipRedactInformationCtrl",
        resolve: {
          args: function() {
            return {
              tip: $scope.tip,
              redaction: $scope.getRedaction(id, entry),
              Utils: $scope.Utils,
              data: {
                type,
                id,
                entry,
                content
              }
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
}]).
controller("TipRedactInformationCtrl", ["$scope", "$document", "$filter", "mask", "$sce", "$uibModalInstance", "args", "$routeParams", "$http", function($scope, $document, $filter, mask, $sce, $uibModalInstance, args, $routeParams, $http) {
  $scope.redaction = null;
  $scope.args = args;
  $scope.forced_visible = false;

  $scope.vars = {
    redaction_switch: true // True: Masking; False: Redaction
  };

  if (!$scope.resources.preferences.can_mask_information && $scope.resources.preferences.can_redact_information) {
    $scope.vars.redaction_switch = false;
  }

  $scope.ranges_selected = [];

  $scope.cancel = function() {
    $uibModalInstance.close();
  };

  $scope.toggleVisibility = function() {
    $scope.forced_visible = !$scope.forced_visible;
  }

  $scope.initializeMasking = function() {
    $scope.redaction = $scope.args.redaction;
    $scope.temporary_redaction = [];
    $scope.permanent_redaction = [];
    $scope.ranges_selected = [];

    if ($scope.redaction) {
      $scope.permanent_redaction = $scope.redaction.permanent_redaction;
      $scope.temporary_redaction = $scope.redaction.temporary_redaction;

      if ($scope.vars.redaction_switch) {
        $scope.ranges_selected = $scope.temporary_redaction;
      }
    }

    $scope.unmaskedContent = $scope.content = $scope.args.data.content;
    $scope.originalContent = $scope.content = mask.maskContent($scope.content, $scope.temporary_redaction, true, String.fromCharCode(0x2591));
  };

  $scope.selectContent = function() {
    let response = mask.getSelectedRanges(true, $scope.ranges_selected);
    if (!$scope.vars.redaction_switch) {
      $scope.ranges_selected = mask.intersectRanges($scope.temporary_redaction, response.new_ranges);
      $scope.content = mask.maskContent($scope.content, $scope.ranges_selected, true, String.fromCharCode(0x2588));
    } else {
      if (!$scope.resources.preferences.can_mask_information) {
        $scope.ranges_selected = mask.intersectRanges($scope.temporary_redaction, response.new_ranges);
      } else {
        $scope.ranges_selected = response.new_ranges;
      }

      $scope.content = mask.maskContent($scope.content, $scope.ranges_selected, true, String.fromCharCode(0x2591));
      $scope.content = mask.maskContent($scope.content, $scope.permanent_redaction, true, String.fromCharCode(0x2588));
    }
  };

  $scope.unSelectContent = function() {
    let response = mask.getSelectedRanges(false, $scope.ranges_selected);
    $scope.ranges_selected = response.new_ranges;
    $scope.content = mask.onUnHighlight($scope.content, $scope.unmaskedContent, [response.selected_ranges]);
  }

  $scope.saveMasking = function() {
    let redactionData = {
      internaltip_id: $scope.args.tip.id,
      reference_id: $scope.args.data.id,
      entry: $scope.args.data.entry,
      temporary_redaction: [],
      permanent_redaction: []
    };

    if ($scope.vars.redaction_switch) {
      redactionData["operation"] = "mask";
      redactionData["content_type"] = $scope.args.data.type;
      redactionData["temporary_redaction"] = $scope.ranges_selected;
    } else {
      redactionData["operation"] = "redact";
      redactionData["content_type"] = $scope.args.data.type;
      redactionData["permanent_redaction"] = $scope.ranges_selected;
    }

    if ($scope.redaction) {
      redactionData.id = $scope.redaction.id;
      $scope.args.tip.updateRedaction(redactionData);
    } else {
      $scope.args.tip.newRedaction(redactionData);
    }

    $scope.cancel();
  }

  $scope.ignoreEdit = function(event) {
    if (event.keyCode >= 37 && event.keyCode <= 40) {
      return;
    }
    event.preventDefault();
  };

  $scope.toggleMasking = function() {
    $scope.initializeMasking();
  };

  $scope.initializeMasking()
}]);
