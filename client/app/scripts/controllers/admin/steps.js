GLClient.controller('AdminStepAddCtrl', ['$scope', function($scope) {

    $scope.new_step = {};

    $scope.add_step = function() {
      var step = new $scope.admin.new_step($scope.context.id);
      step.label = $scope.new_step.label;
      step.presentation_order = $scope.newItemOrder($scope.context.steps, 'presentation_order');

      step.$save(function(new_step){
        $scope.context.steps.push(new_step);
        $scope.new_step = {};
      });
    };
  }
]);

GLClient.controller('AdminStepEditorCtrl', ['$scope', '$modal',
  function($scope, $modal) {

    $scope.editing = false;

    $scope.toggleEditing = function (e) {
      $scope.editing = $scope.editing ^ 1;
      e.stopPropagation();
    };

    $scope.deleteFromList = function(list, elem) {
      var idx = list.indexOf(elem);
      if (idx !== -1) {
        list.splice(idx, 1);
      }
    };

    $scope.save_all = function () {
      $scope.assignUniqueOrderIndex($scope.step.children);
      angular.forEach($scope.step.children, function (field, key) {
        $scope.save_field(field);
      });
    };
 
    $scope.toggle_field = function(field, field_group) {
      $scope.field_group_toggled = true;
      if (field_group.children && field_group.children.indexOf(field) !== -1) {
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
    };

    $scope.add_field_from_template = function(template_id, step) {
      $scope.admin.new_field_from_template(template_id, step.id).then(function(field){
        step.children = step.children || [];
        step.children.push(field);
      });
    };
   
    $scope.addField = function(field) {
      $scope.step.children.push(field);
    };

    $scope.deleteStep = function(step) {
      var idx = $scope.context.steps.indexOf(step);
      $scope.context.steps.splice(idx, 1);
    };

    $scope.deleteField = function(field) {
      var idx = $scope.step.children.indexOf(field);
      $scope.step.children.splice(idx, 1);
    };

    $scope.perform_delete_field = function(field) {
      $scope.admin.field['delete']({
        field_id: field.id
      }, function(){
        $scope.deleteField(field);
      });
    };

    $scope.perform_delete_step = function(step) {
      $scope.admin.step['delete']({
        step_id: step.id
      }, function(){
        $scope.deleteStep(step);
      });
    };

    $scope.save_field = function(field) {
      console.log(field);
      var updated_field = new $scope.admin.field(field);
      if ($scope.field_group_toggled) {
        $scope.field_group_toggled = false;
        $scope.save_all();
      }
      return updated_field.$update();
    };

    $scope.save_step = function(step) {
      var updated_step = new $scope.admin.step(step);
      return updated_step.$update();
    };

    $scope.stepDeleteDialog = function(e, step){
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

      e.stopPropagation();
    };

    $scope.new_field = {};

    $scope.add_field = function() {
      var field = $scope.admin.new_field($scope.step.id);
      field.label = $scope.new_field.label;
      field.type = $scope.new_field.type;
      field.attrs = $scope.admin.get_field_attrs(field.type);
      field.y = $scope.newItemOrder($scope.step.children, 'y');

      field.$save(function(new_field){
        $scope.addField(new_field);
        $scope.new_field = {};
      });

    };

    $scope.composable_fields = [];
    angular.forEach($scope.step.children, function(field, index) {
      $scope.composable_fields.push(field);
      if (field.type === 'fieldgroup') {
        angular.forEach(field.children, function(field_c, index_c) {
          $scope.composable_fields.push(field_c);
       });
      }
    });

    $scope.moveFieldUp = function(field) {
      field.y -= 1;
      $scope.save_field(field);
    };

    $scope.moveFieldDown = function(field) {
      field.y += 1;
      $scope.save_field(field);
    };

  }
]);
