const { defineConfig } = require('@vue/cli-service')
const apiProxyTarget = process.env.VUE_APP_API_PROXY_TARGET || 'http://127.0.0.1:8000'

module.exports = defineConfig({
  transpileDependencies: true,
  chainWebpack: (config) => {
    // Use a glob-based ignore to avoid absolute-path glob issues on Windows paths with parentheses.
    config.plugin('copy').tap((args) => {
      if (args && args[0] && Array.isArray(args[0].patterns) && args[0].patterns[0]) {
        const pattern = args[0].patterns[0]
        pattern.globOptions = pattern.globOptions || {}
        pattern.globOptions.ignore = ['**/.DS_Store', '**/index.html']
      }
      return args
    })
  },
  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true
      }
    }
  }
})
