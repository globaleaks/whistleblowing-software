GLClient.controller('SubmissionCtrl', ['$scope', '$http', 
    'Node', 'Submission', 
  function($scope, $http, Node, Submission) {
  $scope.loading = true;

  $scope.node_info = Node.info(function(){
    $scope.loading = false;
    // XXX here we are actually violating the principle for which the
    // controller should not be stateful. This can possibly be fixed by
    // refactoring how the API works, or by making the logic for creation of
    // the submission into a service.

    // We use the scope variable uploaded_files to keep track of the files
    // that are uploaded.
    $scope.uploaded_files = [];
    $scope.current_context = $scope.node_info.contexts[0];

    $scope.fields = $scope.current_context.fields;

    $scope.create_submission = function(){
      $scope.submission = Submission.create({
        id_or_gus: $scope.current_context.context_gus,
        action: 'new'
      });
    }

    $scope.submit = function() {
      // XXX this is still hackish and somewhat broken.
      var submission = new Submission();

      submission.fields = {};

      angular.forEach($scope.fields, function(field, k) {
        submission.fields[field.name] = field.value;
      });
      submission.$update({
        id_or_gus: $scope.submission.submission_gus,
        action: 'update'
      }, function(){
        submission.$finalize({
          id_or_gus: $scope.submission.submission_gus,
          action: 'finalize'
        }, function(data){
          console.log(data);
          $scope.receipt_id;
        });
      });
    }

    // Here goes step by step wizard related funcions
    $scope.steps = {};
    $scope.steps.all = ['1', '2', '3'];
    $scope.steps.current = $scope.steps.all[0];
    $scope.steps.idx = 0;

    $scope.disable = {};
    $scope.disable.next = false;
    $scope.disable.back = true;
    $scope.disable.submit = true;

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
        $scope.disable.submit = false;
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

    $scope.disable.submit_button = function() {
      if (!$scope.disable.submit && $scope.fields.disclaimer) {
        return false;
      } else {
        return true;
      }
    }
    // End

    $scope.create_submission();

  });
}]);
