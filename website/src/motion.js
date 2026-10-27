/* Page movement for the home page — kept calm and professional:
   • sections and cards fade up as they scroll into view (one after another)
   • numbers count up (25 years, study figures, doctor stats)
   • the top bar gets a shadow when scrolling; a thin progress line shows how far you are
   • the menu highlights the section you are reading
   • the booking card in the hero tilts slightly with the mouse (computers only)
   Everything stays still for visitors who switched off animations on their device,
   and all text is visible even if this script does not run. */
import { useEffect } from "react";

const REVEAL = [
  ".sec-head", ".t-card", ".seg", ".tech-grid", ".scr-photo", ".scr-top > div", ".scr-card", ".scr-benefits > div", ".scr-study",
  ".proto", ".doc-card", ".doc-body > *", ".portal-grid > div:first-child", ".phone", ".book-grid > *", ".faq details",
  ".map", ".visit-card", ".trust > div", ".foot-grid > div",
].join(",");

const COUNT = ".trust dt, .doc-stats dt, .scr-stats dt";

function countUp(el) {
  const m = el.textContent.match(/^(\D*)(\d+(?:\.\d+)?)(.*)$/s);
  if (!m || Number(m[2]) < 2) return;
  const [, pre, num, post] = m;
  const end = Number(num), dec = (num.split(".")[1] || "").length, t0 = performance.now(), dur = 1400;
  const step = (t) => {
    const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
    el.textContent = pre + (end * e).toFixed(dec) + post;
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

export function useMotion() {
  useEffect(() => {
    const still = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const cleanups = [];

    // ── top bar shadow + reading progress ──
    const bar = document.querySelector(".bar");
    const prog = document.querySelector(".scroll-progress");
    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        const y = window.scrollY, max = document.documentElement.scrollHeight - window.innerHeight;
        bar?.classList.toggle("scrolled", y > 8);
        if (prog) prog.style.transform = `scaleX(${max > 0 ? Math.min(1, y / max) : 0})`;
        ticking = false;
      });
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    cleanups.push(() => window.removeEventListener("scroll", onScroll));

    // ── menu: highlight the section on screen ──
    const links = [...document.querySelectorAll('.nav a[href^="/#"]')];
    const byId = Object.fromEntries(links.map((a) => [a.getAttribute("href").slice(2), a]));
    if ("IntersectionObserver" in window) {
      const spy = new IntersectionObserver((entries) => {
        entries.forEach((en) => {
          if (!en.isIntersecting) return;
          links.forEach((a) => a.classList.remove("active"));
          byId[en.target.id]?.classList.add("active");
        });
      }, { rootMargin: "-45% 0px -50% 0px" });
      document.querySelectorAll("main section[id]").forEach((s) => spy.observe(s));
      cleanups.push(() => spy.disconnect());
    }

    if (still || !("IntersectionObserver" in window)) return () => cleanups.forEach((f) => f());

    // ── fade up on scroll, one after another within the same row ──
    const els = [...document.querySelectorAll(REVEAL)];
    const seen = new Map();
    els.forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.top < window.innerHeight * 0.9 && r.bottom > 0) return;     // already on screen: leave as is
      const p = el.parentElement, n = seen.get(p) || 0;
      seen.set(p, n + 1);
      el.style.setProperty("--rd", `${(n % 6) * 80}ms`);
      el.classList.add("rv");
    });
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0 });
    els.filter((el) => el.classList.contains("rv")).forEach((el) => io.observe(el));
    cleanups.push(() => io.disconnect());

    // ── numbers count up when seen ──
    const nums = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { countUp(en.target); nums.unobserve(en.target); } });
    }, { threshold: 0.6 });
    document.querySelectorAll(COUNT).forEach((el) => nums.observe(el));
    cleanups.push(() => nums.disconnect());

    // ── hero: booking card follows the mouse a little ──
    const hero = document.querySelector(".hero");
    if (hero && window.matchMedia("(pointer: fine)").matches) {
      const move = (e) => {
        const r = hero.getBoundingClientRect();
        hero.style.setProperty("--mx", ((e.clientX - r.left) / r.width - 0.5).toFixed(3));
        hero.style.setProperty("--my", ((e.clientY - r.top) / r.height - 0.5).toFixed(3));
      };
      const leave = () => { hero.style.setProperty("--mx", 0); hero.style.setProperty("--my", 0); };
      hero.addEventListener("pointermove", move);
      hero.addEventListener("pointerleave", leave);
      cleanups.push(() => { hero.removeEventListener("pointermove", move); hero.removeEventListener("pointerleave", leave); });
    }

    return () => cleanups.forEach((f) => f());
  }, []);
}