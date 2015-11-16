exports.config = {
  framework: 'jasmine2',

  baseUrl: 'http://127.0.0.1:8082/',

  troubleshoot: true,
  directConnect: false,

  specs: [
    'tests/end2end/test-init.js',
    'tests/end2end/test-admin-perform-wizard.js',
    'tests/end2end/test-admin-login.js',
    'tests/end2end/test-admin-configure-node.js',
    'tests/end2end/test-admin-configure-receivers.js',
    'tests/end2end/test-admin-configure-contexts.js',
    'tests/end2end/test-receiver-first-login.js',
    'tests/end2end/test-globaleaks-process.js'
  ],

  capabilities: {
    'browserName': 'firefox'
  },

  jasmineNodeOpts: {
   isVerbose: true,
  }
};
