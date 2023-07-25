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
controller("AudioUploadCtrl", ["$scope","flowFactory", "Utils", "mediaProcessor", function($scope, flowFactory, Utils, mediaProcessor) {

  let recordingLength = 0;
  let mediaRecorder = null;
  let flow = null;
  let mediaStream = null;
  let context = null;
  let secondsTracker = null;

  $scope.audio_channel = [];
  $scope.seconds = 0;
  $scope.activeButton = null;
  $scope.isRecording = false;
  $scope.audioPlayer = null;

  async function initAudioContext(stream) {
    window.AudioContext = window.AudioContext || window.webkitAudioContext;
    context = new AudioContext();

    mediaStream = context.createMediaStreamSource(stream);
    $scope.recorder = context.createScriptProcessor(2048, 2, 2);

    $scope.recorder.onaudioprocess = function (stream) {
      var buffer = stream.inputBuffer.getChannelData(0);
      $scope.audio_channel.push(new Float32Array(buffer));
      recordingLength += buffer.length;
    };

    mediaStream.connect($scope.recorder);
    $scope.recorder.connect(context.destination);
  }

  $scope.triggerRecording = function (fileId) {
    $scope.activeButton = 'record';

    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function (stream) {
          startRecording(fileId, stream);
          console.log('Audio recording permission is granted');
        })
        .catch(function (error) {
          $scope.activeButton = null;
          $scope.$apply();
          console.error('Error checking audio recording permission:', error);
        });
    } else {
      console.warn('getUserMedia is not supported in this browser');
    }
  };

  async function startRecording(fileId, stream) {
    $scope.audio_channel = [];
    recordingLength = 0;
    $scope.isRecording = true;
    $scope.audioPlayer = '';
    $scope.activeButton = 'record';
    $scope.startTime = Date.now();

    flow = flowFactory.create({
      target: $scope.fileupload_url,
      query: {
        type: 'audio.webm',
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

    $scope.$apply();
  };

  $scope.stopRecording = async function () {
    $scope.vars["recording"] = false;
    $scope.recorder.onaudioprocess = null;

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
      context = null;
      return;
    }

    if (mediaRecorder && (mediaRecorder.state === "recording" || mediaRecorder.state === "paused")) {
      mediaRecorder.stop();
    }

    let modbuffer = mediaProcessor.flattenArray($scope.audio_channel, recordingLength);
    modbuffer = mediaProcessor.applyLowPassFilter(modbuffer, context.sampleRate);
    modbuffer = mediaProcessor.applyPitchShift(modbuffer);
    modbuffer = mediaProcessor.applyGossipRemoval(modbuffer);
    const blob = mediaProcessor.createWavBlob(modbuffer);

    $scope.audioFile = blob;

    const file = new Flow.FlowFile(flow, {
      name: 'audio.webm',
      size: blob.size,
      relativePath: 'audio.webm',
    });
    file.file = blob;
    flow.files = [];

    if ($scope.uploads.hasOwnProperty($scope.fileinput)) {
      delete $scope.uploads[$scope.fileinput];
    }

    if ($scope.seconds >= parseInt($scope.field.attrs.min_len.value) && $scope.seconds <= parseInt($scope.field.attrs.max_len.value)) {
      flow.files.push(file);
      $scope.audioPlayer = URL.createObjectURL(blob);
      $scope.uploads[$scope.fileinput] = flow;
    }
    context = null;
  };

  $scope.deleteRecording = function () {
    if (flow) {
      flow.cancel();
    }

    $scope.recorder.onaudioprocess = null;
    $scope.chunks = [];
    mediaStream = null;
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
