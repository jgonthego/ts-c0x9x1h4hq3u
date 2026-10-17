(function () {
  "use strict";
  var S = window.SITE || {};

  // Mobile nav
  var t = document.querySelector(".nav-toggle"), nav = document.getElementById("site-nav");
  if (t && nav) t.addEventListener("click", function () {
    var open = nav.classList.toggle("is-open");
    t.setAttribute("aria-expanded", open ? "true" : "false");
  });

  // Countdown (only if DROP_AT is a valid future date)
  var box = document.querySelector("[data-countdown]");
  if (box && S.dropAt) {
    var target = Date.parse(S.dropAt);
    if (!isNaN(target)) {
      var grid = box.querySelector("[data-cd-grid]"), tba = box.querySelector("[data-cd-tba]");
      var pad = function (n) { return (n < 10 ? "0" : "") + n; };
      var tick = function () {
        var ms = target - Date.now();
        if (ms <= 0) { grid.hidden = true; tba.hidden = false; tba.textContent = "Live now"; return false; }
        grid.hidden = false; tba.hidden = true;
        var s = Math.floor(ms / 1000);
        var v = { d: Math.floor(s / 86400), h: Math.floor(s / 3600) % 24, m: Math.floor(s / 60) % 60, s: s % 60 };
        for (var k in v) { var el = grid.querySelector('[data-cd="' + k + '"]'); if (el) el.textContent = pad(v[k]); }
        return true;
      };
      if (tick()) setInterval(tick, 1000);
    }
  }

  // Product gallery
  document.querySelectorAll("[data-gallery]").forEach(function (g) {
    var main = g.querySelector("[data-gallery-main]");
    g.querySelectorAll(".thumb").forEach(function (b) {
      b.addEventListener("click", function () {
        main.src = b.dataset.src; main.alt = b.dataset.alt;
        g.querySelectorAll(".thumb").forEach(function (o) {
          o.classList.toggle("is-active", o === b); o.setAttribute("aria-selected", o === b ? "true" : "false");
        });
      });
    });
  });

  // Category filter chips. Chips are plain links (?cat=<slug>), so a filtered view is shareable.
  // With JS the grid filters in place; without JS every design still shows.
  var fbox = document.querySelector("[data-filters]"), grid = document.querySelector("[data-grid]");
  if (fbox && grid) {
    var note = document.querySelector("[data-filter-note]");
    var valid = function (k) { return k && fbox.querySelector('[data-filter="' + k + '"]') ? k : "all"; };
    var apply = function (key) {
      var n = 0;
      grid.querySelectorAll(".card").forEach(function (c) {
        var show = key === "all" || c.getAttribute("data-cat") === key;
        c.hidden = !show; if (show) n++;
      });
      fbox.querySelectorAll(".ftab").forEach(function (b) {
        if (b.dataset.filter === key) b.setAttribute("aria-current", "true"); else b.removeAttribute("aria-current");
      });
      document.querySelectorAll("[data-cat-note]").forEach(function (el) { el.hidden = el.getAttribute("data-cat-note") !== key; });
      if (note) note.textContent = "Showing " + n + " design" + (n === 1 ? "" : "s");
    };
    var fromUrl = function () {
      var k = null;
      try { k = new URLSearchParams(location.search).get("cat"); } catch (x) {}
      if (!k) { var m = /^#c-([a-z0-9-]+)$/.exec(location.hash); if (m) k = m[1]; } // old links
      return valid(k);
    };
    fbox.addEventListener("click", function (ev) {
      var b = ev.target.closest(".ftab"); if (!b || ev.metaKey || ev.ctrlKey || ev.shiftKey) return;
      ev.preventDefault();
      var k = b.dataset.filter; apply(k);
      try { history.pushState(null, "", location.pathname + (k === "all" ? "" : "?cat=" + encodeURIComponent(k))); } catch (x) {}
    });
    window.addEventListener("popstate", function () { apply(fromUrl()); });
    apply(fromUrl());
  }

  // Hero showcase: featured tees. Auto-advances unless the user prefers reduced motion;
  // pauses on hover/focus, when the tab is hidden, or via the pause button.
  var hero = document.querySelector("[data-hero]");
  if (hero) {
    var slides = [].slice.call(hero.querySelectorAll(".hs-slide"));
    var caps = [].slice.call(hero.querySelectorAll(".hs-cap"));
    var rail = [].slice.call(hero.querySelectorAll(".hr-item"));
    var N = slides.length, cur = 0, DUR = 5000, timer = null, hoverHold = false, userPaused = false;
    var rm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
    var reduced = function () { return !!(rm && rm.matches); };
    var pauseBtn = hero.querySelector("[data-hero-pause]");
    var ctrl = hero.querySelector("[data-hero-ctrl]");
    hero.style.setProperty("--hero-dur", DUR + "ms");
    var show = function (i) {
      cur = (i + N) % N;
      slides.forEach(function (s, k) {
        var d = (k - cur + N) % N;
        s.classList.toggle("is-active", d === 0);
        s.classList.toggle("is-next", d === 1);
        s.classList.toggle("is-next2", d === 2 && N > 3);
        s.classList.toggle("is-prev", d === N - 1 && N > 2);
        s.tabIndex = d === 0 ? 0 : -1;
      });
      caps.forEach(function (c, k) { c.hidden = k !== cur; c.classList.toggle("is-active", k === cur); });
      rail.forEach(function (r, k) {
        r.classList.toggle("is-active", k === cur);
        if (k === cur) r.setAttribute("aria-current", "true"); else r.removeAttribute("aria-current");
      });
      var a = rail[cur]; // restart the progress bar
      if (a) { a.classList.remove("is-active"); void a.offsetWidth; a.classList.add("is-active"); }
    };
    var playing = function () { return !reduced() && !userPaused && !hoverHold && !document.hidden; };
    var sync = function () {
      clearInterval(timer); timer = null;
      var on = playing();
      hero.classList.toggle("is-playing", on);
      if (on) timer = setInterval(function () { show(cur + 1); }, DUR);
      if (pauseBtn) {
        var stopped = userPaused || reduced();
        pauseBtn.setAttribute("aria-pressed", stopped ? "true" : "false");
        pauseBtn.setAttribute("aria-label", stopped ? "Play slideshow" : "Pause slideshow");
      }
    };
    if (ctrl) ctrl.hidden = false;
    hero.querySelector("[data-hero-prev]").addEventListener("click", function () { show(cur - 1); sync(); });
    hero.querySelector("[data-hero-next]").addEventListener("click", function () { show(cur + 1); sync(); });
    if (pauseBtn) pauseBtn.addEventListener("click", function () {
      if (reduced()) { userPaused = true; return; } // never autoplay for reduced motion
      userPaused = !userPaused; sync();
    });
    var stage = hero.querySelector(".hs-stage");
    hero.addEventListener("mouseenter", function () { hoverHold = true; sync(); });
    hero.addEventListener("mouseleave", function () { hoverHold = false; sync(); });
    hero.addEventListener("focusin", function () { hoverHold = true; sync(); });
    hero.addEventListener("focusout", function (ev) { if (!hero.contains(ev.relatedTarget)) { hoverHold = false; sync(); } });
    // Rail thumbs are links to the product page; hovering or focusing one previews it in the stage.
    rail.forEach(function (r, k) {
      r.addEventListener("mouseenter", function () { if (k !== cur) show(k); });
      r.addEventListener("focus", function () { if (k !== cur) show(k); });
    });
    // Swipe on touch screens
    var x0 = null;
    stage.addEventListener("touchstart", function (ev) { x0 = ev.touches[0].clientX; }, { passive: true });
    stage.addEventListener("touchend", function (ev) {
      if (x0 === null) return;
      var dx = ev.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) > 40) { show(cur + (dx < 0 ? 1 : -1)); sync(); }
    });
    document.addEventListener("visibilitychange", sync);
    if (rm && rm.addEventListener) rm.addEventListener("change", sync);
    show(0); sync();
  }

  // Belt and braces: never submit the signup form when it's not configured
  document.querySelectorAll(".signup-form").forEach(function (f) {
    f.addEventListener("submit", function (ev) { if (!S.formEnabled || !f.getAttribute("action")) ev.preventDefault(); });
  });
})();
