GLClient.controller('AdminStepAddCtrl', ['$scope',
  function($scope) {
    $scope.new_step = {};

    $scope.add_step = function() {
      var step = new $scope.admin_utils.new_step($scope.questionnaire.id);
      step.label = $scope.new_step.label;
      step.presentation_order = $scope.newItemOrder($scope.questionnaire.steps, 'presentation_order');

      step.$save(function(new_step){
        $scope.questionnaire.steps.push(new_step);
        $scope.new_step = {};
      });
    };
  }
]).
controller('AdminStepEditorCtrl', ['$scope', '$rootScope', '$http', 'Utils', 'AdminStepResource', 'AdminFieldResource',
  function($scope, $rootScope, $http, Utils, AdminStepResource, AdminFieldResource) {
    $scope.editing = false;
    $scope.new_field = {};
    $scope.fields = $scope.step.children;
    $scope.fieldResource = AdminFieldResource;

    $scope.toggleEditing = function () {
      $scope.editing = $scope.editing ^ 1;
    };

    $scope.save_step = function(step) {
      var updated_step = new AdminStepResource(step);
      return Utils.update(updated_step);
    };

    $scope.showAddQuestion = false;
    $scope.toggleAddQuestion= function() {
      $scope.showAddQuestion = !$scope.showAddQuestion;
    };

    $scope.showAddQuestionFromTemplate = false;
    $scope.toggleAddQuestionFromTemplate = function() {
      $scope.showAddQuestionFromTemplate = !$scope.showAddQuestionFromTemplate;
    };

    $scope.addField = function(field) {
      $scope.fields.push(field);
    };

    $scope.delField = function(field) {
      return Utils.deleteResource($scope.fieldResource, $scope.fields, field);
    };

    $scope.add_field = function() {
      var field = $scope.admin_utils.new_field($scope.step.id, '');
      field.label = $scope.new_field.label;
      field.type = $scope.new_field.type;
      field.attrs = $scope.admin.get_field_attrs(field.type);
      field.y = $scope.newItemOrder($scope.fields, 'y');

      if (field.type === 'fileupload') {
        field.multi_entry = true;
      }

      field.$save(function(new_field){
        $scope.addField(new_field);
        $scope.new_field = {};
      });
    };

    $scope.add_field_from_template = function(template_id) {
      var field = $scope.admin_utils.new_field_from_template(template_id, $scope.step.id, '');
      field.y = $scope.newItemOrder($scope.fields, 'y');

      field.$save(function(new_field) {
        $scope.fields.push(new_field);
      });
    };

    $scope.moveUp = function(e, idx) { swap(e, idx, -1); };
    $scope.moveDown = function(e, idx) { swap(e, idx, 1); };

    function swap($event, index, n) {
      $event.stopPropagation();

      var target = index + n;
      if (target < 0 || target >= $scope.questionnaire.steps.length) {
        return;
      }

      var a = $scope.questionnaire.steps[target];
      var b = $scope.questionnaire.steps[index];
      $scope.questionnaire.steps[target] = b;
      $scope.questionnaire.steps[index] = a;

      $http({
        method: 'PUT',
        url: '/admin/steps',
        data: {
          'operation': 'order_elements',
          'args': {
            'ids': $scope.questionnaire.steps.map(function(s) { return s.id; }),
            'questionnaire_id': $scope.questionnaire.id,
           },
        },
      }).then(function() {
        $rootScope.successes.push({});
      });
    }
  }
]);
