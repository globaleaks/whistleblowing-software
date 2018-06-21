GLClient.controller('AdminSubmissionSubStateCtrl', ['$scope', 'AdminSubmissionStateResource',
  function ($scope, AdminSubmissionStateResource) {
}]).controller('AdminSubmissionSubStateEditorCtrl', ['$scope', '$rootScope', '$http', 'Utils', 'AdminSubmissionSubStateResource',
  function ($scope, $rootScope, $http, Utils, AdminSubmissionSubStateResource) {
    $scope.editing = false;
    $scope.toggleEditing = function () {
      $scope.editing = !$scope.editing;
    }

    $scope.deleteSubSubmissionState = function() {
      Utils.deleteDialog($scope.substate).then(function() {
        //return Utils.deleteResource(AdminSubmissionSubStateResource, $scope.admin.submission_state.substates, $scope.substate);
        // Can't use delete resource because I can't pass multiple resources in
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
}]);
