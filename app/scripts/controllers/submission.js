GLClient.controller('SubmissionCtrl', ['$scope', '$rootScope', '$location', 'Node',
    'Submission', 'Receivers', 'WhistleblowerTip', function($scope, $rootScope,
      $location, Node, Submission, Receivers, WhistleblowerTip) {

  var checkReceiverSelected = function() {
    $scope.receiver_selected = false;
    // Check if there is at least one selected receiver
    angular.forEach($scope.submission.receivers_selected, function(receiver) {
      $scope.receiver_selected = $scope.receiver_selected | receiver;
    });
  }

  $scope.receiptConfimation = "";

  Node.get(function(node_info){
    $scope.node_info = node_info;

    new Submission(function(submission){
      $scope.show_context_selector = submission.contexts.length > 1;

      $scope.maximumFilesize = submission.maximum_filesize;

      $scope.current_context = submission.current_context;

      $scope.submission = submission;
      $scope.submit = $scope.submission.submit;

      checkReceiverSelected();
      

    });

  });


  $scope.view_tip = function(receipt) {
    if ($scope.receiptConfirmation != receipt)
      return;

    WhistleblowerTip(receipt, function(tip_id){
      $location.path('/status/' + tip_id);
    });
  };

  $rootScope.fileUploader = {};
  $rootScope.fileUploader.uploadedFiles = [];
  $rootScope.fileUploader.uploadingFiles = [];
  $scope.uploading = false;

  $scope.disclaimer = {accepted: false};
  $scope.steps = [
    '1',
    '2',
    '3'
  ];

  // Watch for changes in certain variables
  $scope.$watch('submission.current_context', function(){
    if ($scope.current_context) {
      $scope.submission.create();
      checkReceiverSelected();
    }
  }, false);

  $scope.$watch('receivers_selected', function() {
    if ($scope.receivers_selected) {
      checkReceiverSelected();
    }
  }, true);

  $scope.$watch('fileUploader', function(){

    if ($scope.fileUploader.uploadingFiles.length === 0)
      $scope.uploading = false;
    else
      $scope.uploading = true;

  }, true);

}]);
