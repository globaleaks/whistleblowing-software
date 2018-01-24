GLClient.controller('ReceiptController', ['$scope', 'Authentication',
  function($scope, Authentication) {
    var format_keycode = function(keycode) {
      if (!keycode || keycode.length !== 16) {
        return '';
      }

      return keycode.substr(0, 4) + ' ' +
             keycode.substr(4, 4) + ' ' +
             keycode.substr(8, 4) + ' ' +
             keycode.substr(12, 4);
    };

    $scope.keycode = Authentication.keycode;
    $scope.formatted_keycode = format_keycode($scope.keycode);
}]);
