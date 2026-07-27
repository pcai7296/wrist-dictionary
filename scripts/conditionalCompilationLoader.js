const officialLoader = require("conditional-compilation-webpack-plugin/loader.js")

function isValidEnvironmentName(name) {
  return /^[A-Za-z_][A-Za-z0-9_]*$/.test(name)
}

module.exports = function conditionalCompilationLoader(source) {
  const originalEnv = process.env
  const safeEnv = {}
  Object.keys(originalEnv).forEach((name) => {
    if (isValidEnvironmentName(name)) {
      safeEnv[name] = originalEnv[name]
    }
  })
  process.env = safeEnv
  try {
    return officialLoader.call(this, source)
  } finally {
    process.env = originalEnv
  }
}
