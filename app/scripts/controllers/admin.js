GLClient.controller('AdminCtrl',
    ['$scope', '$http', '$location', 'localization', 'AdminNode',
    'AdminContexts', 'AdminReceivers',
    function($scope, $http, $location, localization, AdminNode, AdminContexts,
      AdminReceivers) {

  // XXX convert this to a directive
  // This is used for setting the current menu in the sidebar
  var current_menu = $location.path().split('/').slice(-1);
  $scope.active = {};
  $scope.active[current_menu] = "active";

  $scope.localization = localization;
  $scope.node_info = localization.node_info;

  $scope.adminNode = AdminNode.get();
  $scope.adminReceivers = AdminReceivers.query();

  $scope.new_receiver = function() {
    console.log("antani");
    var receiver = new AdminReceivers;
    receiver.notification_address = $scope.new_receiver_address;
    receiver.name = $scope.new_receiver_name;
    receiver.$save();
  }

}]);
