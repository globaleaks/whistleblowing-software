GLClient.controller('AdminContextsCtrl', ['$scope', 'localization',
                    'AdminContexts',
function($scope, localization, AdminContexts) {
  $scope.adminContexts = AdminContexts.query();

  $scope.new_context = function() {
    var context = new AdminContexts;
    context.name = {};
    context.name[localization.selected_language] = $scope.new_context_name;

    context.$save(function(created_context){
      $scope.adminContexts.push(created_context);
    });

  }

}]);
