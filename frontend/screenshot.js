/**
 * ThinkTwice Screenshot Utility
 *
 * Captures responsive screenshots of the application.
 *
 * Usage:
 *   node screenshot.js                          # Default: desktop + mobile
 *   node screenshot.js --url http://localhost:3000
 *   node screenshot.js --device desktop         # Only desktop
 *   node screenshot.js --device mobile          # Only mobile
 *   node screenshot.js --width 1440 --height 900
 *   node screenshot.js --output ./screenshots
 *   node screenshot.js --full-page              # Full page capture
 *   node screenshot.js --delay 2000             # Wait 2s for animations
 *
 * Options:
 *   --url       Base URL to capture (default: http://localhost:3000)
 *   --device    Device preset: desktop, mobile, tablet, or all (default: all)
 *   --width     Custom viewport width (overrides device preset)
 *   --height    Custom viewport height (overrides device preset)
 *   --output    Output directory for screenshots (default: current directory)
 *   --full-page Capture the full scrollable page (default: viewport only)
 *   --delay     Extra delay in ms after page load (default: 1500)
 *   --help      Show this help message
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const DEVICES = {
  desktop: { width: 1280, height: 900, name: 'desktop' },
  mobile: { width: 390, height: 844, name: 'mobile' },
  tablet: { width: 820, height: 1180, name: 'tablet' },
};

function parseArgs(args) {
  const config = {
    url: 'http://localhost:3000',
    device: 'all',
    width: null,
    height: null,
    output: '.',
    fullPage: false,
    delay: 1500,
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--url':
        config.url = args[++i];
        break;
      case '--device':
        config.device = args[++i];
        break;
      case '--width':
        config.width = parseInt(args[++i], 10);
        break;
      case '--height':
        config.height = parseInt(args[++i], 10);
        break;
      case '--output':
        config.output = args[++i];
        break;
      case '--full-page':
        config.fullPage = true;
        break;
      case '--delay':
        config.delay = parseInt(args[++i], 10);
        break;
      case '--help':
        console.log(fs.readFileSync(__filename, 'utf8').match(/\/\*\*([\s\S]*?)\*\//)?.[0] || '');
        process.exit(0);
    }
  }

  return config;
}

function getViewports(config) {
  if (config.width && config.height) {
    return [{ width: config.width, height: config.height, name: `${config.width}x${config.height}` }];
  }

  if (config.device === 'all') {
    return [DEVICES.desktop, DEVICES.mobile];
  }

  const device = DEVICES[config.device];
  if (!device) {
    console.error(`Unknown device: ${config.device}. Available: ${Object.keys(DEVICES).join(', ')}, all`);
    process.exit(1);
  }

  return [device];
}

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function captureScreenshot(page, viewport, config) {
  const filename = `screenshot-${viewport.name}.png`;
  const filepath = path.join(config.output, filename);

  await page.setViewport({ width: viewport.width, height: viewport.height });
  await page.goto(config.url, { waitUntil: 'networkidle0', timeout: 30000 });
  await delay(config.delay);
  await page.screenshot({ path: filepath, fullPage: config.fullPage });

  const stats = fs.statSync(filepath);
  const sizeKb = (stats.size / 1024).toFixed(0);
  console.log(`  ${filename} (${viewport.width}x${viewport.height}) - ${sizeKb}KB`);

  return filepath;
}

(async () => {
  const config = parseArgs(process.argv.slice(2));
  const viewports = getViewports(config);

  if (config.output !== '.' && !fs.existsSync(config.output)) {
    fs.mkdirSync(config.output, { recursive: true });
  }

  console.log(`Capturing screenshots from ${config.url}...`);

  let browser;
  try {
    browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();

    for (const viewport of viewports) {
      await captureScreenshot(page, viewport, config);
    }

    console.log('Done!');
  } catch (error) {
    console.error('Screenshot failed:', error.message);
    console.error('Make sure the application is running at', config.url);
    process.exit(1);
  } finally {
    if (browser) await browser.close();
  }
})();
