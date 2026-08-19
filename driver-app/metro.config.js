const { getDefaultConfig, mergeConfig } = require('@react-native/metro-config');
const fs = require('fs');
const path = require('path');

// Metro must resolve pnpm's linked dependencies through the real workspace path.
// This keeps bundling stable when the app is opened from a Windows SUBST drive.
const realProjectRoot = fs.realpathSync.native(__dirname);
const workspaceRoot = path.dirname(realProjectRoot);
const workspaceNodeModules = path.join(workspaceRoot, 'node_modules');
const babelRuntimeRoot = path.join(realProjectRoot, 'node_modules', '@babel', 'runtime');

// Native CMake output is transient: Gradle creates and removes these folders
// while Metro is scanning pnpm's shared package store. Watching it causes
// Windows to throw ENOENT when a generated folder disappears mid-scan.
const generatedCacheOutputs = [
  /[\\/]android[\\/]\.cxx(?:[\\/]|$)/,
  /[\\/]\.pytest_cache(?:[\\/]|$)/,
  /[\\/]\.gradle(?:[\\/]|$)/,
];

function resolveBabelRuntime(moduleName) {
  if (moduleName !== '@babel/runtime' && !moduleName.startsWith('@babel/runtime/')) {
    return null;
  }

  const relativeModulePath = moduleName.replace('@babel/runtime', '').replace(/^\//, '');
  const basePath = path.join(babelRuntimeRoot, relativeModulePath);
  const candidates = [basePath, `${basePath}.js`, path.join(basePath, 'index.js')];
  return candidates.find(candidate => fs.existsSync(candidate)) ?? null;
}

const config = getDefaultConfig(__dirname);

module.exports = mergeConfig(config, {
  // Watching the full workspace makes Metro scan Passenger, Backend, build output,
  // and caches. Only pnpm's shared package directory is needed by Driver.
  watchFolders: [workspaceNodeModules],
  resolver: {
    blockList: generatedCacheOutputs,
    unstable_enableSymlinks: true,
    nodeModulesPaths: [
      path.join(realProjectRoot, 'node_modules'),
      workspaceNodeModules,
      path.join(__dirname, 'node_modules'),
    ],
    resolveRequest: (context, moduleName, platform) => {
      const runtimeFile = resolveBabelRuntime(moduleName);
      if (runtimeFile) return { type: 'sourceFile', filePath: runtimeFile };
      return context.resolveRequest(context, moduleName, platform);
    },
  },
});
