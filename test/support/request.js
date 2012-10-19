var request = require('superagent');

module.exports = specrequest;

function specrequest(spec, address) {
  var req = new request.Request(spec.method, address+spec.url);
  if (spec.data) req.send(spec.data);
  return req;
};

