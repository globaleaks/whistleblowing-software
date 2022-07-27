GL.
controller("AdminAdvancedCtrl", ["$scope", function($scope) {
  $scope.tabs = [
    {
      title:"Main configuration",
      template:"views/admin/advanced/tab1.html"
    }
  ];

  if ($scope.resources.node.root_tenant) {
    $scope.tabs.push({
      title:"Anomaly detection thresholds",
      template:"views/admin/advanced/tab2.html"
    });
  }

  $scope.resetSubmissions = function() {
    $scope.Utils.deleteDialog().then(function() {
      return $scope.Utils.runAdminOperation("reset_submissions");
    });
  };

  $scope.enableEncryption = function() {
    // do not toggle till confirmation;
    $scope.resources.node.encryption = false;

    if (!$scope.resources.node.encryption) {
      $scope.Utils.openConfirmableModalDialog("views/modals/enable_encryption.html").then(
        function() {
          return $scope.Utils.runAdminOperation('enable_encryption', {}, false).then(
            function() {
              $scope.Authentication.logout();
            },
            function() {}
	  );
        },
        function() { }
      );
    }
  };

  $scope.toggleEscrow = function() {
    // do not toggle till confirmation;
    $scope.resources.node.escrow = !$scope.resources.node.escrow;
    $scope.Utils.runAdminOperation('toggle_escrow', {}, true).then(
      function() {
        $scope.resources.preferences.escrow = $scope.resources.preferences.escrow;
      },
      function() {}
    );
  }
}]);
