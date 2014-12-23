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
    $scope.composable_fields = {};
    $scope.template_field_keys = Object.keys($scope.admin.template_fields);
    $scope.template_fields = $scope.admin.template_fields;
    angular.forEach($scope.step.children, function(field, index) {
      $scope.composable_fields[field.id] = field;
      if (field.type == 'fieldgroup') {
        angular.forEach(field.children, function(field_c, index_c) {
          $scope.composable_fields[field_c.id] = field_c;
       });
      }
    });

    $scope.deleteFromList = function(list, elem) {
      var idx = _.indexOf(list, elem);
      if (idx != -1) {
        list.splice(idx, 1);
      }
    };

    $scope.save_all = function () {
      // XXX this is highly inefficient, could be refactored/improved.
      angular.forEach($scope.step.children, function (field, key) {
        $scope.update_field(field);
      });
    };
 
    $scope.toggle_field = function(field, field_group) {
      $scope.field_group_toggled = true;
      if (field_group.children && (_.indexOf(field_group.children, field) !== -1)) {
        // Remove it from the fieldgroup 
        field.fieldgroup_id = '';
        field.step_id = $scope.step.id;
        $scope.step.children = $scope.step.children || [];
        $scope.step.children.push(field);
        $scope.deleteFromList(field_group.children, field);
      } else {
        // Add it to the fieldgroup 
        field.step_id = '';
        field.fieldgroup_id = field_group.id;
        field_group.children = field_group.children || [];
        field_group.children.push(field);
        $scope.deleteFromList($scope.step.children, field);
      }
    }

    $scope.add_field_from_template = function(field_id, step) {
      $scope.admin.new_field_from_template(field_id, step.id).then(function(field){
        step.children = step.children || [];
        step.children.push(field);
      });
    };
   
    $scope.addField = function(field) {
      $scope.step.children.push(field);
    };

    $scope.create_field = function() {
      return $scope.admin.new_field_to_step($scope.step.id);
    };
   
    $scope.deleteStep = function(step) {
      var idx = _.indexOf($scope.context.steps, step);
      $scope.context.steps.splice(idx, 1);
    };

    $scope.deleteField = function(field) {
      var idx = _.indexOf($scope.step.children, field);
      $scope.step.children.splice(idx, 1);
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
