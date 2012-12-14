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
  $scope.adminContexts = AdminContexts.query();

  $scope.new_receiver = function() {
    var receiver = new AdminReceivers;
    receiver.notification_address = $scope.new_receiver_address;
    receiver.name = $scope.new_receiver_name;
    receiver.$save();
  }

  // XXX find a more elegant solution
  // This is required for the step by step wizard.
  $scope.steps = [
    '1 Content settings',
    '2 Notification and Delivery',
    '3 Review your settings'
  ];

}]);
