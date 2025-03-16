const puppeteer = require('puppeteer');

async function captureScreenshot(url, outputPath) {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    await page.goto(url);
    await page.screenshot({ path: outputPath });
    await browser.close();
}

// Usage: captureScreenshot('http://yourwebsite.com', 'screenshot.png');
captureScreenshot('http://example.com', 'screenshot.png');
