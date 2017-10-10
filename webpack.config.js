var webpack = require('webpack');
var path = require('path');
var node_modules_dir = path.join(__dirname, 'node_modules');

module.exports = {
    devtool: 'inline-cheap-module-source-map',
    entry: path.resolve(__dirname, 'annotator/static/js/index.js'),
    module: {
        rules: [
            {
                test: /\.js$/,
                use: {
                  loader: 'babel-loader',
                  options: {
                    presets: ['react-es2015']
                  }
                },
                exclude: node_modules_dir,
                include: path.join(__dirname, 'annotator/static/js/')
            },
        ]
    },
    plugins: [
        new webpack.ProvidePlugin({
          jQuery: 'jquery',
          $: 'jquery',
          jquery: 'jquery'
        })
    ],
}
