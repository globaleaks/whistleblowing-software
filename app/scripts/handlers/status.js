/*global window */

define(function (require) {
  'use strict';

  var $ = require('libs/jquery'),
      hasher = require('libs/hasher'),
      hogan = require('libs/hogan'),
      utils = require('utils/util'),
      template = hogan.compile(require('text!templates/status.html')),
      requests = {},
      messages = {};
  messages.responses = require('messages/responses');
  requests.status = require('requests/status');

  return function statusHandler(receipt, bar) {
    requests.status.get(receipt).done(function(result) {
      var safe_data = messages.responses.processStatusGet(result),
          content;
      safe_data['receipt'] = utils.htmlEntities(receipt);
      content = template.render(safe_data);
      $('.contentElement').html(content);
    });
  };
});
