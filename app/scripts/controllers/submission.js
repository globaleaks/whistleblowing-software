GLClient.controller('SubmissionCtrl', ['$scope', 'localization', 'Node',
    'Submission', function($scope, 
      localization, Node, Submission) {

  $scope.submission_complete = false;
  $scope.localization = localization;

  // XXX here we are actually violating the principle for which the
  // controller should not be stateful. This can possibly be fixed by
  // refactoring how the API works, or by making the logic for creation of
  // the submission into a service.
  // We use the scope variable uploaded_files to keep track of the files
  // that are uploaded.
  $scope.uploaded_files = [];

  $scope.create_submission = function(){
    $scope.submission = new Submission({
      // XXX This is required because localization is lazily loaded and it is
      // performing a network operation
      context_gus: localization.current_context_gus
    });
    $scope.submission.$save();
  }

  $scope.submit = function() {
    angular.forEach(localization.current_context.fields, function(field, k) {
      $scope.submission.fields[field.name] = field.value;
    });
    $scope.submission.$save();
    $scope.submission_complete = true;
  }

  // Here goes step by step wizard related funcions
  $scope.steps = {};
  $scope.steps.all = ['1', '2', '3'];
  $scope.steps.current = $scope.steps.all[0];
  $scope.steps.idx = 0;

  $scope.disable = {};
  $scope.disable.next = false;
  $scope.disable.back = true;

  $scope.next = function() {
    if ($scope.steps.idx < ($scope.steps.all.length - 1)) {
      var idx = $scope.steps.idx += 1;
      $scope.steps.current = $scope.steps.all[idx];
      $scope.disable.next = false;
      $scope.disable.back = false;
    }
    // We are at the last step
    if ($scope.steps.idx == ($scope.steps.all.length - 1)) {
      $scope.disable.next = true;
    }
  }

  $scope.back = function() {
    if ($scope.steps.idx > 0) {
      var idx = $scope.steps.idx -= 1;
      $scope.steps.current = $scope.steps.all[idx];
      $scope.disable.back = false;
      $scope.disable.next = false;
    }
    if ($scope.steps.idx == 0) {
      $scope.disable.back = true;
    }
  }
  // End

  $scope.create_submission();

}]);
