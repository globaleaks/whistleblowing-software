GLClient.controller('AdminFieldTemplatesCtrl', ['$scope', 'AdminFieldResource', 'AdminFieldTemplateResource',
  function($scope, AdminFieldResource, AdminFieldTemplateResource) {
    $scope.admin.fieldtemplates.$promise.then(function(fields) {
      $scope.fields = fields;
    });

    $scope.addField = function(new_field) {
      $scope.fields.push(new_field);
    };

    $scope.delField = function(fields, field) {
      AdminFieldTemplateResource['delete']({
        id: field.id
      }, function() {
        $scope.deleteFromList(fields, field);
      });
    };

    $scope.delAllFields = function() {
      angular.forEach($scope.fields, function(field) {
        $scope.delField($scope.fields, field);
      });
    };

    $scope.exportQuestionTemplates = function() {
      AdminFieldTemplateResource.query({export: true}).$promise.then(function(fields) {
        $scope.exportJSON(fields, 'question-templates.json');
      });
    };

    $scope.exportQuestion = function(id) {
      AdminFieldTemplateResource.get({export: true, id: id}).$promise.then(function(field) {
        $scope.exportJSON(field, 'question-' + id + '.json');
      });
    };

    $scope.importQuestions = function(fields) {
      var fields = JSON.parse(fields);

      if (Object.prototype.toString.call(fields) !== '[object Array]') {
        fields = [fields];
      }

      angular.forEach(fields, function(field) {
        var field = new AdminFieldTemplateResource(field);
        field.id = '';
        field.$save({import: true}, function(new_field) {
          $scope.reload();
        });

      });
    };
  }
]);

GLClient.controller('AdminFieldEditorCtrl', ['$scope',  '$modal', 'AdminFieldResource', 'AdminFieldTemplateResource',
  function($scope, $modal, AdminFieldResource, AdminFieldTemplateResource) {
    $scope.editable = $scope.field.instance != 'reference';
    $scope.editing = false;
    $scope.new_field = {};
    $scope.fields = $scope.field.children;

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
      if (['inputbox', 'textarea', 'checkbox', 'multichoice', 'tos'].indexOf(field.type) > -1) {
        return true;
      }

      if (field.instance == 'template' && (['whistleblower_identity'].indexOf(field.key) > -1)) {
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
        'activated_fields': [],
        'activated_steps': []
      };

      new_option.presentation_order = $scope.newItemOrder(field.options, 'presentation_order');

      field.options.push(new_option);
    };

    $scope.delOption = function(field, option) {
      var index = field.options.indexOf(option);
      field.options.splice(index, 1);
    };

    $scope.save_field = function(field) {
      $scope.assignUniqueOrderIndex(field.options);

      var updated_field;
      if (field.instance == 'template') {
        updated_field = new AdminFieldTemplateResource(field);
      } else {
        updated_field = new AdminFieldResource(field);
      }

      $scope.update(updated_field);
    };

    $scope.moveUpAndSave = function(elem) {
      $scope.moveUp(elem);
      $scope.save_field(elem);
    };

    $scope.moveDownAndSave = function(elem) {
      $scope.moveDown(elem);
      $scope.save_field(elem);
    };

    $scope.moveLeftAndSave = function(elem) {
      $scope.moveLeft(elem);
      $scope.save_field(elem);
    };

    $scope.moveRightAndSave = function(elem) {
      $scope.moveRight(elem);
      $scope.save_field(elem);
    };

    $scope.add_field = function() {
      var field = $scope.admin.new_field('', $scope.field.id);
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
      var field = $scope.admin.new_field_from_template(template_id, '', $scope.field.id);

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
  }
]);

GLClient.controller('AdminFieldTemplatesAddCtrl', ['$scope',
  function($scope) {
    $scope.new_field = {};

    $scope.add_field = function() {
      var field = $scope.admin.new_field_template($scope.field ? $scope.field.id : '');
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
