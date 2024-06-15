const fs = require('fs')
const path = require('path')

module.exports = (on, config) => {
  require('@cypress/code-coverage/task')(on, config)
  on('file:preprocessor', require('@cypress/code-coverage/use-babelrc'))

  on('before:browser:launch', (browser, launchOptions) => {
    if (browser.family === 'chromium') {
      launchOptions.args.push('--window-size=1920,1080')
      launchOptions.args.push('--force-device-scale-factor=1');
      launchOptions.args.push('--force-color-profile=srgb');
      launchOptions.args.push('--disable-low-res-tiling');
      launchOptions.args.push('--disable-smooth-scrolling');
    }
    return launchOptions;
  });

  on('after:screenshot', (details) => {
    if (details.path.includes('failed')) {
      return;
    }

    return new Promise((resolve, reject) => {
      newPath = __dirname + "/../../../documentation/images/" + details.path.split('/').slice(-2).join('/')

      fs.copyFile(details.path, newPath, (err) => {
        if (err) return reject(err)

        resolve({ path: newPath })
      })
    })
  })

  return config
}
