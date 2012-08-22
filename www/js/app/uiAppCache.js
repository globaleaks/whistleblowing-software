// Manages the UI for showing the appCache state and button actions.

/*global window */

define(function (require) {
    'use strict';

    var $ = require('jquery'),
        appCache = require('appCache');

    // Return a function that can be called to do the DOM binding given a
    // jQuery DOM object to use as the parent container.
    return function uiAppCache(parentDom) {

        // Use the body element if no parentDom provided
        parentDom = parentDom || $('body');

        // Grab the DOM pieces used in the appCache UI
        var appCacheStatusDom = parentDom.find('.appCacheStatus'),
            appCacheEventDom = parentDom.find('.appCacheEvent'),
            updateAlertDom = parentDom.find('.updateAlert'),
            checkUpdateDom = parentDom.find('.checkUpdate'),
            eventSectionDom = parentDom.find('.eventSection');

        // Function that shows updates to the appCache state.
        function updateAppCacheDisplay(eventName, evt) {
            var message;

            appCacheStatusDom.text(appCache.getStatusName());

            // Make sure the check for update button and event list are visible.
            checkUpdateDom.show();
            eventSectionDom.show();

            if (eventName) {
                if (eventName === 'updateready') {
                    updateAlertDom.show();
                } else {
                    updateAlertDom.hide();
                }

                message = eventName;
                if (eventName === 'progress' && evt.total) {
                    message += ': ' + evt.loaded + ' of ' + evt.total;
                } else if (eventName === 'error') {
                    message += ': make sure the manifest file is in the correct ' +
                               'place and .appcache files are served with MIME ' +
                               'type: text/cache-manifest';
                }
                appCacheEventDom.prepend('<div>' + message + '</div>');
            }
        }

        // Listen for any of the appCache events.
        appCache.eventNames.forEach(function (name) {
            appCache.on(name, function (evt) {
                updateAppCacheDisplay(name, evt);
            });
        });

        // Wire up appCache-related button.
        parentDom.find('.updateButton').on('click', function (evt) {
            appCache.swapCache();
            window.location.reload();
        });
        parentDom.find('.checkUpdate').on('click', function (evt) {
            appCache.update();
        });
    };
});
