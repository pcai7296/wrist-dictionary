const path = require("path")

class ConditionalCompilationPlugin {
  apply(compiler) {
    const context = compiler.options.context
    compiler.options.module.rules.push({
      enforce: "pre",
      test: /\.(?:(s[ac]|le|c)ss|[mc]?[jt]sx?|json|html|vue|ux)$/,
      use: path.resolve(context, "scripts/conditionalCompilationLoader.js"),
      exclude: [path.resolve(context, "node_modules")]
    })
  }
}

module.exports = ConditionalCompilationPlugin
