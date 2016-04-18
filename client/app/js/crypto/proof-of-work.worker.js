// stringToUTF8Bytes and sha256 function from scrypt-async-js library 1.2.0

function stringToUTF8Bytes(s) {
  var arr = [];
  for (var i = 0; i < s.length; i++) {
    var c = s.charCodeAt(i);
    if (c < 128) {
      arr.push(c);
    } else if (c > 127 && c < 2048) {
      arr.push((c>>6) | 192);
      arr.push((c & 63) | 128);
    } else {
      arr.push((c>>12) | 224);
      arr.push(((c>>6) & 63) | 128);
      arr.push((c & 63) | 128);
    }
  }
  return arr;
}

function sha256(m) {
  m = stringToUTF8Bytes(m);

  /** @const */ var K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b,
    0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01,
    0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7,
    0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152,
    0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
    0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
    0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819,
    0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08,
    0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f,
    0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];

  var h0 = 0x6a09e667, h1 = 0xbb67ae85, h2 = 0x3c6ef372, h3 = 0xa54ff53a,
      h4 = 0x510e527f, h5 = 0x9b05688c, h6 = 0x1f83d9ab, h7 = 0x5be0cd19,
      w = new Array(64);

  function blocks(p) {
    var off = 0, len = p.length;
    while (len >= 64) {
      var a = h0, b = h1, c = h2, d = h3, e = h4, f = h5, g = h6, h = h7,
          u, i, j, t1, t2;

      for (i = 0; i < 16; i++) {
        j = off + i*4;
        w[i] = ((p[j] & 0xff)<<24) | ((p[j+1] & 0xff)<<16) |
               ((p[j+2] & 0xff)<<8) | (p[j+3] & 0xff);
      }

      for (i = 16; i < 64; i++) {
        u = w[i-2];
        t1 = ((u>>>17) | (u<<(32-17))) ^ ((u>>>19) | (u<<(32-19))) ^ (u>>>10);

        u = w[i-15];
        t2 = ((u>>>7) | (u<<(32-7))) ^ ((u>>>18) | (u<<(32-18))) ^ (u>>>3);

        w[i] = (((t1 + w[i-7]) | 0) + ((t2 + w[i-16]) | 0)) | 0;
      }

      for (i = 0; i < 64; i++) {
        t1 = ((((((e>>>6) | (e<<(32-6))) ^ ((e>>>11) | (e<<(32-11))) ^
             ((e>>>25) | (e<<(32-25)))) + ((e & f) ^ (~e & g))) | 0) +
             ((h + ((K[i] + w[i]) | 0)) | 0)) | 0;

        t2 = ((((a>>>2) | (a<<(32-2))) ^ ((a>>>13) | (a<<(32-13))) ^
             ((a>>>22) | (a<<(32-22)))) + ((a & b) ^ (a & c) ^ (b & c))) | 0;

        h = g;
        g = f;
        f = e;
        e = (d + t1) | 0;
        d = c;
        c = b;
        b = a;
        a = (t1 + t2) | 0;
      }

      h0 = (h0 + a) | 0;
      h1 = (h1 + b) | 0;
      h2 = (h2 + c) | 0;
      h3 = (h3 + d) | 0;
      h4 = (h4 + e) | 0;
      h5 = (h5 + f) | 0;
      h6 = (h6 + g) | 0;
      h7 = (h7 + h) | 0;

      off += 64;
      len -= 64;
    }
  }

  blocks(m);

  var i, bytesLeft = m.length % 64,
      bitLenHi = (m.length / 0x20000000) | 0,
      bitLenLo = m.length << 3,
      numZeros = (bytesLeft < 56) ? 56 : 120,
      p = m.slice(m.length - bytesLeft, m.length);

  p.push(0x80);
  for (i = bytesLeft + 1; i < numZeros; i++) p.push(0);
  p.push((bitLenHi>>>24) & 0xff);
  p.push((bitLenHi>>>16) & 0xff);
  p.push((bitLenHi>>>8)  & 0xff);
  p.push((bitLenHi>>>0)  & 0xff);
  p.push((bitLenLo>>>24) & 0xff);
  p.push((bitLenLo>>>16) & 0xff);
  p.push((bitLenLo>>>8)  & 0xff);
  p.push((bitLenLo>>>0)  & 0xff);

  blocks(p);

  return [
    (h0>>>24) & 0xff, (h0>>>16) & 0xff, (h0>>>8) & 0xff, (h0>>>0) & 0xff,
    (h1>>>24) & 0xff, (h1>>>16) & 0xff, (h1>>>8) & 0xff, (h1>>>0) & 0xff,
    (h2>>>24) & 0xff, (h2>>>16) & 0xff, (h2>>>8) & 0xff, (h2>>>0) & 0xff,
    (h3>>>24) & 0xff, (h3>>>16) & 0xff, (h3>>>8) & 0xff, (h3>>>0) & 0xff,
    (h4>>>24) & 0xff, (h4>>>16) & 0xff, (h4>>>8) & 0xff, (h4>>>0) & 0xff,
    (h5>>>24) & 0xff, (h5>>>16) & 0xff, (h5>>>8) & 0xff, (h5>>>0) & 0xff,
    (h6>>>24) & 0xff, (h6>>>16) & 0xff, (h6>>>8) & 0xff, (h6>>>0) & 0xff,
    (h7>>>24) & 0xff, (h7>>>16) & 0xff, (h7>>>8) & 0xff, (h7>>>0) & 0xff
  ];
}

var iterateOverSHA = function(seed) {
  var i;
  for (i = 0; i < 1024; i++) {
    var x = sha256(seed + i);

    if (x[31] === 0) {
      postMessage(i);
      close();
    }
  }

  postMessage("12345");
  close();
};

onmessage = function(e) {
  iterateOverSHA(e.data.pow);
};
