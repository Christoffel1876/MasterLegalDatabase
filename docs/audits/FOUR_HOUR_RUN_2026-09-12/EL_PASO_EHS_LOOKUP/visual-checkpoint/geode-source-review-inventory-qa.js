const fs = require('fs');
const assert = require('assert/strict');
const path = require('path');
const crypto = require('crypto');
const {chromium} = require('/Users/mcoors/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');

(async () => {
  const output = __dirname;
  const fragment = path.join(output, 'geode-source-review-inventory.html');
  const original = fs.readFileSync(fragment);
  const browser = await chromium.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true,
    args: ['--disable-background-networking', '--disable-component-update', '--no-first-run']
  });
  const results = [];
  const errors = [];
  try {
    for (const theme of ['light', 'dark']) {
      for (const width of [736, 360]) {
        const context = await browser.newContext({viewport: {width, height: 1200}, colorScheme: theme});
        await context.route('**/*', route => {
          const url = new URL(route.request().url());
          return url.hostname === '127.0.0.1' ? route.continue() : route.abort();
        });
        const page = await context.newPage();
        page.on('pageerror', error => errors.push(String(error)));
        await page.goto(`http://127.0.0.1:8788/geode-source-review-inventory-preview-${theme}.html`);
        const frame = page.frames().find(item => item !== page.mainFrame());
        await frame.locator('#geode-review-inventory [data-source-id]').first().waitFor();
        assert.equal(await frame.locator('[data-source-id]').count(), 61);
        assert.equal(await frame.locator('.inv-cell[data-mapped="true"]').count(), 22);
        assert.equal(await frame.locator('.inv-cell[data-mapped="false"]').count(), 39);
        assert.equal(await frame.locator('#geode-review-inventory').getAttribute('data-selected-source'), 'el-paso-boh-ehs-fees-sd011');
        const rows = await frame.locator('#inv-source-data').evaluate(node => JSON.parse(node.textContent));
        for (const row of rows) {
          await frame.locator(`[data-source-id="${row.id}"]`).click();
          assert.equal(await frame.locator('#geode-review-inventory').getAttribute('data-selected-source'), row.id);
          assert.equal(await frame.locator('[data-source-id][aria-pressed="true"]').count(), 1);
          assert.equal(await frame.locator('#inv-selected-scope').textContent(), row.scope || 'No review artifact is mapped in this inventory; prior inspection may still exist.');
          assert.equal(await frame.locator('#inv-selected-limit').textContent(), row.limit || 'Current legal effect, completeness and applicability remain unverified.');
        }
        await frame.locator('[data-source-id="larimer-equity-fee-resolution-sd007-04"]').press('Enter');
        assert.equal(await frame.locator('#geode-review-inventory').getAttribute('data-selected-source'), 'larimer-equity-fee-resolution-sd007-04');
        assert.match(await frame.locator('#inv-selected-limit').textContent(), /20243.*legal dates unverified/);
        await frame.locator('[data-source-id="el-paso-planning-fees-sd011"]').press('Enter');
        assert.match(await frame.locator('#inv-selected-limit').textContent(), /Native text is empty.*clipped.*included/);
        await frame.locator('[data-source-id="colorado-springs-construction-fees-atlas-directed"]').press('Enter');
        assert.match(await frame.locator('#inv-selected-scope').textContent(), /128 fee rows.*13 definitions/);
        assert.match(await frame.locator('#inv-selected-limit').textContent(), /PPRBD.*Code Services/);
        await frame.locator('[data-source-id="el-paso-boh-ehs-fees-sd011"]').press('Enter');
        assert.match(await frame.locator('#inv-selected-scope').textContent(), /65 service\/fee rows.*37 context/);
        assert.match(await frame.locator('#inv-selected-limit').textContent(), /2024\/2025.*Spanish equivalence unverified/);
        const layout = await frame.evaluate(() => {
          const root = document.getElementById('geode-review-inventory');
          const bad = Array.from(root.querySelectorAll('*')).filter(node => {
            if (['SCRIPT', 'STYLE'].includes(node.tagName)) return false;
            const rect = node.getBoundingClientRect();
            return rect.width > 0 && (rect.left < -1 || rect.right > innerWidth + 1);
          }).map(node => ({tag: node.tagName, id: node.id, className: node.className}));
          return {innerWidth, rootWidth: root.getBoundingClientRect().width, overflow: bad,
                  rootHeight: root.getBoundingClientRect().height};
        });
        assert.deepEqual(layout.overflow, []);
        await page.locator('iframe').evaluate((node, height) => {
          node.style.height = `${height + 4}px`;
        }, layout.rootHeight);
        await frame.evaluate(() => window.scrollTo(0, 0));
        await page.evaluate(() => window.scrollTo(0, 0));
        const screenshot = `geode-source-review-inventory-${theme}-${width}.png`;
        await page.screenshot({path: path.join(output, screenshot), fullPage: true});
        results.push({theme, width, selections_checked: rows.length, layout, screenshot});
        await context.close();
      }
    }
    assert.deepEqual(errors, []);
    assert.deepEqual(fs.readFileSync(fragment), original);
    const report = {status: 'passed', fragment_sha256: crypto.createHash('sha256').update(original).digest('hex'),
                    source_inventory_sha256: 'c6a6a68ae65c27d40ce004bff821858917a94340ab3bf38e4eea344cd40b3458',
                    network_boundary: 'localhost preview only; other page requests aborted',
                    errors, results};
    fs.writeFileSync(path.join(output, 'geode-source-review-inventory-qa.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
