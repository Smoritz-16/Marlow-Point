(function() {
 'use strict';
 var PALETTES = {
  cyan: {
   name: 'ARCHIVE CYAN',
   bg: '#071014',
   primary: '#d8fbf7',
   secondary: '#64dfe6',
   accent: '#d9ff3f'
  },
  solar: {
   name: 'SOLAR TRACE',
   bg: '#14100b',
   primary: '#fff3d0',
   secondary: '#ffac3d',
   accent: '#ff5d38'
  },
  mono: {
   name: 'MONO SCHEMATIC',
   bg: '#0a0a0a',
   primary: '#f2f0e8',
   secondary: '#979991',
   accent: '#ffffff'
  },
  violet: {
   name: 'VIOLET DEPTH',
   bg: '#0e0915',
   primary: '#f5e9ff',
   secondary: '#b583ff',
   accent: '#ff8bd7'
  }
 };
 var DITHER = {
  cobalt: {
   ink: '#2446e8',
   paper: '#f3f0e7'
  },
  electric: {
   ink: '#243cdd',
   paper: '#fafafa'
  },
  cyan: {
   ink: '#00a6c8',
   paper: '#f4f5ed'
  },
  forest: {
   ink: '#08704f',
   paper: '#f1efe4'
  },
  signal: {
   ink: '#ef3d2f',
   paper: '#fff1df'
  },
  mono: {
   ink: '#101417',
   paper: '#f2efe6'
  }
 };
 var MEMORY = {
  cobalt: {
   ink: '#243ee4',
   paper: '#f3f0e8',
   accent: '#ff5d38'
  },
  archive: {
   ink: '#102a31',
   paper: '#dff4ef',
   accent: '#36d6dc'
  },
  signal: {
   ink: '#17191f',
   paper: '#f1aa72',
   accent: '#f5eee0'
  },
  mono: {
   ink: '#101214',
   paper: '#f1f2ef',
   accent: '#9b9f98'
  }
 };
 var D = {
  density: 50,
  threshold: 30,
  shapeMin: 6,
  shapeMax: 36,
  connection: 80,
  lineWeight: .7,
  scanlines: 30,
  grain: 20,
  baseOpacity: 70,
  labels: false,
  chain: false,
  grid: false,
  boxes: false
 };
 function look(o) {
  var r = {}, k;
  for (k in D) r[k] = D[k];
  for (k in o) r[k] = o[k];
  return r;
 }
 var LOOKS = {
  'CONTOUR ATLAS': look({
   palette: 'cyan',
   primitive: 'bracket',
   connect: 'none',
   motion: 'none',
   contour: 'topographic',
   contourLevels: 18,
   density: 35,
   threshold: 46,
   baseOpacity: 66,
   scanlines: 0,
   grain: 8
  }),
  'FLOW ENGRAVING': look({
   palette: 'solar',
   primitive: 'none',
   connect: 'none',
   motion: 'none',
   contour: 'flow',
   duotone: true,
   baseOpacity: 28,
   scanlines: 0,
   grain: 12,
   density: 24
  }),
  'TWIN VELOCITY': look({
   palette: 'solar',
   primitive: 'bracket',
   connect: 'contour',
   motion: 'orbit',
   density: 29,
   threshold: 16,
   shapeMin: 5,
   shapeMax: 81,
   connection: 41,
   lineWeight: 1.07,
   scanlines: 71,
   grain: 74,
   baseOpacity: 83,
   chain: true,
   labels: true,
   curtain: true
  }),
  'EDGE BOX ARCHITECTURE': look({
   palette: 'cyan',
   primitive: 'square',
   connect: 'contour',
   motion: 'assemble',
   density: 72,
   threshold: 27,
   shapeMin: 7,
   shapeMax: 54,
   connection: 86,
   scanlines: 78,
   chain: true,
   labels: true,
   boxes: true
  }),
  'DELAUNAY PORTRAIT': look({
   palette: 'mono',
   primitive: 'cross',
   connect: 'triangulate',
   motion: 'pulse',
   density: 84,
   threshold: 25,
   shapeMin: 4,
   shapeMax: 16,
   connection: 72,
   lineWeight: .5,
   scanlines: 44,
   grain: 38
  }),
  'RADIAL SPECIMEN': look({
   palette: 'solar',
   primitive: 'circle',
   connect: 'radial',
   motion: 'orbit',
   density: 48,
   threshold: 40,
   shapeMin: 8,
   shapeMax: 48,
   connection: 124,
   lineWeight: .95,
   scanlines: 48,
   chain: true
  }),
  'ORTHO BLUEPRINT': look({
   palette: 'violet',
   primitive: 'bracket',
   connect: 'orthogonal',
   motion: 'scan',
   density: 62,
   threshold: 31,
   shapeMin: 8,
   shapeMax: 38,
   connection: 108,
   lineWeight: .65,
   scanlines: 88,
   grid: true
  }),
  'GHOST CONSTELLATION': look({
   palette: 'mono',
   primitive: 'diamond',
   connect: 'hybrid',
   motion: 'glitch',
   density: 74,
   threshold: 23,
   shapeMin: 5,
   shapeMax: 28,
   connection: 58,
   lineWeight: .45,
   scanlines: 92,
   grain: 58,
   baseOpacity: 28
  }),
  'SPECTRAL CURTAIN / SOURCE': look({
   palette: 'cyan',
   primitive: 'none',
   connect: 'none',
   motion: 'wave',
   curtain: true,
   baseOpacity: 90,
   scanlines: 6,
   grain: 16
  }),
  'DITHER PRINT / COBALT': look({
   palette: 'cyan',
   primitive: 'none',
   connect: 'none',
   motion: 'none',
   dither: 'electric',
   scanlines: 0,
   grain: 8
  }),
  'PIXEL MEMORY / COBALT': look({
   palette: 'cyan',
   primitive: 'none',
   connect: 'none',
   motion: 'scan',
   memory: 'archive',
   memoryPalette: 'cobalt',
   cell: 8,
   baseOpacity: 28,
   scanlines: 8,
   grain: 6
  }),
  'HORIZONTAL MEMORY / SOURCE': look({
   palette: 'solar',
   primitive: 'bracket',
   connect: 'none',
   motion: 'glitch',
   memory: 'feedback',
   memoryPalette: 'signal',
   cell: 6,
   density: 54,
   threshold: 24,
   baseOpacity: 78,
   scanlines: 18,
   grain: 10
  }),
  'GLYPH MEMORY / MONO': look({
   palette: 'mono',
   primitive: 'none',
   connect: 'none',
   motion: 'none',
   memory: 'glyphs',
   memoryPalette: 'mono',
   cell: 5,
   baseOpacity: 26,
   scanlines: 4,
   grain: 12
  })
 };
 function rng(seed) {
  var a = seed >>> 0;
  return function() {
   a = a + 1831565813 | 0;
   var t = Math.imul(a ^ a >>> 15, 1 | a);
   t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
   return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
 }
 function hexA(h, a) {
  var v = parseInt(h.slice(1), 16);
  return 'rgba(' + (v >> 16 & 255) + ',' + (v >> 8 & 255) + ',' + (v & 255) + ',' + a + ')';
 }
 function rgb(h) {
  var v = parseInt(h.slice(1), 16);
  return [ v >> 16 & 255, v >> 8 & 255, v & 255 ];
 }
 function delaunay(pts) {
  var n = pts.length;
  if (n < 3) return [];
  var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity, i;
  for (i = 0; i < n; i++) {
   minX = Math.min(minX, pts[i].x);
   minY = Math.min(minY, pts[i].y);
   maxX = Math.max(maxX, pts[i].x);
   maxY = Math.max(maxY, pts[i].y);
  }
  var dm = Math.max(maxX - minX, maxY - minY) * 20, mx = (minX + maxX) / 2, my = (minY + maxY) / 2;
  var P = pts.map(function(p) {
   return [ p.x, p.y ];
  });
  P.push([ mx - dm, my - dm ], [ mx, my + dm ], [ mx + dm, my - dm ]);
  function circ(t) {
   var a = P[t[0]], b = P[t[1]], c = P[t[2]], d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]));
   if (Math.abs(d) < 1e-12) return {
    x: 0,
    y: 0,
    r: Infinity
   };
   var a2 = a[0] * a[0] + a[1] * a[1], b2 = b[0] * b[0] + b[1] * b[1], c2 = c[0] * c[0] + c[1] * c[1];
   var x = (a2 * (b[1] - c[1]) + b2 * (c[1] - a[1]) + c2 * (a[1] - b[1])) / d, y = (a2 * (c[0] - b[0]) + b2 * (a[0] - c[0]) + c2 * (b[0] - a[0])) / d;
   return {
    x: x,
    y: y,
    r: (x - a[0]) * (x - a[0]) + (y - a[1]) * (y - a[1])
   };
  }
  var tris = [ {
   v: [ n, n + 1, n + 2 ]
  } ];
  tris[0].c = circ(tris[0].v);
  for (i = 0; i < n; i++) {
   var px = P[i][0], py = P[i][1], bad = [], keep = [], t;
   for (t = 0; t < tris.length; t++) {
    var c = tris[t].c;
    ((px - c.x) * (px - c.x) + (py - c.y) * (py - c.y) < c.r ? bad : keep).push(tris[t]);
   }
   var edges = {};
   bad.forEach(function(tr) {
    for (var e = 0; e < 3; e++) {
     var u = tr.v[e], w = tr.v[(e + 1) % 3], k = u < w ? u + ',' + w : w + ',' + u;
     edges[k] = (edges[k] || 0) + 1;
    }
   });
   for (var key in edges) if (edges[key] === 1) {
    var uv = key.split(','), nt = {
     v: [ +uv[0], +uv[1], i ]
    };
    nt.c = circ(nt.v);
    keep.push(nt);
   }
   tris = keep;
  }
  return tris.filter(function(tr) {
   return tr.v[0] < n && tr.v[1] < n && tr.v[2] < n;
  }).map(function(tr) {
   return tr.v;
  });
 }
 function GeoFX(canvas, opts) {
  opts = opts || {};
  var d = canvas.dataset, self = this;
  this.canvas = canvas;
  this.ctx = canvas.getContext('2d');
  this.L = LOOKS[opts.geo || d.geo] || LOOKS['EDGE BOX ARCHITECTURE'];
  this.pal = PALETTES[opts.palette || d.palette || this.L.palette];
  this.seed = +(opts.seed || d.seed || 7);
  this.still = (opts.motion || d.motion) === 'none' || this.L.motion === 'none';
  this.reduced = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var im = new Image;
  im.crossOrigin = 'anonymous';
  im.onload = function() {
   self.img = im;
   self.resize();
   if (!self.still && !self.reduced) self.raf = requestAnimationFrame(self.loop);
  };
  im.src = opts.image || d.image;
  this.t0 = 0;
  this.loop = function(now) {
   if (!self.t0) self.t0 = now;
   self.render((now - self.t0) / 1e3);
   self.raf = requestAnimationFrame(self.loop);
  };
  if (typeof ResizeObserver === 'function') new ResizeObserver(function() {
   if (self.img) self.resize();
  }).observe(canvas);
 }
 GeoFX.prototype.resize = function() {
  var r = this.canvas.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  this.W = Math.max(1, r.width);
  this.H = Math.max(1, r.height);
  this.canvas.width = Math.round(this.W * dpr);
  this.canvas.height = Math.round(this.H * dpr);
  this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  this.analyse();
  this.render(this.still || this.reduced ? 2.5 : 0);
 };
 GeoFX.prototype.analyse = function() {
  var W = this.W, H = this.H, img = this.img, L = this.L, R = rng(this.seed);
  var s = Math.max(W / img.width, H / img.height);
  this.fit = {
   x: (W - img.width * s) / 2,
   y: (H - img.height * s) / 2,
   w: img.width * s,
   h: img.height * s
  };
  var aw = Math.max(16, Math.round(Math.min(W, 320))), ah = Math.max(16, Math.round(aw * H / W));
  var c = document.createElement('canvas');
  c.width = aw;
  c.height = ah;
  var x = c.getContext('2d');
  x.drawImage(img, this.fit.x * aw / W, this.fit.y * ah / H, this.fit.w * aw / W, this.fit.h * ah / H);
  var px = x.getImageData(0, 0, aw, ah).data, lum = new Float32Array(aw * ah), i;
  for (i = 0; i < aw * ah; i++) lum[i] = (.2126 * px[i * 4] + .7152 * px[i * 4 + 1] + .0722 * px[i * 4 + 2]) / 255;
  var mag = new Float32Array(aw * ah), ang = new Float32Array(aw * ah), maxM = 1e-6;
  for (var yy = 1; yy < ah - 1; yy++) for (var xx = 1; xx < aw - 1; xx++) {
   var k = yy * aw + xx;
   var gx = lum[k - aw + 1] + 2 * lum[k + 1] + lum[k + aw + 1] - lum[k - aw - 1] - 2 * lum[k - 1] - lum[k + aw - 1];
   var gy = lum[k + aw - 1] + 2 * lum[k + aw] + lum[k + aw + 1] - lum[k - aw - 1] - 2 * lum[k - aw] - lum[k - aw + 1];
   mag[k] = Math.hypot(gx, gy);
   ang[k] = Math.atan2(gy, gx);
   if (mag[k] > maxM) maxM = mag[k];
  }
  var sample = [];
  for (i = 0; i < mag.length; i += 7) if (mag[i] > 0) sample.push(mag[i]);
  sample.sort(function(a, b) {
   return a - b;
  });
  if (sample.length) maxM = Math.max(1e-6, sample[Math.floor(sample.length * .92)]);
  this.A = {
   w: aw,
   h: ah,
   lum: lum,
   mag: mag,
   ang: ang,
   maxM: maxM,
   px: px
  };
  var cell = Math.max(3, Math.round(aw / (6 + L.density * .32))), pts = [];
  for (var cy = 0; cy < ah; cy += cell) for (var cx = 0; cx < aw; cx += cell) {
   var best = -1, bm = 0;
   for (var y2 = cy; y2 < Math.min(ah, cy + cell); y2++) for (var x2 = cx; x2 < Math.min(aw, cx + cell); x2++) {
    var m = mag[y2 * aw + x2];
    if (m > bm) {
     bm = m;
     best = y2 * aw + x2;
    }
   }
   if (best >= 0 && bm / maxM > L.threshold / 100 * .6) pts.push({
    x: (best % aw + .5) * W / aw,
    y: (Math.floor(best / aw) + .5) * H / ah,
    s: Math.min(1, bm / maxM),
    a: ang[best],
    r: R()
   });
  }
  pts.sort(function(a, b) {
   return b.s + b.r * .8 - (a.s + a.r * .8);
  });
  pts = pts.slice(0, 40 + L.density * 2);
  pts.sort(function(a, b) {
   return b.s - a.s;
  });
  this.pts = pts;
  this.tris = L.connect === 'triangulate' || L.connect === 'hybrid' ? delaunay(this.pts) : [];
  var sx = 0, sy = 0, sw = 0;
  this.pts.forEach(function(p) {
   sx += p.x * p.s;
   sy += p.y * p.s;
   sw += p.s;
  });
  this.center = sw ? {
   x: sx / sw,
   y: sy / sw
  } : {
   x: W / 2,
   y: H / 2
  };
  this.cache = null;
 };
 GeoFX.prototype.baseLayer = function() {
  if (this.cache) return this.cache;
  var W = this.W, H = this.H, L = this.L, pal = this.pal, A = this.A, c = document.createElement('canvas'), dpr = window.devicePixelRatio || 1;
  c.width = Math.round(W * dpr);
  c.height = Math.round(H * dpr);
  var x = c.getContext('2d');
  x.setTransform(dpr, 0, 0, dpr, 0, 0);
  x.fillStyle = pal.bg;
  x.fillRect(0, 0, W, H);
  var f = this.fit, i, j;
  if (L.dither) {
   var dp = DITHER[L.dither], ink = rgb(dp.ink), paper = rgb(dp.paper), cw = Math.max(1, Math.round(W / 260)), gw = Math.ceil(W / cw), gh = Math.ceil(H / cw);
   var g = document.createElement('canvas');
   g.width = gw;
   g.height = gh;
   var gx = g.getContext('2d');
   gx.drawImage(this.img, f.x / cw, f.y / cw, f.w / cw, f.h / cw);
   var id = gx.getImageData(0, 0, gw, gh), dd = id.data, v = new Float32Array(gw * gh);
   for (i = 0; i < gw * gh; i++) {
    var l = (.2126 * dd[i * 4] + .7152 * dd[i * 4 + 1] + .0722 * dd[i * 4 + 2]) / 255;
    v[i] = Math.min(1, Math.max(0, (l - .5) * 1.62 + .5));
   }
   for (j = 0; j < gh; j++) for (i = 0; i < gw; i++) {
    var k = j * gw + i, o = v[k] < .5 ? 0 : 1, e = v[k] - o, col = o ? paper : ink;
    dd[k * 4] = col[0];
    dd[k * 4 + 1] = col[1];
    dd[k * 4 + 2] = col[2];
    dd[k * 4 + 3] = 255;
    if (i + 1 < gw) v[k + 1] += e * 7 / 16;
    if (j + 1 < gh) {
     if (i > 0) v[k + gw - 1] += e * 3 / 16;
     v[k + gw] += e * 5 / 16;
     if (i + 1 < gw) v[k + gw + 1] += e / 16;
    }
   }
   gx.putImageData(id, 0, 0);
   x.imageSmoothingEnabled = false;
   x.drawImage(g, 0, 0, gw * cw, gh * cw);
   x.imageSmoothingEnabled = true;
  } else if (L.memory) {
   var mp = MEMORY[L.memoryPalette], cs = L.cell, R = rng(this.seed + 3);
   x.globalAlpha = L.baseOpacity / 100;
   x.drawImage(this.img, f.x, f.y, f.w, f.h);
   x.globalAlpha = 1;
   var cols = Math.ceil(W / cs), rows = Math.ceil(H / cs);
   if (L.memory === 'feedback') {
    for (j = 0; j < rows; j++) if (R() < .35) {
     var off = (R() - .5) * W * .25;
     x.drawImage(c, 0, j * cs * dpr, c.width, cs * dpr, off, j * cs, W, cs);
    }
   } else {
    x.font = cs * 1.25 + 'px ui-monospace, Menlo, monospace';
    x.textBaseline = 'top';
    for (j = 0; j < rows; j++) for (i = 0; i < cols; i++) {
     var ax = Math.min(A.w - 1, Math.floor((i + .5) * cs * A.w / W)), ay = Math.min(A.h - 1, Math.floor((j + .5) * cs * A.h / H)), lv = A.lum[ay * A.w + ax];
     if (L.memory === 'archive') {
      x.fillStyle = lv > .48 ? mp.paper : mp.ink;
      x.fillRect(i * cs, j * cs, cs - 1, cs - 1);
     } else if (lv > .3) {
      x.fillStyle = hexA(mp.paper, Math.min(1, lv));
      x.fillText('01#+=-:'.charAt(Math.floor(R() * 7)), i * cs, j * cs);
     }
    }
    for (var w = 0; w < 7; w++) {
     var ww = W * (.12 + R() * .2), wh = H * (.06 + R() * .12), wx = R() * (W - ww), wy = R() * (H - wh);
     x.save();
     x.beginPath();
     x.rect(wx, wy, ww, wh);
     x.clip();
     x.drawImage(this.img, f.x, f.y, f.w, f.h);
     x.restore();
     x.strokeStyle = mp.accent;
     x.lineWidth = 1.5;
     x.strokeRect(wx + .5, wy + .5, ww, wh);
    }
   }
  } else {
   x.globalAlpha = L.baseOpacity / 100;
   if (L.duotone) x.filter = 'grayscale(1) contrast(1.2)';
   x.drawImage(this.img, f.x, f.y, f.w, f.h);
   x.filter = 'none';
   x.globalAlpha = 1;
   if (L.duotone) {
    x.globalCompositeOperation = 'multiply';
    x.fillStyle = pal.secondary;
    x.fillRect(0, 0, W, H);
    x.globalCompositeOperation = 'source-over';
   }
  }
  if (L.contour === 'topographic') {
   var lv2 = L.contourLevels;
   x.fillStyle = hexA(pal.primary, .8);
   for (j = 1; j < A.h; j++) for (i = 1; i < A.w; i++) {
    var q = Math.floor(A.lum[j * A.w + i] * lv2);
    if (q !== Math.floor(A.lum[j * A.w + i - 1] * lv2) || q !== Math.floor(A.lum[(j - 1) * A.w + i] * lv2)) x.fillRect(i * W / A.w, j * H / A.h, Math.max(1, W / A.w * .7), Math.max(1, H / A.h * .7));
   }
  } else if (L.contour === 'flow') {
   x.strokeStyle = hexA(pal.primary, .75);
   x.lineWidth = .8;
   for (j = 2; j < A.h; j += 3) for (i = 2; i < A.w; i += 3) {
    var kk = j * A.w + i, mm = A.mag[kk] / A.maxM, lu = A.lum[kk];
    if (mm < .06 && lu < .35) continue;
    var an = A.ang[kk] + Math.PI / 2, len = 2 + 7 * (mm + lu * .6), cx0 = i * W / A.w, cy0 = j * H / A.h;
    x.beginPath();
    x.moveTo(cx0 - Math.cos(an) * len, cy0 - Math.sin(an) * len);
    x.lineTo(cx0 + Math.cos(an) * len, cy0 + Math.sin(an) * len);
    x.stroke();
   }
  }
  this.cache = c;
  return c;
 };
 GeoFX.prototype.shape = function(x, prim, cx, cy, s) {
  x.beginPath();
  if (prim === 'circle') {
   x.arc(cx, cy, s / 2, 0, Math.PI * 2);
   x.stroke();
  } else if (prim === 'square') x.strokeRect(cx - s / 2, cy - s / 2, s, s); else if (prim === 'diamond') {
   x.moveTo(cx, cy - s / 2);
   x.lineTo(cx + s / 2, cy);
   x.lineTo(cx, cy + s / 2);
   x.lineTo(cx - s / 2, cy);
   x.closePath();
   x.stroke();
  } else if (prim === 'cross') {
   x.moveTo(cx - s / 2, cy);
   x.lineTo(cx + s / 2, cy);
   x.moveTo(cx, cy - s / 2);
   x.lineTo(cx, cy + s / 2);
   x.stroke();
  } else if (prim === 'bracket') {
   var h = s / 2, k = s * .28;
   x.moveTo(cx - h, cy - h + k);
   x.lineTo(cx - h, cy - h);
   x.lineTo(cx - h + k, cy - h);
   x.moveTo(cx + h - k, cy - h);
   x.lineTo(cx + h, cy - h);
   x.lineTo(cx + h, cy - h + k);
   x.moveTo(cx + h, cy + h - k);
   x.lineTo(cx + h, cy + h);
   x.lineTo(cx + h - k, cy + h);
   x.moveTo(cx - h + k, cy + h);
   x.lineTo(cx - h, cy + h);
   x.lineTo(cx - h, cy + h - k);
   x.stroke();
  }
 };
 GeoFX.prototype.render = function(t) {
  var ctx = this.ctx, W = this.W, H = this.H, L = this.L, pal = this.pal, pts = this.pts, self = this, i, j;
  if (!pts) return;
  var R = rng(this.seed + Math.floor(t * 8));
  ctx.clearRect(0, 0, W, H);
  ctx.drawImage(this.baseLayer(), 0, 0, W, H);
  var mo = L.motion, vis = mo === 'assemble' ? Math.min(1, t % 6 / 2.5) : 1;
  var pulse = mo === 'pulse' ? 1 + .15 * Math.sin(t * 3) : 1, rot = mo === 'orbit' ? t * .15 : 0;
  var C = this.center, n = Math.floor(pts.length * vis), SC = Math.max(.5, Math.min(2, Math.min(W, H) / 500));
  function P(p) {
   if (!rot) return p;
   var dx = p.x - C.x, dy = p.y - C.y, cs = Math.cos(rot * (.3 + p.r)), sn = Math.sin(rot * (.3 + p.r));
   return {
    x: C.x + dx * cs - dy * sn,
    y: C.y + dx * sn + dy * cs,
    s: p.s,
    r: p.r,
    a: p.a
   };
  }
  var Q = [];
  for (i = 0; i < pts.length; i++) Q.push(P(pts[i]));
  if (L.curtain) {
   for (i = 0; i < Math.min(n, 90); i++) {
    var p0 = Q[i], len = H * .25 * (.4 + p0.s) * (mo === 'wave' ? .8 + .2 * Math.sin(t * 2 + i) : 1);
    var gr = ctx.createLinearGradient(0, p0.y, 0, p0.y + len);
    gr.addColorStop(0, hexA(pal.secondary, .55));
    gr.addColorStop(1, hexA(pal.secondary, 0));
    ctx.fillStyle = gr;
    ctx.fillRect(p0.x - 1.5, p0.y, 3, len);
   }
  }
  if (L.grid) {
   ctx.strokeStyle = hexA(pal.secondary, .14);
   ctx.lineWidth = 1;
   for (i = 1; i < 12; i++) {
    ctx.beginPath();
    ctx.moveTo(W * i / 12, 0);
    ctx.lineTo(W * i / 12, H);
    ctx.moveTo(0, H * i / 12);
    ctx.lineTo(W, H * i / 12);
    ctx.stroke();
   }
  }
  ctx.lineWidth = L.lineWeight;
  ctx.strokeStyle = hexA(pal.secondary, .55);
  var maxD = L.connection * Math.min(W, H) / 400;
  ctx.beginPath();
  if (L.connect === 'triangulate' || L.connect === 'hybrid') this.tris.forEach(function(tr) {
   if (tr[0] >= n || tr[1] >= n || tr[2] >= n) return;
   var a = Q[tr[0]], b = Q[tr[1]], c = Q[tr[2]];
   if (L.connect === 'hybrid' && Math.hypot(a.x - b.x, a.y - b.y) > maxD * 1.6) return;
   ctx.moveTo(a.x, a.y);
   ctx.lineTo(b.x, b.y);
   ctx.lineTo(c.x, c.y);
   ctx.closePath();
  });
  if (L.connect === 'radial') {
   for (i = 0; i < n; i++) if (Math.hypot(Q[i].x - C.x, Q[i].y - C.y) < maxD * 3) {
    ctx.moveTo(C.x, C.y);
    ctx.lineTo(Q[i].x, Q[i].y);
   }
  }
  if (L.connect === 'contour' || L.connect === 'orthogonal' || L.connect === 'proximity') {
   for (i = 0; i < n; i++) {
    var best = -1, bd = Infinity;
    for (j = 0; j < n; j++) if (j !== i) {
     var dx = Q[j].x - Q[i].x, dy = Q[j].y - Q[i].y, dd = Math.hypot(dx, dy);
     if (dd > maxD) continue;
     if (L.connect === 'contour') dd *= 1.6 - Math.abs(Math.cos(Math.atan2(dy, dx) - (Q[i].a + Math.PI / 2)));
     if (dd < bd) {
      bd = dd;
      best = j;
     }
    }
    if (best < 0) continue;
    ctx.moveTo(Q[i].x, Q[i].y);
    if (L.connect === 'orthogonal') ctx.lineTo(Q[best].x, Q[i].y);
    ctx.lineTo(Q[best].x, Q[best].y);
   }
  }
  ctx.stroke();
  if (L.connect === 'radial') {
   ctx.strokeStyle = hexA(pal.primary, .25);
   for (i = 1; i <= 4; i++) {
    ctx.beginPath();
    ctx.arc(C.x, C.y, maxD * .7 * i, 0, Math.PI * 2);
    ctx.stroke();
   }
  }
  if (L.chain) {
   ctx.strokeStyle = hexA(pal.accent, .5);
   ctx.lineWidth = .8;
   for (i = 0; i < 7; i++) {
    var an = i / 7 * Math.PI * 2 + t * .2;
    ctx.beginPath();
    ctx.arc(C.x + Math.cos(an) * maxD * 1.4, C.y + Math.sin(an) * maxD * 1.4, maxD * .55, 0, Math.PI * 2);
    ctx.stroke();
   }
  }
  if (L.boxes) {
   var f = this.fit, placed = [];
   for (i = 0; i < n && placed.length < 10; i++) {
    var b = Q[i], bs = (L.shapeMin + (L.shapeMax - L.shapeMin) * b.s) * 1.6 * SC, bx = b.x - bs / 2, by = b.y - bs / 2;
    if (placed.some(function(o) {
     return Math.abs(o[0] - b.x) < (o[2] + bs) * .6 && Math.abs(o[1] - b.y) < (o[2] + bs) * .6;
    })) continue;
    placed.push([ b.x, b.y, bs ]);
    ctx.save();
    ctx.beginPath();
    ctx.rect(bx, by, bs, bs);
    ctx.clip();
    ctx.translate(b.x, b.y);
    ctx.scale(1.8, 1.8);
    ctx.translate(-b.x, -b.y);
    ctx.drawImage(this.img, f.x, f.y, f.w, f.h);
    ctx.restore();
    ctx.strokeStyle = hexA(pal.primary, .9);
    ctx.lineWidth = 1;
    ctx.strokeRect(bx + .5, by + .5, bs, bs);
    ctx.fillStyle = pal.primary;
    ctx.font = '7px ui-monospace, Menlo, monospace';
    ctx.fillText('PATTERN ' + (placed.length < 10 ? '0' : '') + placed.length, bx + 2, by - 3);
   }
  }
  ctx.lineWidth = Math.max(.6, L.lineWeight * 1.1);
  if (L.primitive !== 'none') for (i = 0; i < n; i++) {
   var q = Q[i], sz = (L.shapeMin + (L.shapeMax - L.shapeMin) * Math.pow(q.s, 1.5)) * pulse * SC;
   ctx.strokeStyle = i % 9 === 0 ? pal.accent : i % 3 === 0 ? pal.secondary : pal.primary;
   this.shape(ctx, L.primitive, q.x, q.y, sz);
  }
  if (L.labels) {
   ctx.fillStyle = hexA(pal.primary, .8);
   ctx.font = '7px ui-monospace, Menlo, monospace';
   for (i = 0; i < Math.min(n, 18); i++) ctx.fillText(Math.round(Q[i].x) + ',' + Math.round(Q[i].y), Q[i].x + 6, Q[i].y + 10);
  }
  ctx.fillStyle = hexA(pal.primary, .85);
  ctx.font = '8px ui-monospace, Menlo, monospace';
  ctx.fillText('A-01', 8, 14);
  var tag = Math.round(W) + ' x ' + Math.round(H);
  ctx.fillText(tag, W - 8 - ctx.measureText(tag).width, 14);
  ctx.fillText(pal.name + ' / ' + (L.connect || '').toUpperCase(), 8, H - 8);
  if (mo === 'scan') {
   var sy = t * .25 % 1 * H;
   ctx.fillStyle = hexA(pal.accent, .18);
   ctx.fillRect(0, sy, W, 2);
  }
  if (mo === 'glitch' && R() < .5) {
   var cv = this.canvas, dpr = cv.width / W;
   for (i = 0; i < 4; i++) {
    var gy = R() * H, gh = 4 + R() * 18, gx = (R() - .5) * 30;
    ctx.drawImage(cv, 0, gy * dpr, cv.width, gh * dpr, gx, gy, W, gh);
   }
  }
  if (L.scanlines) {
   ctx.fillStyle = 'rgba(0,0,0,' + L.scanlines / 100 * .28 + ')';
   for (j = 0; j < H; j += 3) ctx.fillRect(0, j, W, 1);
  }
  if (L.grain) {
   ctx.fillStyle = 'rgba(255,255,255,' + L.grain / 100 * .08 + ')';
   for (i = 0; i < W * H / 260 * L.grain / 50; i++) ctx.fillRect(R() * W, R() * H, 1, 1);
  }
 };
 GeoFX.prototype.set = function(opts) {
  if (opts.geo && LOOKS[opts.geo]) {
   this.L = LOOKS[opts.geo];
   this.pal = PALETTES[this.L.palette];
  }
  if (opts.palette && PALETTES[opts.palette]) this.pal = PALETTES[opts.palette];
  if (this.img) {
   this.analyse();
   this.render(2.5);
  }
 };
 GeoFX.prototype.destroy = function() {
  cancelAnimationFrame(this.raf);
 };
 GeoFX.LOOKS = LOOKS;
 GeoFX.PALETTES = PALETTES;
 GeoFX._delaunay = delaunay;
 if (typeof window !== 'undefined') {
  window.GeoFX = GeoFX;
  var boot = function() {
   var els = document.querySelectorAll('canvas.geo-fx');
   for (var i = 0; i < els.length; i++) if (!els[i]._geoFx) els[i]._geoFx = new GeoFX(els[i]);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
 }
 if (typeof module !== 'undefined') module.exports = GeoFX;
})();