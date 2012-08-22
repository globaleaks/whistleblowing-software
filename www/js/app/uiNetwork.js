// Manages the UI for showing the networks state.

/*global window */

define(function (require) {
    'use strict';

    var $ = require('jquery'),
        network = require('network'),
        latenza = require('latenza');

    // Return a function that can be called to do the DOM binding given a
    // jQuery DOM object to use as the parent container.
    return function uiNetwork(parentDom) {

        // Use the body element if no parentDom provided
        parentDom = parentDom || $('body');

        var latenzaBox = parentDom.find('.latenzaStatusBox');
        var networkDom = parentDom.find('.networkStatus');
        var latencyDom = parentDom.find('.latencyStatus');

        // Handles update to the DOM that shows the network state.
        function updateNetworkDisplay(on) {
            networkDom.text(on ? 'on' : 'off');
            networkDom.toggleClass('label-success', on);
            networkDom.toggleClass('label-important', !on);
        }

        function updateLatencyDisplay() {
            var rtt = latenza.latency;
            latencyDom.text(rtt + ' ms');
            if (rtt > 2000) {
                latencyDom.toggleClass('label-important');
            } else if (rtt > 1000) {
                latencyDom.toggleClass('label-warning');
            } else if (rtt == 'inf') {
                latencyDom.text('no data');
            } else {
                latencyDom.toggleClass('label-info');
            }
        }

        // Display the current network state.
        updateNetworkDisplay(network());

        latenza.getLatency(updateLatencyDisplay);

        // Listen for changes in the network.
        network.on('online', function () {
            updateNetworkDisplay(true);
        });
        network.on('offline', function () {
            updateNetworkDisplay(false);
        });

        latenzaBox.hover(function() {
            $(this).stop(true).fadeTo("fast", '1');
        }, function() {
            $(this).delay(800).fadeTo("slow", '0.4');
        });

    };
});
