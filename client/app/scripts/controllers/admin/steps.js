GLClient.controller('AdminStepAddCtrl', ['$scope',
  function($scope) {

    $scope.add_step = function() {
      context = $scope.context;

      if (context.steps === undefined) {
        context.steps = [];
      }

      context.steps.push(
        {
          context_id: context.id,
          label: $scope.new_step_label,
          description: '',
          hint: '',
          children: []
        }
      );
    };
  }
]);

GLClient.controller('AdminFieldsTemplateAdderCtrl', ['$scope',
  function($scope) {
    $scope.field = $scope.template_fields[$scope.field_key];
  }
]);

GLClient.controller('AdminStepEditorCtrl', ['$scope', '$modal',
  function($scope, $modal) {
    $scope.template_field_keys = Object.keys($scope.admin.template_fields);
    $scope.template_fields = $scope.admin.template_fields;

    $scope.composable_fields = angular.copy($scope.step.children);
    angular.forEach($scope.step.children, function(field_group, key) {
      if (field_group.type == 'fieldgroup') {
        angular.forEach(field_group.children, function(field, key) {
          $scope.composable_fields[key] = field;
        });
      }
    });

    $scope.save_all = function () {
      // XXX this is highly inefficient, could be refactored/improved.
      angular.forEach($scope.step.children, function (field, key) {
        $scope.update_field(field);
      });
    };
 
    $scope.toggle_field = function(field, field_group) {
      $scope.field_group_toggled = true;
      if (field_group.children && field_group.children[field.id]) {
        // Remove it from the fieldgroup 
        field.fieldgroup_id = "";
        $scope.step.children = $scope.step.children || {};
        $scope.step.children[field.id] = field;
        $scope.composable_fields[field.id] = field;
        delete field_group.children[field.id];
      } else {
        // Add it to the fieldgroup 
        field.fieldgroup_id = field_group.id;
        field_group.children = field_group.children || {};
        field_group.children[field.id] = field;
        $scope.composable_fields[field.id] = field;
        delete $scope.step.children[field.id];
      }
    }

    $scope.add_field_from_template = function(field_id, step) {
      $scope.admin.new_field_from_template(field_id, step.id).then(function(field){
        step.children = step.children || [];
        step.children.push(field.id);
      });
    };
   
    $scope.addField = function(field) {
      $scope.step.children[field.id] = field;
    };

    $scope.create_field = function() {
      return $scope.admin.new_field_to_step($scope.step.id);
    };
   
    $scope.deleteStep = function(step) {
      var idx = _.indexOf($scope.context.steps, step);
      $scope.context.steps.splice(idx, 1);
    };

    $scope.deleteField = function(field) {
      delete $scope.step.children[field.id];
    };

    $scope.perform_delete = function(field) {
      $scope.admin.field.delete({
        field_id: field.id
      }, function(){
        $scope.deleteField(field);
      });
    };

    $scope.perform_delete_step = function(step) {
      $scope.deleteStep(step);
      $scope.update($scope.context);
    };

    $scope.update_field = function(field) {
      var updated_field = new $scope.admin.field(field);
      if ($scope.field_group_toggled) {
        $scope.field_group_toggled = false;
        $scope.save_all();
      }
      return updated_field.$update();
    };

    $scope.stepDeleteDialog = function(step){
      var modalInstance = $modal.open({
          templateUrl:  'views/partials/step_delete.html',
          controller: 'ConfirmableDialogCtrl',
          resolve: {
            object: function () {
              return step;
            }
          }

      });

      modalInstance.result.then(
         function(result) { $scope.perform_delete_step(result); },
         function(result) { }
      );
    };

  }
]);
