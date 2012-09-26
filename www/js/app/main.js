// Defines the main app module. This one does the top level app wiring.

define(function (require) {
    'use strict';

    var $ = require('jquery');
    var latenza = require('latenza');

    // Dependencies that do not have an export of their own, just attach
    // to other objects, like jQuery. These are just used in the example
    // bootstrap modal, not directly in the UI for the network and appCache
    // displays.
    require('bootstrap');

    require('datatables');

    // Wait for the DOM to be ready before showing the network and appCache
    // state.
    $(function () {
        require('./routes')();
        // Enable the UI bindings for the network and appCache displays
        require('./uiNetwork')();
        require('./uiAppCache')();
        require('./uiWebAppInstall')();
        $('#tor2web').hide();
        //require('./uiSubmission')();

    });
});
