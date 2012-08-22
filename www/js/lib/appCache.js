/*global navigator, window */

define(function () {
    'use strict';

    var cache = window.applicationCache,
        appCache;

    /**
     * A helper module for dealing with window.applicationCache:
     * https://developer.mozilla.org/en/Using_Application_Cache
     */
    appCache = {
        cache: window.applicationCache,

        statusNames: [
            'uncached',
            'idle',
            'checking',
            'downloading',
            'updateready',
            'obsolete'
        ],

        // Valid event names and descriptions taken from:
        // http://www.html5rocks.com/en/tutorials/appcache/beginner/
        eventNames: [
            'cached', // fired after first cache of manifest.
            'checking', // checking for an event. Always the first event.
            'downloading', // update found, browser is downloading resources.
            'error', // 404 or 410 for manifest, downloading failed, or manifest changed.
            'noupdate', // fired after frist download of the manifest.
            'obsolete', // 404 or 410 for manifest. The appcache will be deleted.
            'progress', // fired for each resource listed in manifest as it is fetched
            'updateready' // all manifest resources have been freshly downloaded.
        ],

        getStatus: function () {
            return cache.status;
        },

        getStatusName: function () {
            return appCache.statusNames[cache.status] || 'unknown';
        },

        update: function () {
            return cache.update();
        },

        swapCache: function () {
            return cache.swapCache();
        },

        abort: function () {
            return cache.abort();
        },

        /**
         * Listen to an appCache event. See eventNames above for a list
         * of valid event names.
         */
        on: function (name, func) {
            return cache.addEventListener(name, func, false);
        },

        /**
         * Remove a listener for an appCache event.
         */
        removeListener: function(name, func) {
            return cache.removeEventListener(name, func, false);
        }
    };

    return appCache;
});