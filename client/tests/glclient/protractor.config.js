exports.config = {
  seleniumAddress: 'http://localhost:4444/wd/hub',

  framework: 'jasmine2',

  baseUrl: 'http://127.0.0.1:8082/',

  troubleshoot: true,
  directConnect: true,

  specs: [
    'test-init.js',
    'test-admin-perform-wizard.js',
    'test-admin-login.js',
    'test-admin-grant-tor2web-permissions.js',
    'test-admin-add-receivers.js',
    'test-admin-add-contexts.js',
    'test-receiver-first-login.js'
  ],

  capabilities: {
    'browserName': 'firefox'
  },

  jasmineNodeOpts: {
   isVerbose: true,
  }

}
