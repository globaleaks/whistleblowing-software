GLClient.controller('AdminReceiversCtrl', ['$scope', 'Utils', 'AdminReceiverResource',
  function($scope, Utils, AdminReceiverResource) {
  $scope.save_receiver = function(receiver, cb) {
    if (receiver.pgp_key_remove) {
      receiver.pgp_key_public = '';
    }

    if (receiver.pgp_key_public !== undefined &&
        receiver.pgp_key_public !== '') {
      receiver.pgp_key_remove = false;
    }

    var updated_receiver = new AdminReceiverResource(receiver);

    return Utils.update(updated_receiver, cb);
  };
}]).
controller('AdminReceiverEditorCtrl', ['$scope',
  function($scope) {
    $scope.editing = false;

    $scope.toggleEditing = function () {
      $scope.editing = !$scope.editing;
    };

    $scope.save = function() {
      $scope.save_receiver($scope.receiver, false);
    };
}]);
