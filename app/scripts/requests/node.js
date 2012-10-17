define(['latenza'], function(latenza) {
  return {
    root: function() {
      return latenza.ajax({'url': '/node',
                'type': 'GET'
      });
    }
  }
});
