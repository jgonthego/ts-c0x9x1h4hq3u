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

  // Belt and braces: never submit the signup form when it's not configured
  document.querySelectorAll(".signup-form").forEach(function (f) {
    f.addEventListener("submit", function (ev) { if (!S.formEnabled || !f.getAttribute("action")) ev.preventDefault(); });
  });
})();
