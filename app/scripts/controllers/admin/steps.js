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

GLClient.controller('AdminStepEditorCtrl', ['$scope',
  function($scope) {

    $scope.add_field_to_step = function() {
      step = $scope.step;

      if (step.children == undefined) {
        step.children = [];
      }

      console.log($scope.step.children);
      console.log($scope.field_to_add);

      step.children.push($scope.field_to_add);

      step.children = _.uniq(step.children, function(item){return JSON.stringify(item);});
    }

    $scope.indexed_fields = {};
    angular.forEach($scope.admin.fields, function (field, key) {
      $scope.indexed_fields[field.id] = field.label;
    });

    $scope.deleteStep = function(step) {
      var idx = _.indexOf($scope.context.step, step);
      $scope.context.steps.splice(idx, 1);
    };

    $scope.deleteField = function(field) {
      var idx = _.indexOf($scope.step.children, field);
      $scope.step.children.splice(idx, 1);
    };

  }
]);
