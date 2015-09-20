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

    $scope.save_step = function(step) {
      var updated_step = new $scope.admin.step(step);
      return $scope.update(updated_step);
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
      var field = $scope.admin.new_field($scope.step.id, '');
      field.label = $scope.new_field.label;
      field.type = $scope.new_field.type;
      field.attrs = $scope.admin.get_field_attrs(field.type);
      field.y = $scope.newItemOrder($scope.step.children, 'y');

      field.$save(function(new_field){
        $scope.addField(new_field);
        $scope.new_field = {};
      });
    };

    $scope.add_field_from_template = function(template_id) {
      var field = $scope.admin.new_field_from_template(template_id, $scope.step.id, '');
      field.y = $scope.newItemOrder($scope.step.children, 'y');

      field.$save(function(new_field){
        $scope.step.children.push(new_field);
      });
    };

    $scope.moveUpAndSave = function(event, elem) {
      $scope.moveUp(event, elem);
      $scope.save_step(elem);
    };

    $scope.moveDownAndSave = function(event, elem) {
      $scope.moveDown(event, elem);
      $scope.save_step(elem);
    };

    $scope.moveLeftAndSave = function(event, elem) {
      $scope.moveLeft(event, elem);
      $scope.save_step(elem);
    };

    $scope.moveRightAndSave = function(event, elem) {
      $scope.moveRight(event, elem);
      $scope.save_step(elem);
    };
  }
]);
