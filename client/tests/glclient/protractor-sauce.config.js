browser_capabilities = JSON.parse(process.env.TEST_E2E)
browser_capabilities['name'] = 'GlobaLeaks Travis Test using Protractor'
browser_capabilities['tunnel-identifier'] = process.env.TRAVIS_JOB_NUMBER
browser_capabilities['build'] = process.env.TRAVIS_BUILD_NUMBER

exports.config = {
  sauceUser: process.env.SAUCE_USERNAME,
  sauceKey: process.env.SAUCE_ACCESS_KEY,
  capabilities: browser_capabilities,

  framework: 'jasmine2',

  baseUrl: 'http://localhost:8080/',

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

  jasmineNodeOpts: {
    showColors: true,
  }
};
