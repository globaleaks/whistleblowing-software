GLClient.controller('HomeCtrl', ['$scope', '$location', '$uibModal',
                    'WhistleblowerTip',
  function ($scope, $location, $uibModal, WhistleblowerTip) {
    $scope.keycode = '';
    $scope.configured = false;
    $scope.step = 1;
    $scope.answer = {value: null};
    $scope.answered = false;
    $scope.correctAnswer = false;
    $scope.showQuestions = false;

    var open_quiz = function () {
      var modalInstance = $uibModal.open({
        templateUrl: 'views/partials/security_awareness_quiz.html',
        controller: 'QuizCtrl',
        size: 'lg',
        scope: $scope
      });
    };

    $scope.goToSubmission = function () {
      if (!$scope.anonymous && !$scope.node.tor2web_whistleblower) {
        return;
      }
      // Before showing the security awareness panel
      if ($scope.anonymous ||
          $scope.node.disable_security_awareness_badge) {
        $location.path("/submission");
      } else {
        open_quiz();
      }
    };
    
}]);


GLClient.controller('QuizCtrl', ['$scope', '$uibModalInstance', '$location',
                    function($scope, $uibModalInstance, $location) {
  $scope.goToSubmission = function() {
    // After showing the security awareness panel
    if ($scope.node.disable_security_awareness_questions ||
        $scope.answer.value === 'b') {
      $uibModalInstance.close();
      $location.path("/submission");
    }
  };

  $scope.cancel = function () {
    $uibModalInstance.close();
  };

}]);
