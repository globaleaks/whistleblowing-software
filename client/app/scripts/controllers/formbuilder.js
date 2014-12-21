GLClient.controller('FormBuilderCtrl',
    ['$scope', '$rootScope', function ($scope, $rootScope) {

  $scope.newField = {};
  $scope.newField.required = false;
  $scope.newField.type = 'text';
  // XXX implement the presentation order of the submission fields
  $scope.newField.presentation_order = 0;

  $scope.editing = false;
  $scope.tokenize = function(slug1, slug2) {
    var result = slug1;
    result = result.replace(/[^-a-zA-Z0-9,&\s]+/ig, '');
    result = result.replace(/-/gi, "_");
    result = result.replace(/\s/gi, "-");
    if (slug2) {
      result += '-' + $scope.token(slug2);
    }
    return result;
  };

  $scope.saveField = function() {
    if ($scope.newField.type == 'checkboxes') {
      $scope.newField.value = {};
    }
    if ($scope.editing !== false) {
      $rootScope.fieldsToEdit[$scope.editing] = $scope.newField;
      $scope.editing = false;
    } else {
      $rootScope.fieldsToEdit.push($scope.newField);
    }
    $scope.newField = { order: 0 };
  };

  $scope.editField = function(field) {
    $scope.editing = $rootScope.fieldsToEdit.indexOf(field);
    $scope.newField = field;
  };

  $scope.deleteField = function(field) {
    $rootScope.fieldsToEdit.pop(field);
  };

  $scope.splice = function(field, fields) {
    fields.splice(fields.indexOf(field), 1);
  };

  $scope.addOption = function() {
    if ($scope.newField.options === undefined) {
      $scope.newField.options = [];
    }
    $scope.newField.options.push({ order: 0 });
  };

  $scope.typeSwitch = function (type) {
    if (_.indexOf(['checkbox', 'selectbox'], type) !== -1)
      return 'checkbox_or_selectbox';
    return type;
  };

}]);
