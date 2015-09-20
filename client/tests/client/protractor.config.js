exports.config = {
  framework: 'jasmine2',

  baseUrl: 'http://127.0.0.1:8082/',

  troubleshoot: true,
  directConnect: false,

  specs: [
    'test-init.js',
    'test-admin-perform-wizard.js',
    'test-admin-login.js',
    'test-admin-configure-node.js',
    'test-admin-add-receivers.js',
    'test-admin-add-contexts.js',
    'test-receiver-first-login.js',
    'test-globaleaks-process.js'
  ],

  capabilities: {
    'browserName': 'chrome'
  },

  jasmineNodeOpts: {
   isVerbose: true,
  };
};
