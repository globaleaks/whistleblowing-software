// Manages the UI for showing a web apps install button.
// Use Firefox Nightly to try this out. This is important for B

/*global window, navigator, location, console */

define(function (require) {
    'use strict';

    var $ = require('jquery'),
        dom;


    // Trigger the web app install. The web app install uses
    // a manifest file that is documented here:
    // https://developer.mozilla.org/en/Apps/Manifest
    // NOTE: the icon paths in the manifest are absolute URLs,
    // and only one app is allowed to be installed per unique domain.
    // So when testing, be sure to serve the index.html from the
    // root of a test domain. It is best to map the domain in your
    // /etc/hosts file to 127.0.0.1 when testing locally.
    // Also, currently the URL to install() needs to be a complete
    // URL with protocol and domain.
    function onInstallClick(evt) {
        var errorDom = dom.find('.webapp-error'),
            installRequest = navigator.mozApps.install(location.href + 'manifest.webapp');

        installRequest.onsuccess = function (data) {
            // Hide error just incase it was showing.
            errorDom.hide();

            // Installed now so no need to show the install button.
            dom.find('.webapp-install').hide();
        };

        installRequest.onerror = function (error) {
            errorDom.find('webapp-error-details')
                    .text(error.toString())
                    .end()
                .show();
        };
    }

    // Return a function that can be called to do the DOM binding given a
    // jQuery DOM object to use as the parent container.
    return function uiWebAppInstall(parentDom) {
        // Use the body element if no parentDom provided
        dom = parentDom = parentDom || $('body');

        var apps = navigator.mozApps,
            request;

        // Test if web app installation is available. If so, test if
        // installed. See here for more information:
        // https://developer.mozilla.org/en/Apps/Getting_Started
        if (apps) {
            request = apps.getSelf();
            request.onsuccess = function () {
                if (this.result) {
                    // installed, nothing to do.
                } else {
                    // Not installed, show installation button.
                    parentDom.find('.webapp-install')
                        .bind('click', onInstallClick)
                        .show();
                }
            };

            request.onerror = function () {
                // Just console log it, no need to bother the user.
                console.log('mozApps error: ', this.error.message);
            };
        }
    };
});