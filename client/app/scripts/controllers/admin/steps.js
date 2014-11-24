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

GLClient.controller('AdminStepEditorCtrl', ['$scope',
  function($scope) {
    $scope.template_field_keys = Object.keys($scope.admin.template_fields);
    $scope.template_fields = $scope.admin.template_fields;

    $scope.add_field_to_step = function() {
      step = $scope.step;

      step.children = step.children || [];
      step.children.push($scope.field_to_add);

      step.children = _.uniq(step.children, function(item){return JSON.stringify(item);});
    };
    
    $scope.add_field_from_template = function(field_id, step) {
      $scope.admin.new_field_from_template(field_id, step.id).then(function(field){
        step.children = step.children || [];
        step.children.push(field.id);
      });
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
    }

    $scope.update_field = function(field) {
      var updated_field = new $scope.admin.field(field);
      return updated_field.$update();
    }
    

  }
]);
