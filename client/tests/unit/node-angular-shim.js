// Adapted from https://github.com/rikukissa/angular-test-examples/blob/master/test-helper.js

var openpgp = require('./../../app/js/lib/openpgp');

var jsdom = require('jsdom').JSDOM;

var document = global.document = new jsdom('<html><head><script></script></head><body></body></html>');

var window = global.window = document.window;

global.navigator = window.navigator = {};
global.Node = window.Node;

global.window.mocha = {};
global.window.beforeEach = beforeEach;
global.window.afterEach = afterEach;

global.window.Worker = require('webworker-threads').Worker;

require('angular/angular');
require('angular-mocks');


c = require('crypto');
console.log('detected crypto', c);

global.angular = window.angular;
global.inject = global.angular.mock.inject;
global.ngModule = global.angular.mock.module;

global.openpgp = window.openpgp = openpgp;

//require('./../../app/js/app');
//require('./../../app/js/lib/angular-filter.min');
require('./../../app/js/crypto/main');
require('./../../app/js/crypto/user');
require('./../../app/js/crypto/receiver');
require('./../../app/js/crypto/whistleblower');
require('./module');

require('./unittest');
