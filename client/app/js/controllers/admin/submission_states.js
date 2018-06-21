GLClient.controller('AdminSubmissionStateCtrl', ['$scope', 'AdminSubmissionStateResource',
  function ($scope, AdminSubmissionStateResource) {
    $scope.showAddState = false;
    $scope.toggleAddState = function () {
      $scope.showAddState = !$scope.showAddState;
    };
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
}]);
