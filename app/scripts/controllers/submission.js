GLClient.controller('SubmissionCtrl', ['$scope', '$rootScope', '$location', 'Node',
    'Submission', 'Receivers', 'WhistleblowerTip', function($scope, $rootScope,
      $location, Node, Submission, Receivers, WhistleblowerTip) {

  $scope.node_configured = false;

  var checkReceiverSelected = function() {
    $scope.receiver_selected = false;
    // Check if there is at least one selected receiver
    angular.forEach($scope.receivers_selected, function(receiver) {
      $scope.receiver_selected = $scope.receiver_selected | receiver;
    });
  }

  new Submission(function(submission){
    $scope.submission = submission;

    $scope.current_context = submission.current_context;
    $scope.receivers_selected = submission.receivers_selected;

    $scope.submit = $scope.submission.submit;
    $scope.current_context_receivers = $scope.submission.current_context_receivers;
    checkReceiverSelected();

    if (submission.contexts.length === 0) {
      $scope.node_configured = false;
    } else {
      $scope.node_configured = true;
    }

  });

  $scope.view_tip = function(receipt) {
    WhistleblowerTip(receipt, function(tip_id){
      $location.path('/status/' + tip_id);
    });
  };

  $rootScope.uploadedFiles = [];
  $rootScope.uploadingFiles = [];
  $scope.uploading = false;

  $scope.disclaimer = {accepted: false};
  $scope.steps = [
    '1 Receiver selection',
    '2 Fill out your submission',
    '3 Final Step'
  ];

  // Watch for changes in certain variables
  $scope.$watch('submission.current_context', function(){
    if ($scope.current_context) {
      $scope.submission.create();
      checkReceiverSelected();
    }
  }, true);

  $scope.$watch('receivers_selected', function() {
    if ($scope.receivers_selected) {
      checkReceiverSelected();
    }
  }, true);

  $scope.$watch('uploadingFiles', function(){

    if ($scope.uploadingFiles.length === 0)
      $scope.uploading = false;
    else
      $scope.uploading = true;

  }, true);

}]);
