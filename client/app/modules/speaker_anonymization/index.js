function generateVocoderBands(startFreq, endFreq, numBands) {
  const vocoderBands = [];
  const logStep = Math.log(endFreq / startFreq) / (numBands - 1);

  for (let i = 0; i < numBands; i++) {
    var lo = startFreq * Math.exp(i * logStep);
    var hi = startFreq * Math.exp((i+1) * logStep);
    var fc = (hi + lo) / 2;
    var bw = hi - lo;
    var Q = fc / bw;

    vocoderBands.push({freq: fc, Q: Q});
  }

  return vocoderBands;
}

function generateRectifierCurve() {
  const rectifierCurve = new Float32Array(65536);
  for (let i=-32768; i < 32768; i++)
    rectifierCurve[i + 32768] = ((i>0) ? i : -i) / 32768;
  return rectifierCurve;
}

function anonymizeSpeaker(audioContext) {
  const input = this.input = audioContext.createGain();
  const output = this.output = audioContext.createGain();

  input.gain.value = output.gain.value = 1;

  const vocoderBands = generateVocoderBands(200, 16000, 128);
  const vocoderPitchShift = -(1/12 - Math.random() * 1/24);

  for (let i=0; i < vocoderBands.length; i++) {
    const carrier = audioContext.createOscillator();
    carrier.frequency.value = vocoderBands[i].freq * Math.pow(2, vocoderPitchShift);

    const modulatorBandFilter = audioContext.createBiquadFilter();

    modulatorBandFilter.type = "bandpass";
    modulatorBandFilter.frequency.value = vocoderBands[i].freq;
    modulatorBandFilter.Q.value = vocoderBands[i].Q;

    const rectifier = audioContext.createWaveShaper();
    rectifier.curve = generateRectifierCurve();

    const postRectifierBandFilter = audioContext.createBiquadFilter();
    postRectifierBandFilter.type = "lowpass";
    postRectifierBandFilter.frequency.value = 20;
    postRectifierBandFilter.gain.value = 1;

    const postRectifierGain = audioContext.createGain();
    postRectifierGain.gain.value = 1;

    const bandGain = audioContext.createGain();
    bandGain.gain.value = 0;

    input.connect(modulatorBandFilter);
    modulatorBandFilter.connect(rectifier);
    rectifier.connect(postRectifierGain);
    postRectifierGain.connect(bandGain.gain);

    carrier.connect(bandGain);
    bandGain.connect(output);

    carrier.start();
  }
}
