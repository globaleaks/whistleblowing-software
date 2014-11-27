GLClient.controller('AdminFieldsCtrl', ['$scope', '$filter',
                    function($scope, $filter) {
    $scope.composable_fields = {};
    $scope.admin.field_templates.$promise
      .then(function(fields) {
        $scope.fields = fields;
        angular.forEach(fields, function(field_group, key) {
          $scope.composable_fields[field_group.id] = field_group;
          if (field_group.type == 'fieldgroup') {
            angular.forEach(field_group.children, function(field, key) {
              $scope.composable_fields[key] = field;
            });
          }
        });
      });

    $scope.toggle_field = function(field, field_group) {
      $scope.field_group_toggled = true;
      if (field_group.children && field_group.children[field.id]) {
        // Remove it from the fieldgroup 
        $scope.fields = $scope.fields || {};
        $scope.fields.push(field);
        $scope.composable_fields[field.id] = field;
        delete field_group.children[field.id];
      } else {
        // Add it to the fieldgroup 
        field_group.children = field_group.children || {};
        field_group.children[field.id] = field;
        $scope.composable_fields[field.id] = field;
        $scope.admin.field_templates = $filter('filter')($scope.admin.field_templates, 
                                                         {id: '!'+field.id}, true);
      }
    }

    $scope.save_all = function () {
      // XXX this is highly inefficient, could be refactored/improved.
      angular.forEach($scope.admin.field_templates, function (field, key) {
        $scope.update_field(field);
      });
    };
    
    $scope.addField = function(new_field) {
      $scope.fields.push(new_field);
    };

    $scope.deleteField = function(field) {
      var idx = _.indexOf($scope.fields, field);
      $scope.fields.splice(idx, 1);
    };

    $scope.update_field = function(field) {
      var updated_field = new $scope.admin.field_template(field);
      if ($scope.field_group_toggled) {
        $scope.field_group_toggled = false;
        $scope.save_all();
      }
      return updated_field.$update();
    }

    $scope.perform_delete = function(field) {
      $scope.admin.field_template.delete({
        template_id: field.id
      }, function(){
        $scope.deleteField(field);
      });
    }

    $scope.create_field = function() {
      return $scope.admin.new_template_field();
    };
  }
]);

GLClient.controller('AdminFieldsEditorCtrl', ['$scope',  '$modal',
  function($scope, $modal) {
    $scope.field_group_toggled = false;

    $scope.save_field = function() {
      $scope.update($scope.field);
    };

    $scope.fieldDeleteDialog = function(field){
      var modalInstance = $modal.open({
          templateUrl:  'views/partials/field_delete.html',
          controller: 'ConfirmableDialogCtrl',
          resolve: {
            object: function () {
              return field;
            }
          }

      });

      modalInstance.result.then(
         function(result) { $scope.perform_delete(result); },
         function(result) { }
      );
    };


    $scope.isSelected = function (field) {
      // XXX this very inefficient as it cycles infinitely on the f in
      // admin.fields | filter:filterSelf ng-repeat even when you are not using
      // a field group.
      if (!$scope.field.children) {
        return false; 
      }
      return Object.keys($scope.field.children).indexOf(field.id) !== -1;
    };

    function tokenize(input) {
      var result = input.replace(/[^-a-zA-Z0-9,&\s]+/ig, '');
      result = result.replace(/-/gi, "_");
      result = result.replace(/\s/gi, "-");
      return result;
    }

    $scope.typeSwitch = function (type) {
      if (_.indexOf(['checkbox', 'selectbox'], type) !== -1)
        return 'checkbox_or_selectbox';
      return type;
    };

    $scope.addOption = function (field) {
      field.options.push({});
    };

    $scope.$watch('field.type', function (newVal, oldVal) {

      if (newVal && newVal !== oldVal) {
        $scope.field.options = [];
      }

    });

  }
]);

GLClient.controller('AdminFieldsAddCtrl', ['$scope',
  function($scope) {

    $scope.new_field = {};

    $scope.add_field = function(label) {
      var field = new $scope.create_field();

      field.label = $scope.new_field.label;
      field.description = $scope.new_field.label;
      field.type = $scope.new_field.type;

      if (field.type == 'tos') {
        field.options.push({'attrs':
          {
            'clause': '',
            'agreemet_statement': ''
          }
        });
      }

      if (field.type == 'fileupload') {
        field.options.push({'attrs': {'require_description': false}});
      }

      field.$save(function(new_field){
        $scope.addField(new_field);
        $scope.new_field = {};
      });
    }
  }
]);
