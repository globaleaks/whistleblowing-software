GLClient.controller('AdminCaseManagementCtrl', ['$scope', function($scope){
  $scope.tabs = [
    {
      title:"Submission states",
      template:"views/admin/case_management/tab1.html"
    }
  ];
}]).controller('AdminSubmissionStateCtrl', ['$scope', 'AdminSubmissionStateResource',
  function ($scope, AdminSubmissionStateResource) {
    $scope.showAddState = false;
    $scope.toggleAddState = function () {
      $scope.showAddState = !$scope.showAddState;
    };
  }
]).controller('AdminSubmissionStateEditorCtrl', ['$scope', '$http', 'Utils', 'AdminSubmissionStateResource',
  function ($scope, $http, Utils, AdminSubmissionStateResource) {
    $scope.editing = false;
    $scope.toggleEditing = function () {
      $scope.editing = !$scope.editing;
    };

    $scope.showAddSubstate = false;
    $scope.toggleAddSubstate = function () {
      $scope.showAddSubstate = !$scope.showAddSubstate;
    };

    $scope.deleteSubmissionState = function() {
      Utils.deleteDialog($scope.context).then(function() {
        return Utils.deleteResource(AdminSubmissionStateResource, $scope.admin.submission_states, $scope.submission_state);
      });
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

      if (target < 0 || target >= $scope.admin.submission_states.length) {
        return;
      }
  
      $scope.admin.submission_states[index] = $scope.admin.submission_states[target];
      $scope.admin.submission_states[target] = $scope.submission_state;

      // Return only the ids we want to reorder
      reordered_ids = {
        'ids': $scope.admin.submission_states.map(function(c) {
          if (c.system_defined === false) return c.id;
          }
        ).filter(function (c) {
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
      new_submission_state = {
        'label': $scope.new_submission_state.label,
        'presentation_order': presentation_order
      }

      $http.post(
        '/admin/submission_states',
        new_submission_state
      ).then(function (response) {
        $scope.reload();
      })
    }
}]).controller('AdminSubmissionSubStateCtrl', ['$scope', 'AdminSubmissionStateResource',
  function ($scope, AdminSubmissionStateResource) {
}]).controller('AdminSubmissionSubStateEditorCtrl', ['$scope', '$http', 'Utils', 'AdminSubmissionSubStateResource',
  function ($scope, $http, Utils, AdminSubmissionSubStateResource) {
    $scope.editing = false;
    $scope.toggleEditing = function () {
      $scope.editing = !$scope.editing;
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
  }
]).controller('AdminSubmissionSubStateAddCtrl', ['$scope', '$http',
  function ($scope, $http) {
    $scope.addSubmissionSubState = function () {
      var presentation_order = $scope.newItemOrder($scope.admin.submission_states, 'presentation_order');

      new_submission_substate = {
        'label': $scope.new_substate.label,
        'presentation_order': $scope.presentation_order
      }

      $http.post(
        '/admin/submission_states/' + $scope.submission_state.id + '/substates',
        new_submission_substate
      ).then(function (response) {
        $scope.reload();
      })
    }
}]).controller('AdminSubmissionClosingStateCtrl', ['$scope', '$http',
  function ($scope, $http) {

    $scope.closedState = undefined;

    // Find the closed state from the states list so we can directly manipulate it
    for (var i = 0; i < $scope.admin.submission_states.length; i++) {
      var state = $scope.admin.submission_states[i];
      if (state.system_defined === true && state.system_usage === 'closed') {
        $scope.closedState = state;
        break;
      }
    }

    $scope.editing = false;
    $scope.showAddState = false;

    $scope.toggleEditing = function () {
      $scope.editing = !$scope.editing;
    };

    $scope.toggleAddState = function () {
      $scope.showAddState = !$scope.showAddState;
    };
  }
]).controller('AdminSubmissionClosedSubStateAddCtrl', ['$scope', '$http',
  function ($scope, $http) {

    // It would be nice to refactor this with addSubmissionSubState
  $scope.addClosingSubmissionSubState = function () {
    new_submission_substate = {
      'label': $scope.new_closed_submission_substate.label
    }

    $http.post(
      '/admin/submission_states/' + $scope.closedState.id + '/substates',
      new_submission_substate
    ).then(function (response) {
      $scope.reload();
    })
  }

  }
])