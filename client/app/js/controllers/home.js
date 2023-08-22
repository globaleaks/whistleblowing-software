GL.controller("HomeCtrl", ["$scope", function ($scope) {
  if ($scope.public.node.user_privacy_policy_text && $scope.resources.preferences.accepted_privacy_policy === "1970-01-01T00:00:00Z"){
    $scope.Utils.acceptPrivacyPolicyDialog();
  }
}]);
