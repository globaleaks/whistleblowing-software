GLClient.controller('AdminReceiversCtrl', ['$scope',
function($scope) {
  $scope.randomFluff = Math.round(Math.random()*1000000);
  $scope.delete = function(receiver) {
    var idx = _.indexOf($scope.admin.receivers, receiver);

    receiver.$delete(function(){
      $scope.admin.receivers.splice(idx, 1);
    });

  };
}]);

GLClient.controller('AdminReceiversEditorCtrl', ['$scope', 'passwordWatcher',
  function($scope, passwordWatcher) {

    passwordWatcher($scope, 'receiver.password');

    $scope.editing = false;

    $scope.toggleEditing = function() {
      $scope.editing = $scope.editing ^ 1;
    }

    $scope.isSelected = function(context) {
      if ($scope.receiver.contexts.indexOf(context.context_gus) !== -1) {
        return true;
      } else {
        return false;
      }
    }

    $scope.toggle = function(context) {
      var idx = $scope.receiver.contexts.indexOf(context.context_gus)
      if (idx === -1) {
        $scope.receiver.contexts.push(context.context_gus);
      } else {
        $scope.receiver.contexts.splice(idx, 1);
      }
    }

}]);

GLClient.controller('AdminReceiverAddCtrl', ['$scope', 'passwordWatcher',
  function($scope, passwordWatcher) {

    passwordWatcher($scope, 'new_receiver.password');

  $scope.new_receiver = {};

  $scope.add_receiver = function() {
    var receiver = new $scope.admin.receiver;

    receiver.name = $scope.new_receiver.name;
    receiver.password = $scope.new_receiver.password;
    receiver.notification_fields = {'mail_address': $scope.new_receiver.email};

    // receiver.languages = [];
    // receiver.tags = [];

    // Under here go default settings
    receiver.contexts =  [];
    receiver.description = "";
    receiver.can_delete_submission = false;
    receiver.receiver_level = 1;
    receiver.tags = [];
    receiver.tip_notification = true;
    receiver.file_notification = true;
    receiver.comment_notification = false;
    receiver.gpg_key_info = '';
    receiver.gpg_key_fingerprint = '';
    receiver.gpg_key_remove = false;
    receiver.gpg_key_armor = '';
    receiver.gpg_key_status = 'ignored';
    receiver.gpg_enable_notification = false;
    receiver.gpg_enable_files = false;
    receiver.$save(function(added_receiver){
      $scope.admin.receivers.push(added_receiver);
      $scope.new_receiver = {};
    });

  };

}]);
