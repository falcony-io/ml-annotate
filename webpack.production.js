const merge = require('webpack-merge');
const webpack = require('webpack');
const common = require('./webpack.config');

module.exports = merge.smart(common, {
  plugins: [
    new webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify('production')
    }),
    new webpack.optimize.UglifyJsPlugin(),
  ],
  devtool: 'source-map',
});
