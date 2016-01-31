exports.config = {
  framework: 'jasmine',

  baseUrl: 'http://127.0.0.1:8082/',

  troubleshoot: true,
  directConnect: true,

  specs: [
    'tests/end2end/test-init.js',
    'tests/end2end/test-admin-perform-wizard.js',
    'tests/end2end/test-admin-login.js',
    'tests/end2end/test-admin-configure-node.js',
    'tests/end2end/test-admin-configure-users.js',
    'tests/end2end/test-admin-configure-contexts.js',
    'tests/end2end/test-receiver-first-login.js',
    'tests/end2end/test-globaleaks-process.js'
  ],

  capabilities: {
    'browserName': 'firefox'
  },

  jasmineNodeOpts: {
    isVerbose: true,
    includeStackTrace: true,
    defaultTimeoutInterval: 60000
  }
};
