GLClient.controller('AdminContextsCtrl',
    ['$scope', '$rootScope', 'Admin',
    function($scope, $rootScope, Admin) {

  $scope.new_context = Admin.create_context;

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
