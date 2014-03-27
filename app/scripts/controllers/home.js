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

    $scope.goToSubmission = function () {
      if (!$scope.anonymous && !$scope.node.tor2web_submission)
        return;

      if ($scope.anonymous || $scope.answer.value == 'b') {
        $location.path("/submission");
      } else {
        $scope.showQuestions = true;
      }

    };
    
}]);
