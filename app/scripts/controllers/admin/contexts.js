GLClient.controller('AdminContextsCtrl', 
    ['$scope', '$rootScope', 'localization', 'AdminContexts',
    function($scope, $rootScope, localization, AdminContexts) {

  $scope.new_context = function() {
    var context = new AdminContexts;
    //context.name[localization.selected_language] = $scope.new_context_name;

    context.name = $scope.new_context_name;
    context.description = '';

    context.fields = [];
    context.languages = [];
    context.receivers = [];

    context.escalation_threshold =  42;
    context.file_max_download = 42;
    context.tip_max_access = 42;
    context.selectable_receiver = true;
    context.tip_timetolive = 42;

    context.$save(function(created_context){
      $scope.adminContexts.push(created_context);
    });
  };

  $scope.editFields = function(fields) {
    // XXX this is *very* hackish. See #15 for a bug.
    $rootScope.fieldEditor = true;
    $rootScope.fieldsToEdit = fields;
  };

  $scope.delete_context = function(context) {
    var idx = _.indexOf($scope.adminContexts, context);

    context.$delete();
    $scope.adminContexts.splice(idx, 1);
  }

}]);
