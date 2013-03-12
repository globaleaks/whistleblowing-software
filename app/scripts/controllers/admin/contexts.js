GLClient.controller('AdminContextsCtrl',
    ['$scope', '$rootScope', 'Admin',
    function($scope, $rootScope, Admin) {

  $scope.delete = function(context) {
    var idx = _.indexOf($scope.admin.contexts, context);

    context.$delete(function(){
      $scope.admin.contexts.splice(idx, 1);
    });

  };

  $scope.addField = function(context) {
    if (context.fields === undefined) {
      context.fields = [];
    }
    context.fields.push({presentation_order: 0,
                        type: 'text',
                        required: false});
  }

}]);

GLClient.controller('AdminFieldEditorCtrl',
    ['$scope',
    function($scope) {
    $scope.editing = false;

    if ($scope.field.name === undefined) {
      $scope.editing = true;
    }

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

    $scope.deleteField = function(field) {
      var idx = $scope.context.fields.indexOf(field);
      $scope.context.fields.splice(idx, 1);
    }

}]);

GLClient.controller('AdminContextsEditorCtrl', ['$scope',
  function($scope) {
    $scope.editing = false;
    console.log($scope.context);
    if ($scope.context.description === "") {
      $scope.editing = true;
    }

    $scope.toggleEditing = function() {
      $scope.editing = $scope.editing ^ 1;
    }

}]);
