GLClient.controller('AdminContextsCtrl',
  ['$scope', '$modal',
  function($scope, $modal) {

  $scope.new_context = {};

  $scope.add_context = function() {
    var context = new $scope.admin.new_context();

    context.name = $scope.new_context.name;

    context.$save(function(new_context){
      $scope.admin.contexts.push(new_context);
      $scope.new_context = {};
    });
  };

  $scope.save_context = function (context, cb) {
    var updated_context = new $scope.admin.context(context);

    return $scope.update(updated_context, cb);
  };

  $scope.save_single = function (context) {
    $scope.save_context(context, $scope.reload);
  };

  $scope.save_all = function () {
    angular.forEach($scope.admin.contexts, function (context, key) {
      $scope.save_context(context);
    });
  };

  $scope.perform_delete = function(context) {
    $scope.admin.context['delete']({
      context_id: context.id
    }, function(){
      var idx = $scope.admin.contexts.indexOf(context);
      $scope.admin.contexts.splice(idx, 1);
    });
  };

  $scope.fieldsSortableOptions = {
    stop: function (e, ui) {
      var i = 0;
      angular.forEach(ui.item.scope().context.fields, function (field, key) {
        field.presentation_order = i + 1;
        i += 1;
      });
    }
  };

  $scope.contextDeleteDialog = function(context){
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
  };

  $scope.update_contexts_order = function () {
    var i = 0;
    angular.forEach($scope.admin.contexts, function (context, key) {
      context.presentation_order = i + 1;
      i += 1;
    });
  };

  $scope.sortableOptions = {
    orderChanged: function(e) {
      var contexts = angular.copy($scope.admin.contexts);

      var i = 0;
      angular.forEach(contexts, function (context, key) {
        context.presentation_order = i + 1;
        i += 1;
      });

      $scope.admin.contexts = contexts;
    }
  };

}]);

GLClient.controller('AdminContextsEditorCtrl', ['$scope',
  function($scope) {

    $scope.editing = $scope.context.description === undefined;

    $scope.toggleEditing = function () {
      $scope.editing = $scope.editing ^ 1;
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
