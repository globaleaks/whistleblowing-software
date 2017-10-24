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

  $scope.isSelected = function (receiver) {
    return $scope.context.receivers.indexOf(receiver.id) !== -1;
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
