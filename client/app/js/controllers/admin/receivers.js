GLClient.controller('AdminReceiversCtrl', ['$scope', '$uibModal', 'AdminReceiverResource',
  function($scope, $uibModal, AdminReceiverResource) {
  $scope.save_receiver = function(receiver, cb) {
    if (receiver.pgp_key_remove === true) {
      receiver.pgp_key_public = '';
    }

    if (receiver.pgp_key_public !== undefined &&
        receiver.pgp_key_public !== '') {
      receiver.pgp_key_remove = false;
    }

    var updated_receiver = new AdminReceiverResource(receiver);

    return $scope.update(updated_receiver, cb);
  };

  $scope.moveUpAndSave = function(elem) {
    $scope.moveUp(elem);
    $scope.save_receiver(elem);
  };

  $scope.moveDownAndSave = function(elem) {
    $scope.moveDown(elem);
    $scope.save_receiver(elem);
  };
}]).
controller('AdminReceiverEditorCtrl', ['$scope', 'CONSTANTS',
  function($scope, CONSTANTS) {
    $scope.editing = false;

    $scope.toggleEditing = function () {
      $scope.editing = !$scope.editing;
    };

    $scope.save = function() {
      $scope.save_receiver($scope.receiver, false);
    };

    $scope.timezones = CONSTANTS.timezones;

    $scope.isSelected = function (context) {
      return $scope.receiver.contexts.indexOf(context.id) !== -1;
    };

    $scope.toggle = function (context) {
      var idx = $scope.receiver.contexts.indexOf(context.id);
      if (idx === -1) {
        $scope.receiver.contexts.push(context.id);
      } else {
        $scope.receiver.contexts.splice(idx, 1);
      }
      $scope.editReceiver.$dirty = true;
      $scope.editReceiver.$pristine = false;
    };
}]);
