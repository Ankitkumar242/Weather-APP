/**
 * Build step for Capacitor WebDir.
 * Copies app/static and generates a standalone mobile index.html configured with API_BASE_URL.
 */

const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..', '..');
const STATIC_DIR = path.join(ROOT_DIR, 'app', 'static');
const TEMPLATES_DIR = path.join(ROOT_DIR, 'app', 'templates');
const DIST_DIR = path.resolve(__dirname, '..', 'dist');

function copyDirRecursive(src, dest) {
  if (!fs.existsSync(src)) return;
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      copyDirRecursive(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

console.log('==> Preparing Capacitor web distribution in /mobile/dist...');

// 1. Clean or recreate dist directory
if (fs.existsSync(DIST_DIR)) {
  fs.rmSync(DIST_DIR, { recursive: true, force: true });
}
fs.mkdirSync(DIST_DIR, { recursive: true });

// 2. Copy static files into dist/static
const distStatic = path.join(DIST_DIR, 'static');
copyDirRecursive(STATIC_DIR, distStatic);
console.log('✔ Copied app/static to dist/static');

// 3. Read template and generate mobile index.html
const templatePath = path.join(TEMPLATES_DIR, 'index.html');
let indexHtml = fs.readFileSync(templatePath, 'utf8');

// Replace Jinja2 variables
indexHtml = indexHtml.replace(/\{\{\s*app_name\s*\}\}/g, 'SkyPulse');

// Default API backend URL from environment or standard Render deployment
const apiBaseUrl = process.env.API_BASE_URL || 'https://skypulse.onrender.com';

// Inject mobile config before closing head tag
const mobileConfigScript = `
  <script>
    // Configured API backend for native Capacitor app
    window.API_BASE_URL = "${apiBaseUrl}";
    console.log("[SkyPulse Mobile] API backend configured:", window.API_BASE_URL);
  </script>
`;

indexHtml = indexHtml.replace('</head>', `${mobileConfigScript}\n</head>`);

// Write mobile index.html to dist root
fs.writeFileSync(path.join(DIST_DIR, 'index.html'), indexHtml, 'utf8');
console.log(`✔ Generated dist/index.html with API_BASE_URL = "${apiBaseUrl}"`);

// Also copy manifest and offline fallback to dist root
const manifestSrc = path.join(STATIC_DIR, 'manifest.webmanifest');
if (fs.existsSync(manifestSrc)) {
  fs.copyFileSync(manifestSrc, path.join(DIST_DIR, 'manifest.webmanifest'));
}
const offlineSrc = path.join(STATIC_DIR, 'offline.html');
if (fs.existsSync(offlineSrc)) {
  fs.copyFileSync(offlineSrc, path.join(DIST_DIR, 'offline.html'));
}

console.log('✨ Capacitor webDir build complete!');
