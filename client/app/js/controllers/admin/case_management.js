GLClient.controller('AdminCaseManagementCtrl', ['$scope', function($scope){
  $scope.tabs = [
    {
      title:"Submission states",
      template:"views/admin/case_management/tab1.html"
    }
  ];
}]).controller('AdminSubmissionStateCtrl', ['$scope',
  function ($scope) {
    $scope.showAddState = false;
    $scope.toggleAddState = function () {
      $scope.showAddState = !$scope.showAddState;
    };

    $scope.editableStatesList = function() {
      var displayedStates = []
      for (var i = 0; i < $scope.admin.submission_states.length; i++) {
        var state = $scope.admin.submission_states[i];
        if (state.system_defined === false) {
          displayedStates.push(state);
        }
      }

      return displayedStates;
    }
  }
]).controller('AdminSubmissionStateEditorCtrl', ['$scope', '$rootScope', '$http', 'Utils', 'AdminSubmissionStateResource',
  function ($scope, $rootScope, $http, Utils, AdminSubmissionStateResource) {
    $scope.editing = false;
    $scope.toggleEditing = function () {
      $scope.editing = !$scope.editing;
    };

    $scope.showAddSubstate = false;
    $scope.toggleAddSubstate = function () {
      $scope.showAddSubstate = !$scope.showAddSubstate;
    };

    $scope.deleteSubmissionState = function() {
      Utils.deleteDialog($scope.submission_state).then(function() {
        return Utils.deleteResource(AdminSubmissionStateResource, $scope.admin.submission_states, $scope.submission_state);
      });
    }

    function ss_idx(ss_id) {
      for (var i = 0; i < $scope.admin.submission_states.length; i++) {
        var state = $scope.admin.submission_states[i];
        if (state.id === ss_id) {
          return i;
        }
      }
    }

    $scope.save_submission_state = function (context, cb) {
      var updated_submission_state = new AdminSubmissionStateResource(context);
      return Utils.update(updated_submission_state, cb);
    }

    $scope.moveUp = function(e, idx) { swap(e, idx, -1); };
    $scope.moveDown = function(e, idx) { swap(e, idx, 1); };

    function swap($event, index, n) {
      $event.stopPropagation();

      var target = index + n;
      var states_list = $scope.editableStatesList();

      if (target < 0 || target >= states_list.length) {
        return;
      }

      // Because the base data structure and the one we display don't match ...
      var orig_index = ss_idx(states_list[index].id);
      var orig_target = ss_idx(states_list[target].id)

      var moving_state = $scope.admin.submission_states[orig_index]
      $scope.admin.submission_states[orig_index] = $scope.admin.submission_states[orig_target];
      $scope.admin.submission_states[orig_target] = moving_state;

      // Return only the ids we want to reorder
      var reordered_ids = {
        'ids': $scope.admin.submission_states.map(function(c) {
          if (c.system_defined === false) return c.id;
        }).filter(function (c) {
          if (c !== null) {
            return c
          }
        })
      }

      $http({
        method: 'PUT',
        url: '/admin/submission_states',
        data: {
          'operation': 'order_elements',
          'args': reordered_ids,
        },
      }).then(function() {
        $rootScope.successes.push({});
      });
    }
  }
]).controller('AdminSubmissionStateAddCtrl', ['$scope', '$http',
  function ($scope, $http) {
    var presentation_order = $scope.newItemOrder($scope.admin.submission_states, 'presentation_order');

    $scope.addSubmissionState = function () {
      var new_submission_state = {
        'label': $scope.new_submission_state.label,
        'presentation_order': presentation_order
      }

      $http.post(
        '/admin/submission_states',
        new_submission_state
      ).then(function () {
        $scope.reload();
      })
    }
}]).controller('AdminSubmissionSubStateCtrl', [
  function () {
}]).controller('AdminSubmissionSubStateEditorCtrl', ['$scope', '$rootScope', '$http', 'Utils', 'AdminSubmissionSubStateResource',
  function ($scope, $rootScope, $http, Utils, AdminSubmissionSubStateResource) {
    $scope.substate_editing = false;
    $scope.toggleSubstateEditing = function () {
      $scope.substate_editing = !$scope.substate_editing;
    }

    $scope.deleteSubSubmissionState = function() {
      Utils.deleteDialog($scope.substate).then(function() {
        AdminSubmissionSubStateResource.delete({
          id: $scope.substate.id,
          submissionstate_id: $scope.substate.submissionstate_id
        }, function() {
          var list = $scope.submission_state.substates
          list.splice(list.indexOf($scope.substate), 1);
        });
      });
    }

    $scope.save_submission_substate = function (substate, cb) {
      var updated_submission_substate = new AdminSubmissionSubStateResource(substate);
      return Utils.update(updated_submission_substate, cb);
    };

    $scope.moveSsUp = function(e, idx) { swapSs(e, idx, -1); };
    $scope.moveSsDown = function(e, idx) { swapSs(e, idx, 1); };

    function swapSs($event, index, n) {
      $event.stopPropagation();

      var target = index + n;

      if (target < 0 || target >= $scope.submission_state.substates.length) {
        return;
      }

      $scope.submission_state.substates[index] = $scope.submission_state.substates[target];
      $scope.submission_state.substates[target] = $scope.substate;

      $http({
        method: 'PUT',
        url: '/admin/submission_states/' + $scope.submission_state.id + '/substates',
        data: {
          'operation': 'order_elements',
          'args':  {'ids' : $scope.submission_state.substates.map(function(c) { return c.id })}
        },
      }).then(function() {
        $rootScope.successes.push({});
      });
    }
  }
]).controller('AdminSubmissionSubStateAddCtrl', ['$scope', '$http',
  function ($scope, $http) {
    $scope.presentation_order = $scope.newItemOrder($scope.submission_state.substates, 'presentation_order');

    $scope.addSubmissionSubState = function () {
      var new_submission_substate = {
        'label': $scope.new_substate.label,
        'presentation_order': $scope.presentation_order
      }

      $http.post(
        '/admin/submission_states/' + $scope.submission_state.id + '/substates',
        new_submission_substate
      ).then(function () {
        $scope.reload();
      })
    }
  }
]).controller('AdminSubmissionClosingStateCtrl', ['$scope',
  function ($scope) {

    $scope.closedState = undefined;

    // Find the closed state from the states list so we can directly manipulate it
    for (var i = 0; i < $scope.admin.submission_states.length; i++) {
      var state = $scope.admin.submission_states[i];
      if (state.system_defined === true && state.system_usage === 'closed') {
        $scope.closedState = state;
        break;
      }
    }

    // When we're under this controller, submission state changes
    $scope.submission_state = $scope.closedState;

    $scope.showAddState = false;

    $scope.toggleAddState = function () {
      $scope.showAddState = !$scope.showAddState;
    };
  }
]).controller('AdminSubmissionClosedSubStateAddCtrl', ['$scope', '$http',
  function ($scope, $http) {
    $scope.closed_ss_presentation_order = $scope.newItemOrder($scope.closedState.substates, 'presentation_order');

    // It would be nice to refactor this with addSubmissionSubState
    $scope.addClosingSubmissionSubState = function () {
      var new_submission_substate = {
        'label': $scope.new_closed_submission_substate.label,
        'presentation_order': $scope.closed_ss_presentation_order
      }

      $http.post(
        '/admin/submission_states/' + $scope.closedState.id + '/substates',
        new_submission_substate
      ).then(function () {
        $scope.reload();
      })
    }
  }
])