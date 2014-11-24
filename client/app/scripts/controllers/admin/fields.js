GLClient.controller('AdminFieldsCtrl', ['$scope',
                    function($scope, $modal) {
    $scope.fields = $scope.admin.field_templates;

    $scope.save_all = function () {
      angular.forEach($scope.admin.fields, function (field, key) {
        $scope.update(fields);
      });
    };
    
    $scope.addField = function(field) {
      $scope.fields.push(new_field);
    };

    $scope.deleteField = function(field) {
      var idx = _.indexOf($scope.fields, field);
      $scope.fields.splice(idx, 1);
    };

    $scope.update_field = function(field) {
      var updated_field = new $scope.admin.field_template(field);
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
    $scope.save_field = function() {
      $scope.update($scope.field);
    };

    $scope.deleteDialog = function(field){
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

    $scope.toggle = function(field) {
      if ($scope.isSelected(field)) {
        delete $scope.field.children[field.id];
      } else {
        $scope.field.children[field.id] = field;
      }
      $scope.fieldForm.$dirty = true;
      $scope.fieldForm.$pristine = false;
    }

    $scope.filterSelf = function(field)
    {
      // avoid auto reference
      return $scope.field.id != field.id;
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
