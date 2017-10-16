GLClient.controller('AdminContextsCtrl',
  ['$scope', '$uibModal', 'AdminContextResource',
  function($scope, $uibModal, AdminContextResource) {

  $scope.save_context = function (context, cb) {
    var updated_context = new AdminContextResource(context);

    return $scope.Utils.update(updated_context, cb);
  };

  $scope.perform_delete = function(context) {
    AdminContextResource.delete({
      id: context.id
    }, function(){
      var idx = $scope.admin.contexts.indexOf(context);
      $scope.admin.contexts.splice(idx, 1);
    });
  };

  $scope.contextDeleteDialog = function(context){
    var modalInstance = $scope.Utils.openConfirmableModalDialog('views/partials/context_delete.html', context);

    modalInstance.result.then(
       function(result) { $scope.perform_delete(result); },
       function() { }
    );
  };

  $scope.moveUpAndSave = function(elem) {
    $scope.Utils.moveUp(elem);
    $scope.save_context(elem);
  };

  $scope.moveDownAndSave = function(elem) {
    $scope.Utils.moveDown(elem);
    $scope.save_context(elem);
  };
}]).
controller('AdminContextEditorCtrl', ['$scope', 'AdminStepResource',
  function($scope, AdminStepResource) {

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

  $scope.delStep = function(step) {
    AdminStepResource.delete({
      id: step.id
    }, function() {
      $scope.context.steps.splice($scope.context.steps.indexOf(step), 1);
    });
  };

  $scope.updateContextImgUrl = function() {
    $scope.contextImgUrl = '/admin/contexts/' + $scope.context.id + '/img#' + $scope.Utils.randomFluff();
  };

  $scope.updateContextImgUrl();

  $scope.tip_ttl_off = $scope.context.tip_timetolive === -1;
  $scope.$watch('context.tip_timetolive', function(new_val) {
    if (angular.isDefined(new_val)) {
      $scope.tip_ttl_off = new_val === -1;
    }
  });
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
