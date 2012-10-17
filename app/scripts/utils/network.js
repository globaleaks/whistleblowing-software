/*global navigator, window */

define(function () {
    'use strict';

    /**
     * Module for returning the network state, and for listening for
     * changes in the network state.
     *
     * Note: Different browsers use different triggers for online vs
     * offline. See the details in:
     *
     * https://developer.mozilla.org/en/DOM/window.navigator.onLine
     * and
     * http://www.html5rocks.com/en/mobile/workingoffthegrid.html
     */
    function network() {
        return navigator.onLine;
    }

    /**
     * Listen to a network event.
     * The two acceptable state values are 'online' and 'offline'
     */
    network.on = function (state, func) {
        return window.addEventListener(state, func, false);
    };

    /**
     * Remove a listener for a network event.
     * The two acceptable state values are 'online' and 'offline'
     */
    network.removeListener = function(state, func) {
        return window.removeEventListener(state, func, false);
    };

    return network;
});
