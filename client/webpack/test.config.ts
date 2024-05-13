import * as path from 'path';

const config = {
  output: {
    chunkFilename: 'js/lazy/[id].[chunkhash].js',
  },
  module: {
    rules: [
      {
        test: /\.(js|ts)$/,
        loader: "@jsdevtools/coverage-istanbul-loader",
        options: { esModules: true },
        enforce: "post",
        include: path.join(__dirname, "..", "app"),
        exclude: [
          /\.(e2e|spec)\.ts$/,
          /node_modules/,
          /(ngfactory|ngstyle)\.js/,
        ],
      },
    ],
  },
};

export default config;

