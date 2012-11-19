GLClient.controller('AdminCtrl',
    ['$scope', '$http', 'localization', 'AdminNode',
    'AdminContexts', 'AdminReceivers', 'HelpStrings',
    function($scope, $http, localization, AdminNode, AdminContexts,
      AdminReceivers, HelpStrings) {

  $scope.localization = localization;
  $scope.node_info = localization.node_info;

  $scope.adminNode = new AdminNode();
  $scope.adminNode.$get();
  
  //$scope.node_info.admin_email = 'me@example.com';

  //$scope.help_strings = {};

  //$scope.all_help_strings = HelpStrings.get(function() {
  //  $scope.help_strings.name =  $scope.all_help_strings.name[$scope.selected_language];
  //});

}]);
