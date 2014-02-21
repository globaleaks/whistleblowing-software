GLClient.controller('AdminReceiversCtrl', ['$scope', '$modal',
function($scope, $modal) {
  $scope.save_all = function () {
    angular.forEach($scope.admin.receivers, function (receiver, key) {
      $scope.update(receiver);
    });
  };

  $scope.delete = function(receiver) {
    var idx = _.indexOf($scope.admin.receivers, receiver);

    receiver.$delete(function(){
      $scope.admin.receivers.splice(idx, 1);
    });

  };

  $scope.deleteDialog = function(receiver){
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
       function(result) { $scope.delete(result); },
       function(result) { }
    );
  };

  $scope.sortableOptions = {
    stop: function(e, ui) {
      $scope.update_receivers_order();
    }
  };

  $scope.reorder_receivers_alphabetically = function () {
    $scope.admin.receivers = _($scope.admin.receivers).sortBy(function (receiver) {
      return receiver.name;
    });

    $scope.update_receivers_order();
  };

  $scope.update_receivers_order = function() {
    var i = 0;
    angular.forEach($scope.admin.receivers, function(receiver, key) {
        receiver.presentation_order = i + 1;
        i += 1;
    });
  }

}]);

GLClient.controller('AdminReceiversEditorCtrl', ['$scope', 'passwordWatcher',
  function($scope, passwordWatcher) {

    passwordWatcher($scope, 'receiver.password');

    $scope.editing = false;

    $scope.toggleEditing = function () {
      $scope.editing = $scope.editing ^ 1;
    };

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
    };

    $scope.save_receiver = function() {
      if ($scope.receiver.gpg_key_remove == true) {
        $scope.receiver.gpg_key_armor = '';
      }

      if ($scope.receiver.gpg_key_armor !== undefined &&
          $scope.receiver.gpg_key_armor != '') {
        $scope.receiver.gpg_key_remove = false;
      }

      $scope.update($scope.receiver);

    }

}]);

GLClient.controller('AdminReceiverAddCtrl', ['$scope', 'passwordWatcher',
  function($scope, passwordWatcher) {

    passwordWatcher($scope, 'new_receiver.password');

    $scope.new_receiver = {};

    $scope.add_receiver = function() {
      receiver = new $scope.admin.new_receiver();

      receiver.name = $scope.new_receiver.name;
      receiver.password = $scope.new_receiver.password;
      receiver.mail_address = $scope.new_receiver.email;

      receiver.$save(function(new_receiver){
        $scope.admin.receivers.push(new_receiver);
        $scope.new_receiver = {};
      });
    }

}]);
