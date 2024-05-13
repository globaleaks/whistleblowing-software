import * as path from "path";

export default {
  module: {
    rules: [
      {
        test: /\.(js|ts)$/,
        loader: "@jsdevtools/coverage-istanbul-loader",
        options: {esModules: true},
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
