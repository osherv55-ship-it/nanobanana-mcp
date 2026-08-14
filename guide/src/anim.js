/* Timeline engine for the routine diagrams.
   Every element tagged with data-a/data-t0/data-t1 is a keyframe. seek(svg, t)
   is pure — the same t always produces the same frame — so the guide can play
   it live and the video renderer can step it frame by frame. */
(function () {
  var EASE = function (p) { return p <= 0 ? 0 : p >= 1 ? 1 : p * p * (3 - 2 * p); };

  function prep(svg) {
    if (svg.__items) return svg.__items;
    var items = [];
    svg.querySelectorAll('[data-a]').forEach(function (el) {
      var kind = el.dataset.a;
      var it = {
        el: el, kind: kind,
        t0: parseFloat(el.dataset.t0), t1: parseFloat(el.dataset.t1),
        base: el.getAttribute('transform') || '',
        cx: parseFloat(el.dataset.cx || 0), cy: parseFloat(el.dataset.cy || 0),
        dy: parseFloat(el.dataset.dy || 0)
      };
      if ((kind === 'draw' || kind === 'sweep') && el.getTotalLength) {
        try { it.len = el.getTotalLength(); } catch (e) { it.len = 0; }
        if (it.len) {
          el.style.strokeDasharray = it.len + ' ' + it.len;
          el.style.strokeDashoffset = it.len;
        }
      }
      items.push(it);
    });
    svg.__items = items;
    svg.__app = svg.querySelector('.applicator');
    svg.__appDot = svg.querySelector('.applicator-dot');
    return items;
  }

  function seek(svg, t) {
    var items = prep(svg), app = svg.__app, dot = svg.__appDot, appAt = null;
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      var raw = it.t1 > it.t0 ? (t - it.t0) / (it.t1 - it.t0) : (t >= it.t1 ? 1 : 0);
      var p = EASE(raw);
      var el = it.el;
      if (it.kind === 'draw' || it.kind === 'sweep') {
        if (it.len) el.style.strokeDashoffset = it.len * (1 - p);
        el.style.opacity = it.kind === 'sweep' ? Math.min(1, p * 3) : 1;
        if (raw > 0 && raw < 1 && it.len) appAt = { el: el, len: it.len * p };
      } else if (it.kind === 'fade') {
        el.style.opacity = p;
      } else if (it.kind === 'pop') {
        el.style.opacity = Math.min(1, p * 2);
        var s = 0.55 + 0.45 * p;
        el.setAttribute('transform',
          'translate(' + it.cx + ',' + it.cy + ') scale(' + s.toFixed(3) + ') translate(' +
          (-it.cx) + ',' + (-it.cy) + ') ' + it.base);
      } else if (it.kind === 'drop') {
        el.style.opacity = Math.min(1, p * 2.2);
        el.setAttribute('transform', 'translate(0,' + (-it.dy * (1 - p)).toFixed(2) + ') ' + it.base);
      }
    }
    if (app) {
      if (appAt) {
        var pt = appAt.el.getPointAtLength(appAt.len);
        app.setAttribute('cx', pt.x); app.setAttribute('cy', pt.y); app.style.opacity = .95;
        if (dot) { dot.setAttribute('cx', pt.x); dot.setAttribute('cy', pt.y); dot.style.opacity = .95; }
      } else {
        app.style.opacity = 0; if (dot) dot.style.opacity = 0;
      }
    }
  }
  window.__seekFig = seek;

  /* ---- live playback ---- */
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var figs = [].slice.call(document.querySelectorAll('svg.fig.anim'));
  if (!figs.length) return;

  figs.forEach(function (svg) {
    svg.__dur = (parseFloat(svg.dataset.dur) || 8) * 1000;
    svg.__t0 = 0; svg.__playing = false;
    seek(svg, reduce ? 1 : 0);
  });

  if (reduce || window.__videoMode) return;

  var visible = new Set();
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (e.isIntersecting) { visible.add(e.target); if (!e.target.__started) { e.target.__started = performance.now(); } }
        else { visible.delete(e.target); }
      });
    }, { threshold: .35 });
    figs.forEach(function (f) { io.observe(f); });
  } else { figs.forEach(function (f) { visible.add(f); f.__started = performance.now(); }); }

  var paused = false;
  function frame(now) {
    if (!paused) {
      visible.forEach(function (svg) {
        if (svg.__paused) return;
        var el = ((now - (svg.__started || now)) % (svg.__dur + 900)) / svg.__dur;
        seek(svg, Math.min(1, el));
      });
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  /* click a figure to freeze it on the finished state, click again to resume */
  figs.forEach(function (svg) {
    svg.style.cursor = 'pointer';
    svg.addEventListener('click', function () {
      svg.__paused = !svg.__paused;
      if (svg.__paused) seek(svg, 1); else svg.__started = performance.now();
    });
  });

  /* global toggle in the routine header */
  var btn = document.getElementById('animToggle');
  if (btn) {
    btn.addEventListener('click', function () {
      paused = !paused;
      btn.setAttribute('aria-pressed', String(paused));
      btn.querySelector('.lbl').textContent = paused ? 'הפעלת אנימציות' : 'עצירת אנימציות';
      if (paused) figs.forEach(function (s) { seek(s, 1); });
      else figs.forEach(function (s) { s.__started = performance.now(); });
    });
  }
})();
