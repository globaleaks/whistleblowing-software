/*global window */

define(["jquery", "hasher",
        "hogan", "crossroads",
        "text!templates/debug.html", "text!templates/loading.html"],
  function ($, hasher, hogan, crossroads, debug_template, loading_template) {
    'use strict';

    var templates = {},
        handlers = {};



    templates.debug = hogan.compile(debug_template)

    //templates.admin = {}
    //templates.admin.content = hogan.compile(require('text!templates/admin/content.html'));
    //templates.admin.wizard = hogan.compile(require('text!templates/admin/wizard.html'));
    //templates.admin.basic = hogan.compile(require('text!templates/admin/basic.html'));
    //templates.admin.advanced = hogan.compile(require('text!templates/admin/advanced.html'));

    //templates.receiver = {}
    //templates.receiver.list = hogan.compile(require('text!templates/receiver/list.html'));
    //templates.receiver.preferences = hogan.compile(require('text!templates/receiver/preferences.html'));

    templates.loading = hogan.compile(loading_template);

    function debugHandler(data) {
      var content = templates.debug.render(),
          debug = require('utils/debug');

      require('./dummy/requests');
      $('.contentElement').html(content);
      debug.debugDeck();
    };

    function homeHandler(data) {
      templates.home = hogan.compile(require('text!templates/home.html'));
      var content = templates.home.render();
      $('.contentElement').html(content);
    };

    function aboutHandler(data) {
      require(['text!templates/about.html'], function(template){
        var compiled = hogan.compile(template);
        latenza.ajax({'url': '/about/'}).done(function(data) {
          var parsed = JSON.parse(data);
          var content = compiled.render(parsed);
          $('.contentElement').html(content);
        });
      });
    };

    function statusHandler(token) {

      //templates.status = hogan.compile(require('text!templates/status.html'));
      //var content = templates.status.render({tip_id: token});
      //$('.contentElement').html(content);
      require(['handlers/status'], function(handler) {
        handler(token);
      });
    };

    function adminHandler(data) {
        var content = templates.admin.content.render();
        $('.contentElement').html(content);
    };

    function receiverHandlerList(token) {
        handlers.receiver = require('handlers/receiver');
        var content = templates.receiver.list.render()
        $('.contentElement').html(content);
        handlers.receiver();
    };

    function receiverHandlerPreferences(token) {
        var content = templates.receiver.preferences.render()
        $('.contentElement').html(content);
        handlers.receiver();
    };


    function submissionHandler(data) {
      require(['handlers/submission'], function(submission, data) {

        //hogan.compile(require('text!templates/submission.html'));
        submission(data);
      });
    };


    return function routes(parentDom) {

      parentDom = parentDom || $('body');

      crossroads.addRoute('', homeHandler);
      crossroads.addRoute('about', aboutHandler);

      crossroads.addRoute('submission', submissionHandler);
      //crossroads.addRoute('submission', handlers.submission);

      crossroads.addRoute('status/{token}', statusHandler);
      //crossroads.addRoute('status/{token}', handlers.status);

      crossroads.addRoute('admin', adminHandler);
      crossroads.addRoute('receiver/{token}', receiverHandlerList);

      crossroads.addRoute('receiver/{token}/preferences',receiverHandlerPreferences);
      //crossroads.addRoute('receiver/{token}/preferences',handlers.receiver.preferences);

      //crossroads.addRoute('receiver/{token}/list', handlers.receiver.list);
      crossroads.addRoute('receiver/{token}/list', receiverHandlerList);

      // Hi, I am a new feature to assist you in debugging :)
      crossroads.addRoute('debug', debugHandler);

      crossroads.routed.add(console.log, console); //log all routes
       
      //setup hasher
      function parseHash(newHash, oldHash){
          latenza.renderProgressbar($('.contentElement'), templates.loading.render());
          crossroads.parse(newHash);
      }

      hasher.initialized.add(parseHash); //parse initial hash
      hasher.changed.add(parseHash); //parse hash changes
      hasher.init(); //start listening for history change
         
    };
});
