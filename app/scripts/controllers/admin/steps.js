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
    $scope.field = $scope.get_field($scope.field_key);
  }
]);

GLClient.controller('AdminStepEditorCtrl', ['$scope',
  function($scope) {
    $scope.template_field_keys = [];
    $scope.template_fields = {};
    angular.forEach($scope.admin.fields, function (field, key) {
      if (field.is_template === true) {
        $scope.template_field_keys.push(field.id);
        $scope.template_fields[field.id] = field;
      }
    });

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
   
    $scope.get_field = function(field_key) {
      var selected_field = undefined;
      angular.forEach($scope.admin.fields, function (field, key) {
        if (field.id == field_key) {
          selected_field = field;
          return;
        }
      });
      return selected_field;
    };

    $scope.deleteStep = function(step) {
      var idx = _.indexOf($scope.context.steps, step);
      $scope.context.steps.splice(idx, 1);
    };

    $scope.deleteField = function(field) {
      var idx = _.indexOf($scope.step.children, field);
      $scope.step.children.splice(idx, 1);
    };
    

  }
]);
