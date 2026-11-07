/* Extra movement for the website (works with styles.css "EFFECTS" section)
   - small tooth mouse pointer (laptop / desktop only, drawn in styles.css)
   - buttons lean toward the mouse, and show a ripple when tapped or clicked
   - cards show a soft light where the mouse is
   Phones and tablets get the ripple and the tap feedback only.
   Everything is switched off when the visitor's device asks for less motion. */
import { useEffect } from "react";

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

    if (finePointer && !reduce) {
      document.documentElement.classList.add("fx-on");

      /* the tooth pointer itself is set in styles.css (html.fx-on) */
      on(window, "pointermove", (e) => {
        if (e.pointerType !== "mouse") return;
        const t = e.target;

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