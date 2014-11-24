GLClient.controller('AdminContextsCtrl',
  ['$scope', '$modal', 'Admin',
  function($scope, $modal, Admin) {

  $scope.add_context = function (name) {
    context = $scope.admin.new_context();
    context.name = name;
    context.$save(function (new_context) {
      $scope.admin.contexts.push(new_context);
    });
  };

  $scope.save_context = function (context) {
    $scope.update(context);
  };

  $scope.save_all = function () {
    angular.forEach($scope.admin.contexts, function (context, key) {
      $scope.update(context);
    });
  };

  $scope.perform_delete = function(context) {
    var idx = _.indexOf($scope.admin.contexts, context);

    context['$delete'](function(){
      $scope.admin.contexts.splice(idx, 1);
    });
  };

  $scope.reorder_contexts_alphabetically = function () {
    $scope.admin.contexts = _($scope.admin.contexts).sortBy(function (context) {
      return context.name;
    });

    $scope.update_contexts_order();

    $scope.save_all();
  };

  $scope.update_contexts_order = function () {
    var i = 0;
    angular.forEach($scope.admin.contexts, function (context, key) {
      context.presentation_order = i + 1;
      i += 1;
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

  $scope.sortableOptions = {
    placeholder: "placeholder",
    handle: ".handle",
    axis: 'x',
    stop: function(e, ui) {
      $scope.update_contexts_order();
    }
  };

}]);

GLClient.controller('AdminContextsEditorCtrl', ['$scope',
  function($scope) {

    $scope.editing = $scope.context.description === undefined;

     $scope.sortableOptions = {
      placeholder: "placeholder",
      handle: ".handle",
      axis: 'x',
      stop: function(e, ui) {
        $scope.contextForm.$dirty = true;
        $scope.contextForm.$pristine = false;
        $scope.update_contexts_order();
      }
    };

   
    $scope.toggleEditing = function () {
      $scope.editing = $scope.editing ^ 1;
    };

    $scope.isSelected = function (receiver) {
      return $scope.context.receivers.indexOf(receiver.id) !== -1;
    };

    $scope.toggle = function(receiver) {
      var idx = $scope.context.receivers.indexOf(receiver.id);
      $scope.contextForm.$dirty = true;
      $scope.contextForm.$pristine = false;
      if (idx === -1) {
        $scope.context.receivers.push(receiver.id);
      } else {
        $scope.context.receivers.splice(idx, 1);
      }
    }

}]);
