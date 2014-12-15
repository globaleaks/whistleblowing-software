GLClient.controller('PrivacyBadgeBoxCtrl',
  ['$scope', '$http', '$rootScope',
  function($scope, $http, $rootScope) {

    var TBB_UAS = [
      "Mozilla/5.0 (Windows NT 6.1; rv:10.0) Gecko/20100101 Firefox/10.0",
      "Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0",
      "Mozilla/5.0 (Windows NT 6.1; rv:24.0) Gecko/20100101 Firefox/24.0",
      "Mozilla/5.0 (Windows NT 6.1; rv:31.0) Gecko/20100101 Firefox/31.0"
    ]

    function is_likely_tor_browser() {
      return TBB_UAS.indexOf(window.navigator.userAgent) > -1
        && (window.navigator.mimeTypes && window.navigator.mimeTypes.length === 0);
    }

    $scope.showBox = function () {
      $scope.displayBox = true;
      $scope.boxes = 'open';
    };

    $scope.hideBox = function() {
      $scope.displayBox = false;
      $scope.boxes = 'closed';
    }

    $scope.displayBox = true;
    $scope.boxes = 'open';

    /** XXX we are making the *strong* assumption that the GlobaLeaks instances
     *  will only be served as a Tor Hidden Service.
     *  If the address bar contains a hidden service address we consider the
     *  user to be over Tor.
     *  We can make this assumption because globaleaks is to be deployed with in
     *  front of it a tor2web instance (public or private) that will
     *  automatically redirect to the .onion address if it detectes that the
     *  client is coming from Tor.
     **/

    if (window.location.hostname.match(/^[a-z0-9]{16}\.onion$/)) {
      $rootScope.anonymous = true;
      if (is_likely_tor_browser()) {
        $rootScope.privacy = 'high';
      } else {
        $rootScope.privacy = 'medium';
      }
    } else {
      $rootScope.anonymous = false;
      $rootScope.privacy = 'low';
    }
}]);
