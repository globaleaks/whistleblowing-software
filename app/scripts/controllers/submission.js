GLClient.controller('SubmissionCtrl', ['$scope', 'localization', 'Node',
    'Submission', function($scope,
      localization, Node, Submission) {

  $scope.submission_complete = false;
  $scope.localization = localization;
  $scope.receivers_selected = localization.receivers_selected;

  $scope.accept_disclaimer = false;
  $scope.steps = [
    '1 Receiver selection',
    '2 Fill out your submission',
    '3 Choose receipt'
  ];

  // XXX here we are actually violating the principle for which the
  // controller should not be stateful. This can possibly be fixed by
  // refactoring how the API works, or by making the logic for creation of
  // the submission into a service.
  // We use the scope variable uploaded_files to keep track of the files
  // that are uploaded.
  $scope.uploaded_files = [];

  $scope.receivers_selected = {};
  $scope.current_context_receivers = {};

  var isReceiverInContext = function(receiver, context) {

    if (receiver.contexts.indexOf(context.context_gus)) {
      return true;
    } else {
      return false
    };

  };

  var setReceiversForCurrentContext = function(submissionID) {

    // Make sure all the receivers are selected by default
    for (var r in $scope.localization.receivers) {
      var c_receiver = $scope.localization.receivers[r];

      // Check if receiver belongs to the currently selected context
      if (isReceiverInContext(c_receiver,
          $scope.localization.current_context)) {
        $scope.current_context_receivers[r] = c_receiver;
        $scope.receivers_selected[c_receiver.receiver_gus] = true;
      }
    }

  };

  var createSubmission = function() {
    $scope.submission = new Submission({context_gus:
        $scope.localization.current_context.context_gus});

    $scope.submission.$save(function(submissionID){
      // XXX the backend should return this.
      $scope.submission.fields = {};
      setReceiversForCurrentContext(submissionID);
    });

  };

  // XXX This is not as clean as I would like it to be.
  // The issue lies in the fact that we need to wait for the localization
  // current context to be initialized via an async XML HTTP request.
  // There may be a better way to do this.
  $scope.$watch('localization.current_context', function(){
    if ($scope.localization.current_context) {
      createSubmission();
    }
  });

  $scope.submit = function() {

    // Set the submission field values
    _.each(localization.current_context.fields, function(field, k) {
      $scope.submission.fields[field.name] = field.value;
    });

    // Set the currently selected receivers
    $scope.submission.receivers = [];
      _.each($scope.receivers_selected, function(selected, receiver_gus){
        if (selected) {
          $scope.submission.receivers.push(receiver_gus);
        }
      });

    $scope.submission.$submit();
    $scope.submission_complete = true;
  }

}]);
