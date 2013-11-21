'use strict';

GLClient.controller('HomeCtrl', ['$scope', '$location', 'Node', 'Authentication',
                    'WhistleblowerTip', 'Contexts', 'Receivers',
  function ($scope, $location, Node, Authentication, WhistleblowerTip, Contexts, Receivers) {
    $scope.receipt = '';
    $scope.configured = false;
    $scope.anonymous = false;
    $scope.step = 1;
    $scope.answer = {value: null}
    $scope.answered = false;
    $scope.correctAnswer = false;
    $scope.showQuestions = false;


    if ($scope.privacy == 'high') {
      $scope.anonymous = true;
    }

    Node.get(function(node_info){
      $scope.node_info = node_info;
    });

    $scope.view_tip = function(receipt) {
      WhistleblowerTip(receipt, function(tip_id) {
        $location.path('/status/' + tip_id);
      });
    };

    $scope.checkAnswer = function() {
      if (!$scope.answer.value)
        return;
      if ($scope.answer.value == 'b') {
        $scope.correctAnswer = true;
      }
      $scope.answered = true;
      $scope.step = 3;
    }

    $scope.goToSubmission = function() {
      if ( !$scope.anonymous && !$scope.node_info.tor2web_submission)
        return;

      if ($scope.anonymous || $scope.correctAnswer) {
        $location.path("/submission");
      } else {
        $scope.showQuestions = true; 
      }
      
    }
    
    $scope.goToStep = function(idx) {
      $scope.step = idx; 
    }

    $scope.goToStart = function() {
      $scope.answered = false;
      $scope.correctAnswer = false;
      $scope.goToStep(1);
    }

}]);
