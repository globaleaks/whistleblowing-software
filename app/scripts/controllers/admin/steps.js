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

    $scope.add_field_to_step = function() {
      step = $scope.step;

      if (step.children == undefined) {
        step.children = [];
      }

      step.children.push($scope.field_to_add);

      step.children = _.uniq(step.children, function(item){return JSON.stringify(item);});
    }
    
    $scope.template_field_keys = [];
    angular.forEach($scope.admin.fields, function (field, key) {
      if (field.is_template === true) {
        $scope.template_field_keys.push(field.id);
      }
    });

    $scope.get_field = function(field_key) {
      var selected_field = undefined;
      angular.forEach($scope.admin.fields, function (field, key) {
        if (field.id == field_key) {
          selected_field = field;
          return;
        }
      });
      return selected_field;
    }

    $scope.deleteStep = function(step) {
      var idx = _.indexOf($scope.context.steps, step);
      $scope.context.steps.splice(idx, 1);
    };

    $scope.deleteField = function(field) {
      var idx = _.indexOf($scope.step.children, field);
      $scope.step.children.splice(idx, 1);
    };
    
    var originalFields = $scope.template_field_keys.slice();
    $scope.sortableOptions = {
      connectWith: ".configuredFields",
      placeholder: "placeholder",
      stop: function (e, ui) {
        // if the element is removed from the first container
        if ($(e.target).hasClass('templateFieldAdder') &&
            ui.item.sortable.droptarget &&
            e.target != ui.item.sortable.droptarget[0]) {
          // clone the original model to restore the removed item
          $scope.template_field_keys = originalFields.slice();
        }
      }
    };

  }
]);
