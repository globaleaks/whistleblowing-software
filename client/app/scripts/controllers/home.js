'use strict';

GLClient.controller('HomeCtrl', ['$scope', '$location', 'Node', 'Authentication',
                    'WhistleblowerTip', 'Contexts', 'Receivers',
  function ($scope, $location, Node, Authentication, WhistleblowerTip, Contexts, Receivers) {
    $scope.receipt = '';
    $scope.configured = false;
    $scope.step = 1;
    $scope.answer = {value: null};
    $scope.answered = false;
    $scope.correctAnswer = false;
    $scope.showQuestions = false;

    $scope.view_tip = function(receipt) {
      WhistleblowerTip(receipt, function() {
        $location.path('/status');
      });
    };

    $scope.goToSubmission = function (stage) {
      if (!$scope.anonymous && !$scope.node.tor2web_submission)
        return;

      if (stage == 1) {
        // Before showing the security awareness badge
        if ($scope.anonymous ||
            $scope.node.disable_security_awareness_badge) {
          $location.path("/submission");
        } else {
          $scope.showQuestions = true;
        }
      } else if (stage == 2) {
        // After showing the security awareness badge
        if ($scope.node.disable_security_awareness_questions ||
            $scope.answer.value == 'b') {
          $location.path("/submission");
        }
      }
    };
    
}]);
