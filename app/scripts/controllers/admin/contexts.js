GLClient.controller('AdminContextsCtrl',
    ['$scope', '$rootScope', 'Admin',
    function($scope, $rootScope, Admin) {

  // XXX this is *very* hackish.
  $scope.editFields = function(fields) {
    $rootScope.fieldEditor = true;
    $rootScope.fieldsToEdit = fields;
  };

  $rootScope.closeEditor = function() {
    $rootScope.fieldEditor = false;
  };

  $scope.delete = function(context) {
    var idx = _.indexOf($scope.admin.contexts, context);

    context.$delete(function(){
      $scope.admin.contexts.splice(idx, 1);
    });

  };
}]);

GLClient.controller('AdminFieldEditorCtrl',
    ['$scope',
    function($scope) {
    $scope.editing = false;

    $scope.typeSwitch = function(type) {
      if (_.indexOf(['checkboxes','select','radio'], type) === -1)
        return type;
      return 'multiple';
    }

    $scope.addOption = function(field) {
      if (field.options === undefined) {
        field.options = [];
      }
      field.options.push({order: 0})
    }

}]);


