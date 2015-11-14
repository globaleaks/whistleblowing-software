GLClient.controller('AdminReceiversCtrl', ['$scope', '$modal', 'AdminReceiverResource',
  function($scope, $modal, AdminReceiverResource) {
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

  $scope.perform_delete = function(receiver) {
    AdminReceiverResource['delete']({
      id: receiver.id
    }, function(){
      var idx = $scope.admin.receivers.indexOf(receiver);
      $scope.admin.receivers.splice(idx, 1);
    });

  };

  $scope.receiverDeleteDialog = function(receiver){
    var modalInstance = $modal.open({
        templateUrl:  'views/partials/receiver_delete.html',
        controller: 'ConfirmableDialogCtrl',
        resolve: {
          object: function () {
            return receiver;
          }
        }
    });

    modalInstance.result.then(
       function(result) { $scope.perform_delete(result); },
       function(result) { }
    );
  };

  $scope.moveUpAndSave = function(elem) {
    $scope.moveUp(elem);
    $scope.save_receiver(elem);
  };

  $scope.moveDownAndSave = function(elem) {
    $scope.moveDown(elem);
    $scope.save_receiver(elem);
  };
}]);

GLClient.controller('AdminReceiverEditorCtrl', ['$scope', 'passwordWatcher', 'CONSTANTS',
  function($scope, passwordWatcher, CONSTANTS) {

    $scope.editing = false;

    $scope.toggleEditing = function () {
      $scope.editing = !$scope.editing;
    };

    $scope.save = function() {
      $scope.save_receiver($scope.receiver, false);
    };

    $scope.timezones = CONSTANTS.timezones;

    passwordWatcher($scope, 'receiver.password');

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
