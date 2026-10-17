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

  // Belt and braces: never submit the signup form when it's not configured
  document.querySelectorAll(".signup-form").forEach(function (f) {
    f.addEventListener("submit", function (ev) { if (!S.formEnabled || !f.getAttribute("action")) ev.preventDefault(); });
  });
})();
