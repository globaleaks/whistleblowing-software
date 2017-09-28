// Adapted from https://github.com/rikukissa/angular-test-examples/blob/master/test-helper.js

var jsdom = require('jsdom').JSDOM;

var document = global.document = new jsdom('<html><head><script></script></head><body></body></html>');

var window = global.window = document.window;

global.navigator = window.navigator = {};
global.Node = window.Node;

global.window.mocha = {};
global.window.beforeEach = beforeEach;
global.window.afterEach = afterEach;

/*
 *  * Only for NPM users
 *   */
require('angular/angular');
require('angular-mocks');

global.angular = window.angular;
global.inject = global.angular.mock.inject;
global.ngModule = global.angular.mock.module;
