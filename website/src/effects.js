/* Extra movement for the website (works with styles.css "EFFECTS" section)
   - small tooth mouse pointer (laptop / desktop only, drawn in styles.css)
   - buttons lean toward the mouse, and show a ripple when tapped or clicked
   - cards show a soft light where the mouse is
   - clinic name and headings: light sweep (styles.css) + small sparkles from the mouse
   Phones and tablets get the ripple and the tap feedback only.
   Everything is switched off when the visitor's device asks for less motion. */
import { useEffect } from "react";

const SPARKLE_TEXT = ".hero-name, .motto, .brand-name, h2, h3, .hero-place";
const SPARK_COLORS = ["#f3a6b4", "#ffd36b", "#8fd6cc", "#ffffff", "#c4475f"];

/* one small star that pops and fades at (x, y) */
function sparkle(x, y, spread = 14) {
  const s = document.createElement("span");
  s.className = "sparkle";
  s.setAttribute("aria-hidden", "true");
  const size = 12 + Math.random() * 12;
  s.style.left = x + (Math.random() - 0.5) * spread * 2 + "px";
  s.style.top = y + (Math.random() - 0.5) * spread * 2 + "px";
  s.style.width = s.style.height = size + "px";
  s.style.color = SPARK_COLORS[(Math.random() * SPARK_COLORS.length) | 0];
  s.style.setProperty("--dx", (Math.random() - 0.5) * 30 + "px");
  s.style.setProperty("--dy", -10 - Math.random() * 24 + "px");
  document.body.appendChild(s);
  setTimeout(() => s.remove(), 900);
}

const CARDS = ".t-card, .tc, .hero-pillars li, .trust > div, .faq details, .visit-card, .hb-card";

export function useEffects() {
  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    const cleanups = [];
    const on = (el, ev, fn, opt) => { el.addEventListener(ev, fn, opt); cleanups.push(() => el.removeEventListener(ev, fn, opt)); };

    /* ripple on every button, on every device */
    on(document, "pointerdown", (e) => {
      const btn = e.target.closest?.(".btn");
      if (!btn || reduce) return;
      const r = btn.getBoundingClientRect();
      const size = Math.max(r.width, r.height) * 2.2;
      const dot = document.createElement("span");
      dot.className = "btn-ripple";
      dot.style.width = dot.style.height = size + "px";
      dot.style.left = e.clientX - r.left - size / 2 + "px";
      dot.style.top = e.clientY - r.top - size / 2 + "px";
      btn.appendChild(dot);
      setTimeout(() => dot.remove(), 700);
    }, { passive: true });

    /* tap or click on the clinic name / headings: a small burst of sparkles */
    on(document, "pointerdown", (e) => {
      if (reduce || !e.target.closest?.(SPARKLE_TEXT)) return;
      for (let i = 0; i < 7; i++) sparkle(e.clientX, e.clientY, 22);
    }, { passive: true });

    if (finePointer && !reduce) {
      document.documentElement.classList.add("fx-on");

      /* the tooth pointer itself is set in styles.css (html.fx-on) */
      let lastSpark = 0;
      on(window, "pointermove", (e) => {
        if (e.pointerType !== "mouse") return;
        const t = e.target;

        /* sparkles while the mouse moves over the clinic name and headings */
        const now = performance.now();
        if (now - lastSpark > 70 && t.closest?.(SPARKLE_TEXT)) { lastSpark = now; sparkle(e.clientX, e.clientY); }

        /* soft light inside cards */
        const card = t.closest?.(CARDS);
        if (card) {
          const r = card.getBoundingClientRect();
          card.style.setProperty("--sx", e.clientX - r.left + "px");
          card.style.setProperty("--sy", e.clientY - r.top + "px");
        }

        /* buttons lean a little toward the mouse */
        const btn = t.closest?.(".btn");
        if (btn) {
          const r = btn.getBoundingClientRect();
          const dx = (e.clientX - (r.left + r.width / 2)) / (r.width / 2);
          const dy = (e.clientY - (r.top + r.height / 2)) / (r.height / 2);
          btn.style.setProperty("--bx", (dx * 6).toFixed(1) + "px");
          btn.style.setProperty("--by", (dy * 4).toFixed(1) + "px");
        }
      }, { passive: true });
      on(document, "pointerout", (e) => {
        const btn = e.target.closest?.(".btn");
        if (btn && !btn.contains(e.relatedTarget)) { btn.style.removeProperty("--bx"); btn.style.removeProperty("--by"); }
      }, { passive: true });
      cleanups.push(() => document.documentElement.classList.remove("fx-on"));
    }

    return () => cleanups.forEach((f) => f());
  }, []);
}