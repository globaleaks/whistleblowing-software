GLClient.controller('SubmissionCtrl', ['$scope', '$location', 'Node',
    'Submission', 'Receivers', 'WhistleblowerTip', function($scope,
      $location, Node, Submission, Receivers, WhistleblowerTip) {
  Submission(function(submission){
    $scope.submission = submission;

    $scope.current_context = submission.current_context;
    $scope.receivers_selected = submission.receivers_selected;

    $scope.submit = $scope.submission.submit;
    $scope.current_context_receivers = $scope.submission.current_context_receivers;

  });

  $scope.uploadedFiles = [];

  $scope.accept_disclaimer = false;
  $scope.steps = [
    '1 Receiver selection',
    '2 Fill out your submission',
    '3 Final Step'
  ];

  $scope.$watch('current_context', function(){
    if ($scope.current_context) {
      $scope.submission.create();
    }
  });

}]);
