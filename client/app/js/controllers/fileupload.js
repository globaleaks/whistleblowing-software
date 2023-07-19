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
}])
.controller("AudioUploadCtrl", ["$scope", "flowFactory", function($scope, flowFactory) {
  var mediaRecorder;
  var flow;
  var startTime;

  $scope.isRecording = false;

  function onDataAvailable(event) {
    chunks.push(event.data);
  }

  function onStart() {
    startTime = Date.now();
  }

  function onStop() {
    var blob = new Blob(chunks, { type: 'audio/webm' });
    chunks = [];
    $scope.audioPlayer = URL.createObjectURL(blob);
    $scope.$apply(function() {
      var durationInSeconds = (Date.now() - startTime) / 1000;
      $scope.isRecordingTooShort = durationInSeconds < parseInt($scope.field.attrs.min_time.value);
      $scope.isRecordingTooLong = ($scope.field.attrs.max_time.value>0 && durationInSeconds > parseInt($scope.field.attrs.max_time.value)) || durationInSeconds > 180;
      $scope.audioFile = blob;
      if (!$scope.isRecordingTooShort && !$scope.isRecordingTooLong) {
        var file = new Flow.FlowFile(flow, {
          name: 'audio.webm',
          size: blob.size,
          relativePath: 'audio.webm'
        });
        file.file = blob;
        flow.files.push(file);
        if ($scope.uploads.hasOwnProperty($scope.fileinput)) {
          delete $scope.uploads[$scope.fileinput];
        }
        $scope.uploads[$scope.fileinput] = flow;
      } else {
        $scope.audioPlayer = null;
      }
    });
  }

  $scope.startRecording = function(fileId) {
    flow = flowFactory.create({
      target: $scope.fileupload_url,
      query: {
        type: 'audio.webm',
        reference: fileId
      }
    });
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(function(stream) {
        chunks = [];
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.addEventListener('dataavailable', onDataAvailable);
        mediaRecorder.addEventListener('start', onStart);
        mediaRecorder.addEventListener('stop', onStop);

        mediaRecorder.start();
      })
      .catch(function(err) {
        console.error('Error accessing microphone', err);
      });
  };

  $scope.stopRecording = function() {
    if (mediaRecorder && (mediaRecorder.state === 'recording' || mediaRecorder.state === 'paused')) {
      mediaRecorder.stop();
      $scope.isRecording = false;

      var tracks = mediaRecorder.stream.getTracks();
      tracks.forEach(function(track) {
        track.stop();
      });
    }
  };
}])
.controller("ImageUploadCtrl", ["$http", "$scope", "$rootScope", "uploadUtils", "Utils", function($http, $scope, $rootScope, uploadUtils, Utils) {
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
