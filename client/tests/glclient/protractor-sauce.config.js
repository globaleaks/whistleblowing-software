browser_capabilities = JSON.parse(process.env.SELENIUM_BROWSER_CAPABILITIES)
browser_capabilities['name'] = 'GlobaLeaks Travis Test using Protractor'
browser_capabilities['tunnel-identifier'] = process.env.TRAVIS_JOB_NUMBER
browser_capabilities['build'] = process.env.TRAVIS_BUILD_NUMBER

exports.config = {
  sauceUser: process.env.SAUCE_USERNAME,
  sauceKey: process.env.SAUCE_ACCESS_KEY,
  capabilities: browser_capabilities,

  baseUrl: 'http://localhost:8082/',

  framework: 'jasmine',

  specs: [
    'test-wizard.js',
  ],

  jasmineNodeOpts: {
    showColors: true,
  }
};
