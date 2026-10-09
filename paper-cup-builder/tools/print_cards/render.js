// Renders the front / side / top views of all 12 preset groups for the A4 contest cards.
//
//   node tools/print_cards/render.js [background-gray]      (run from the paper-cup-builder folder)
//
// Needs Node and Playwright with a Chromium build:  npm install playwright && npx playwright install chromium
// (or set CHROME_PATH to an existing Chrome / Chromium executable).
// Output: tools/print_cards/out/<group>_<view>.png and meta.json, then run compose.py.
const fs = require('fs'), path = require('path');
let chromium; try { ({ chromium } = require('playwright')); } catch (e) { ({ chromium } = require('playwright-core')); }

const ROOT = path.resolve(__dirname, '..', '..');
const OUT = path.join(__dirname, 'out');
const BG = process.argv[2] || '#c4c8ca';            // one gray for all three views, light enough that black straws stand out
const IDS = ['r1g1','r1g2','r1g3','r1g4','r1g5','r1g6','r2g1','r2g2','r2g3','r2g4','r2g5','r2g6'];
const IW = 2240, IH = 1000, MARGIN = 2.5;           // image size in px (300 dpi strip) and cm of air around the content
const HOOK = `
  // ---- print hook (injected by tools/print_cards/render.js) ----
  window.__print = {
    setup: function (bg) {
      tint = false; rebuild();
      M.inside.color.set(0xe8e7e3); M.insideFloor.color.set(0xe1dfda);
      scene.background = new THREE.Color(bg);
      floor.material = new THREE.MeshBasicMaterial({ color: new THREE.Color(bg) });
      grid.visible = false; ghost.visible = false;
    },
    load: function (id) { loadPreset(id, false); tint = false; rebuild(); },
    bounds: function () {
      var b = new THREE.Box3().setFromObject(model);
      return { min: [b.min.x, b.min.y, b.min.z], max: [b.max.x, b.max.y, b.max.z], side: state.side, topUp: state.topUp };
    },
    render: function (v, w, h, cmPerPx, cx, cy) {
      // cx: horizontal centre in world units for this view; cy: for top view the second axis centre
      var W = w * cmPerPx / 2, Hh = h * cmPerPx;
      grid.visible = false; ghost.visible = false;
      ortho.left = -W; ortho.right = W;
      if (v === 'top') {
        ortho.top = Hh / 2; ortho.bottom = -Hh / 2;
        var up = state.topUp || [0, -1]; ortho.up.set(up[0], 0, up[1]);
        ortho.position.set(cx, 500, cy); ortho.lookAt(cx, 0, cy);
      } else {
        var base = 2.2;                       // cm of floor shown below the table line
        ortho.bottom = -base; ortho.top = Hh - base; ortho.up.set(0, 1, 0);
        if (v === 'front') { ortho.position.set(cx, 0, 500); ortho.lookAt(cx, 0, 0); }
        else { var sx = state.side === 'L' ? -500 : 500; ortho.position.set(sx, 0, cx); ortho.lookAt(0, 0, cx); }
      }
      ortho.near = 0.1; ortho.far = 2000; ortho.updateProjectionMatrix();
      mini.setSize(w, h, false); mini.render(scene, ortho);
      return mini.domElement.toDataURL('image/png');
    }
  };
`;

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8').replace('  window.__cupTool = {', HOOK + '  window.__cupTool = {');
  const tmp = path.join(ROOT, '.print_tmp.html'); fs.writeFileSync(tmp, html);
  const opts = { args: ['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'] };
  if (process.env.CHROME_PATH) opts.executablePath = process.env.CHROME_PATH;
  const b = await chromium.launch(opts);
  try {
    const p = await (await b.newContext({ viewport: { width: 1280, height: 1000 }, locale: 'zh-CN' })).newPage();
    p.on('pageerror', e => console.error('page error:', e.message));
    await p.goto('file://' + tmp); await p.waitForTimeout(1500);
    await p.evaluate(bg => window.__print.setup(bg), BG);
    const meta = { background: BG, groups: {} };
    for (const id of IDS) {
      await p.evaluate(id => window.__print.load(id), id); await p.waitForTimeout(150);
      const B = await p.evaluate(() => window.__print.bounds());
      const sx = B.max[0] - B.min[0], sy = B.max[1], sz = B.max[2] - B.min[2];
      const alongX = Math.abs(B.topUp[0]) > 0.5;      // top view turned 90°: screen vertical = world x
      // one scale per group, shared by its three views so they line up like a real three-view drawing
      let cm = 0;
      for (const [w, h] of [[sx, sy + 2.2], [sz, sy + 2.2], alongX ? [sz, sx] : [sx, sz]]) cm = Math.max(cm, (w + 2 * MARGIN) / IW, (h + MARGIN) / IH);
      const c = [(B.min[0] + B.max[0]) / 2, (B.min[2] + B.max[2]) / 2];
      for (const v of ['front', 'side', 'top']) {
        const url = await p.evaluate(([v, w, h, cm, cx, cy]) => window.__print.render(v, w, h, cm, cx, cy), [v, IW, IH, cm, v === 'side' ? c[1] : c[0], c[1]]);
        fs.writeFileSync(path.join(OUT, `${id}_${v}.png`), Buffer.from(url.split(',')[1], 'base64'));
      }
      meta.groups[id] = { side: B.side, cmPerPx: cm };
      console.log(id, '1 cup =', (7.6 / cm / 300 * 25.4).toFixed(1), 'mm on paper');
    }
    fs.writeFileSync(path.join(OUT, 'meta.json'), JSON.stringify(meta, null, 1));
  } finally { await b.close(); fs.unlinkSync(tmp); }
})();
