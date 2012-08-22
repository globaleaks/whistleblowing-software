// Defines the main app module. This one does the top level app wiring.

define(function (require) {
    'use strict';

    var $ = require('jquery');
    var latenza = require('latenza');
    var pages = require('latenza/pages');

    // Dependencies that do not have an export of their own, just attach
    // to other objects, like jQuery. These are just used in the example
    // bootstrap modal, not directly in the UI for the network and appCache
    // displays.
    require('bootstrap/modal');
    require('bootstrap/transition');

    // Wait for the DOM to be ready before showing the network and appCache
    // state.
    $(function () {
        // Enable the UI bindings for the network and appCache displays
        require('./uiNetwork')();
        require('./uiAppCache')();
        require('./uiWebAppInstall')();
        require('./uiSubmission')();

        require(['latenza/pages'], function(pages) {
            latenza.ajax({url: "/latenza"}).done(function(data){
                var website = JSON.parse(data);
                pages.menu(website.menu, '.menuElement');
                pages.content(website.content, '.contentElement');
            });
        });

        //var menuHandler = new pages.menu('.menuElement');
        //var contentHandler = new pages.content('.contentElement');
        //var siteHandler = new pages.site();


    });
});
