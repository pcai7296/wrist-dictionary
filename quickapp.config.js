const ConditionalCompilationWebpackPlugin = require("./scripts/conditionalCompilationPlugin")

module.exports = {
  cli: {
    enableJsc: true
  },
  webpack: {
    plugins: [new ConditionalCompilationWebpackPlugin()]
  }
}
