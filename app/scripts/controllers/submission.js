GLClient.controller('SubmissionCtrl', ['$scope', '$location', 'Node',
    'Submission', 'Receivers', 'WhistleblowerTip', function($scope,
      $location, Node, Submission, Receivers, WhistleblowerTip) {

  new Submission(function(submission){
    $scope.submission = submission;

    $scope.current_context = submission.current_context;
    $scope.receivers_selected = submission.receivers_selected;

    $scope.submit = $scope.submission.submit;
    $scope.current_context_receivers = $scope.submission.current_context_receivers;

  });

  $scope.view_tip = function(receipt) {
    WhistleblowerTip(receipt, function(tip_id){
      $location.path('/status/' + tip_id);
    });
  };

  $scope.uploadedFiles = [];
  $scope.uploadingFiles = [];
  $scope.uploading = false;

  $scope.disclaimer = {accepted: false};
  $scope.steps = [
    '1 Receiver selection',
    '2 Fill out your submission',
    '3 Final Step'
  ];

  $scope.$watch('submission.current_context', function(){
    if ($scope.current_context) {
      $scope.submission.create();
    }
  });

  $scope.$watch('uploadingFiles', function(){

    if ($scope.uploadingFiles.length === 0)
      $scope.uploading = false;
    else
      $scope.uploading = true;

  }, true);

}]);
