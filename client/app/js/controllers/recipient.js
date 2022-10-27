
GL.controller("ReceiverTipsCtrl", ["$scope",  "$filter", "$http", "$location", "$uibModal", "$window", "RTipExport", "TokenResource",
  function($scope, $filter, $http, $location, $uibModal, $window, RTipExport, TokenResource) {

  $scope.search = undefined;
  $scope.currentPage = 1;
  $scope.itemsPerPage = 20;
  $scope.dropdownSettings = {dynamicTitle: false, showCheckAll: false, showUncheckAll: false, enableSearch: true, displayProp: "label", idProp: "label", itemsShowLimit: 5};

  $scope.reportDateFilter = null;
  $scope.updateDateFilter = null;
  $scope.expiryDateFilter = null;

  $scope.dropdownStatusModel = [];
  $scope.dropdownStatusData = [];
  $scope.dropdownContextModel = [];
  $scope.dropdownContextData = [];
  $scope.dropdownScoreModel = [];
  $scope.dropdownScoreData = [];

  var unique_keys = new Set([]);
  angular.forEach($scope.resources.rtips.rtips, function(tip) {
     tip.context = $scope.contexts_by_id[tip.context_id];
     tip.context_name = tip.context.name;
     tip.questionnaire = $scope.resources.rtips.questionnaires[tip.questionnaire];
     tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText(tip.status, tip.substatus, $scope.submission_statuses);

     if (unique_keys.has(tip.submissionStatusStr) === false){
         unique_keys.add(tip.submissionStatusStr);
         $scope.dropdownStatusData.push({id: $scope.dropdownStatusData.length+1, label: tip.submissionStatusStr});
     }
     if (unique_keys.has(tip.context_name) === false){
         unique_keys.add(tip.context_name);
         $scope.dropdownContextData.push({id: $scope.dropdownContextData.length+1, label: tip.context_name});
     }

     var scoreLabel = $scope.Utils.maskScore(tip.score);
     if (unique_keys.has(scoreLabel) === false){
         unique_keys.add(scoreLabel);
         $scope.dropdownScoreData.push({id: $scope.dropdownScoreData.length+1, label: scoreLabel});
     }
  });

  $scope.filteredTips = $filter("orderBy")($scope.resources.rtips.rtips, "update_date");

  function onApplyFIlter()
  {
     $scope.filteredTips = $scope.Utils.getStaticFilter($scope.resources.rtips.rtips, $scope.dropdownStatusModel, "submissionStatusStr");
     $scope.filteredTips = $scope.Utils.getStaticFilter($scope.filteredTips, $scope.dropdownContextModel, "context_name");
     $scope.filteredTips = $scope.Utils.getStaticFilter($scope.filteredTips, $scope.dropdownScoreModel, "score");
     $scope.filteredTips = $scope.Utils.getDateFilter($scope.filteredTips, $scope.reportDateFilter, $scope.updateDateFilter, $scope.expiryDateFilter);
  }
  function onDateFilterChanged(scope, newvalue)
  {
      if (!$scope.dateRange.start) {
        $scope.dateRange.start = newvalue;
        $scope.options.minDate = newvalue;
      } else if ($scope.dateRange.start && !$scope.dateRange.end) {
        $scope.dateRange.end = scope;
        $scope.options.minDate = null;
        $scope.reportDateFilter = [new Date($scope.dateRange.start).getTime(), new Date($scope.dateRange.end).getTime()];
        onApplyFIlter();
      } else if ($scope.dateRange.start && $scope.dateRange.end) {
        $scope.dateRange.start = newvalue;
        $scope.dateRange.end = newvalue;
        $scope.options.minDate = newvalue;
      }
  }

  $scope.$watch("dateRange.reportDate", function(newvalue) {
    if (newvalue) {
        onDateFilterChanged($scope.dateRange.reportDate, newvalue)
    }else{
        $scope.reportDateFilter = [new Date().getTime(), new Date().getTime()];
        onApplyFIlter();
    }
  });
  $scope.$watch("dateRange.updateDate", function(newvalue) {
    if (newvalue) {
        onDateFilterChanged($scope.dateRange.updateDate, newvalue)
    }else{
        $scope.reportDateFilter = [new Date().getTime(), new Date().getTime()];
        onApplyFIlter();
    }
  });
  $scope.$watch("dateRange.expiryDate", function(newvalue) {
    if (newvalue) {
        onDateFilterChanged($scope.dateRange.expiryDate, newvalue)
    }else{
        $scope.reportDateFilter = [new Date().getTime(), new Date().getTime()];
        onApplyFIlter();
    }
  });

  $scope.dateFilterClear = function (scope) {
    scope = null;
  };

  $scope.dropdownDefaultText = {
       buttonDefaultText:"",
       searchPlaceholder:" ..."
  };

  $scope.datePicker = {
      reportDateStatus: { opened: false },
      updateDateStatus: { opened: false },
      expiryDateStatus: { opened: false },

      reportDateOpen: function () {
          $scope.datePicker.reportDateStatus.opened = true;
      },
      updateDateOpen: function () {
          $scope.datePicker.updateDateStatus.opened = true;
      },
      expiryDateOpen: function () {
          $scope.datePicker.expiryDateStatus.opened = true;
      }
  };

  $scope.on_changed = {
    onSelectionChanged: function() {
        onApplyFIlter();
    }
  };

  $scope.$watch("search", function (value) {
    if (typeof value !== "undefined") {
      $scope.currentPage = 1;
      $scope.filteredTips = $filter("orderBy")($filter("filter")($scope.resources.rtips.rtips, value), "update_date");
    }
  });

  $scope.open_grant_access_modal = function () {
    return $scope.Utils.runUserOperation("get_user_names").then(function(response) {
      $uibModal.open({
      templateUrl: "views/modals/grant_access.html",
        controller: "ConfirmableModalCtrl",
        resolve: {
          arg: {
            users_names: response.data
          },
          confirmFun: function() {
            return function(receiver_id) {
              var args = {
                rtips: $scope.selected_tips,
                receiver: receiver_id
              };

              return $scope.Utils.runRecipientOperation("grant", args, true);
            };
          },
          cancelFun: null
        }
      });
    });
  };

  $scope.open_revoke_access_modal = function () {
    return $scope.Utils.runUserOperation("get_user_names").then(function(response) {
      $uibModal.open({
      templateUrl: "views/modals/revoke_access.html",
        controller: "ConfirmableModalCtrl",
        resolve: {
          arg: {
            users_names: response.data
          },
          confirmFun: function() {
            return function(receiver_id) {
              var args = {
                rtips: $scope.selected_tips,
                receiver: receiver_id
              };

              return $scope.Utils.runRecipientOperation("revoke", args, true);
            };
          },
          cancelFun: null
        }
      });
    });
  };

  $scope.exportTip = RTipExport;

  $scope.selected_tips = [];

  $scope.select_all = function () {
    $scope.selected_tips = [];
    angular.forEach($scope.filteredTips, function (tip) {
      $scope.selected_tips.push(tip.id);
    });
  };

  $scope.toggle_star = function(tip) {
    return $http({
      method: "PUT",
      url: "api/rtips/" + tip.id,
      data: {
        "operation": "set",
        "args": {
          "key": "important",
          "value": !tip.important
        }
      }
    }).then(function() {
      tip.important = !tip.important;
    });
  };

  $scope.deselect_all = function () {
    $scope.selected_tips = [];
  };

  $scope.tip_switch = function (id) {
    var index = $scope.selected_tips.indexOf(id);
    if (index > -1) {
      $scope.selected_tips.splice(index, 1);
    } else {
      $scope.selected_tips.push(id);
    }
  };

  $scope.isSelected = function (id) {
    return $scope.selected_tips.indexOf(id) !== -1;
  };

  $scope.tip_delete_selected = function () {
    $uibModal.open({
      templateUrl: "views/modals/delete_confirmation.html",
      controller: "TipBulkOperationsCtrl",
      resolve: {
        selected_tips: function () {
          return $scope.selected_tips;
        },
        operation: function() {
          return "delete";
        }
      }
    });
  };

  $scope.tips_export = function () {
    for(var i=0; i<$scope.selected_tips.length; i++) {
      (function(i) {
        new TokenResource().$get().then(function(token) {
          return $window.open("api/rtips/" + $scope.selected_tips[i] + "/export?token=" + token.id + ":" + token.answer);
        });
      })(i);
    }
  };
}]).
controller("TipBulkOperationsCtrl", ["$scope", "$http", "$location", "$uibModalInstance", "selected_tips", "operation",
  function ($scope, $http, $location, $uibModalInstance, selected_tips, operation) {
  $scope.selected_tips = selected_tips;
  $scope.operation = operation;

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

  $scope.confirm = function () {
    $uibModalInstance.close();

    if (["delete"].indexOf(operation) === -1) {
      return;
    }

    return $scope.Utils.runRecipientOperation($scope.operation, {"rtips": $scope.selected_tips}, true);
  };
}]);
