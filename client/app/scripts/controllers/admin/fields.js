GLClient.controller('AdminFieldTemplatesCtrl', ['$scope', function($scope) {
    $scope.admin.field_templates.$promise.then(function(fields) {
      $scope.fields = fields;
    });

    $scope.deleteFromList = function(list, elem) {
      var idx = list.indexOf(elem);
      if (idx !== -1) {
        list.splice(idx, 1);
      }
    };

    $scope.addField = function(new_field) {
      $scope.fields.push(new_field);
    };

    $scope.delField = function(field) {
      $scope.admin.fieldtemplate['delete']({
        id: field.id
      }, function() {
        $scope.fields.splice($scope.fields.indexOf(field), 1);
      });
    };

    $scope.delAllFields = function() {
      angular.forEach($scope.fields, function(field) {
        $scope.delField(field);
      });
    };

    $scope.save_field = function(field) {
      $scope.assignUniqueOrderIndex(field.options);

      var updated_field;
      if (field.instance == 'template') {
        updated_field = new $scope.admin.fieldtemplate(field);
      } else {
        updated_field = new $scope.admin.field(field);
      }

      $scope.update(updated_field);
    };

    $scope.exportQuestions = function() {
      AdminFieldTemplatesResource.query().$promise.then(function(fields) {
        $scope.exportJSON(fields);
      });
    };

    $scope.importQuestions = function(fields) {
      var fields = JSON.parse(fields);
      if(Object.prototype.toString.call(fields) !== '[object Array]') {
        fields = [fields];
      }

      angular.forEach(fields, function(field) {
        var field = new $scope.admin.fieldtemplate(field);
        delete field.id;
        field.$save(function(new_field){
          $scope.fields.push(new_field);
        });

      });
    };
  }
]);

GLClient.controller('AdminFieldEditorCtrl', ['$scope',  '$modal',
  function($scope, $modal) {
    $scope.editable = $scope.field.instance != 'reference';
    $scope.editing = false;

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

      if (['checkbox', 'selectbox'].indexOf(type) !== -1) {
        return 'checkbox_or_selectbox';
      }

      return type;
    };

    $scope.shouldShowOptions = function(field) {
      if (['inputbox', 'textarea', 'selectbox', 'checkbox', 'tos'].indexOf(field.type) > -1) {
        return true;
      } else {
        return false;
      }
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

    $scope.new_field = {};

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
