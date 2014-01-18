GLClient.controller('SubmissionCtrl',
      ['$scope', '$rootScope', '$location', 'Authentication', 'Node', 'Submission', 'Receivers', 'WhistleblowerTip',
      function($scope, $rootScope, $location, Authentication, Node, Submission, Receivers, WhistleblowerTip) {

  $rootScope.invalidForm = true;
  $scope.receiptConfimation = "";

  Node.get(function(node){
    $scope.node = node;

    new Submission(function(submission){
      $scope.maximumFilesize = submission.maximum_filesize;

      $scope.current_context = submission.current_context;

      $scope.submission = submission;
      $scope.submit = $scope.submission.submit;

      checkReceiverSelected();

    });

  });

  var checkReceiverSelected = function() {
    $scope.receiver_selected = false;
    // Check if there is at least one selected receiver
    angular.forEach($scope.submission.receivers_selected, function(receiver) {
      $scope.receiver_selected = $scope.receiver_selected | receiver;
    });

  }

  $scope.selected_receivers_count = function() {
    var count = 0;

    if ($scope.submission) {
      angular.forEach($scope.submission.receivers_selected, function(selected) {
        if (selected) {
          count += 1;
        }
      });
    }

    return count;
  }

  $scope.selectable = function() {

    if ($scope.submission.current_context.maximum_selectable_receivers == 0) {
      return true;
    }

    return $scope.selected_receivers_count() < $scope.submission.current_context.maximum_selectable_receivers;
  }

  $scope.switch_selection = function(receiver_gus) {
    if ($scope.submission.receivers_selected[receiver_gus] || $scope.selectable()) {
      $scope.submission.receivers_selected[receiver_gus] = !$scope.submission.receivers_selected[receiver_gus];
    }
  }

  $scope.view_tip = function(receipt) {
    if ($scope.receiptConfirmation != receipt)
      return;

    WhistleblowerTip(receipt, function(){
      $location.path('/status/');
    });
  };

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
      $scope.submission.create(function(){
        var url = '/submission/' + $scope.submission.current_submission.submission_gus + '/file';
        
        $scope.queue = [];
        $scope.options = {
          url: url,
          multipart: false,
          headers: Authentication.headers(),
          autoUpload: true,
          maxFileSize: $scope.node.maximum_filesize * 1024 * 1024,
        };
        
      });
      checkReceiverSelected();

    }
  }, false);

  $scope.$watch('submission.receivers_selected', function() {
    if ($scope.submission) {
      checkReceiverSelected();
    }
  }, true);

  $scope.$watch('queue', function(){
    $scope.uploading = false;
    if ($scope.queue) {
      $scope.submission.current_submission.files = [];
      $scope.queue.forEach(function(k){
        if (!k.id)
          $scope.uploading = true;
        else
          $scope.submission.current_submission.files.push(k.id);
      });
    }
  }, true);

}]).
  controller('SubmissionFormController', ['$scope', '$rootScope', function($scope, $rootScope){
    $scope.$watch('submissionForm.$valid', function() {
      $rootScope.invalidForm = $scope.submissionForm.$invalid;
    }, true);
}])
