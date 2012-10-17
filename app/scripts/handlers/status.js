/*global window */

define(['jquery', 'hasher',
        'hogan', 'utils/util',
        'text!templates/status.html',
        'messages/responses', 'requests/status'
        ],
  function ($, hasher, hogan, utils, template_file,
            messages_responses, requests_status) {
    'use strict';

    var template = hogan.compile(template_file),
        requests = {},
        messages = {};
    messages.responses = messages_responses;
    requests.status = requests_status;

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
