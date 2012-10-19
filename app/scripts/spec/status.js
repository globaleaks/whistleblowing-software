var status = {};

status.get = function(receipt) {
  return {'url': '/tip' + receipt,
    'method': 'GET'
  }
};

module.exports = status;
