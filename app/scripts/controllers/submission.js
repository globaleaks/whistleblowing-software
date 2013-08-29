GLClient.controller('SubmissionCtrl', ['$scope', '$rootScope', '$location', 'Node',
    'Submission', 'Receivers', 'WhistleblowerTip', function($scope, $rootScope,
      $location, Node, Submission, Receivers, WhistleblowerTip) {

  var checkReceiverSelected = function() {
    $scope.receiver_selected = false;
    // Check if there is at least one selected receiver
    angular.forEach($scope.submission.receivers_selected, function(receiver) {
      $scope.receiver_selected = $scope.receiver_selected | receiver;
    });

  }
  
  $rootScope.invalidForm = true;
  $scope.receiptConfimation = "";

  Node.get(function(node_info){
    $scope.node_info = node_info;

    new Submission(function(submission){
      $scope.maximumFilesize = submission.maximum_filesize;

      $scope.current_context = submission.current_context;

      $scope.submission = submission;
      $scope.submit = $scope.submission.submit;

      checkReceiverSelected();

    });

  });


  $scope.view_tip = function(receipt) {
    if ($scope.receiptConfirmation != receipt)
      return;

    WhistleblowerTip(receipt, function(tip_id){
      $location.path('/status/' + tip_id);
    });
  };

  $scope.uploading = false;

  $scope.disclaimer = {accepted: false};
  $scope.steps = [
    '1',
    '2',
    '3'
  ];

  // Watch for changes in certain variables
  $scope.$watch('submission.current_context', function(){
    if ($scope.current_context) {
      $scope.submission.create(function(){
        var url = '/submission/' + $scope.submission.current_submission.submission_gus + '/file',
          headers = {};
        if ($.cookie('session_id')) {
          headers['X-Session'] = $.cookie('session_id');
        };

        if ($.cookie('XSRF-TOKEN')) {
          headers['X-XSRF-TOKEN'] = $.cookie('XSRF-TOKEN');
        }

        if ($.cookie('language')) {
          headers['GL-Language'] = $.cookie('language');
        };
        
        $scope.queue = [];
        $scope.options = {
          url: url,
          multipart: false,
          headers: headers,
          autoUpload: true,
        };
        
      });
      checkReceiverSelected();

    }
  }, false);

  $scope.$watch('receivers_selected', function() {
    if ($scope.receivers_selected) {
      checkReceiverSelected();
    }
  }, true);

  $scope.$watch('queue', function(){
    $scope.uploading = false;
    if ($scope.queue) {
      $scope.queue.forEach(function(k){
        if (!k.id)
          $scope.uploading = true;
      });
    }
  }, true);

}]).
  controller('SubmissionFormController', ['$scope', '$rootScope', function($scope, $rootScope){
    $scope.$watch('submissionForm.$valid', function() {
      $rootScope.invalidForm = $scope.submissionForm.$invalid;
    }, true);
}])

angular.module('GLClient.fileuploader', ['blueimp.fileupload'])
  .config(['$httpProvider', 'fileUploadProvider',
    function ($httpProvider, fileUploadProvider) {
      delete $httpProvider.defaults.headers.common['X-Requested-With'];
      angular.extend(fileUploadProvider.defaults, {
        multipart: false,
        maxFileSize: 5000000,
      });
    }
])
  .controller('FileDestroyController', [
            '$scope', '$http',
    function ($scope, $http) {
      var file = $scope.file,
      state;
      if (file.url) {
        file.$state = function () {
          return state;
        };
        file.$destroy = function () {
          state = 'pending';
          return $http({
            url: file.deleteUrl,
            method: file.deleteType
          }).then(
          function () {
            state = 'resolved';
            $scope.clear(file);
          },
          function () {
            state = 'rejected';
          }
          );
        };
      } else if (!file.$cancel && !file._index) {
        file.$cancel = function () {
          $scope.clear(file);
        };
      }
    }
]);
