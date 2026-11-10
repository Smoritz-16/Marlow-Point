/* GLR: one WebGL pass that draws the renders AND the Liquid Glass panels.
   Based on liquid-glass.js (refraction + rim + reflection), but the background is
   sampled straight from image textures (uploaded once per image) instead of a
   2D canvas re-uploaded every frame. Layer A is mixed over layer B by `mix`;
   each layer is either a flat image placed in a screen rect, or a 360 equirect. */
(function (global) {
  'use strict';
  var MAX = 16;
  var VS = 'attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}';
  var FS = [
    'precision highp float;',
    'uniform sampler2D tA,tB;uniform vec2 res;uniform float dpr;uniform vec2 light;uniform int count;',
    'uniform int mA,mB;uniform vec4 rA,rB;uniform float mixv,yaw,pitch,tanf,dimTop,dimBot;',
    'uniform vec4 rects[' + MAX + '];uniform vec4 shape[' + MAX + '];uniform vec4 tint[' + MAX + '];uniform vec4 look[' + MAX + '];',
    'vec2 eq(vec2 px){vec2 v=vec2(px.x/res.x*2.-1.,1.-px.y/res.y*2.);float asp=res.x/res.y;',
    '  vec3 d=normalize(vec3(v.x*tanf,1.,v.y*tanf/asp));float cp=cos(pitch),sp=sin(pitch);d=vec3(d.x,d.y*cp-d.z*sp,d.y*sp+d.z*cp);',
    '  float cy=cos(yaw),sy=sin(yaw);d=vec3(d.x*cy+d.y*sy,-d.x*sy+d.y*cy,d.z);',
    '  return vec2(fract(.5+atan(d.x,d.y)/6.2831853),.5-asin(clamp(d.z,-1.,1.))/3.1415927);}',
    'vec3 LA(vec2 px){ if(mA==1) return texture2D(tA,eq(px)).rgb; vec2 uv=(px-rA.xy)/rA.zw; return texture2D(tA,clamp(uv,0.,1.)).rgb; }',
    'vec3 LB(vec2 px){ if(mB==1) return texture2D(tB,eq(px)).rgb; vec2 uv=(px-rB.xy)/rB.zw; return texture2D(tB,clamp(uv,0.,1.)).rgb; }',
    'vec3 B(vec2 px){ vec3 c=LA(px); if(mixv<.999) c=mix(LB(px),c,mixv);',
    '  float y=px.y/res.y; c*=1.-dimTop*smoothstep(.18,0.,y)-dimBot*smoothstep(.8,1.,y); return c; }',
    'float sdRR(vec2 p,vec2 b,float r){vec2 q=abs(p)-b+r;return length(max(q,0.))+min(max(q.x,q.y),0.)-r;}',
    'void main(){',
    '  vec2 px=vec2(gl_FragCoord.x,res.y-gl_FragCoord.y);',
    '  vec3 col=B(px);',
    '  for(int i=0;i<' + MAX + ';i++){',
    '    if(i>=count) break;',
    '    vec4 R=rects[i]*dpr; vec4 S=shape[i]; vec4 T=tint[i]; vec4 L=look[i];',
    '    float rad=min(S.x*dpr,min(R.z,R.w)); float bez=max(S.y*dpr,1.);',
    '    vec2 p=px-R.xy; float d=sdRR(p,R.zw,rad);',
    '    if(d>0.){ if(d<40.*dpr){ float sh=exp(-d/(18.*dpr))*L.w; col*=1.-sh*smoothstep(-6.*dpr,24.*dpr,p.y+R.w*.2);} continue; }',
    '    float inside=-d; float t=clamp(inside/bez,0.,1.); float slope=1.-t;',
    '    vec3 g;',
    '    if(slope>0.){',
    '      vec2 n=normalize(vec2(sdRR(p+vec2(1.,0.),R.zw,rad)-sdRR(p-vec2(1.,0.),R.zw,rad),sdRR(p+vec2(0.,1.),R.zw,rad)-sdRR(p-vec2(0.,1.),R.zw,rad))+1e-6);',
    '      vec2 off=n*S.z*bez*pow(slope,1.35); float ch=L.z*pow(slope,2.)*bez*.12;',
    '      g=vec3(B(px+off+n*ch).r,B(px+off).g,B(px+off-n*ch).b);',
    '      float ld=dot(n,normalize(light));',
    '      float rim=smoothstep(1.6*dpr*2.2,0.,inside); float facing=.35+.65*pow(abs(ld),1.5);',
    '      g=mix(g,T.rgb,T.a); g+=vec3(1.)*rim*facing*L.x; g+=vec3(1.)*smoothstep(bez*.9,0.,inside)*max(ld,0.)*.10*L.x;',
    '    } else { g=mix(col,T.rgb,T.a); }',
    '    float lum=dot(g,vec3(.299,.587,.114)); g=mix(vec3(lum),g,1.12);',
    '    g*=1.+.06*(1.-t);',
    '    float yN=clamp((px.y-(R.y-R.w))/(2.*R.w),0.,1.);',
    '    g+=smoothstep(.55,0.,yN)*.08*L.y;',
    '    vec2 hp=(p/R.zw)-vec2(-.55,-.75); g+=vec3(1.)*exp(-dot(hp,hp)*3.2)*.07*L.y;',
    '    col=mix(col,g,smoothstep(0.,1.2*dpr,inside));',
    '  }',
    '  gl_FragColor=vec4(col,1.);',
    '}'
  ].join('\n');
  function num(el, k, d) { var v = el.getAttribute('data-lg-' + k); return v == null ? d : parseFloat(v); }

  var GLR = {
    state: { A: null, B: null, mix: 1, yaw: 0, pitch: 0, fov: 84, dimTop: 0, dimBot: 0 },
    dirty: true,
    init: function (opts) {
      opts = opts || {};
      var cv = document.createElement('canvas');
      cv.setAttribute('aria-hidden', 'true');
      cv.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;z-index:-1;pointer-events:none;display:block';
      document.body.prepend(cv);
      var gl = cv.getContext('webgl', { antialias: false, alpha: false, powerPreference: 'high-performance' });
      if (!gl) { cv.remove(); return null; }
      function sh(type, src) { var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }
      var pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr);
      if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) { cv.remove(); return null; }
      gl.useProgram(pr);
      var buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
      var loc = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      var U = {}; ['tA', 'tB', 'res', 'dpr', 'light', 'count', 'mA', 'mB', 'rA', 'rB', 'mixv', 'yaw', 'pitch', 'tanf', 'dimTop', 'dimBot', 'rects', 'shape', 'tint', 'look'].forEach(function (n) { U[n] = gl.getUniformLocation(pr, n); });
      gl.uniform1i(U.tA, 0); gl.uniform1i(U.tB, 1);

      /* texture cache: each image is uploaded once and kept while it is recently used */
      var slots = [], SLOTS = opts.slots || 4, tick = 0;
      function texFor(el) {
        for (var i = 0; i < slots.length; i++) if (slots[i].el === el) { slots[i].used = ++tick; return slots[i].tex; }
        var s;
        if (slots.length < SLOTS) { s = { tex: gl.createTexture() }; slots.push(s); }
        else { s = slots[0]; for (i = 1; i < slots.length; i++) if (slots[i].used < s.used && !slots[i].pin) s = slots[i]; }
        gl.bindTexture(gl.TEXTURE_2D, s.tex);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, el);
        s.el = el; s.used = ++tick;
        return s.tex;
      }
      GLR.preload = function (el) { if (el) texFor(el); };

      var els = [], pressScale = new WeakMap(), sel = opts.selector || '.lg';
      function collect() { els = Array.prototype.slice.call(document.querySelectorAll(sel)); els.forEach(bindPress); }
      function bindPress(el) {
        if (el.__lgBound) return; el.__lgBound = true;
        var s = { v: 1, target: 1, vel: 0 }; pressScale.set(el, s);
        el.addEventListener('pointerdown', function () { s.target = 1.04; });
        ['pointerup', 'pointerleave', 'pointercancel'].forEach(function (ev) { el.addEventListener(ev, function () { s.target = 1; }); });
      }
      var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
      collect();
      new MutationObserver(function () { collect(); }).observe(document.body, { childList: true, subtree: true });
      addEventListener('resize', function () { els.forEach(function (e) { e.__lgRad = null; }); GLR.dirty = true; });

      var rects = new Float32Array(MAX * 4), shape = new Float32Array(MAX * 4), tint = new Float32Array(MAX * 4), look = new Float32Array(MAX * 4);
      var lastSig = '', maxDpr = opts.maxDpr || 1.5;
      var D = { bend: 0.55, bezel: 22, tint: [1, 1, 1, 0.06], rim: 0.55, shine: 1.0, chroma: 1.0, shadow: 0.22 };
      function frame() {
        var dpr = Math.min(window.devicePixelRatio || 1, maxDpr);
        var w = Math.round(innerWidth * dpr), h = Math.round(innerHeight * dpr);
        if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; GLR.dirty = true; }
        var n = 0, sig = '';
        for (var i = 0; i < els.length && n < MAX; i++) {
          var el = els[i];
          var r = el.getBoundingClientRect();
          if (r.width < 2 || r.height < 2 || r.bottom < -50 || r.top > innerHeight + 50) continue;
          var s = pressScale.get(el), k = 1;
          if (s && (s.target !== 1 || s.v !== 1)) { if (reduce) s.v = s.target; else { s.vel += (s.target - s.v) * 0.18; s.vel *= 0.72; s.v += s.vel; if (Math.abs(s.v - s.target) < 1e-4 && Math.abs(s.vel) < 1e-4) s.v = s.target; } k = s.v; el.style.transform = k !== 1 ? 'scale(' + k.toFixed(4) + ')' : ''; }
          if (el.__lgRad == null) el.__lgRad = parseFloat(getComputedStyle(el).borderTopLeftRadius) || 0;
          rects.set([r.left + r.width / 2, r.top + r.height / 2, r.width / 2, r.height / 2], n * 4);
          shape.set([el.__lgRad * k, num(el, 'bezel', D.bezel), num(el, 'bend', D.bend), 0], n * 4);
          var ta = el.getAttribute('data-lg-tint'); tint.set(ta ? ta.split(',').map(Number) : D.tint, n * 4);
          look.set([num(el, 'rim', D.rim), num(el, 'shine', D.shine), num(el, 'chroma', D.chroma), num(el, 'shadow', D.shadow)], n * 4);
          sig += (r.left | 0) + ',' + (r.top | 0) + ',' + (r.width | 0) + ',' + (r.height | 0) + ',' + k.toFixed(3) + ';';
          n++;
        }
        var st = GLR.state;
        if ((GLR.dirty || sig !== lastSig) && st.A && st.A.el) {
          GLR.draws = (GLR.draws || 0) + 1; if (sig !== lastSig) GLR.sigDraws = (GLR.sigDraws || 0) + 1;
          gl.viewport(0, 0, w, h);
          gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, texFor(st.A.el));
          var useB = st.B && st.B.el && st.mix < 0.999;
          gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, useB ? texFor(st.B.el) : texFor(st.A.el));
          function rr(L) { var q = (L && L.rect) || [0, 0, innerWidth, innerHeight]; return [q[0] * dpr, q[1] * dpr, q[2] * dpr, q[3] * dpr]; }
          gl.uniform1i(U.mA, st.A.mode || 0); gl.uniform1i(U.mB, useB ? (st.B.mode || 0) : 0);
          gl.uniform4fv(U.rA, rr(st.A)); gl.uniform4fv(U.rB, rr(useB ? st.B : st.A));
          gl.uniform1f(U.mixv, useB ? st.mix : 1);
          gl.uniform1f(U.yaw, st.yaw); gl.uniform1f(U.pitch, st.pitch); gl.uniform1f(U.tanf, Math.tan(st.fov * Math.PI / 360));
          gl.uniform1f(U.dimTop, st.dimTop); gl.uniform1f(U.dimBot, st.dimBot);
          gl.uniform2f(U.res, w, h); gl.uniform1f(U.dpr, dpr); gl.uniform2f(U.light, -0.6, -0.8); gl.uniform1i(U.count, n);
          gl.uniform4fv(U.rects, rects); gl.uniform4fv(U.shape, shape); gl.uniform4fv(U.tint, tint); gl.uniform4fv(U.look, look);
          gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
          lastSig = sig; GLR.dirty = false;
        }
        requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
      return GLR;
    },
    set: function (s) { for (var k in s) GLR.state[k] = s[k]; GLR.dirty = true; }
  };
  global.GLR = GLR;
})(window);
