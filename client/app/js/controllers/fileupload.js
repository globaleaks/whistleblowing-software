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

  var mediaStream = null;
  var context = null;
  var mediaRecorder = null;
  var leftchannel = [];
  var rightchannel = [];
  var recorder = null;
  var recordingLength = 0;
  var volume = null;
  var mediaStream = null;
  var context = null;
  var blob = null;
  var flow = flowFactory.create({ target: $scope.fileupload_url, query: { type: 'audio.webm' } });
  var startTime;
  var noiseGateThreshold = 0.2;
  var noiseReductionAmount = 0.5;

  $scope.activeButton = null;

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

  function applyReverb(buffer, reverbTime, decay) {
    var reverberatedBuffer = new Float32Array(buffer.length);
    var delayTime = reverbTime * context.sampleRate; // Convert reverb time to samples
    var delayAmount = decay * 0.7; // Adjust the decay amount as needed
    var delayBuffer = new Float32Array(Math.ceil(delayTime) + 1);
    var index = 0;

    for (var i = 0; i < buffer.length; i++) {
      var sample = buffer[i];
      var delayedSample = delayBuffer[index];
      reverberatedBuffer[i] = sample + delayedSample * delayAmount;
      delayBuffer[index] = sample + delayedSample * decay;
      index++;
      if (index >= delayBuffer.length) {
        index = 0;
      }
    }

    return reverberatedBuffer;
  }

  // Function to apply Reverb effect to an audio buffer
  function applyReverb(buffer, reverbTime, decay) {
    var reverberatedBuffer = new Float32Array(buffer.length);
      sampleRate = Math.floor(Math.random() * (60001 - 38000) + 38000);
    var delayTime = reverbTime * sampleRate; // Convert reverb time to samples
    var delayAmount = decay * 0.7; // Adjust the decay amount as needed
    var delayBuffer = new Float32Array(Math.ceil(delayTime) + 1);
    var index = 0;
    for (var i = 0; i < buffer.length; i++) {
      var sample = buffer[i];
      var delayedSample = delayBuffer[index];
      reverberatedBuffer[i] = sample + delayedSample * delayAmount;
      delayBuffer[index] = sample + delayedSample * decay;
      index++;
      if (index >= delayBuffer.length) {
        index = 0;
      }
    }
    return reverberatedBuffer;
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

  function interleave(leftChannel, rightChannel) {
    var length = leftChannel.length + rightChannel.length;
    var result = new Float32Array(length);

    var inputIndex = 0;

    for (var index = 0; index < length;) {
      result[index++] = leftChannel[inputIndex];
      result[index++] = rightChannel[inputIndex];
      inputIndex++;
    }
    return result;
  }

  function writeUTFBytes(view, offset, string) {
    for (var i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  $scope.startRecording = function() {
    leftchannel = [];
    rightchannel = [];
    recordingLength = 0;
    isRecording = true;
    $scope.activeButton = 'record';
    startTime = Date.now();

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.log('getUserMedia is not supported in this browser.');
      return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(function(stream) {
        mediaRecorder = new MediaRecorder(stream)

        // Create the audio context
        window.AudioContext = window.AudioContext || window.webkitAudioContext;
        context = new AudioContext();

        // Create an audio node from the microphone incoming stream
        mediaStream = context.createMediaStreamSource(stream);

        // ScriptProcessorNode for audio processing
        recorder = context.createScriptProcessor(2048, 2, 2);

        recorder.onaudioprocess = function(stream) {
          var leftBuffer = stream.inputBuffer.getChannelData(0);
          var rightBuffer = stream.inputBuffer.getChannelData(1);

          // Apply noise reduction
          for (var i = 0; i < leftBuffer.length; i++) {
            if (Math.abs(leftBuffer[i]) < noiseGateThreshold) {
              leftBuffer[i] *= noiseReductionAmount;
            }

            if (Math.abs(rightBuffer[i]) < noiseGateThreshold) {
              rightBuffer[i] *= noiseReductionAmount;
            }
          }

          leftchannel.push(new Float32Array(leftBuffer));
          rightchannel.push(new Float32Array(rightBuffer));
          recordingLength += leftBuffer.length;
        };

        // Connect the recorder
        mediaStream.connect(recorder);
        recorder.connect(context.destination);
      })
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

    var stretchAmount = Math.random() * 0.3 + 1.1; // Random stretch amount for the left channel
    var randomPitch = Math.random() * (1.2 - 0.7) + 0.7;

    // Flatten the left and right channels down
    var modbuffer = flattenArray(leftchannel, recordingLength);
    modbuffer = applyLowPassFilter(modbuffer, randomPitch);
    modbuffer = pitchShift(modbuffer, randomPitch);
    modbuffer = applyTimeStretching(modbuffer, stretchAmount);
    modbuffer = applyBitcrusher(modbuffer);

    var interleaved = interleave(modbuffer, modbuffer);
    var buffer = new ArrayBuffer(44 + interleaved.length * 2);
    var view = new DataView(buffer);

    // RIFF chunk descriptor
    writeUTFBytes(view, 0, "RIFF");
    view.setUint32(4, 44 + interleaved.length * 2, true);
    writeUTFBytes(view, 8, "WAVE");
    // FMT sub-chunk
    writeUTFBytes(view, 12, "fmt ");
    view.setUint32(16, 16, true); // chunkSize
    view.setUint16(20, 1, true); // wFormatTag
    view.setUint16(22, 2, true); // wChannels: stereo (2 channels)
    sampleRate = Math.floor(Math.random() * (60001 - 38000) + 38000);
    alert(sampleRate)
    view.setUint32(24, sampleRate, true); // dwSamplesPerSec
    view.setUint32(28, sampleRate * 4, true); // dwAvgBytesPerSec
    view.setUint16(32, 4, true); // wBlockAlign
    view.setUint16(34, 16, true); // wBitsPerSample
    // data sub-chunk
    writeUTFBytes(view, 36, "data");
    view.setUint32(40, interleaved.length * 2, true);

    // Write the PCM samples
    var index = 44;
    var volume = 1;
    for (var i = 0; i < interleaved.length; i++) {
      view.setInt16(index, interleaved[i] * (0x7FFF * volume), true);
      index += 2;
    }

    // Create the final blob
    blob = new Blob([view], { type: "audio/wav" });
    $scope.audioPlayer = URL.createObjectURL(blob);

    var durationInSeconds = (Date.now() - startTime) / 1000;
    $scope.isRecordingTooShort = durationInSeconds < parseInt($scope.field.attrs.min_time.value);

    $scope.audioFile = blob;
    var file = new Flow.FlowFile(flow, {
      name: 'audio.webm',
      size: blob.size,
      relativePath: 'audio.webm'
    });
    file.file = blob;
    flow.files = [];
    if (!$scope.isRecordingTooShort) {
      flow.files.push(file);
    }

    if ($scope.uploads.hasOwnProperty($scope.fileinput)) {
      delete $scope.uploads[$scope.fileinput];
    }
    if (!$scope.isRecordingTooShort) {
      $scope.uploads[$scope.fileinput] = flow;
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
