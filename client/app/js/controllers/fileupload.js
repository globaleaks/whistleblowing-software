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
controller("WBFileUploadCtrl", ["$scope", function($scope) {
  $scope.disabled = false;

  $scope.$on("flow::fileAdded", function (event, $flow, flowFile) {
    flowFile.pause();

    $scope.file_error_msgs = [];

    $scope.$emit("GL::uploadsUpdated");
  });
}]).
controller("RFileUploadCtrl", ["$scope", function($scope) {
  $scope.file_upload_description = "";

  $scope.beginUpload = function ($files, $event, $flow, visibility) {
    $scope.file_error_msgs = [];
    $flow.opts.query = { "description": $scope.file_upload_description, "visibility": visibility };
    $flow.upload();
  };
}]).
controller("AudioUploadCtrl", ["$scope","flowFactory", function($scope, flowFactory) {
  $scope.chunks = [];
  $scope.flow = null;
  $scope.mediaStream = null;
  $scope.seconds = 0;
  $scope.secondsTracker = null;

  $scope.audioPlayer = null;
  $scope.activeButton = null;
  $scope.disablePlayer = true;
  $scope.isRecording=false;

  function onDataAvailable(event) {
    $scope.chunks.push(event.data);
  }

  function onStop() {
    var blob = new Blob($scope.chunks, { type: "audio/webm" });
    $scope.audioPlayer = URL.createObjectURL(blob);
    $scope.audioFile = blob;

    var file = new Flow.FlowFile($scope.flow, {
      name: "audio.webm",
      size: blob.size,
      relativePath: "audio.webm"
    });

    file.file = blob;

    if($scope.seconds > $scope.field.attrs.min_len.value){
      $scope.flow.files.push(file);
    }

    if ($scope.uploads.hasOwnProperty($scope.fileinput)) {
      delete $scope.uploads[$scope.fileinput];
    }

    if($scope.seconds > $scope.field.attrs.min_len.value){
      $scope.uploads[$scope.fileinput] = $scope.flow;
    }

    $scope.$apply();
  }

  $scope.deleteRecording = function () {
    if ($scope.flow) {
      $scope.flow.cancel();
    }

    $scope.chunks = [];
    $scope.mediaStream = null;
    $scope.mediaRecorder = null;
    $scope.seconds = 0;
    $scope.audioPlayer = null;
    delete $scope.uploads[$scope.fileinput];
  };

  $scope.startRecording = function (fileId) {
    if ($scope.vars["recording"]) {
      return;
    }

    $scope.vars["recording"] = true;

    if (!$scope.flow) {
      $scope.flow = flowFactory.create({
        target: $scope.fileupload_url,
        query: {
          type: "audio.webm",
          reference_id: fileId
        }
      });
    }

    $scope.secondsTracker = setInterval(() => {
      $scope.seconds += 1;
      if ($scope.seconds > $scope.field.attrs.max_len.value) {
        $scope.isRecording = false;
        clearInterval($scope.secondsTracker);
        $scope.secondsTracker = null;
        $scope.stopRecording();
      }
      $scope.$apply();
    }, 1000);

    $scope.isRecording = true;
    $scope.recordButton = true;
    $scope.stopButton = false;
    $scope.activeButton = "record";

    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(function(stream) {
        $scope.mediaRecorder = new MediaRecorder(stream);

        $scope.mediaRecorder.addEventListener("dataavailable", onDataAvailable);

        $scope.mediaRecorder.addEventListener("stop", onStop);

        $scope.mediaRecorder.start();
      });
  };

  $scope.stopRecording = function () {
    $scope.vars["recording"] = false;

    $scope.isRecording = false;
    $scope.recordButton = false;
    $scope.stopButton = true;
    $scope.activeButton = null;
    clearInterval($scope.secondsTracker);
    $scope.secondsTracker = null;

    if ($scope.seconds < $scope.field.attrs.min_len.value) {
      $scope.deleteRecording();
      return;
    }

    if ($scope.mediaRecorder && ($scope.mediaRecorder.state === "recording" || $scope.mediaRecorder.state === "paused")) {
      $scope.mediaRecorder.stop();
    }
  };

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
