GLClient.controller('AdminFieldEditorCtrl', ['$scope', '$uibModal', 'Utils',
  function($scope, $uibModal, Utils) {
    $scope.editing = false;
    $scope.new_field = {};

    if ($scope.children) {
      $scope.fields = $scope.children;
    }

    $scope.children = $scope.field.children;

    $scope.toggleEditing = function () {
      $scope.editing = !$scope.editing;
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
      if (['inputbox', 'textarea', 'checkbox', 'multichoice', 'selectbox', 'tos', 'date'].indexOf(field.type) > -1) {
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

    $scope.addField = function(new_field) {
      $scope.field.children.push(new_field);
    };

    $scope.delField = function(field) {
      return Utils.deleteResource($scope.fieldResource, $scope.fields, field);

    $scope.showAddQuestion = false;
    $scope.toggleAddQuestion= function() {
      $scope.showAddQuestion = !$scope.showAddQuestion;
    };

    $scope.showAddQuestionFromTemplate = false;
    $scope.toggleAddQuestionFromTemplate = function() {
      $scope.showAddQuestionFromTemplate = !$scope.showAddQuestionFromTemplate;
    };

    $scope.addOption = function () {
      var new_option = {
        'id': '',
        'label': '',
        'score_points': 0,
        'trigger_field': ''
      };

      new_option.presentation_order = $scope.newItemOrder($scope.field.options, 'presentation_order');

      $scope.field.options.push(new_option);
    };

    $scope.moveOptionUp = function(idx) { swapOption(idx, -1); };
    $scope.moveOptionDown = function(idx) { swapOption(idx, 1); };

    function swapOption(index, n) {
      var target = index + n;
      if (target < 0 || target >= $scope.field.options.length) {
        return;
      }
      var a = $scope.field.options[target];
      var b = $scope.field.options[index];
      $scope.field.options[target] = b;
      $scope.field.options[index] = a;
    }

    $scope.delOption = function(option) {
      $scope.field.options.splice($scope.field.options.indexOf(option), 1);
    };

    $scope.save_field = function(field) {
      var updated_field;

      Utils.assignUniqueOrderIndex(field.options);

      updated_field = new $scope.fieldResource(field);

      Utils.update(updated_field);
    };

    $scope.moveUpAndSave = function(elem) {
      Utils.moveUp(elem);
      $scope.save_field(elem);
    };

    $scope.moveDownAndSave = function(elem) {
      Utils.moveDown(elem);
      $scope.save_field(elem);
    };

    $scope.moveLeftAndSave = function(elem) {
      Utils.moveLeft(elem);
      $scope.save_field(elem);
    };

    $scope.moveRightAndSave = function(elem) {
      Utils.moveRight(elem);
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

    $scope.fieldIsMarkableMultiEntry = $scope.isMarkableMultiEntry($scope.field);
    $scope.fieldIsMarkableSubjectToStats = $scope.isMarkableSubjectToStats($scope.field);
    $scope.fieldIsMarkableSubjectToPreview = $scope.isMarkableSubjectToPreview($scope.field);

    function findParents(field_id, field_lst) {
       for (var i = 0; i < field_lst.length; i++) {
         var field = field_lst[i];
         var pot = [field.id].concat(findParents(field_id, field.children));
         if (pot.indexOf(field_id) > -1) {
            return pot;
         }
       }
       return [];
    }

    $scope.triggerFieldDialog = function(option) {
      var t = [];
      $scope.questionnaire.steps.forEach(function(step) {
        step.children.forEach(function(f) {
          t.push(f);
          t = t.concat(enumerateChildren(f));
        });
      });

      var direct_parents = findParents($scope.field.id, $scope.step.children);
      $scope.all_fields = t.filter(function(f) { return direct_parents.indexOf(f.id) < 0; })

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

      return Utils.openConfirmableModalDialog('views/partials/trigger_field.html', option, $scope);
    };

    $scope.assignScorePointsDialog = function(option) {
      return Utils.openConfirmableModalDialog('views/partials/assign_score_points.html', option, $scope);
    };
  }
]).
controller('AdminFieldTemplatesCtrl', ['$scope', 'Utils', 'AdminFieldTemplateResource',
  function($scope, Utils, AdminFieldTemplateResource) {
    $scope.fieldResource = AdminFieldTemplateResource;

    $scope.admin.fieldtemplates.$promise.then(function(fields) {
      $scope.fields = fields;
    });

    $scope.addField = function(new_field) {
      $scope.fields.push(new_field);
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
