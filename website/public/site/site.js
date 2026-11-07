/* Small helpers for the treatment and aftercare pages:
   open-now badge (India time), light that follows the mouse over the clinic name,
   menu bar shadow on scroll, back-to-top ring, and the "how it works" step animations. */
(function () {
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* open now / closed: Mon–Sat 11 am – 7 pm, India time */
  var DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  function status() {
    var ist = new Date(Date.now() + 330 * 60000), day = ist.getUTCDay(), m = ist.getUTCHours() * 60 + ist.getUTCMinutes();
    if (day !== 0 && m >= 660 && m < 1140) {
      var left = 1140 - m;
      return { c: left <= 60 ? "is-open is-soon" : "is-open", f: left <= 60 ? "Open now · closes in " + left + " min" : "Open now · closes 7 pm", s: "Open now" };
    }
    if (day !== 0 && m < 660) return { c: "", f: "Closed now · opens today 11 am", s: "Closed now" };
    var d = (day + 1) % 7; while (d === 0) d = (d + 1) % 7;
    return { c: "", f: "Closed now · opens " + (d === (day + 1) % 7 ? "tomorrow" : DAYS[d]) + " 11 am", s: "Closed now" };
  }
  function paintBadge() {
    var b = document.querySelector(".ss-open"); if (!b) return;
    var st = status();
    b.className = "ss-open " + st.c;
    b.innerHTML = '<i aria-hidden="true"></i><span class="f">' + st.f + '</span><span class="s">' + st.s + "</span>";
  }
  paintBadge(); setInterval(paintBadge, 30000);

  /* light follows the mouse across the clinic name */
  var h = document.querySelector(".ss-h");
  if (h && !reduce) {
    h.addEventListener("pointermove", function (e) { var r = h.getBoundingClientRect(); h.style.setProperty("--tx", e.clientX - r.left + "px"); });
    h.addEventListener("pointerleave", function () { h.style.removeProperty("--tx"); });
  }

  /* menu bar shadow + back to top */
  var bar = document.querySelector(".ss-bar");
  var top = document.createElement("button");
  top.className = "ss-top"; top.type = "button"; top.setAttribute("aria-label", "Back to top");
  var C = 2 * Math.PI * 21;
  top.innerHTML = '<svg viewBox="0 0 48 48" aria-hidden="true"><circle class="t" cx="24" cy="24" r="21"/><circle class="r" cx="24" cy="24" r="21" stroke-dasharray="' + C + '" stroke-dashoffset="' + C + '"/><path class="a" d="M24 31V17M18 23l6-6 6 6"/></svg>';
  top.onclick = function () { window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" }); };
  document.body.appendChild(top);
  var ring = top.querySelector(".r");
  function onScroll() {
    var max = document.documentElement.scrollHeight - window.innerHeight, p = max > 0 ? Math.min(1, window.scrollY / max) : 0;
    ring.setAttribute("stroke-dashoffset", C * (1 - p));
    top.classList.toggle("show", window.scrollY > 500);
    if (bar) bar.classList.toggle("scrolled", window.scrollY > 200);
  }
  window.addEventListener("scroll", onScroll, { passive: true }); onScroll();

  /* "how it works": frames change every few seconds; tap a step to jump to it */
  Array.prototype.forEach.call(document.querySelectorAll(".how"), function (box) {
    var frames = box.querySelectorAll(".fr"), steps = box.querySelectorAll(".how-steps li"), fill = box.querySelector(".how-bar i");
    var i = 0, n = frames.length, timer = 0, t0 = 0, DUR = 3800, raf = 0, paused = false;
    function show(k) {
      i = (k + n) % n;
      for (var j = 0; j < n; j++) { frames[j].classList.toggle("on", j === i); if (steps[j]) steps[j].classList.toggle("on", j === i); }
      t0 = performance.now();
    }
    function tick(t) {
      if (!paused && !reduce) {
        var k = (t - t0) / DUR;
        if (fill) fill.style.width = Math.min(100, ((i + Math.min(k, 1)) / n) * 100) + "%";
        if (k >= 1) show(i + 1);
      }
      raf = requestAnimationFrame(tick);
    }
    Array.prototype.forEach.call(steps, function (li, k) { li.addEventListener("click", function () { show(k); }); });
    box.addEventListener("mouseenter", function () { paused = true; });
    box.addEventListener("mouseleave", function () { paused = false; t0 = performance.now(); });
    show(0);
    if (reduce && fill) fill.style.width = "100%";
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting && !raf) { t0 = performance.now(); raf = requestAnimationFrame(tick); } });
      }, { threshold: 0.3 }).observe(box);
    } else { raf = requestAnimationFrame(tick); }
  });

  /* print button on aftercare pages */
  Array.prototype.forEach.call(document.querySelectorAll(".print-btn"), function (b) { b.addEventListener("click", function () { window.print(); }); });
})();
