/*global window */

define(function (require) {
    'use strict';

    var $ = require('jquery'),
        hogan = require('hogan'),
        template = hogan.compile(require('text!../templates/submission.html'));

    return function submissionHandler(data) {
        var content = template.render(data);
        $('.contentElement').html(content);
        require('../uiSubmission')();
    };
});
