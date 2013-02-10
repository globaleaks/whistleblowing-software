GLClient.controller('AdminContextsCtrl',
    ['$scope', '$rootScope', 'AdminContexts',
    function($scope, $rootScope, AdminContexts) {

  $scope.new_context = function() {
    var context = new AdminContexts;

    context.name = $scope.new_context_name;
    context.description = '';

    context.fields = [];
    context.languages = [];
    context.receivers = [];

    context.escalation_threshold = null;
    context.file_max_download = 42;
    context.tip_max_access = 42;
    context.selectable_receiver = true;
    context.tip_timetolive = 42;

    context.$save(function(created_context){
      $scope.adminContexts.push(created_context);
    });
  };

  // XXX this is *very* hackish.
  $scope.editFields = function(fields) {
    $rootScope.fieldEditor = true;
    $rootScope.fieldsToEdit = fields;
  };

  $rootScope.closeEditor = function() {
    $rootScope.fieldEditor = false;
  };

  $scope.delete_context = function(context) {
    var idx = _.indexOf($scope.adminContexts, context);

    context.$delete(function(){
      $scope.adminContexts.splice(idx, 1);
    });

  };

}]);
