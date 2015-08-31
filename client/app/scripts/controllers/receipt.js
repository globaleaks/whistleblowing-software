GLClient.controller('ReceiptController', ['$scope', '$location', 'Authentication',
  function($scope, $location, Authentication) {
    var format_keycode = function(keycode) {
      var ret = keycode;
      if (keycode && keycode.length === 16) {
        ret =  keycode.substr(0, 4) + ' ' +
               keycode.substr(4, 4) + ' ' +
               keycode.substr(8, 4) + ' ' +
               keycode.substr(12, 4);
      }

      return ret;

    };

    $scope.keycode = format_keycode(Authentication.keycode);
    $scope.formatted_keycode = format_keycode($scope.keycode);
}]);
