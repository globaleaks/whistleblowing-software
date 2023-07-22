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
.controller("SecureAudioUploadCtrl", ["$scope","flowFactory","mediaProcessor","Utils", function($scope, flowFactory, mediaProcessor, Utils) {
  const recordingData = {
    audio_channel: [],
    recordingLength: 0,
    mediaRecorder: null,
    flow: null,
    mediaStream: null,
    context: null,
    startTime: null,
    noiseGateThreshold: 0.2,
    noiseReductionAmount: 0.5,
    activeButton: null,
    disablePlayer: true,
    isRecording: false,
    audioPlayer: '',
  };

  async function initAudioContext(stream) {
    window.AudioContext = window.AudioContext || window.webkitAudioContext;
    recordingData.context = new AudioContext();

    recordingData.mediaStream = recordingData.context.createMediaStreamSource(stream);
    recordingData.recorder = recordingData.context.createScriptProcessor(2048, 2, 2);

    recordingData.recorder.onaudioprocess = function (stream) {
      var buffer = stream.inputBuffer.getChannelData(0);
      buffer = mediaProcessor.applyNoiseReduction(buffer, recordingData.noiseGateThreshold, recordingData.noiseReductionAmount)
      recordingData.audio_channel.push(new Float32Array(buffer));
      recordingData.recordingLength += buffer.length;
    };

    recordingData.mediaStream.connect(recordingData.recorder);
    recordingData.recorder.connect(recordingData.context.destination);
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
    recordingData.audio_channel = [];
    recordingData.recordingLength = 0;
    $scope.isRecording = true;
    $scope.isRecordingTooLarge = false;
    $scope.isRecordingTooShort = false;
    $scope.audioPlayer = '';
    $scope.activeButton = 'record';
    recordingData.startTime = Date.now();

    recordingData.flow = flowFactory.create({
      target: $scope.fileupload_url,
      query: {
        type: 'audio.webm',
        reference: fileId,
      },
    });

    recordingData.mediaRecorder = new MediaRecorder(stream);
    await initAudioContext(stream);

    $scope.$apply();
  }

  $scope.stopRecording = async function () {
    $scope.isRecording = false;
    $scope.activeButton = null;

    if (recordingData.recorder && recordingData.mediaStream) {
      recordingData.recorder.disconnect(0);
      recordingData.mediaStream.disconnect(0);
    }

    const tracks = recordingData.mediaRecorder.stream.getTracks();
    tracks.forEach((track) => {
      track.stop();
    });

    let modbuffer = mediaProcessor.flattenArray(recordingData.audio_channel, recordingData.recordingLength);
    modbuffer = mediaProcessor.applyLowPassFilter(modbuffer, recordingData);
    modbuffer = mediaProcessor.applyTimeStretching(modbuffer);
    modbuffer = mediaProcessor.applyPitchShift(modbuffer);

    const blob = mediaProcessor.createWavBlob(modbuffer);

    const durationInSeconds = (Date.now() - recordingData.startTime) / 1000;
    $scope.isRecordingTooShort = durationInSeconds < parseInt($scope.field.attrs.min_time.value);
    $scope.isRecordingTooLarge = durationInSeconds > parseInt($scope.field.attrs.max_time.value) || durationInSeconds > 180;

    $scope.disablePlayer = $scope.isRecordingTooShort || $scope.isRecordingTooLarge;
    $scope.audioFile = blob;

    const file = new Flow.FlowFile(recordingData.flow, {
      name: 'audio.webm',
      size: blob.size,
      relativePath: 'audio.webm',
    });
    file.file = blob;
    recordingData.flow.files = [];
    if (!$scope.isRecordingTooShort && !$scope.isRecordingTooLarge) {
      recordingData.flow.files.push(file);
      $scope.audioPlayer = URL.createObjectURL(blob);
    }

    if ($scope.uploads.hasOwnProperty($scope.fileinput)) {
      delete $scope.uploads[$scope.fileinput];
    }
    if (!$scope.isRecordingTooShort && !$scope.isRecordingTooLarge) {
      $scope.uploads[$scope.fileinput] = recordingData.flow;
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
