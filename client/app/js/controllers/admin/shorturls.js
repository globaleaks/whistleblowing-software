GLClient.controller('AdminShorturlAddCtrl', ['$scope', function($scope) {
    $scope.dummy_new_shorturl = {
      'shorturl': '/s/',
      'longurl': '/'
    };

    $scope.new_shorturl = angular.copy($scope.dummy_new_shorturl);

    $scope.add_shorturl = function() {
      var shorturl = new $scope.admin.new_shorturl();

      shorturl.shorturl = $scope.new_shorturl.shorturl;
      shorturl.longurl = $scope.new_shorturl.longurl;

      shorturl.$save(function(new_shorturl){
        $scope.admin.shorturls.push(new_shorturl);
        $scope.new_shorturl = angular.copy($scope.dummy_new_shorturl);
      });
    };
}]);

GLClient.controller('AdminShorturlEditCtrl', ['$scope', 'AdminShorturlResource',
  function($scope, AdminShorturlResource) {
    $scope.delete_shorturl = function(shorturl) {
      AdminShorturlResource['delete']({
        id: shorturl.id
      }, function(){
        var idx = $scope.admin.shorturls.indexOf(shorturl);
        $scope.admin.shorturls.splice(idx, 1);
      });
    };
}]);
