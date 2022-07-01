const path = require('path');

module.exports = {
  mode: "production",
  devtool: "inline-source-map",
  entry: {
    main: "./ts/main.ts",
  },
  output: {
    path: path.resolve(__dirname, './js'),
    filename: "exafs-bundle.js",
    libraryTarget: 'var',
    library: {
      name: 'ExaFS',
      type: 'var',
      umdNamedDefine: true
    }
  },
  resolve: {
    extensions: [".ts", ".tsx", ".js"],
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        loader: "ts-loader"
      }
    ]
  }
};