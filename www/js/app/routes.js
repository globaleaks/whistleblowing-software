/*global window */

define(function (require) {
    'use strict';

    var $ = require('jquery'),
        hasher = require('hasher'),
        hogan = require('hogan'),
        crossroads = require('crossroads'),
        templates = {};
   
    templates.home = hogan.compile(require('text!./templates/home.html'));
    templates.about = hogan.compile(require('text!./templates/about.html'));
    templates.submission = hogan.compile(require('text!./templates/submission.html'));
    templates.status = hogan.compile(require('text!./templates/status.html'));
    templates.admin = hogan.compile(require('text!./templates/admin.html'));
    templates.receiver = hogan.compile(require('text!./templates/receiver.html'));
    
    function homeHandler(data) {
        var content = templates.home.render();
        $('.contentElement').html(content);
    };

    function aboutHandler(data) {
        var content = templates.about.render();
        $('.contentElement').html(content);
    };

    function submissionHandler(data) {
        var content = templates.submission.render({'intro': 'Foobar'});
        $('.contentElement').html(content);
        require('./uiSubmission')();
    };

    function statusHandler(token) {
        var content = templates.status.render();
        $('.contentElement').html(content);
        console.log(data);
    };

    function adminHandler(data) {
        var content = templates.admin.render();
        $('.contentElement').html(content);
    };

    function receiverHandler(data) {
        var content = templates.receiver.render();
        $('.contentElement').html(content);
    };


    return function routes(parentDom) {
        

        parentDom = parentDom || $('body');
        
        crossroads.addRoute('', homeHandler); 
        crossroads.addRoute('about', aboutHandler); 
        crossroads.addRoute('submission', submissionHandler); 
        crossroads.addRoute('status/{token}', statusHandler); 
        crossroads.addRoute('admin', adminHandler); 
        crossroads.addRoute('receiver/{token}', receiverHandler); 

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
            $('.contentElement').html(''); 
            crossroads.parse(newHash);
        }

        hasher.initialized.add(parseHash); //parse initial hash
        hasher.changed.add(parseHash); //parse hash changes
        hasher.init(); //start listening for history change
         
    };
});
