/*global window */

define(function (require) {
    'use strict';

    var $ = require('jquery'),
        hasher = require('hasher'),
        crossroads = require('crossroads');

    return function myFunc(parentDom) {
        parentDom = parentDom || $('body');
        console.log($parentDom);
        $parentDom.find("#receiptNumber").focus(function(){
                // Select input field contents
                this.select();
        });

    };
});
