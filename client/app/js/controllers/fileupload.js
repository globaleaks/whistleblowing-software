GL.factory("uploadUtils", ["$filter", function($filter) {
  // Utils shared across file upload controllers and directives

  return {
    "translateInvalidSizeErr": function(filename, maxSize) {
      var strs = ["File size not accepted.", "Maximum file size is:"];
      angular.forEach(strs, function(s, i) {
        strs[i] = $filter("translate")(s);
      });
      return strs[0] + " " + filename + " - " + strs[1] + " " + $filter("byteFmt")(maxSize, 2);
    },
  };
}]).
controller("RFileUploadCtrl", ["$scope", function($scope) {
  $scope.disabled = false;

  $scope.$on("flow::fileAdded", function (event, $flow, flowFile) {
    flowFile.pause();

    $scope.file_error_msgs = [];

    $scope.$emit("GL::uploadsUpdated");
  });
}]).
controller("WBFileUploadCtrl", ["$scope", function($scope) {
  $scope.file_upload_description = "";

  $scope.beginUpload = function($files, $event, $flow) {
    $scope.file_error_msgs = [];

    $flow.opts.query = {"description": $scope.file_upload_description};
    $flow.upload();
  };
}]).
controller("AudioUploadCtrl", ["$scope","flowFactory", function($scope, flowFactory) {
  var chunks = [];
  var mediaRecorder;
  var flow = flowFactory.create({ target: $scope.fileupload_url, query: { type: 'audio.webm' } });
  var startTime;

  $scope.audioPlayer = null;
  $scope.recordButton = false;
  $scope.stopButton = false;
  $scope.activeButton = null;

  $scope.startRecording = function() {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(function(stream) {
        chunks = [];
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.addEventListener('dataavailable', function(event) {
          chunks.push(event.data);
        });
        mediaRecorder.addEventListener('start', function() {
          startTime = Date.now();
        });
        mediaRecorder.addEventListener('stop', function() {
          var durationInSeconds = (Date.now() - startTime) / 1000;
          $scope.isRecordingTooShort = durationInSeconds < parseInt($scope.field.attrs.min_time.value);

          var blob = new Blob(chunks, { type: 'audio/webm' });
          chunks = [];
          $scope.audioPlayer = URL.createObjectURL(blob);
          $scope.$apply(function() {
            $scope.audioFile = blob;
            var file = new Flow.FlowFile(flow, {
              name: 'audio.webm',
              size: blob.size,
              relativePath: 'audio.webm'
            });
            file.file = blob;
            if(!$scope.isRecordingTooShort){
              flow.files.push(file);
            }

            if ($scope.uploads.hasOwnProperty($scope.fileinput)) {
              delete $scope.uploads[$scope.fileinput];
            }
            if(!$scope.isRecordingTooShort){
              $scope.uploads[$scope.fileinput] = flow
            }
          });
        });

        mediaRecorder.start();
        $scope.isRecording = true;
        $scope.recordButton = true;
        $scope.stopButton = false;
        $scope.activeButton = 'record';
      })
      .catch(function(err) {
        console.error('Error accessing microphone', err);
      });
    $scope.activeButton = 'record';
  };

  $scope.stopRecording = function() {
    if (mediaRecorder && (mediaRecorder.state === 'recording' || mediaRecorder.state === 'paused')) {
      mediaRecorder.stop();
      $scope.recordButton = false;
      $scope.stopButton = true;
      $scope.activeButton = null;

      var durationInSeconds = (Date.now() - startTime) / 1000;
      $scope.isRecordingTooShort = durationInSeconds < parseInt($scope.field.attrs.min_time.value);

      // Release microphone access
      var tracks = mediaRecorder.stream.getTracks();
      tracks.forEach(function(track) {
        track.stop();
      });

      setTimeout(function() {
        $scope.$apply(function() {
          $scope.isRecording = false;
        });
      }, 0);
    }
  };

  $scope.recordButton = false;

}]).
controller("ImageUploadCtrl", ["$http", "$scope", "$rootScope", "uploadUtils", "Utils", function($http, $scope, $rootScope, uploadUtils, Utils) {
  $scope.Utils = Utils;
  $scope.imageUploadObj = {};

  $scope.$on("flow::complete", function () {
    $scope.imageUploadModel[$scope.imageUploadModelAttr] = true;
  });

  $scope.deletePicture = function() {
    $http({
      method: "DELETE",
      url: "api/admin/files/" + $scope.imageUploadId,
    }).then(function() {
      if ($scope.imageUploadModel) {
        $scope.imageUploadModel[$scope.imageUploadModelAttr] = "";
      }
      $scope.imageUploadObj.flow.files = [];
    });
  };
}]);
