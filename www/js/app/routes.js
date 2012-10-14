/*global window */

define(function (require) {
    'use strict';

    var $ = require('jquery'),
        hasher = require('hasher'),
        hogan = require('hogan'),
        crossroads = require('crossroads'),
        templates = {},
        handlers = {};

    handlers.submission = require('./handlers/submission');

    handlers.receiver = require('./handlers/receiver');

    handlers.status = require('./handlers/status');

    templates.home = hogan.compile(require('text!./templates/home.html'));
    templates.about = hogan.compile(require('text!./templates/about.html'));
    templates.submission = hogan.compile(require('text!./templates/submission.html'));
    templates.status = hogan.compile(require('text!./templates/status.html'));
    templates.admin = {}
    templates.admin.content = hogan.compile(require('text!./templates/admin/content.html'));
    templates.admin.wizard = hogan.compile(require('text!./templates/admin/wizard.html'));
    templates.admin.basic = hogan.compile(require('text!./templates/admin/basic.html'));
    templates.admin.advanced = hogan.compile(require('text!./templates/admin/advanced.html'));

    templates.receiver = {}
    templates.receiver.list = hogan.compile(require('text!./templates/receiver/list.html'));
    templates.receiver.preferences = hogan.compile(require('text!./templates/receiver/preferences.html'));

    templates.loading = hogan.compile(require('text!./templates/loading.html'));

    function homeHandler(data) {
        var content = templates.home.render();
        $('.contentElement').html(content);
    };

    function aboutHandler(data) {
        latenza.ajax({'url': '/about/'}).done(function(data) {
            var parsed = JSON.parse(data);
            var content = templates.about.render(parsed);
            $('.contentElement').html(content);
        });
    };

    function statusHandler(token) {
        var content = templates.status.render({tip_id: token});
        $('.contentElement').html(content);
    };

    function adminHandler(data) {
        var content = templates.admin.content.render();
        $('.contentElement').html(content);
    };

    function receiverHandlerList(token) {
        var content = templates.receiver.list.render()
        $('.contentElement').html(content);
        handlers.receiver();
    };

    function receiverHandlerPreferences(token) {
        var content = templates.receiver.preferences.render()
        $('.contentElement').html(content);
        handlers.receiver();
    };


    return function routes(parentDom) {


        parentDom = parentDom || $('body');

        crossroads.addRoute('', homeHandler);
        crossroads.addRoute('about', aboutHandler);
        crossroads.addRoute('submission', handlers.submission);
        crossroads.addRoute('status/{token}', handlers.status);
        crossroads.addRoute('admin', adminHandler);
        crossroads.addRoute('receiver/{token}', receiverHandlerList);
        crossroads.addRoute('receiver/{token}/preferences', receiverHandlerPreferences);
        crossroads.addRoute('receiver/{token}/list', receiverHandlerList);

        crossroads.routed.add(console.log, console); //log all routes
         
        //setup hasher
        function parseHash(newHash, oldHash){
            if (newHash != '') {
                $('#homeMenu').removeClass('active');
            } else {
                $('#homeMenu').addClass('active');
            }
            $('#'+oldHash+'Menu').removeClass('active');
            $('#'+newHash+'Menu').addClass('active');
            latenza.renderProgressbar($('.contentElement'), templates.loading.render());
            crossroads.parse(newHash);
        }

        hasher.initialized.add(parseHash); //parse initial hash
        hasher.changed.add(parseHash); //parse hash changes
        hasher.init(); //start listening for history change
         
    };
});
