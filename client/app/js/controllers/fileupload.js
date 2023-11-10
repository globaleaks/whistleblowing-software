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
    if ($scope.entry) {
      if (!$scope.entry["files"]) {
        $scope.entry["files"] = [];
      }

      $scope.entry["files"].push(flowFile.uniqueIdentifier);
    }

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
controller("AudioUploadCtrl", ["$scope", "flowFactory", "Utils", "mediaProcessor", function ($scope, flowFactory, Utils, mediaProcessor) {
  let mediaRecorder = null;
  let flow = null;
  let secondsTracker = null;

  $scope.seconds = 0;
  $scope.activeButton = null;
  $scope.isRecording = false;
  $scope.audioPlayer = null;

  $scope.recording_blob = null;

  function onRecorderDataAvailable(e) {
    $scope.recording_blob = e.data;
  }

  function onRecorderStop() {
    const file = new Flow.FlowFile(flow, {
      name: "audio.webm",
      size: $scope.recording_blob.size,
      relativePath: "audio.webm",
    });

    file.file = $scope.recording_blob;
    flow.files = [];

    if ($scope.uploads.hasOwnProperty($scope.fileinput)) {
      delete $scope.uploads[$scope.fileinput];
    }

    if ($scope.seconds >= parseInt($scope.field.attrs.min_len.value) && $scope.seconds <= parseInt($scope.field.attrs.max_len.value)) {
      flow.files.push(file);

      window.addEventListener("message", function(message) {
        const iframe = document.getElementById($scope.fieldEntry + "-audio");

        if (message.source !== iframe.contentWindow) {
          return;
        }

        var data = {
          tag: "audio",
          blob: $scope.recording_blob
        };

        iframe.contentWindow.postMessage(data, "*");
      }, {once: true});

      $scope.audioPlayer = true;

      $scope.uploads[$scope.fileinput] = flow;

      if ($scope.entry) {
        if (!$scope.entry["files"]) {
          $scope.entry["files"] = [];
        }

        $scope.entry["files"].push(file.uniqueIdentifier);
      }
    }

    $scope.$apply();
  }

  $scope.triggerRecording = function (fileId) {
    $scope.activeButton = "record";

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function (stream) {
          $scope.startRecording(fileId, stream);
        })
        .catch(function () {
          $scope.activeButton = null;
          $scope.$apply();
        });
    }
  };

  $scope.startRecording = async function(fileId, stream) {
    $scope.isRecording = true;
    $scope.audioPlayer = "";
    $scope.activeButton = "record";
    $scope.startTime = Date.now();

    flow = flowFactory.create({
      target: $scope.fileupload_url,
      query: {
        type: "audio.webm",
        reference_id: fileId,
      },
    });

    secondsTracker = setInterval(() => {
      $scope.seconds += 1;
      if ($scope.seconds > $scope.field.attrs.max_len.value) {
        $scope.isRecording = false;
        clearInterval(secondsTracker);
        secondsTracker = null;
        $scope.stopRecording();
      }
      $scope.$apply();
    }, 1000);

    await mediaProcessor.enableNoiseSuppression(stream);

    var context = new AudioContext();
    var mediaStreamDestination = new MediaStreamAudioDestinationNode(context);
    const source = context.createMediaStreamSource(stream);
    const anonymization_filter = new anonymizeSpeaker(context);

    source.connect(anonymization_filter.input);
    anonymization_filter.output.connect(mediaStreamDestination);

    var recorder = new MediaRecorder(mediaStreamDestination.stream);
    recorder.onstop = onRecorderStop;
    recorder.ondataavailable = onRecorderDataAvailable;
    recorder.start();

    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.onstop = function() {
      recorder.stop();
    };

    mediaRecorder.start();

    $scope.$apply();
  };

  $scope.stopRecording = async function() {
    $scope.vars["recording"] = false;

    const tracks = mediaRecorder.stream.getTracks();
    tracks.forEach((track) => {
      track.stop();
    });

    mediaRecorder.stop();

    $scope.isRecording = false;
    $scope.recordButton = false;
    $scope.stopButton = true;
    $scope.activeButton = null;
    clearInterval(secondsTracker);
    secondsTracker = null;

    if ($scope.seconds < $scope.field.attrs.min_len.value) {
      $scope.deleteRecording();
      return;
    }

    if (mediaRecorder && (mediaRecorder.state === "recording" || mediaRecorder.state === "paused")) {
      mediaRecorder.stop();
    }
  };

  $scope.deleteRecording = function () {
    $scope.audioPlayer = false;

    if (flow) {
      flow.cancel();
    }

    $scope.chunks = [];
    mediaRecorder = null;
    $scope.seconds = 0;
    $scope.audioPlayer = null;
    delete $scope.uploads[$scope.fileinput];

    if ($scope.entry && $scope.entry.files) {
      delete $scope.entry.files;
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
