GLClient.controller('AdminCtrl',
    ['$scope', '$http', 'AdminNode',
    'AdminContexts', 'AdminReceivers',
    'HelpStrings',
    function($scope, $http, AdminNode, AdminContexts,
      AdminReceivers, HelpStrings) {

  // XXX when the API has been extended we can remove this
  // hackish callback
  scope.loading = true;
  $scope.node_info = AdminNode.get(function() {
    scope.loading = true;
    // XXX I need in the API of the admin to get back the list of languages that
    // it supports.
    // The language code should follow:
    // http://en.wikipedia.org/wiki/ISO_639-1
    $scope.node_info.available_languages = [{'name': 'English', 'code': 'en'}, 
      {'name': 'Italiano', 'code': 'it'}];
    $scope.selected_language = $scope.node_info.available_languages[1].code;

    // XXX I need this in the API
    $scope.node_info.admin_email = 'me@example.com';

    $scope.help_strings = {};
    $scope.all_help_strings = HelpStrings.get(function() {
      $scope.help_strings.name =  $scope.all_help_strings.name[$scope.selected_language];
    });

  });

}]);
