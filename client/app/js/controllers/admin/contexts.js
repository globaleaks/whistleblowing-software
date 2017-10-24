GLClient.controller('AdminContextsCtrl',
  ['$scope', 'Utils', 'AdminContextResource',
  function($scope, Utils, AdminContextResource) {

  $scope.save_context = function (context, cb) {
    var updated_context = new AdminContextResource(context);

    return Utils.update(updated_context, cb);
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
controller('AdminContextEditorCtrl', ['$rootScope', '$scope', 'AdminStepResource', 'AdminContextResource',
  function($rootScope, $scope, AdminStepResource, AdminContextResource) {

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
    $scope.contextImgUrl = '/admin/contexts/' + $scope.context.id + '/img#' + $scope.Utils.randomFluff();
  };

  $scope.updateContextImgUrl();

  $scope.tip_ttl_off = $scope.context.tip_timetolive === -1;
  $scope.$watch('context.tip_timetolive', function(new_val) {
    if (angular.isDefined(new_val)) {
      $scope.tip_ttl_off = new_val === -1;
    }
  });

  $scope.deleteContext = function() {
    $scope.deleteDialog($scope.context).then(function() {
      return AdminContextResource.delete({id: $scope.context.id}).$promise;
    }).then(function() {
      var idx = $scope.admin.contexts.indexOf($scope.context);
      $scope.admin.contexts.splice(idx, 1);
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
