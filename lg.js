/*! liquid-glass.js: Apple iOS 26 "Liquid Glass" for the web (WebGL). Refraction + rim + reflection. */
(function (global) {
  'use strict';
  var MAX = 16;
  var VS = 'attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}';
  var FS = [
    'precision highp float;',
    'uniform sampler2D bg;uniform vec2 res;uniform vec2 bgSize;uniform float dpr;uniform vec2 light;',
    'uniform int count;',
    'uniform vec4 rects[' + MAX + '];',   // cx, cy, hw, hh (px, top-left origin)
    'uniform vec4 shape[' + MAX + '];',   // radius, bezel, bend, frost
    'uniform vec4 tint[' + MAX + '];',    // rgb, amount
    'uniform vec4 look[' + MAX + '];',    // rim, shine, chroma, shadow
    'vec3 B(vec2 px){',
    '  vec2 uv=px/res; float ra=res.x/res.y, ba=bgSize.x/bgSize.y; vec2 s=vec2(1.);',
    '  if(ra>ba) s.y=ba/ra; else s.x=ra/ba;',
    '  uv=(uv-.5)*s+.5; return texture2D(bg,clamp(uv,0.001,.999)).rgb;}',
    'float sdRR(vec2 p,vec2 b,float r){vec2 q=abs(p)-b+r;return length(max(q,0.))+min(max(q.x,q.y),0.)-r;}',
    'void main(){',
    '  vec2 px=vec2(gl_FragCoord.x,res.y-gl_FragCoord.y);',
    '  vec3 col=B(px);',
    '  for(int i=0;i<' + MAX + ';i++){',
    '    if(i>=count) break;',
    '    vec4 R=rects[i]*dpr; vec4 S=shape[i]; vec4 T=tint[i]; vec4 L=look[i];',
    '    float rad=min(S.x*dpr,min(R.z,R.w)); float bez=max(S.y*dpr,1.);',
    '    vec2 p=px-R.xy; float d=sdRR(p,R.zw,rad);',
    '    if(d>0.){ float sh=exp(-d/(18.*dpr))*L.w; col*=1.-sh*smoothstep(-6.*dpr,24.*dpr,p.y+R.w*.2); continue; }',
    '    float e=1.;',
    '    vec2 n=normalize(vec2(sdRR(p+vec2(e,0.),R.zw,rad)-sdRR(p-vec2(e,0.),R.zw,rad),',
    '                          sdRR(p+vec2(0.,e),R.zw,rad)-sdRR(p-vec2(0.,e),R.zw,rad))+1e-6);',
    '    float inside=-d;',
    '    float t=clamp(inside/bez,0.,1.);',
    '    float slope=1.-t;',
    // 1. REFRACTION
    '    vec2 off=n*S.z*bez*pow(slope,1.35);',
    '    float ch=L.z*pow(slope,2.)*bez*.12;',
    '    vec3 g;',
    '    if(S.w>.001){',
    '      float fr=S.w*8.*dpr; g=vec3(0.);',
    '      for(int k=0;k<8;k++){float a=float(k)*.785398; vec2 o=vec2(cos(a),sin(a))*fr;',
    '        g+=vec3(B(px+off+o+n*ch).r,B(px+off+o).g,B(px+off+o-n*ch).b);}',
    '      g=(g/8.)*.6+.4*vec3(B(px+off+n*ch).r,B(px+off).g,B(px+off-n*ch).b);',
    '    } else { g=vec3(B(px+off+n*ch).r,B(px+off).g,B(px+off-n*ch).b); }',
    '    float lum=dot(g,vec3(.299,.587,.114)); g=mix(vec3(lum),g,1.12);',
    '    g=mix(g,T.rgb,T.a);',
    '    g*=1.+.06*(1.-t);',
    // 2. RIM
    '    float ld=dot(n,normalize(light));',
    '    float rimW=1.6*dpr;',
    '    float rim=smoothstep(rimW*2.2,0.,inside);',
    '    float facing=.35+.65*pow(abs(ld),1.5);',
    '    g+=vec3(1.)*rim*facing*L.x;',
    '    g+=vec3(1.)*smoothstep(bez*.9,0.,inside)*max(ld,0.)*.10*L.x;',
    // 3. REFLECTION
    '    float yN=clamp((px.y-(R.y-R.w))/(2.*R.w),0.,1.);',
    '    float sheen=smoothstep(.55,0.,yN)*.10*L.y;',
    '    vec3 env=B(vec2(px.x,(R.y-R.w)-(px.y-(R.y-R.w))*.6));',
    '    g+=sheen*(.6+.4*env);',
    '    vec2 hp=(p/R.zw)-vec2(-.55,-.75);',
    '    g+=vec3(1.)*exp(-dot(hp,hp)*3.2)*.07*L.y;',
    '    float aa=smoothstep(0.,1.2*dpr,inside);',
    '    col=mix(col,g,aa);',
    '  }',
    '  gl_FragColor=vec4(col,1.);',
    '}'
  ].join('\n');

  function num(el, k, d) { var v = el.getAttribute('data-lg-' + k); return v == null ? d : parseFloat(v); }

  var LG = {
    defaults: { bend: 0.55, bezel: 22, frost: 0.0, tint: [1, 1, 1, 0.06], rim: 0.55, shine: 1.0, chroma: 1.0, shadow: 0.22, light: [-0.6, -0.8], selector: '.lg', press: true },
    init: function (opts) {
      opts = opts || {};
      var o = {}; for (var k in LG.defaults) o[k] = opts[k] !== undefined ? opts[k] : LG.defaults[k];
      var cv = document.createElement('canvas');
      cv.setAttribute('aria-hidden', 'true');
      cv.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;z-index:-1;pointer-events:none;display:block';
      document.body.prepend(cv);
      var gl = cv.getContext('webgl', { premultipliedAlpha: false, antialias: false });
      if (!gl) { LG.fallback(o); return null; }
      function sh(type, src) { var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }
      var pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr); gl.useProgram(pr);
      var buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
      var loc = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      var U = {}; ['bg', 'res', 'bgSize', 'dpr', 'light', 'count', 'rects', 'shape', 'tint', 'look'].forEach(function (n) { U[n] = gl.getUniformLocation(pr, n); });
      var tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

      var src = opts.background, srcEl = null, drawFn = null, live = false, bgW = 1, bgH = 1, ready = false;
      var off = document.createElement('canvas'), octx = off.getContext('2d');
      if (typeof src === 'function') { drawFn = src; live = !!opts.animate; }
      else if (typeof src === 'string') { srcEl = new Image(); srcEl.crossOrigin = 'anonymous'; srcEl.onload = function () { upload(srcEl); }; srcEl.src = src; }
      else if (src) { srcEl = src; live = src.tagName === 'VIDEO' || src.tagName === 'CANVAS'; if (src.complete || live) upload(src); else src.onload = function () { upload(src); }; }
      else { drawFn = LG.defaultBackground; }
      function upload(el) {
        bgW = el.videoWidth || el.naturalWidth || el.width; bgH = el.videoHeight || el.naturalHeight || el.height;
        if (!bgW || !bgH) return;
        gl.bindTexture(gl.TEXTURE_2D, tex); gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, el); ready = true;
      }
      function drawBg(t) { off.width = Math.max(1, cv.width); off.height = Math.max(1, cv.height); drawFn(octx, off.width, off.height, t); upload(off); }

      var els = [], pressScale = new WeakMap();
      function collect() { els = Array.prototype.slice.call(document.querySelectorAll(o.selector)).slice(0, MAX); if (o.press) els.forEach(bindPress); }
      function bindPress(el) {
        if (el.__lgBound) return; el.__lgBound = true;
        var s = { v: 1, target: 1, vel: 0 }; pressScale.set(el, s);
        el.addEventListener('pointerdown', function () { s.target = 1.04; });
        ['pointerup', 'pointerleave', 'pointercancel'].forEach(function (ev) { el.addEventListener(ev, function () { s.target = 1; }); });
      }
      var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
      collect();
      new MutationObserver(collect).observe(document.body, { childList: true, subtree: true });

      var rects = new Float32Array(MAX * 4), shape = new Float32Array(MAX * 4), tint = new Float32Array(MAX * 4), look = new Float32Array(MAX * 4);
      var dpr = 1, start = performance.now(), firstBg = true, lastSig = '';
      function frame(now) {
        var t = (now - start) / 1000;
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        var w = Math.round(innerWidth * dpr), h = Math.round(innerHeight * dpr);
        if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; firstBg = true; }
        var bgChanged = false;
        if (drawFn && ((live && (!opts.dirty || opts.dirty())) || firstBg)) { drawBg(t); firstBg = false; bgChanged = true; }
        else if (srcEl && live) { upload(srcEl); bgChanged = true; }
        gl.viewport(0, 0, w, h);
        var n = 0;
        for (var i = 0; i < els.length; i++) {
          var el = els[i], r = el.getBoundingClientRect();
          if (r.width < 2 || r.bottom < -50 || r.top > innerHeight + 50) continue;
          var s = pressScale.get(el), k = 1;
          if (s) { if (reduce) s.v = s.target; else { s.vel += (s.target - s.v) * 0.18; s.vel *= 0.72; s.v += s.vel; } k = s.v; el.style.transform = k !== 1 ? 'scale(' + k.toFixed(4) + ')' : ''; }
          if (el.__lgRad == null) el.__lgRad = parseFloat(getComputedStyle(el).borderTopLeftRadius) || 0; var rad = el.__lgRad;
          rects.set([r.left + r.width / 2, r.top + r.height / 2, r.width / 2, r.height / 2], n * 4);
          shape.set([rad * k, num(el, 'bezel', o.bezel), num(el, 'bend', o.bend), num(el, 'frost', o.frost)], n * 4);
          var ta = el.getAttribute('data-lg-tint'); var tv = ta ? ta.split(',').map(Number) : o.tint;
          tint.set(tv, n * 4);
          look.set([num(el, 'rim', o.rim), num(el, 'shine', o.shine), num(el, 'chroma', o.chroma), num(el, 'shadow', o.shadow)], n * 4);
          n++;
        }
        gl.uniform1i(U.bg, 0); gl.uniform2f(U.res, w, h); gl.uniform2f(U.bgSize, bgW, bgH); gl.uniform1f(U.dpr, dpr);
        gl.uniform2f(U.light, o.light[0], o.light[1]); gl.uniform1i(U.count, n);
        gl.uniform4fv(U.rects, rects); gl.uniform4fv(U.shape, shape); gl.uniform4fv(U.tint, tint); gl.uniform4fv(U.look, look);
        var sig = n + ':' + w + 'x' + h + ':' + Array.prototype.slice.call(rects, 0, n * 4).map(function (v) { return v.toFixed(1); }).join(',');
        if (ready && (bgChanged || sig !== lastSig)) { gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); lastSig = sig; }
        requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
      return { canvas: cv, refresh: collect, options: o };
    },
    // Only when WebGL is unavailable: near-clear, edge-lit; never a frosted slab.
    fallback: function (o) {
      var st = document.createElement('style');
      st.textContent = o.selector + '{background:rgba(255,255,255,.08);-webkit-backdrop-filter:blur(2px) saturate(1.5);backdrop-filter:blur(2px) saturate(1.5);' +
        'box-shadow:inset 0 1px 0 rgba(255,255,255,.55),inset 0 -1px 0 rgba(255,255,255,.18),inset 1px 0 0 rgba(255,255,255,.22),inset -1px 0 0 rgba(255,255,255,.12),0 8px 30px rgba(0,0,0,.18);}';
      document.head.appendChild(st);
    },
    defaultBackground: function (c, w, h) {
      var g = c.createLinearGradient(0, 0, w, h); g.addColorStop(0, '#ff7a59'); g.addColorStop(.5, '#7b5cff'); g.addColorStop(1, '#00c2ff');
      c.fillStyle = g; c.fillRect(0, 0, w, h);
      c.globalAlpha = .9; c.fillStyle = '#fff'; c.font = '900 ' + Math.round(h * .22) + 'px -apple-system,Helvetica,Arial,sans-serif';
      c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillText('Liquid Glass', w / 2, h * .8); c.globalAlpha = 1;
      for (var i = 0; i < 14; i++) { c.strokeStyle = 'rgba(255,255,255,.25)'; c.lineWidth = 2; c.beginPath(); c.moveTo(0, h * i / 14); c.lineTo(w, h * i / 14); c.stroke(); }
    }
  };
  global.LiquidGlass = LG;
})(window);