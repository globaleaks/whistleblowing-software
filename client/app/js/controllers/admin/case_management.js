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
  }
]).controller('AdminSubmissionStateAddCtrl', ['$scope', '$http',
  function ($scope, $http) {
    $scope.addSubmissionState = function () {
      new_submission_state = {
        'label': $scope.new_submission_state.label
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
      new_submission_substate = {
        'label': $scope.new_substate.label
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