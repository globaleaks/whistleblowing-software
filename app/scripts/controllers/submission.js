GLClient.controller('SubmissionCtrl', ['$scope', 'localization', 'Node',
    'Submission', 'Receivers', function($scope,
      localization, Node, Submission, Receivers) {

  Submission(function(submission){
    $scope.submission = submission;
    $scope.current_context = submission.current_context;

    $scope.receivers_selected = submission.receivers_selected;

    $scope.submit = $scope.submission.submit;

    $scope.receivers_selected = $scope.submission.receivers_selected;
    $scope.current_context_receivers = $scope.submission.current_context_receivers;

  });

  $scope.submission_complete = false;

  $scope.uploadedFiles = [];

  $scope.accept_disclaimer = false;
  $scope.steps = [
    '1 Receiver selection',
    '2 Fill out your submission',
    '3 Choose receipt'
  ];

  $scope.$watch('current_context', function(){
    if ($scope.current_context) {
      $scope.submission.create();
    }
  });



}]);
