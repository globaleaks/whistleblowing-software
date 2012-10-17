define(['latenza'], function(latenza) {
  return {
    get: function(receipt) {
      return latenza.ajax({'url': '/tip/' + receipt,
                'type': 'GET'
      });
    }
  }
});
