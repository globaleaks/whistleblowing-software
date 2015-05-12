exports.config = {
  seleniumAddress: 'http://localhost:4444/wd/hub',

  troubleshoot: true,
  directConnect: true,

  specs: [
    'test-init.js',
    'test-admin-perform-wizard.js',
    'test-admin-login.js',
    'test-admin-grant-tor2web-permissions.js',
    'test-admin-add-receivers.js'
  ],

  capabilities: {
    'browserName': 'firefox'
  },

  framework: 'jasmine2',

  jasmineNodeOpts: {
   isVerbose: true,
   //defaultTimeoutInterval: 30000
  },

  baseUrl: 'http://127.0.0.1:8082/',

  onPrepare: function() {
     browser.driver.manage().window().setSize(1200, 600);
  },
}


