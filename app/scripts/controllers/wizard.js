GLClient.controller('WizardCtrl', ['$scope', 'Node',
  function($scope, Node) {

    Node.get(function(node){
      $scope.node = node;
    });

  }
]);
