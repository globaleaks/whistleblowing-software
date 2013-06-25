GLClient.controller('StatusCtrl',
  ['$scope', '$rootScope', '$routeParams', 'Tip', '$cookies',
  function($scope, $rootScope, $routeParams, Tip, $cookies) {
    $scope.tip_id = $routeParams.tip_id;

    var TipID = {tip_id: $scope.tip_id};

    new Tip(TipID, function(tip){
      $scope.tip = tip;
      $rootScope.fileUploader = {};
      $rootScope.fileUploader.uploadedFiles = [];
      $rootScope.fileUploader.uploadingFiles = [];
    });

    $scope.newComment = function() {
      $scope.tip.comments.newComment($scope.newCommentContent);
      $scope.newCommentContent = '';
    };

    if ($cookies['role'] === 'wb') {
      $rootScope.whistleblower_tip_id = $cookies['tip_id'];
    }

}]);

GLClient.controller('FileDetailsCtrl', ['$scope', function($scope){
    $scope.securityCheckOpen = false;

    $scope.openSecurityCheck = function() {
      $scope.securityCheckOpen = true;
    };

    $scope.closeSecurityCheck = function() {
      $scope.securityCheckOpen = false;
    };

    $scope.securityCheckOptions = {
      backdropFade: true,
      dialogFade: true
    }
}]);
