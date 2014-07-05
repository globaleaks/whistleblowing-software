GLClient.controller('SubmissionCtrl',
    ['$scope', '$rootScope', '$location', 'Authentication', 'Node', 'Submission', 'Receivers', 'WhistleblowerTip',
      function ($scope, $rootScope, $location, Authentication, Node, Submission, Receivers, WhistleblowerTip) {

        $rootScope.invalidForm = true;
        $scope.receiptConfimation = "";

        Node.get(function (node) {
          $scope.node = node;

          new Submission(function (submission) {
            $scope.maximumFilesize = submission.maximum_filesize;

            $scope.current_context = submission.current_context;

            $scope.submission = submission;

            if ($scope.submission.contexts.length == 1 && !$scope.submission.current_context.show_receivers) {

              $scope.skip_first_step = true;

            } else {

              $scope.skip_first_step = false;

            }

            $scope.submit = $scope.submission.submit;
            $scope.selection = $scope.steps[0];

            checkReceiverSelected();
          });

        });

        var checkReceiverSelected = function () {
          $scope.receiver_selected = false;
          // Check if there is at least one selected receiver
          angular.forEach($scope.submission.receivers_selected, function (receiver) {
            $scope.receiver_selected = $scope.receiver_selected | receiver;
          });

        };

        $scope.selected_receivers_count = function () {
          var count = 0;

          if ($scope.submission) {
            angular.forEach($scope.submission.receivers_selected, function (selected) {
              if (selected) {
                count += 1;
              }
            });
          }

          return count;
        };

        $scope.selectable = function () {

          if ($scope.submission.current_context.maximum_selectable_receivers == 0) {
            return true;
          }

          return $scope.selected_receivers_count() < $scope.submission.current_context.maximum_selectable_receivers;
        };

        $scope.switch_selection = function (receiver) {
          if (receiver.disabled)
            return;
          if ($scope.submission.receivers_selected[receiver.id] || $scope.selectable()) {
            $scope.submission.receivers_selected[receiver.id] = !$scope.submission.receivers_selected[receiver.id];
          }
        };

        $scope.view_tip = function (receipt) {
          if ($scope.receiptConfirmation != receipt)
            return;

          WhistleblowerTip(receipt, function () {
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
        $scope.$watch('submission.current_context', function () {
          if ($scope.current_context) {
            $scope.submission.create(function () {
              var url = '/submission/' + $scope.submission.current_submission.id + '/file';

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

        $scope.$watch('submission.receivers_selected', function () {
          if ($scope.submission) {
            checkReceiverSelected();
          }
        }, true);

        $scope.$watch('queue', function () {
          $scope.uploading = false;
          if ($scope.queue) {
            $scope.submission.current_submission.files = [];
            $scope.queue.forEach(function (k) {
              if (!k.id)
                $scope.uploading = true;
              else
                $scope.submission.current_submission.files.push(k.id);
            });
          }
        }, true);

        $rootScope.$watch('anonymous', function (newVal, oldVal) {
          if ($scope.node) {
            if (newVal == false && !$scope.node.tor2web_submission) {
              $location.path("/");
            }
          }
        })

      }]).
  controller('SubmissionFormController', ['$scope', '$rootScope', function ($scope, $rootScope) {
    $scope.$watch('submissionForm.$valid', function () {
      $rootScope.invalidForm = $scope.submissionForm.$invalid;
    }, true);
  }]);

GLClient.controller('SubmissionStepsCtrl', ['$scope', function($scope) {

  $scope.getCurrentStepIndex = function(){
    // Get the index of the current step given selectio
    return _.indexOf($scope.steps, $scope.selection);
  };

  // Go to a defined step index
  $scope.goToStep = function(index) {
    if ( $scope.uploading )
      return;

    if ( !_.isUndefined($scope.steps[index]) )
    {
      $scope.selection = $scope.steps[index];
    }
  };

  $scope.hasNextStep = function(){
    var stepIndex = $scope.getCurrentStepIndex();
    var nextStep = stepIndex + 1;
    // Return true if there is a next step, false if not
    return !_.isUndefined($scope.steps[nextStep]);
  };

  $scope.hasPreviousStep = function(){
    var stepIndex = $scope.getCurrentStepIndex();
    var previousStep = stepIndex - 1;
    // Return true if there is a next step, false if not
    return !_.isUndefined($scope.steps[previousStep]);
  };

  $scope.incrementStep = function() {
    if ( $scope.uploading )
      return;

    if ( $scope.hasNextStep() )
    {
      var stepIndex = $scope.getCurrentStepIndex();
      var nextStep = stepIndex + 1;
      $scope.selection = $scope.steps[nextStep];
    }
  };

  $scope.decrementStep = function() {
    if ( $scope.uploading )
      return;

    if ( $scope.hasPreviousStep() )
    {
      var stepIndex = $scope.getCurrentStepIndex();
      var previousStep = stepIndex - 1;
      $scope.selection = $scope.steps[previousStep];
    }
  };

}]);
