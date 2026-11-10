/* Shown for any address that does not exist on the website */
import { useEffect } from "react";
import { Bar, Footer } from "../components/Chrome";
import { clinic } from "../content";

const LINKS = [
  ["/", "Home page", "Treatments, the doctor, timings and how to reach us"],
  ["/treatments/", "All treatments", "How each treatment is done at the clinic"],
  ["/#book", "Book a visit", "Send a request on WhatsApp"],
  ["/aftercare/", "Aftercare", "What to do at home after your treatment"],
];

export default function NotFound() {
  useEffect(() => {
    const prev = document.title;
    document.title = `Page not found | ${clinic.name}`;
    const m = document.createElement("meta");
    m.name = "robots"; m.content = "noindex";
    document.head.appendChild(m);
    return () => { document.title = prev; m.remove(); };
  }, []);
  return (
    <div className="p-shell">
      <Bar />
      <main className="nf">
        <div className="wrap">
          <span className="nf-code" aria-hidden="true">404</span>
          <h1>This page could not be found</h1>
          <p className="nf-lead">The link may be old or mistyped. These pages will help you find what you need.</p>
          <ul className="nf-links">
            {LINKS.map(([href, t, d]) => (
              <li key={href}><a href={href}><b>{t}</b><span>{d}</span></a></li>
            ))}
          </ul>
          <p className="nf-call">Or call the clinic on <a href={`tel:${String(clinic.phone).replace(/[^\d+]/g, "")}`}>{clinic.phone}</a>, Monday to Saturday, 11 am – 7 pm.</p>
        </div>
      </main>
      <Footer />
    </div>
  );
}
