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

  $scope.generateAcceptedFileTypes = function() {
    allowedFileTypes = $scope.field.allowed_file_type;
    var acceptedTypes = allowedFileTypes.split(' ').map(function(type) {
      return '.' + type;
    }).join(',');

    return acceptedTypes;
  };

  $scope.$on("flow::fileAdded", function (event, $flow, flowFile) {
    flowFile.pause();

    $scope.file_error_msgs = [];

    $scope.$emit("GL::uploadsUpdated");
  });

  $scope.allowed_file_type = $scope.generateAcceptedFileTypes();
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

  $scope.context = new AudioContext();

  $scope.mediaStreamDestination = new MediaStreamAudioDestinationNode($scope.context);
  $scope.recorder = new MediaRecorder($scope.mediaStreamDestination.stream);

  $scope.recording_blob = null;
  $scope.recorder.ondataavailable = function(e) {
    $scope.recording_blob = e.data;
  };

  $scope.recorder.onstop = function() {
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
      $scope.audioPlayer = URL.createObjectURL($scope.recording_blob);
      $scope.uploads[$scope.fileinput] = flow;
    }

    $scope.$apply();
  };


  async function initAudioContext(stream) {
    window.AudioContext = window.AudioContext || window.webkitAudioContext;
    await mediaProcessor.enableNoiseSuppression(stream);

    const source = $scope.context.createMediaStreamSource(stream);
    const filter1 = mediaProcessor.createHighPassFilter($scope.context);
    const filter2 = mediaProcessor.createLowPassFilter($scope.context);
    const filter3 = mediaProcessor.createDynamicCompressor($scope.context);

    source.connect(filter1);
    filter1.connect(filter2);
    filter2.connect(filter3);
    filter3.connect($scope.mediaStreamDestination);
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
        reference: fileId,
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

    mediaRecorder = new MediaRecorder(stream);

    await initAudioContext(stream);

    $scope.recorder.start();
    mediaRecorder.start();

    $scope.$apply();
  };

  $scope.stopRecording = async function() {
    $scope.vars["recording"] = false;

    $scope.recorder.stop();

    const tracks = mediaRecorder.stream.getTracks();
    tracks.forEach((track) => {
      track.stop();
    });

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
    if (flow) {
      flow.cancel();
    }

    $scope.chunks = [];
    mediaRecorder = null;
    $scope.seconds = 0;
    $scope.audioPlayer = null;
    delete $scope.uploads[$scope.fileinput];
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
