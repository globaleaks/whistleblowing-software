GL.controller("TipCtrl",
  ["$scope", "$location", "$filter", "$http", "$interval", "$routeParams", "$uibModal", "Authentication", "RTip", "WBTip", "RTipExport", "RTipDownloadWBFile", "WBTipDownloadFile", "fieldUtilities","RTipViewWBFile",
  function($scope, $location, $filter, $http, $interval, $routeParams, $uibModal, Authentication, RTip, WBTip, RTipExport, RTipDownloadWBFile, WBTipDownloadFile, fieldUtilities, RTipViewWBFile) {
    $scope.fieldUtilities = fieldUtilities;
    $scope.tip_id = $routeParams.tip_id;

    $scope.itemsPerPage = 5;
    $scope.currentCommentsPage = 1;

    $scope.answers = {};
    $scope.uploads = {};

    $scope.showEditLabelInput = false;

    $scope.editMode = false
    $scope.mode = false;
    $scope.permanentMaskingObjects = []
    $scope.maskingObjects = []

    $scope.tabs = [
      {
        title: "Public",
        key: "public"
      },
      {
        title: "Internal",
        key: "internal"
      },
      {
        title: "Personal",
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

        $scope.tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText($scope.tip.status, $scope.tip.substatus, $scope.submission_statuses);

        $scope.downloadRFile = function(file) {
          WBTipDownloadFile(file);
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
        $scope.fetchAudioFiles();

        $scope.exportTip = RTipExport;
        $scope.downloadWBFile = RTipDownloadWBFile;
        $scope.viewWBFile = RTipViewWBFile;

        $scope.show = function(id) {
          return !!$scope.tip.masking.find(mask => mask.content_id === id);
        }
        var reloadUI = function() {
          $scope.reload();
        };
        $scope.deleteWBFile = function(f) {
          let maskingObjects = $scope.tip.masking.filter(function(masking) {
            return masking.content_id === f.ifile_id;
          });
          if (maskingObjects.length !== 0) {
            return $http({
              method: "DELETE",
              url: "api/recipient/rtips/" + tip.id + "/masking/" + maskingObjects[0].id
            }).then(reloadUI);
          }
        };
        $scope.unmaskFile = function(f) {
          let maskingObjects = $scope.tip.masking.filter(function(masking) {
            return masking.content_id === f.ifile_id;
          });
          if (maskingObjects.length !== 0) {
            $scope.status = false
            var maskingData = {
              content_id: f.id,
              permanent_masking: [],
              temporary_masking: []
            }
            maskingData['operation'] = 'redact'
            $scope.tip.updateMasking(maskingObjects[0].id, maskingData);
            }
        };
        $scope.masking = function(f) {
          $scope.status = true
          var maskingData = {
            content_id: f.ifile_id,
            permanent_masking: [],
            temporary_masking: [
              { file_masking_status: $scope.status }
            ]
          }
          maskingData['operation'] = 'mask'
          $scope.tip.newMasking(maskingData);
        }

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

    function permanentRefineContent(content, ranges) {
      var maskedText = content.split('');

      ranges.forEach(function (range) {
        if (range.start >= 0 && range.start <= maskedText.length && range.end >= 0) {
          for (var i = range.start; i <= range.end; i++) {
            maskedText.splice(i, 0, String.fromCharCode(0x2588));
          }
        }
      });

      return maskedText.join('');
    }

    $scope.edited = function(id) {
      $scope.maskingObjects = $scope.tip.masking.filter(function(masking) {
        return masking.content_id === id;
      });

      if ($scope.maskingObjects.length !== 0 && $scope.maskingObjects[0].permanent_masking.length > 0) {
        return true
      } else {
        return false
      }
    }

    $scope.isMaskingEdited = function(id) {
      $scope.permanentMaskingObjects = $scope.tip.masking.filter(function(masking) {
        return masking.content_id === id;
      });
      if ($scope.permanentMaskingObjects.length !== 0 && $scope.permanentMaskingObjects[0].temporary_masking.length > 0) {
        return true
      } else {
        return false
      }
    }

    $scope.maskingContent = function(content, id) {
      $scope.permanentMaskingObjects = $scope.tip.masking.filter(function(masking) {
        return masking.content_id === id;
      });
      if ($scope.permanentMaskingObjects.length !== 0 && $scope.permanentMaskingObjects[0].permanent_masking.length > 0) {
        var permanentMaskingArray = Object.values($scope.permanentMaskingObjects[0].permanent_masking);
        permanentMaskingArray.sort(function(a, b) {
          return a.start - b.start;
        });
        var contentData = permanentRefineContent(content, permanentMaskingArray);
        return contentData
      } else {
        return content
      }
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

    $scope.fetchAudioFiles = function() {
      $scope.audiolist = {};

      for (let file of $scope.tip.wbfiles) {
        $scope.Utils.load("api/recipient/wbfiles/" + file.id).then(function(url) {
          $scope.audiolist[file["reference_id"]] = url;
        });
      }
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
    $scope.tip_mode = function(value) {
      $scope.mode = value;
    }
    $scope.editReport = function(content, id, type) {
      $uibModal.open({
        templateUrl: "views/modals/report_reduct.html",
        controller: "TipEditReportCtrl",
        resolve: {
          args: function() {
            return {
              tip: $scope.tip,
              operation: "editReport",
              contexts_by_id: $scope.contexts_by_id,
              reminder_date: $scope.Utils.getPostponeDate($scope.contexts_by_id[$scope.tip.context_id].tip_reminder),
              dateOptions: {
                minDate: new Date($scope.tip.creation_date)
              },
              opened: false,
              Utils: $scope.Utils,
              data: {
                content,
                id,
                type
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

  $scope.downloadRFile = function(f) {
    RTipDownloadRFile(f);
  };

  $scope.deleteRFile = function(f) {
    RTipRFileResource.remove({"id":f.id}).$promise.finally(reloadUI);
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
controller("TipEditReportCtrl", ["$scope", "$document", "masking", "$sce", "$uibModalInstance", "args", "Authentication", "$routeParams", "$http", function($scope, $document, masking, $sce, $uibModalInstance, args, Authentication, $routeParams, $http) {

  $scope.args = args;
  $scope.forced_visible = false
  $scope.maskingSwitch = $scope.resources.preferences.can_privilege_mask_information ? true : false;
  $scope.ranges_selected = []

  $scope.cancel = function() {
    $uibModalInstance.close();
    onClose()
  };

  $scope.toggleForcedView = function() {
    $scope.forced_visible = !$scope.forced_visible
    window.getSelection().removeAllRanges();
  }

  $scope.initializeMasking = function() {
    $scope.temporary_masking = []
    $scope.permanent_masking = []
    $scope.ranges_selected = []
    $scope.maskingObjects = $scope.args.tip.masking.filter(function(masking) {
      return masking.content_id === $scope.args.data.id;
    })[0];

    if ($scope.maskingSwitch) {
      var selectedHighlightChar = String.fromCharCode(0x2588)
      if($scope.maskingObjects){
        $scope.ranges_selected = $scope.temporary_masking = $scope.maskingObjects.temporary_masking
        $scope.permanent_masking = $scope.maskingObjects.permanent_masking
      }
    } else {
      var selectedHighlightChar = String.fromCharCode(0x2591)
      if($scope.maskingObjects){
        $scope.permanent_masking = $scope.maskingObjects.permanent_masking
        $scope.temporary_masking = $scope.maskingObjects.temporary_masking
      }
    }

    $scope.unmaskedContent = $scope.content = masking.injectPermanentMasking($scope.args.data.content, $scope.permanent_masking, String.fromCharCode(0x2588));
    $scope.originalContent = $scope.content = masking.maskContent($scope.content, $scope.temporary_masking, true, selectedHighlightChar);
  };

  $scope.selectContent = function() {
    response = masking.getSelectedRanges(true, $scope.ranges_selected)
    if (!$scope.maskingSwitch) {
      $scope.ranges_selected = masking.intersectRanges($scope.temporary_masking, response.new_ranges)
    }else{
      if(!$scope.resources.preferences.can_privilege_mask_information){
        $scope.ranges_selected = masking.intersectRanges($scope.temporary_masking, response.new_ranges)
      }else{
        $scope.ranges_selected = response.new_ranges
      }
    }

    $scope.content = masking.onHighlight($scope.content, $scope.ranges_selected)
  };

  $scope.unSelectContent = function() {
    response = masking.getSelectedRanges(false, $scope.ranges_selected)
    $scope.ranges_selected = response.new_ranges
    $scope.content = masking.onUnHighlight($scope.content, $scope.unmaskedContent, [response.selected_ranges])
    if (!$scope.maskingSwitch) {
      $scope.content = masking.onUnHighlight($scope.content, $scope.originalContent, [response.selected_ranges])
    }
  }

  function clickHandler(event) {
    var element = event.target.getAttribute('name');
    if(element != "controlElement"){
      let textarea = document.getElementById('redact');
      textarea.selectionEnd = textarea.selectionStart
    }
  }

  $scope.saveMasking = function() {
    let maskingData = {
      content_id: $scope.args.data.id,
      temporary_masking: []
    };

    if($scope.maskingSwitch){
      maskingData['temporary_masking'] = $scope.ranges_selected
      maskingData['operation'] = 'mask'
    }else{
      maskingData['operation'] = 'redact'
      maskingData['content_type'] = $scope.args.data.type
      maskingData['permanent_masking'] = $scope.ranges_selected
    }

    if($scope.maskingObjects){
      $scope.args.tip.updateMasking($scope.maskingObjects.id, maskingData);
      onClose()
    }else{
      $scope.args.tip.newMasking(maskingData);
      onClose()
    }
    $scope.cancel()
  }

  $scope.ignoreEdit = function(event) {
    if (event.keyCode >= 37 && event.keyCode <= 40) {
      return;
    }
    event.preventDefault();
  };

  $scope.toggleMasking = function() {
    $scope.initializeMasking()
  };

  function onClose(event) {
    $document.off('click', clickHandler);
  }


  $scope.initializeMasking()
  $document.on('click', clickHandler);

}]);
