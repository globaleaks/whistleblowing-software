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
  var flow;
  var mediaStream = null;
  var context = null;
  var mediaRecorder = null;
  var audio_channel = [];
  var recorder = null;
  var recordingLength = 0;
  var volume = null;
  var mediaStream = null;
  var context = null;
  var blob = null;
  var startTime;
  var noiseGateThreshold = 0.2;
  var noiseReductionAmount = 0.5;
  $scope.activeButton = null;
  $scope.disablePlayer = true;
  $scope.isAudioProtected=false;

  $scope.applySoundrotection = function (fieldid){
    $scope.isAudioProtected=true;
    $scope.triggerRecording(fieldid);
  }

  function applySubtleDistortion(buffer, amount) {
    var distortedBuffer = new Float32Array(buffer.length);
    for (var i = 0; i < buffer.length; i++) {
      var sample = buffer[i];
      // Apply distortion by adding/subtracting a small random value
      distortedBuffer[i] = sample + (Math.random() * 2 - 1) * amount;
    }
    return distortedBuffer;
  }

  function applyLowPassFilter(buffer) {
    var minCutoff = 500; // Minimum cutoff frequency (in Hz)
    var maxCutoff = 20000; // Maximum cutoff frequency (in Hz)

    // Generate a random cutoff frequency within the range
    var cutoffFrequency = Math.floor(Math.random() * (maxCutoff - minCutoff + 1)) + minCutoff;

    // Apply the low-pass filter to the buffer
    for (var i = 1; i < buffer.length; i++) {
      buffer[i] = (buffer[i - 1] + buffer[i]) / 2;
    }
    return buffer;
  }

  function applyTimeStretching(buffer, amount) {
    var originalLength = buffer.length;
    var stretchedLength = Math.floor(originalLength * amount);
    var stretchedBuffer = new Float32Array(stretchedLength);
    var index = 0;
    for (var i = 0; i < stretchedLength; i++) {
      var position = i / stretchedLength * originalLength;
      var previousIndex = Math.floor(position);
      var nextIndex = Math.ceil(position);
      var weight = position - previousIndex;
      var previousSample = buffer[previousIndex];
      var nextSample = buffer[nextIndex];
      var stretchedSample = previousSample + (nextSample - previousSample) * weight;
      stretchedBuffer[index++] = stretchedSample;
    }
    return stretchedBuffer;
  }
  // Function to apply Bitcrusher effect to an audio buffer
  function applyBitcrusher(buffer) {
    var minBitDepth = 8; // Minimum bit depth
    var maxBitDepth = 15; // Maximum bit depth
    var bitDepth = Math.floor(Math.random() * (maxBitDepth - minBitDepth + 1)) + minBitDepth; // Random bit depth between 8 and 15

    var step = Math.pow(0.5, bitDepth - 1);
    var crushedBuffer = new Float32Array(buffer.length);
    for (var i = 0; i < buffer.length; i++) {
      var sample = buffer[i];
      var quantized = Math.floor(sample / step + 0.5) * step;
      crushedBuffer[i] = quantized;
    }
    return crushedBuffer;
  }


  function pitchShift(buffer, pitchShiftAmount) {
    // Apply pitch shifting to the buffer
    var pitchShiftedBuffer = new Float32Array(buffer.length);
    var playbackRate = 1 / pitchShiftAmount;

    for (var i = 0; i < buffer.length; i++) {
      var index = Math.floor(i * playbackRate);
      pitchShiftedBuffer[i] = buffer[index];
    }

    return pitchShiftedBuffer;
  }

  function flattenArray(channelBuffer, recordingLength) {
    var result = new Float32Array(recordingLength);
    var offset = 0;
    for (var i = 0; i < channelBuffer.length; i++) {
      var buffer = channelBuffer[i];
      result.set(buffer, offset);
      offset += buffer.length;
    }
    return result;
  }

  function interleave(audio_Channel) {
    var length = audio_Channel.length;
    var result = new Float32Array(length);

    var inputIndex = 0;

    for (var index = 0; index < length;) {
      result[index++] = audio_Channel[inputIndex];
      inputIndex++;
    }
    return result;
  }

  function writeUTFBytes(view, offset, string) {
    for (var i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  $scope.triggerRecording = function(fileId) {
    $scope.activeButton = 'record';
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
          $scope.startRecording(fileId, stream);
          console.log('Audio recording permission is granted');
        })
        .catch(function(error) {
          // Audio recording permission is denied or an error occurred
          $scope.activeButton = null;
          $scope.$apply()

          console.error('Error checking audio recording permission:', error);
        });
    } else {
      // getUserMedia is not supported in this browser
      console.warn('getUserMedia is not supported in this browser');
    }
  }
  

  $scope.startRecording = function(fileId, stream) {
    audio_channel = [];
    recordingLength = 0;
    isRecording = true;
    $scope.isRecordingTooLarge=false;
    $scope.isRecordingTooShort=false;
    $scope.activeButton = 'record';
    startTime = Date.now();
    flow = flowFactory.create({
      target: $scope.fileupload_url,
      query: {
        type: 'audio.webm',
        reference: fileId
      }
    });

    mediaRecorder = new MediaRecorder(stream)

    // Create the audio context
    window.AudioContext = window.AudioContext || window.webkitAudioContext;
    context = new AudioContext();

    // Create an audio node from the microphone incoming stream
    mediaStream = context.createMediaStreamSource(stream);

    // ScriptProcessorNode for audio processing
    recorder = context.createScriptProcessor(2048, 2, 2);

    recorder.onaudioprocess = function(stream) {
      var buffer = stream.inputBuffer.getChannelData(0);

      // Apply noise reduction
      for (var i = 0; i < buffer.length; i++) {
        if (Math.abs(buffer[i]) < noiseGateThreshold) {
          buffer[i] *= noiseReductionAmount;
        }
      }

      audio_channel.push(new Float32Array(buffer));
      recordingLength += buffer.length;
    };

    // Connect the recorder
    mediaStream.connect(recorder);
    recorder.connect(context.destination);
  };

 

  $scope.stopRecording = function() {
    isRecording = false;
    $scope.activeButton = null;

    // Stop recording

    if (recorder && mediaStream) {
      recorder.disconnect(0);
      mediaStream.disconnect(0);
    }
    var tracks = mediaRecorder.stream.getTracks();
      tracks.forEach(function(track) {
      track.stop();
    });
    var stretchAmount =    0.7 + (Math.random() * (1.6 - 0.7));
    var randomPitch = Math.random() * (1.2 - 0.7) + 0.7;
    var modbuffer = flattenArray(audio_channel, recordingLength);


    if($scope.isAudioProtected){
      // modbuffer = applyLowPassFilter(modbuffer);
      // modbuffer = pitchShift(modbuffer, randomPitch);
      modbuffer = applyTimeStretching(modbuffer, stretchAmount);
      // modbuffer = applyBitcrusher(modbuffer);
    }

    // var interleaved = interleave(modbuffer);
  var buffer = new ArrayBuffer(44 + modbuffer.length * 2);
  var view = new DataView(buffer);

  // RIFF chunk descriptor
  writeUTFBytes(view, 0, "RIFF");
  view.setUint32(4, 44 + modbuffer.length * 2, true);
  writeUTFBytes(view, 8, "WAVE");
  // FMT sub-chunk
  writeUTFBytes(view, 12, "fmt ");
  view.setUint32(16, 16, true); // chunkSize
  view.setUint16(20, 1, true); // wFormatTag
  view.setUint16(22, 2, true); // wChannels: stereo (2 channels)
  var sampleRate =  24000 // Set the desired sample rate
  view.setUint32(24, sampleRate, true); // dwSamplesPerSec
  view.setUint32(28, sampleRate, true); // dwAvgBytesPerSec
  view.setUint16(32, 4, true); // wBlockAlign
  view.setUint16(34, 16, true); // wBitsPerSample
  // data sub-chunk
  writeUTFBytes(view, 36, "data");
  view.setUint32(40, modbuffer.length * 2, true);

  // Write the PCM samples
  var index = 44;
  var volume = 1;
  for (var i = 0; i < modbuffer.length; i++) {
    view.setInt16(index, modbuffer[i] * (0x7FFF * volume), true);
    index += 2;
  }


    // Create the final blob
    blob = new Blob([view], { type: "audio/wav" });

    var durationInSeconds = (Date.now() - startTime) / 1000;
    $scope.isRecordingTooShort = durationInSeconds < parseInt($scope.field.attrs.min_time.value);
    $scope.isRecordingTooLarge = durationInSeconds > parseInt($scope.field.attrs.max_time.value) || durationInSeconds > 180;
    
    $scope.disablePlayer= $scope.isRecordingTooShort || $scope.isRecordingTooLarge;
    $scope.audioFile = blob;

    var file = new Flow.FlowFile(flow, {
      name: 'audio.webm',
      size: blob.size,
      relativePath: 'audio.webm'
    });
    file.file = blob;
    flow.files = [];
    if (!$scope.isRecordingTooShort && !$scope.isRecordingTooLarge) {
      flow.files.push(file);
      $scope.audioPlayer = URL.createObjectURL(blob);
    }

    if ($scope.uploads.hasOwnProperty($scope.fileinput)) {
      delete $scope.uploads[$scope.fileinput];
    }
    if (!$scope.isRecordingTooShort && !$scope.isRecordingTooLarge) {
      $scope.uploads[$scope.fileinput] = flow;
    }

    $scope.isAudioProtected=false;
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
