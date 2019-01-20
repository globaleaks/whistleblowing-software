GLClient.controller("AdminCaseManagementCtrl", ["$scope", function($scope){
  $scope.tabs = [
    {
      title:"Submission statuses",
      template:"views/admin/case_management/tab1.html"
    }
  ];
}]).controller("AdminSubmissionStatusCtrl", ["$scope",
  function ($scope) {
    $scope.showAddStatus = false;
    $scope.toggleAddStatus = function () {
      $scope.showAddStatus = !$scope.showAddStatus;
    };

    $scope.editableStatusesList = function() {
      var displayedStatuses = [];
      for (var i = 0; i < $scope.admin.submission_statuses.length; i++) {
        var status = $scope.admin.submission_statuses[i];
        if (status.system_defined === false) {
          displayedStatuses.push(status);
        }
      }

      return displayedStatuses;
    };
  }
]).controller("AdminSubmissionStatusEditorCtrl", ["$scope", "$http", "AdminSubmissionStatusResource",
  function ($scope, $http, AdminSubmissionStatusResource) {
    $scope.editing = false;
    $scope.toggleEditing = function () {
      $scope.editing = !$scope.editing;
    };

    $scope.showAddSubstatus = false;
    $scope.toggleAddSubstatus = function () {
      $scope.showAddSubstatus = !$scope.showAddSubstatus;
    };

    $scope.deleteSubmissionStatus = function() {
      $scope.Utils.deleteDialog($scope.submissions_status).then(function() {
        return $scope.Utils.deleteResource(AdminSubmissionStatusResource, $scope.admin.submission_statuses, $scope.submissions_status);
      });
    };

    function ss_idx(ss_id) {
      for (var i = 0; i < $scope.admin.submission_statuses.length; i++) {
        var status = $scope.admin.submission_statuses[i];
        if (status.id === ss_id) {
          return i;
        }
      }
    }

    $scope.save_submissions_status = function (context, cb) {
      var updated_submissions_status = new AdminSubmissionStatusResource(context);
      return $scope.Utils.update(updated_submissions_status, cb);
    };

    function swap($event, index, n) {
      $event.stopPropagation();

      var target = index + n;
      var statuses_list = $scope.editableStatusesList();

      if (target < 0 || target >= statuses_list.length) {
        return;
      }

      // Because the base data structure and the one we display don't match ...
      var orig_index = ss_idx(statuses_list[index].id);
      var orig_target = ss_idx(statuses_list[target].id);

      var moving_status = $scope.admin.submission_statuses[orig_index];
      $scope.admin.submission_statuses[orig_index] = $scope.admin.submission_statuses[orig_target];
      $scope.admin.submission_statuses[orig_target] = moving_status;

      // Return only the ids we want to reorder
      var reordered_ids = {
        "ids": $scope.admin.submission_statuses.map(function(c) {
          if (c.system_defined === false) {
            return c.id;
          }
        }).filter(function (c) {
          if (c !== null) {
            return c;
          }
        })
      };

      $http({
        method: "PUT",
        url: "/admin/submission_statuses",
        data: {
          "operation": "order_elements",
          "args": reordered_ids,
        },
      });
    }

    $scope.moveUp = function(e, idx) { swap(e, idx, -1); };
    $scope.moveDown = function(e, idx) { swap(e, idx, 1); };
  }
]).controller("AdminSubmissionStatusAddCtrl", ["$scope", "$http",
  function ($scope, $http) {
    var presentation_order = $scope.newItemOrder($scope.admin.submission_statuses, "presentation_order");

    $scope.addSubmissionStatus = function () {
      var new_submissions_status = {
        "label": $scope.new_submissions_status.label,
        "presentation_order": presentation_order
      };

      $http.post(
        "/admin/submission_statuses",
        new_submissions_status
      ).then(function (result) {
        $scope.admin.submission_statuses.push(result.data);
      });
    };
}]).controller("AdminSubmissionSubStatusCtrl", [
  function () {
}]).controller("AdminSubmissionSubStatusEditorCtrl", ["$scope", "$http", "AdminSubmissionSubStatusResource",
  function ($scope, $http, AdminSubmissionSubStatusResource) {
    $scope.substatus_editing = false;
    $scope.toggleSubstatusEditing = function () {
      $scope.substatus_editing = !$scope.substatus_editing;
    };

    $scope.deleteSubSubmissionStatus = function() {
      $scope.Utils.deleteDialog($scope.substatus).then(function() {
        AdminSubmissionSubStatusResource.delete({
          id: $scope.substatus.id,
          submissionstatus_id: $scope.substatus.submissionstatus_id
        }, function() {
          var index = $scope.submissions_status.substatuses.indexOf($scope.substatus);
          $scope.submissions_status.substatuses.splice(index, 1);
        });
      });
    };

    $scope.save_submissions_substatuses = function (substatus, cb) {
      var updated_submissions_substatuses = new AdminSubmissionSubStatusResource(substatus);
      return $scope.Utils.update(updated_submissions_substatuses, cb);
    };

    $scope.moveSsUp = function(e, idx) { swapSs(e, idx, -1); };
    $scope.moveSsDown = function(e, idx) { swapSs(e, idx, 1); };

    function swapSs($event, index, n) {
      $event.stopPropagation();

      var target = index + n;

      if (target < 0 || target >= $scope.submissions_status.substatuses.length) {
        return;
      }

      $scope.submissions_status.substatuses[index] = $scope.submissions_status.substatuses[target];
      $scope.submissions_status.substatuses[target] = $scope.substatus;

      $http({
        method: "PUT",
        url: "/admin/submission_statuses/" + $scope.submissions_status.id + "/substatuses",
        data: {
          "operation": "order_elements",
          "args":  {"ids" : $scope.submissions_status.substatuses.map(function(c) { return c.id; })}
        },
      });
    }
  }
]).controller("AdminSubmissionSubStatusAddCtrl", ["$scope", "$http",
  function ($scope, $http) {
    $scope.presentation_order = $scope.newItemOrder($scope.submissions_status.substatuses, "presentation_order");

    $scope.addSubmissionSubStatus = function () {
      var new_submissions_substatuses = {
        "label": $scope.new_substatus.label,
        "presentation_order": $scope.presentation_order
      };

      $http.post(
        "/admin/submission_statuses/" + $scope.submissions_status.id + "/substatuses",
        new_submissions_substatuses
      ).then(function (result) {
        $scope.submissions_status.substatuses.push(result.data);
      });
    };
  }
]).controller("AdminSubmissionClosingStatusCtrl", ["$scope",
  function ($scope) {
    $scope.submissions_status = undefined;

    $scope.showAddStatus = false;

    $scope.toggleAddStatus = function () {
      $scope.showAddStatus = !$scope.showAddStatus;
    };

    // Find the closed status from the statuses list so we can directly manipulate it
    for (var i = 0; i < $scope.admin.submission_statuses.length; i++) {
      var status = $scope.admin.submission_statuses[i];
      if (status.system_defined === true && status.system_usage === "closed") {
        $scope.submissions_status = status;
        return;
      }
    }
  }
]).controller("AdminSubmissionClosedSubStatusAddCtrl", ["$scope", "$http",
  function ($scope, $http) {
    $scope.closed_ss_presentation_order = $scope.newItemOrder($scope.submissions_status.substatuses, "presentation_order");

    // It would be nice to refactor this with addSubmissionSubStatus
    $scope.addClosingSubmissionSubStatus = function () {
      var new_submissions_substatuses = {
        "label": $scope.new_closed_submissions_substatuses.label,
        "presentation_order": $scope.closed_ss_presentation_order
      };

      $http.post(
        "/admin/submission_statuses/" + $scope.submissions_status.id + "/substatuses",
        new_submissions_substatuses
      ).then(function (result) {
        $scope.submissions_status.substatuses.push(result.data);
      });
    };
  }
]);
