GLClient.controller('AdminContextsCtrl',
  ['$scope', '$modal',
  function($scope, $modal) {

  $scope.save_context = function (context, cb) {
    var updated_context = new $scope.admin.context(context);

    return $scope.update(updated_context, cb);
  };

  $scope.perform_delete = function(context) {
    $scope.admin.context['delete']({
      context_id: context.id
    }, function(){
      var idx = $scope.admin.contexts.indexOf(context);
      $scope.admin.contexts.splice(idx, 1);
    });
  };

  $scope.contextDeleteDialog = function(e, context){
    var modalInstance = $modal.open({
        templateUrl:  'views/partials/context_delete.html',
        controller: 'ConfirmableDialogCtrl',
        resolve: {
          object: function () {
            return context;
          }
        }
    });

    modalInstance.result.then(
       function(result) { $scope.perform_delete(result); },
       function(result) { }
    );

    e.stopPropagation();
  };

  $scope.update_contexts_order = function () {
    var i = 0;
    angular.forEach($scope.admin.contexts, function (context, key) {
      context.presentation_order = i + 1;
      i += 1;
    });
  };

  $scope.moveUpAndSave = function(event, elem) {
    $scope.moveUp(event, elem);
    $scope.save_context(elem);
  };

  $scope.moveDownAndSave = function(event, elem) {
    $scope.moveDown(event, elem);
    $scope.save_context(elem);
  };

}]);

GLClient.controller('AdminContextEditorCtrl', ['$scope',
  function($scope) {

  $scope.editing = false;

  $scope.toggleEditing = function (e) {
    $scope.editing = !$scope.editing;
    e.stopPropagation();
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

}]);

GLClient.controller('AdminContextAddCtrl', ['$scope', function($scope) {

  $scope.new_context = {};

  $scope.add_context = function() {
    var context = new $scope.admin.new_context();

    context.name = $scope.new_context.name;
    context.presentation_order = $scope.newItemOrder($scope.admin.contexts, 'presentation_order');

    context.$save(function(new_context){
      $scope.admin.contexts.push(new_context);
      $scope.new_context = {};
    });
  };

}]);
