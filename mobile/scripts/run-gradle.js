/**
 * Cross-platform Gradle execution helper for Android builds.
 * Runs gradlew.bat on Windows or ./gradlew on Linux/macOS.
 */

const { spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const targetTask = process.argv[2] || 'assembleDebug';
const androidDir = path.resolve(__dirname, '..', 'android');

if (!fs.existsSync(androidDir)) {
  console.error('Error: Android project directory not found at', androidDir);
  console.error('Please run "npm run android:sync" first to generate the Android project.');
  process.exit(1);
}

const isWindows = process.platform === 'win32';
const gradlewCmd = isWindows ? 'gradlew.bat' : './gradlew';
const gradlewPath = path.join(androidDir, gradlewCmd);

console.log(`==> Executing: ${gradlewCmd} ${targetTask} in ${androidDir}`);

if (fs.existsSync(gradlewPath)) {
  const result = spawnSync(gradlewCmd, [targetTask], {
    cwd: androidDir,
    stdio: 'inherit',
    shell: true,
    env: process.env,
  });
  process.exit(result.status || 0);
} else {
  console.log(`[Notice] Gradle wrapper not found at ${gradlewPath}.`);
  console.log('To build Android APK / AAB locally:');
  console.log('1. Install Android Studio & Android SDK');
  console.log('2. Run: npx cap add android');
  console.log(`3. Run: cd android && ${gradlewCmd} ${targetTask}`);
  process.exit(0);
}
