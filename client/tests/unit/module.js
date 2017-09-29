angular.module('GLUnitTest', ['GLClient', 'GLBrowserCrypto']).
factory('TestEnv', ['$q', '$timeout', function($q, $timeout) {
    return {
      asyncPromiseTimeout: function() {
        var defer = $q.defer();
        $timeout(function() {
          defer.resolve(true);
        }, 500);
        return defer.promise;
      },

      asyncPromiseTimeoutErr: function() {
        var defer = $q.defer();
        $timeout(function() {
          defer.reject(false);
        }, 500);
        return defer.promise;
      },

      syncPromise: function() {
        var defer = $q.defer();
        defer.resolve(true);
        return defer.promise;
      },

      syncPromiseErr: function() {
        var defer = $q.defer();
        defer.reject(false);
        return defer.promise;
      },
    };
}]);
