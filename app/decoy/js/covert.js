sjcl.random.setDefaultParanoia(9);
sjcl.random.startCollectors();

function getRandomRange(start, end) {
  var rw = sjcl.random.randomWords(1),
    rnd_num = parseInt(sjcl.codec.hex.fromBits(rw), 16);

  rnd_num = rnd_num % end - start;
  rnd_num += start;
  return rnd_num;
}

function getRandomAction() {
  return getRandomRange(0, 3);
}

function randomAction() {
  
  var action = getRandomAction(),
    xhr = new XMLHttpRequest(),
    base_url = '/dev/null';

  if (action == 0) {
    var payload_size = getRandomRange(0, 180);

    base_url += Array(payload_size).join("A");
    xhr.open('GET', base_url, false);
    xhr.send(null);

  } else if (action == 1) {
    var payload_size = getRandomRange(0, 180);

    xhr.open('POST', base_url, false);
    xhr.send(Array(payload_size).join("A"));

  } else if (action == 2) {
    var payload_size = getRandomRange(500, 5000);

    xhr.open('POST', base_url, false);
    xhr.send(Array(payload_size).join("A"));
  }
}

function randomActionLoop() {
  randomAction();
  window.setTimeout(randomActionLoop, getRandomRange(100, 4000))
}

randomActionLoop();
