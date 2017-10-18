GLClient.controller('AdminContextsCtrl',
  ['$scope', 'Utils', 'AdminContextResource',
  function($scope, Utils, AdminContextResource) {

  $scope.save_context = function (context, cb) {
    var updated_context = new AdminContextResource(context);

    return Utils.update(updated_context, cb);
  };

  $scope.moveUpAndSave = function(elem) {
    Utils.moveUp(elem);
    $scope.save_context(elem);
  };

  $scope.moveDownAndSave = function(elem) {
    Utils.moveDown(elem);
    $scope.save_context(elem);
  };
}]).
controller('AdminContextEditorCtrl', ['$scope', 'Utils', 'AdminStepResource', 'AdminContextResource',
  function($scope, Utils, AdminStepResource, AdminContextResource) {

  $scope.editing = false;

  $scope.toggleEditing = function () {
    $scope.editing = !$scope.editing;
  };

  $scope.potential_receivers = $scope.admin.receivers.filter(function(rec) {
    return $scope.context.receivers.indexOf(rec.id) < 0;
  });

  $scope.showSelect = false;
  $scope.toggleSelect = function() {
    $scope.showSelect = true;
  };

  $scope.toggle = function(receiver) {
    var idx = $scope.context.receivers.indexOf(receiver.id);
    if (idx === -1) {
      $scope.context.receivers.push(receiver.id);
    } else {
      $scope.context.receivers.splice(idx, 1);
    }

    $scope.editContext.$dirty = true;
    $scope.editContext.$pristine = false;
  };

  $scope.updateContextImgUrl = function() {
    $scope.contextImgUrl = '/admin/contexts/' + $scope.context.id + '/img#' + Utils.randomFluff();
  };

  $scope.updateContextImgUrl();

  $scope.tip_ttl_off = $scope.context.tip_timetolive === -1;
  $scope.$watch('context.tip_timetolive', function(new_val) {
    if (angular.isDefined(new_val)) {
      $scope.tip_ttl_off = new_val === -1;
    }
  });

  $scope.deleteContext = function() {
    Utils.deleteDialog($scope.context).then(function() {
      return Utils.deleteResource(AdminContextResource, $scope.admin.contexts, $scope.context);
    });
  };
}]).
controller('AdminContextReceiverSelectorCtrl', ['$scope', function($scope) {
  var i = $scope.admin.receivers.map(function(r) {
    return r.id;
  }).indexOf($scope.rec_id);
  $scope.receiver = $scope.admin.receivers[i];

  $scope.swap = function(index, n) {
    var target = index + n;
    if (target !== $scope.context.receivers.length && target !== -1) {
      $scope.context.receivers[index] = $scope.context.receivers[target];
      $scope.context.receivers[target] = $scope.rec_id;
    }
  };

  $scope.removeElem = function(i) {
    $scope.context.receivers.splice(i, 1);
    var j = $scope.admin.receivers.map(function(r) {
      return r.id;
    }).indexOf($scope.rec_id);
    $scope.potential_receivers.push($scope.admin.receivers[j]);
  };
}]).
controller('AdminContextAddCtrl', ['$scope', function($scope) {
  $scope.new_context = {};

  $scope.add_context = function() {
    var context = new $scope.admin_utils.new_context();

    context.name = $scope.new_context.name;
    context.questionnaire_id = $scope.admin.node.default_questionnaire;
    context.presentation_order = $scope.newItemOrder($scope.admin.contexts, 'presentation_order');

    context.$save(function(new_context){
      $scope.admin.contexts.push(new_context);
      $scope.new_context = {};
    });
  };
}]);
