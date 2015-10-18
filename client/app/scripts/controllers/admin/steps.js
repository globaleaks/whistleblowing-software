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

    $scope.toggleEditing = function () {
      $scope.editing = $scope.editing ^ 1;
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

    $scope.delField = function(field) {
      $scope.admin.field['delete']({
        id: field.id
      }, function() {
        $scope.step.splice($scope.step.children.indexOf(field), 1);
      });
    };

    $scope.delAllFields = function() {
      angular.forEach($scope.step, function(field) {
        $scope.delField(field);
      });
    };

    $scope.save_step = function(step) {
      var updated_step = new $scope.admin.step(step);
      return $scope.update(updated_step);
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

    $scope.moveUpAndSave = function(elem) {
      $scope.moveUp(elem);
      $scope.save_step(elem);
    };

    $scope.moveDownAndSave = function(elem) {
      $scope.moveDown(elem);
      $scope.save_step(elem);
    };

    $scope.moveLeftAndSave = function(elem) {
      $scope.moveLeft(elem);
      $scope.save_step(elem);
    };

    $scope.moveRightAndSave = function(elem) {
      $scope.moveRight(elem);
      $scope.save_step(elem);
    };
  }
]);
