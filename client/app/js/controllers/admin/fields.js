GLClient.controller('AdminFieldTemplatesCtrl', ['$scope', 'AdminFieldResource', 'AdminFieldTemplateResource',
  function($scope, AdminFieldResource, AdminFieldTemplateResource) {
    $scope.admin.fieldtemplates.$promise.then(function(fields) {
      $scope.fields = fields;
    });

    $scope.addField = function(new_field) {
      $scope.fields.push(new_field);
    };

    $scope.delField = function(fields, field) {
      AdminFieldTemplateResource.delete({
        id: field.id
      }, function() {
        $scope.Utils.deleteFromList(fields, field);
      });
    };
  }
]).
controller('AdminFieldEditorCtrl', ['$scope', '$filter', '$uibModal', 'AdminFieldResource', 'AdminFieldTemplateResource',
  function($scope, $filter, $uibModal, AdminFieldResource, AdminFieldTemplateResource) {
    $scope.editable = $scope.field.editable && $scope.field.instance !== 'reference';
    $scope.editing = false;
    $scope.new_field = {};
    $scope.fields = $scope.field.children;

    $scope.siblings = $filter('filter')($scope.siblings, {'id': '!' + $scope.field.id});

    $scope.toggleEditing = function () {
      $scope.editing = !$scope.editing;
    };

    $scope.isMarkableRequired = function(field) {
      return (['fieldgroup', 'fileupload'].indexOf(field.type) === -1);
    };

    $scope.isMarkableMultiEntry = function(field) {
      return (['checkbox', 'selectbox', 'tos'].indexOf(field.type) === -1);
    };

    $scope.isMarkableSubjectToStats = function(field) {
      return (['inputbox', 'textarea', 'fieldgroup'].indexOf(field.type) === -1);
    };

    $scope.isMarkableSubjectToPreview = function(field) {
      return (['fieldgroup', 'fileupload'].indexOf(field.type) === -1);
    };

    $scope.typeSwitch = function (type) {
      if (['inputbox', 'textarea'].indexOf(type) !== -1) {
        return 'inputbox_or_textarea';
      }

      if (['checkbox', 'selectbox', 'multichoice'].indexOf(type) !== -1) {
        return 'checkbox_selectbox_multichoice';
      }

      return type;
    };

    $scope.showConfiguration = function(field) {
      if (['inputbox', 'textarea', 'checkbox', 'multichoice', 'tos', 'date'].indexOf(field.type) > -1) {
        return true;
      }

      if (field.instance === 'template' && (['whistleblower_identity'].indexOf(field.id) > -1)) {
        return true;
      }

      return false;
    };

    $scope.showOptions = function(field) {
      if (['checkbox', 'selectbox', 'multichoice'].indexOf(field.type) > -1) {
        return true;
      }

      return false;
    };

    $scope.addField = function(field) {
      $scope.field.children.push(field);
    };

    $scope.addOption = function (field) {
      var new_option = {
        'id': '',
        'label': '',
        'score_points': 0,
        'trigger_field': '',
        'trigger_step': ''
      };

      new_option.presentation_order = $scope.newItemOrder(field.options, 'presentation_order');

      field.options.push(new_option);
    };

    $scope.delOption = function(field, option) {
      var index = field.options.indexOf(option);
      field.options.splice(index, 1);
    };

    $scope.save_field = function(field) {
      var updated_field;

      $scope.Utils.assignUniqueOrderIndex(field.options);

      if (field.instance === 'template') {
        updated_field = new AdminFieldTemplateResource(field);
      } else {
        updated_field = new AdminFieldResource(field);
      }

      $scope.Utils.update(updated_field);
    };

    $scope.moveUpAndSave = function(elem) {
      $scope.Utils.moveUp(elem);
      $scope.save_field(elem);
    };

    $scope.moveDownAndSave = function(elem) {
      $scope.Utils.moveDown(elem);
      $scope.save_field(elem);
    };

    $scope.moveLeftAndSave = function(elem) {
      $scope.Utils.moveLeft(elem);
      $scope.save_field(elem);
    };

    $scope.moveRightAndSave = function(elem) {
      $scope.Utils.moveRight(elem);
      $scope.save_field(elem);
    };

    $scope.add_field = function() {
      var field = $scope.admin_utils.new_field('', $scope.field.id);
      field.label = $scope.new_field.label;
      field.type = $scope.new_field.type;
      field.attrs = $scope.admin.get_field_attrs(field.type);
      field.y = $scope.newItemOrder($scope.field.children, 'y');

      field.instance = $scope.field.instance;

      if (field.type === 'fileupload') {
        field.multi_entry = true;
      }

      field.$save(function(new_field){
        $scope.addField(new_field);
        $scope.new_field = {};
      });
    };

    $scope.add_field_from_template = function(template_id) {
      var field = $scope.admin_utils.new_field_from_template(template_id, '', $scope.field.id);

      if ($scope.$parent.field) {
        field.y = $scope.newItemOrder($scope.$parent.field.children, 'y');
      } else {
        field.y = $scope.newItemOrder($scope.step.children, 'y');
      }

      field.$save(function(new_field){
        $scope.field.children.push(new_field);
      });
    };

    $scope.fieldIsMarkableRequired = $scope.isMarkableRequired($scope.field);
    $scope.fieldIsMarkableMultiEntry = $scope.isMarkableMultiEntry($scope.field);
    $scope.fieldIsMarkableSubjectToStats = $scope.isMarkableSubjectToStats($scope.field);
    $scope.fieldIsMarkableSubjectToPreview = $scope.isMarkableSubjectToPreview($scope.field);

    $scope.triggerFieldDialog = function(option) {

      $scope.all_fields = []
      if (angular.isDefined($scope.questionnaire.steps)) {
        $scope.questionnaire.steps.forEach(function(step) {
          step.children.forEach(function(f) {
            $scope.all_fields.push(f);
            $scope.all_fields = $scope.all_fields.concat(enumerateChildren(f));
          });
        });
      }

      function enumerateChildren(field) {
        var c = [];
        if (angular.isDefined(field.children)) {
          field.children.forEach(function(field) {
            c.push(field);
            c = c.concat(enumerateChildren(field));
          });
        }
        return c;
      }

      return $scope.Utils.openConfirmableModalDialog('views/partials/trigger_field.html', option, $scope);
    };

    $scope.triggerStepDialog = function(option) {
      return $scope.Utils.openConfirmableModalDialog('views/partials/trigger_step.html', option, $scope);
    };

    $scope.assignScorePointsDialog = function(option) {
      return $scope.Utils.openConfirmableModalDialog('views/partials/assign_score_points.html', option, $scope);
    };
  }
]).
controller('AdminFieldTemplatesAddCtrl', ['$scope',
  function($scope) {
    $scope.new_field = {};

    $scope.add_field = function() {
      var field = $scope.admin_utils.new_field_template($scope.field ? $scope.field.id : '');
      field.instance = 'template';
      field.label = $scope.new_field.label;
      field.type = $scope.new_field.type;
      field.attrs = $scope.admin.get_field_attrs(field.type);

      field.$save(function(new_field){
        $scope.addField(new_field);
        $scope.new_field = {};
      });
    };
  }
]);
