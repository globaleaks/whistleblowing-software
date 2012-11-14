GLClient.controller('SubmissionCtrl', ['$scope', '$http', 
    'Node', 'Submission', 
  function($scope, $http, Node, Submission) {
  $scope.node_info = Node.info(function(){
    // XXX here we are actually violating the principle for which the
    // controller should not be stateful. This can possibly be fixed by
    // refactoring how the API works, or by making the logic for creation of
    // the submission into a service.

    // We use the scope variable uploaded_files to keep track of the files
    // that are uploaded.
    $scope.uploaded_files = [];
    $scope.current_context = $scope.node_info.contexts[0];

    $scope.create_submission = function(){
      $scope.submission = Submission.create({
        id_or_gus: $scope.current_context.context_gus
      });
    }

    $scope.create_submission();

    $scope.submit = function() {
    }

  });
}]);
