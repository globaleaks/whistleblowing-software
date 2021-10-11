GL.controller("ReceiverTipsCtrl", ["$scope",  "$filter", "$q", "$http", "$location", "$uibModal", "$window", "RTipExport", "ReceiverTips", "TokenResource",
  function($scope, $filter, $q, $http, $location, $uibModal, $window, RTipExport, ReceiverTips, TokenResource) {
  $scope.search = undefined;
  $scope.currentPage = 1;
  $scope.itemsPerPage = 20;

  $scope.tips = ReceiverTips.query(function(tips) {
    angular.forEach(tips, function(tip) {
      tip.context = $scope.contexts_by_id[tip.context_id];
      tip.context_name = tip.context.name;
      tip.submissionStatusStr = $scope.Utils.getSubmissionStatusText(tip.status, tip.substatus, $scope.submission_statuses);
    });
  });

  $scope.filteredTips = $scope.tips;

  $scope.$watch("search", function (value) {
    if (typeof value !== "undefined") {
      $scope.currentPage = 1;
      $scope.filteredTips = $filter("filter")($scope.tips, value);
    }
  });

  $scope.open_grant_access_modal = function () {
    $uibModal.open({
    templateUrl: "views/modals/grant_access.html",
      controller: "ConfirmableModalCtrl",
      resolve: {
        arg: {},
        confirmFun: function() {
          return function(receiver_id) {
            var req = {
              operation: "grant",
              args: {
                rtips: $scope.selected_tips,
                receiver: receiver_id
              }
            };
           return $http({method: "PUT", url: "api/recipient/operations", data: req}).then(function () {
              $scope.reload();
            });
          };
        },
        cancelFun: null
      }
    });
  };

  $scope.open_revoke_access_modal = function () {
    $uibModal.open({
    templateUrl: "views/modals/revoke_access.html",
      controller: "ConfirmableModalCtrl",
      resolve: {
        arg: {},
        confirmFun: function() {
          return function(receiver_id) {
            var req = {
              operation: "revoke",
              args: {
                rtips: $scope.selected_tips,
                receiver: receiver_id
              }
            };
           return $http({method: "PUT", url: "api/recipient/operations", data: req}).then(function () {
              $scope.reload();
            });
          };
        },
        cancelFun: null
      }
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
    tip.important = !tip.important;

    return $http({method: "PUT",
                  url: "api/rtips/" + tip.id,
                  data: {"operation": "update_important",
                         "args": {"value": tip.important}}});
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
          return $window.open("api/rtips/" + $scope.selected_tips[i] + "/export?token=" + token.id);
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

    return $http({method: "PUT", url: "api/recipient/operations", data:{
      operation: $scope.operation,
      args: {
        rtips: $scope.selected_tips
      }
    }}).then(function(){
      $scope.selected_tips = [];
      $scope.reload();
    });
  };
}]);
