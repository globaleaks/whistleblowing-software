
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

  var unique_keys = [];
  angular.forEach($scope.resources.rtips.rtips, function(tip) {
     tip.context = $scope.contexts_by_id[tip.context_id];
     tip.context_name = tip.context.name;
     tip.questionnaire = $scope.resources.rtips.questionnaires[tip.questionnaire];
     tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText(tip.status, tip.substatus, $scope.submission_statuses);

     if (unique_keys.includes(tip.submissionStatusStr) === false) {
       unique_keys.push(tip.submissionStatusStr);
       $scope.dropdownStatusData.push({id: $scope.dropdownStatusData.length + 1, label: tip.submissionStatusStr});
     }

     if (unique_keys.includes(tip.context_name) === false) {
       unique_keys.push(tip.context_name);
       $scope.dropdownContextData.push({id: $scope.dropdownContextData.length + 1, label: tip.context_name});
     }

     var scoreLabel = $scope.Utils.maskScore(tip.score);

     if (unique_keys.includes(scoreLabel) === false) {
       unique_keys.push(scoreLabel);
       $scope.dropdownScoreData.push({id: $scope.dropdownScoreData.length + 1, label: scoreLabel});
     }
  });

  $scope.filteredTips = $filter("orderBy")($scope.resources.rtips.rtips, "update_date");

  $scope.dropdownDefaultText = {
    buttonDefaultText: "",
    searchPlaceholder: $filter("translate")("Search")
  };

  function applyFilter()
  {
     $scope.filteredTips = $scope.Utils.getStaticFilter($scope.resources.rtips.rtips, $scope.dropdownStatusModel, "submissionStatusStr");
     $scope.filteredTips = $scope.Utils.getStaticFilter($scope.filteredTips, $scope.dropdownContextModel, "context_name");
     $scope.filteredTips = $scope.Utils.getStaticFilter($scope.filteredTips, $scope.dropdownScoreModel, "score");
     $scope.filteredTips = $scope.Utils.getDateFilter($scope.filteredTips, $scope.reportDateFilter, $scope.updateDateFilter, $scope.expiryDateFilter);
  }

  $scope.on_changed = {
    onSelectionChanged: function() {
      applyFilter();
    }
  };

  $scope.onReportFilterChange = function(reportFilter) {
    $scope.reportDateFilter = reportFilter;
    applyFilter();
  };

  $scope.onUpdateFilterChange = function(updateFilter) {
    $scope.updateDateFilter = updateFilter;
    applyFilter();
  };

  $scope.onExpiryFilterChange = function(expiryFilter) {
    $scope.expiryDateFilter = expiryFilter;
    applyFilter();
  };

  $scope.checkFilter = function(filter) {
    return filter.length > 0;
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

  $scope.markReportStatus = function (date) {
    var report_date = new Date(date);
    var current_date = new Date();
    return current_date > report_date;
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
}])
.controller("TipBulkOperationsCtrl", ["$scope", "$http", "$location", "$uibModalInstance", "selected_tips", "operation",
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
