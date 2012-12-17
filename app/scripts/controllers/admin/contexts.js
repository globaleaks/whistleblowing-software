GLClient.controller('AdminContextsCtrl', 
    ['$scope', 'localization', 'AdminContexts',
    function($scope, localization, AdminContexts) {

  $scope.new_context = function() {
    var context = new AdminContexts;
    //context.name[localization.selected_language] = $scope.new_context_name;

    context.name = $scope.new_context_name;
    context.description = '';

    context.fields = [];
    context.escalation_threshold =  42;
    context.file_max_download = 42;
    context.tip_max_access = 42;
    context.selectable_receiver = true;
    context.tip_timetolive = 42;

    context.$save(function(created_context){
      $scope.adminContexts.push(created_context);
    });
  }

  $scope.delete_context = function(context) {
    var idx = _.indexOf($scope.adminContexts, context);

    context.$delete();
    $scope.adminContexts.pop(idx);
  }

}]);
