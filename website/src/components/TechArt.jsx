/* Original 3-D style illustrations of the equipment, drawn for this site
   (generic devices, not copies of any maker's product photo).
   To use a real photo of the clinic's own equipment instead, put the photo in
   public/equipment/ and set `photo: "/equipment/name.jpg"` on the item in content.js. */

const Defs = () => (
  <defs>
    <linearGradient id="ta-metal" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stopColor="#8a979b" /><stop offset=".35" stopColor="#f4f7f8" /><stop offset=".65" stopColor="#c3ccd0" /><stop offset="1" stopColor="#7d8a8f" />
    </linearGradient>
    <linearGradient id="ta-metal-v" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stopColor="#f4f7f8" /><stop offset=".5" stopColor="#c3ccd0" /><stop offset="1" stopColor="#7d8a8f" />
    </linearGradient>
    <linearGradient id="ta-body" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stopColor="#ffffff" /><stop offset=".55" stopColor="#e8f1ef" /><stop offset="1" stopColor="#b9d3cc" />
    </linearGradient>
    <linearGradient id="ta-ink" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stopColor="#2c7a76" /><stop offset="1" stopColor="#0b2f30" />
    </linearGradient>
    <linearGradient id="ta-gum" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stopColor="#ef8ea0" /><stop offset="1" stopColor="#b23a53" />
    </linearGradient>
    <linearGradient id="ta-screen" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stopColor="#1f5a58" /><stop offset="1" stopColor="#0b2526" />
    </linearGradient>
    <linearGradient id="ta-tooth" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stopColor="#ffffff" /><stop offset="1" stopColor="#dfe9e6" />
    </linearGradient>
    <radialGradient id="ta-glow" cx=".5" cy=".5" r=".5">
      <stop offset="0" stopColor="#7cc9ff" stopOpacity=".9" /><stop offset="1" stopColor="#7cc9ff" stopOpacity="0" />
    </radialGradient>
    <radialGradient id="ta-floor" cx=".5" cy=".5" r=".5">
      <stop offset="0" stopColor="#0f3d3e" stopOpacity=".22" /><stop offset="1" stopColor="#0f3d3e" stopOpacity="0" />
    </radialGradient>
  </defs>
);
const Floor = ({ cx = 60, cy = 104, rx = 40 }) => <ellipse cx={cx} cy={cy} rx={rx} ry="7" fill="url(#ta-floor)" />;
const Tooth = ({ x = 0, y = 0, s = 1 }) => (
  <path transform={`translate(${x} ${y}) scale(${s})`} d="M6 2c-4 0-6 3-6 7 0 4 2 6 3 9 1 4 1 8 3.5 8 2.4 0 2.5-6 6.5-6s4.1 6 6.5 6c2.5 0 2.5-4 3.5-8 1-3 3-5 3-9 0-4-2-7-6-7-3 0-4 1.5-7 1.5S9 2 6 2z"
    fill="url(#ta-tooth)" stroke="#9fbcb8" strokeWidth="1" />
);

const ART = {
  oroscope: (
    <>
      <Floor />
      <circle cx="34" cy="40" r="26" fill="url(#ta-glow)" />
      <path d="M26 40 L8 28 L8 52 Z" fill="#7cc9ff" opacity=".35" />
      <rect x="30" y="31" width="64" height="18" rx="9" fill="url(#ta-ink)" transform="rotate(18 62 40)" />
      <rect x="28" y="33" width="14" height="14" rx="4" fill="url(#ta-metal)" transform="rotate(18 62 40)" />
      <circle cx="30" cy="33" r="5" fill="#bfe6ff" stroke="#3a8fd0" strokeWidth="1.5" />
      <rect x="62" y="44" width="34" height="14" rx="7" fill="url(#ta-body)" transform="rotate(18 62 40)" />
      <circle cx="74" cy="46" r="2.4" fill="#4f9bff" /><circle cx="81" cy="48.5" r="2.4" fill="#e85d5d" /><circle cx="88" cy="51" r="2.4" fill="#e8b84d" />
      <path d="M92 60 q10 14 0 34" fill="none" stroke="#0f3d3e" strokeWidth="2.5" strokeLinecap="round" />
      <rect x="80" y="86" width="26" height="14" rx="3" fill="url(#ta-screen)" />
    </>
  ),
  rvg: (
    <>
      <Floor />
      <rect x="18" y="18" width="52" height="40" rx="5" fill="url(#ta-screen)" />
      <rect x="22" y="22" width="44" height="32" rx="2" fill="#0b2526" />
      <path d="M30 50c0-12 4-22 7-22s3 10 7 10 4-10 7-10 7 10 7 22" fill="none" stroke="#e9f3f1" strokeWidth="2.6" opacity=".9" />
      <rect x="40" y="58" width="8" height="10" fill="url(#ta-metal-v)" />
      <rect x="30" y="68" width="28" height="4" rx="2" fill="url(#ta-metal)" />
      <rect x="66" y="66" width="34" height="24" rx="6" fill="url(#ta-ink)" transform="rotate(-14 83 78)" />
      <rect x="72" y="71" width="22" height="14" rx="3" fill="#1f5a58" transform="rotate(-14 83 78)" />
      <path d="M68 86 q-14 10 -30 6" fill="none" stroke="#0f3d3e" strokeWidth="2.5" strokeLinecap="round" />
    </>
  ),
  camera: (
    <>
      <Floor />
      <rect x="20" y="52" width="84" height="16" rx="8" fill="url(#ta-body)" stroke="#9fbcb8" transform="rotate(-24 62 60)" />
      <rect x="16" y="56" width="22" height="10" rx="5" fill="url(#ta-metal)" transform="rotate(-24 62 60)" />
      <circle cx="22" cy="72" r="5" fill="#1f5a58" stroke="#e9f3f1" strokeWidth="2" />
      <circle cx="22" cy="72" r="2" fill="#7cc9ff" />
      <circle cx="70" cy="49" r="3" fill="url(#ta-gum)" />
      <rect x="62" y="14" width="40" height="28" rx="4" fill="url(#ta-screen)" />
      <Tooth x="72" y="17" s=".75" />
    </>
  ),
  apex: (
    <>
      <Floor />
      <path d="M22 40 L78 30 L98 44 L42 56 Z" fill="#e8f1ef" />
      <path d="M22 40 L42 56 L42 92 L22 76 Z" fill="#b9d3cc" />
      <path d="M42 56 L98 44 L98 80 L42 92 Z" fill="url(#ta-body)" stroke="#9fbcb8" />
      <path d="M50 60 L90 52 L90 70 L50 78 Z" fill="url(#ta-screen)" />
      <path d="M54 72 l6-2 5-6 5 3 5-8 5 2" fill="none" stroke="#5fe0b0" strokeWidth="2" />
      <circle cx="56" cy="85" r="3" fill="url(#ta-gum)" /><circle cx="66" cy="83" r="3" fill="#2c7a76" />
      <path d="M98 62 q14 6 6 26" fill="none" stroke="#0f3d3e" strokeWidth="2.2" />
      <path d="M104 88 l-6 10" stroke="url(#ta-metal)" strokeWidth="3" strokeLinecap="round" />
    </>
  ),
  rotary: (
    <>
      <Floor />
      <rect x="30" y="56" width="70" height="16" rx="8" fill="url(#ta-metal)" transform="rotate(-20 65 64)" />
      <rect x="86" y="36" width="20" height="16" rx="6" fill="url(#ta-ink)" transform="rotate(-20 96 44)" />
      <rect x="20" y="66" width="20" height="14" rx="5" fill="url(#ta-metal-v)" transform="rotate(-20 30 73)" />
      <path d="M22 80 l-6 18" stroke="#b8860b" strokeWidth="2.5" />
      <path d="M22 80 l-6 18" stroke="url(#ta-metal)" strokeWidth="1.6" strokeDasharray="2 2" />
      <rect x="18" y="74" width="8" height="6" rx="2" fill="#e8b84d" />
    </>
  ),
  obturationPen: (
    <>
      <Floor />
      <rect x="34" y="40" width="70" height="16" rx="8" fill="url(#ta-body)" stroke="#9fbcb8" transform="rotate(30 69 48)" />
      <rect x="70" y="64" width="24" height="12" rx="6" fill="url(#ta-ink)" transform="rotate(30 82 70)" />
      <rect x="20" y="22" width="22" height="10" rx="4" fill="url(#ta-metal)" transform="rotate(30 31 27)" />
      <path d="M22 22 l-10 -8" stroke="#f08a3c" strokeWidth="3" strokeLinecap="round" />
      <circle cx="12" cy="14" r="6" fill="#f08a3c" opacity=".35" />
      <circle cx="60" cy="54" r="3" fill="url(#ta-gum)" />
    </>
  ),
  obturationGun: (
    <>
      <Floor />
      <rect x="26" y="34" width="62" height="20" rx="8" fill="url(#ta-body)" stroke="#9fbcb8" />
      <path d="M58 54 l8 0 l6 34 l-14 0 z" fill="url(#ta-ink)" />
      <rect x="86" y="38" width="16" height="12" rx="4" fill="url(#ta-metal-v)" />
      <path d="M102 44 L116 50" stroke="#e8b84d" strokeWidth="3" strokeLinecap="round" />
      <circle cx="117" cy="50.5" r="2.5" fill="#f08a3c" />
      <rect x="34" y="40" width="20" height="8" rx="2" fill="url(#ta-screen)" />
      <rect x="52" y="58" width="8" height="12" rx="3" fill="url(#ta-gum)" />
    </>
  ),
  anaesthesia: (
    <>
      <Floor />
      <rect x="30" y="42" width="56" height="18" rx="6" fill="url(#ta-body)" stroke="#9fbcb8" />
      <rect x="36" y="46" width="30" height="10" rx="2" fill="#dff1ff" stroke="#7cc9ff" />
      <rect x="86" y="46" width="14" height="10" rx="3" fill="url(#ta-metal-v)" />
      <path d="M100 51 L118 51" stroke="url(#ta-metal)" strokeWidth="2" />
      <rect x="14" y="44" width="16" height="14" rx="3" fill="url(#ta-ink)" />
      <path d="M44 30 q6 -6 12 0 q6 6 12 0" fill="none" stroke="#2c7a76" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M44 72 q6 6 12 0 q6 -6 12 0" fill="none" stroke="#2c7a76" strokeWidth="2.4" strokeLinecap="round" />
    </>
  ),
  scanner: (
    <>
      <Floor />
      <path d="M58 84 q-4 -24 18 -30 q22 -6 26 16" fill="#e8f1ef" stroke="#9fbcb8" />
      {[0, 1, 2, 3].map((i) => <Tooth key={i} x={60 + i * 10} y={62 - i * 3} s=".42" />)}
      <path d="M60 70 L104 56" stroke="#7cc9ff" strokeWidth="1" strokeDasharray="2 2" />
      <rect x="12" y="34" width="74" height="18" rx="9" fill="url(#ta-ink)" transform="rotate(-28 49 43)" />
      <rect x="62" y="16" width="26" height="14" rx="5" fill="url(#ta-metal)" transform="rotate(-28 75 23)" />
      <path d="M86 18 L100 52" stroke="#7cc9ff" strokeWidth="6" opacity=".25" strokeLinecap="round" />
      <circle cx="40" cy="52" r="3" fill="url(#ta-gum)" />
    </>
  ),
  blaster: (
    <>
      <Floor />
      <rect x="18" y="58" width="56" height="12" rx="6" fill="url(#ta-body)" stroke="#9fbcb8" transform="rotate(-30 46 64)" />
      <rect x="64" y="34" width="16" height="8" rx="3" fill="url(#ta-metal)" transform="rotate(-30 72 38)" />
      {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => <circle key={i} cx={86 + (i % 3) * 5} cy={26 + Math.floor(i / 3) * 6 + (i % 2) * 2} r="1.4" fill="#9aa7ab" />)}
      <path d="M86 50 q10 -26 22 -10 q-2 20 -14 22 z" fill="url(#ta-tooth)" stroke="#9fbcb8" />
      <rect x="28" y="40" width="14" height="22" rx="4" fill="url(#ta-ink)" transform="rotate(-30 35 51)" />
    </>
  ),
  guide: (
    <>
      <Floor />
      <path d="M16 70 q44 -54 88 0 l-10 8 q-34 -40 -68 0 z" fill="#d7ecff" fillOpacity=".75" stroke="#7cc9ff" />
      {[[30, 58], [48, 44], [72, 44], [90, 58]].map(([x, y]) => <g key={x}><ellipse cx={x} cy={y} rx="5" ry="3" fill="url(#ta-metal-v)" /><rect x={x - 5} y={y} width="10" height="7" fill="url(#ta-metal)" /></g>)}
      <path d="M58 54 l4 0 l1 34 l-6 0 z" fill="url(#ta-metal)" />
      <path d="M57 60 h6 M57 66 h6 M57 72 h6 M57 78 h6" stroke="#7d8a8f" strokeWidth="1" />
    </>
  ),
  centrifuge: (
    <>
      <Floor />
      <ellipse cx="60" cy="74" rx="40" ry="14" fill="#b9d3cc" />
      <path d="M20 54 v20 a40 14 0 0 0 80 0 v-20" fill="url(#ta-body)" stroke="#9fbcb8" />
      <ellipse cx="60" cy="54" rx="40" ry="14" fill="#f6fbfa" stroke="#9fbcb8" />
      <ellipse cx="60" cy="54" rx="28" ry="9" fill="#dff1ff" fillOpacity=".7" stroke="#7cc9ff" />
      {[-18, -6, 6, 18].map((dx, i) => <g key={i}><rect x={60 + dx - 3} y={40 + Math.abs(dx) / 3} width="6" height="18" rx="2" fill="#f7e0b5" stroke="#c9a76a" /><rect x={60 + dx - 3} y={50 + Math.abs(dx) / 3} width="6" height="8" rx="2" fill="#b23a53" /></g>)}
      <rect x="44" y="76" width="32" height="8" rx="2" fill="url(#ta-screen)" />
    </>
  ),
  implant: (
    <>
      <Floor />
      <path d="M40 20 q20 -10 40 0 q6 14 -4 24 h-32 q-10 -10 -4 -24z" fill="url(#ta-tooth)" stroke="#9fbcb8" />
      <rect x="50" y="44" width="20" height="10" fill="url(#ta-metal)" />
      <path d="M48 54 h24 l-4 40 q-8 8 -16 0 z" fill="url(#ta-metal)" />
      {[60, 66, 72, 78, 84].map((y, i) => <path key={y} d={`M${48 + i * 0.8} ${y} L${72 - i * 0.8} ${y - 4}`} stroke="#7d8a8f" strokeWidth="1.6" />)}
    </>
  ),
  records: (
    <>
      <Floor />
      <rect x="22" y="22" width="56" height="74" rx="8" fill="url(#ta-ink)" />
      <rect x="27" y="30" width="46" height="58" rx="3" fill="#f6fbfa" />
      <rect x="31" y="35" width="38" height="16" rx="2" fill="#1f5a58" />
      <path d="M34 47c0-6 2-9 3-9s1 3 3 3 2-3 3-3 3 3 3 9" fill="none" stroke="#e9f3f1" strokeWidth="1.4" />
      <rect x="31" y="55" width="30" height="3" rx="1.5" fill="#b9d3cc" /><rect x="31" y="61" width="24" height="3" rx="1.5" fill="#b9d3cc" /><rect x="31" y="67" width="34" height="3" rx="1.5" fill="#b9d3cc" />
      <rect x="31" y="75" width="16" height="7" rx="3.5" fill="url(#ta-gum)" />
      <circle cx="86" cy="36" r="14" fill="url(#ta-gum)" />
      <path d="M80 36 l4 4 l8 -8" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" />
    </>
  ),
  toothTitan: (
    <>
      <Floor />
      <rect x="28" y="40" width="64" height="54" rx="10" fill="url(#ta-body)" stroke="#9fbcb8" />
      <rect x="34" y="78" width="52" height="10" rx="3" fill="url(#ta-screen)" />
      <circle cx="44" cy="83" r="2.4" fill="#5fe0b0" /><circle cx="52" cy="83" r="2.4" fill="url(#ta-gum)" />
      <ellipse cx="60" cy="40" rx="30" ry="9" fill="#f6fbfa" stroke="#9fbcb8" />
      <path d="M34 40 v-10 a26 9 0 0 1 52 0 v10" fill="#dff1ff" fillOpacity=".6" stroke="#7cc9ff" />
      <ellipse cx="60" cy="22" rx="26" ry="8" fill="url(#ta-ink)" />
      <Tooth x="50" y="27" s=".62" />
      {[[40, 60], [48, 66], [72, 62], [80, 68], [60, 70]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r={1.6 + (i % 3) * .7} fill="#efe6d2" stroke="#c9b48a" strokeWidth=".6" />)}
    </>
  ),
  teethTracer: (
    <>
      <Floor />
      <rect x="62" y="20" width="48" height="34" rx="4" fill="url(#ta-screen)" />
      {[[70, 28, "#5fe0b0"], [80, 26, "#e8b84d"], [90, 28, "#e85d5d"], [100, 32, "#5fe0b0"], [74, 40, "#e8b84d"], [86, 42, "#5fe0b0"], [98, 44, "#e85d5d"]].map(([x, y, c], i) => <circle key={i} cx={x} cy={y} r="3.4" fill={c} opacity=".9" />)}
      <path d="M14 82 q34 -46 68 0" fill="none" stroke="#0f3d3e" strokeWidth="9" strokeLinecap="round" />
      <path d="M14 82 q34 -46 68 0" fill="none" stroke="#7cc9ff" strokeWidth="6" strokeLinecap="round" strokeDasharray="5 3" />
      <rect x="42" y="84" width="12" height="16" rx="3" fill="url(#ta-ink)" />
      <path d="M54 92 q30 4 40 -38" fill="none" stroke="#0f3d3e" strokeWidth="2.2" />
    </>
  ),
  gutta: (
    <>
      <Floor />
      <rect x="18" y="70" width="84" height="26" rx="5" fill="url(#ta-body)" stroke="#9fbcb8" />
      {[0, 1, 2, 3, 4, 5].map((i) => (
        <g key={i} transform={`translate(${26 + i * 13} 0)`}>
          <path d={`M0 ${78 - i} L3.2 ${22 + i * 2} L6.4 ${78 - i} Z`} fill="#f08a6b" stroke="#c75b3e" strokeWidth=".8" />
          <rect x="-0.6" y={78 - i} width="7.6" height="4" rx="1" fill={["#ffffff", "#f5d90a", "#e74c3c", "#3b82f6", "#22c55e", "#111827"][i]} stroke="#9aa7ab" strokeWidth=".5" />
        </g>
      ))}
      <path d="M24 90 h72" stroke="#9fbcb8" strokeWidth="1" />
    </>
  ),
  sealer: (
    <>
      <Floor />
      <rect x="16" y="50" width="62" height="18" rx="4" fill="url(#ta-body)" stroke="#9fbcb8" transform="rotate(-18 47 59)" />
      <rect x="22" y="52" width="30" height="12" rx="2" fill="#efe9da" transform="rotate(-18 47 59)" />
      <rect x="74" y="34" width="20" height="10" rx="3" fill="url(#ta-ink)" transform="rotate(-18 84 39)" />
      <path d="M93 33 l14 -6" stroke="url(#ta-metal)" strokeWidth="3" strokeLinecap="round" />
      <path d="M106 27 q4 -1 5 3" stroke="#e9e3d0" strokeWidth="3" fill="none" strokeLinecap="round" />
      <rect x="6" y="64" width="16" height="10" rx="3" fill="url(#ta-gum)" transform="rotate(-18 14 69)" />
      <path d="M40 92 q8 -14 20 -6 q10 8 22 -2" fill="none" stroke="#e9e3d0" strokeWidth="5" strokeLinecap="round" />
    </>
  ),
  electrosurgery: (
    <>
      <Floor />
      <rect x="44" y="30" width="62" height="46" rx="8" fill="url(#ta-body)" stroke="#9fbcb8" />
      <rect x="51" y="37" width="30" height="14" rx="2" fill="url(#ta-screen)" />
      <text x="66" y="47.5" textAnchor="middle" fontSize="8" fontFamily="monospace" fill="#5fe0b0">CUT</text>
      <circle cx="92" cy="42" r="5" fill="url(#ta-metal-v)" stroke="#7d8a8f" />
      <circle cx="56" cy="64" r="3" fill="#f5c542" /><circle cx="66" cy="64" r="3" fill="#3b82f6" /><circle cx="76" cy="64" r="3" fill="url(#ta-gum)" />
      <path d="M48 70 q-18 8 -20 20" fill="none" stroke="#0f3d3e" strokeWidth="2.2" />
      <rect x="6" y="84" width="36" height="9" rx="4.5" fill="url(#ta-ink)" transform="rotate(-24 24 88)" />
      <path d="M8 98 L1 104" stroke="url(#ta-metal)" strokeWidth="2" strokeLinecap="round" />
      <circle cx="2" cy="103" r="4" fill="#7cc9ff" opacity=".45" />
    </>
  ),
  printer3d: (
    <>
      <Floor rx="44" />
      <rect x="22" y="76" width="76" height="22" rx="5" fill="url(#ta-body)" stroke="#9fbcb8" />
      <rect x="30" y="82" width="20" height="10" rx="2" fill="url(#ta-screen)" />
      <path d="M33 87 h5 l2 -3 l3 6 l2 -3 h3" fill="none" stroke="#5fe0b0" strokeWidth="1" />
      <rect x="90" y="16" width="5" height="62" rx="2" fill="url(#ta-metal)" />
      <path d="M26 24 h60 v52 h-60 z" fill="#f59e0b" fillOpacity=".28" stroke="#d97706" strokeWidth="1.2" />
      <path d="M26 24 l8 -8 h60 l-8 8" fill="#f59e0b" fillOpacity=".18" stroke="#d97706" strokeWidth="1" />
      <rect x="40" y="30" width="34" height="5" rx="1" fill="url(#ta-metal)" />
      <rect x="54" y="35" width="6" height="8" fill="url(#ta-metal-v)" />
      <path d="M48 43 q9 -4 18 0 q2 8 -2 12 h-14 q-4 -4 -2 -12z" fill="url(#ta-tooth)" stroke="#9fbcb8" />
      <rect x="32" y="66" width="50" height="8" rx="2" fill="#dff1ff" fillOpacity=".8" stroke="#7cc9ff" />
      <path d="M57 56 v10" stroke="#7cc9ff" strokeWidth="5" opacity=".35" />
    </>
  ),
  laser: (
    <>
      <Floor />
      <rect x="40" y="24" width="56" height="44" rx="8" fill="url(#ta-body)" stroke="#9fbcb8" />
      <rect x="47" y="31" width="30" height="16" rx="2" fill="url(#ta-screen)" />
      <path d="M50 42 h6 l3 -6 l4 10 l3 -4 h8" fill="none" stroke="#5fe0b0" strokeWidth="1.6" />
      <circle cx="86" cy="36" r="4" fill="url(#ta-gum)" /><circle cx="86" cy="52" r="3" fill="#2c7a76" />
      <path d="M68 68 q-6 14 -24 16" fill="none" stroke="#0f3d3e" strokeWidth="2.4" />
      <rect x="14" y="78" width="40" height="10" rx="5" fill="url(#ta-ink)" transform="rotate(-22 34 83)" />
      <rect x="8" y="90" width="12" height="6" rx="2" fill="url(#ta-metal)" transform="rotate(-22 14 93)" />
      <path d="M8 96 L0 104" stroke="#e85d5d" strokeWidth="2.4" strokeLinecap="round" />
      <circle cx="2" cy="103" r="5" fill="#e85d5d" opacity=".3" />
    </>
  ),
};

export default function TechArt({ name, photo, label }) {
  if (photo) return <img className="tech-art" src={photo} alt={label || ""} loading="lazy" />;
  const art = ART[name];
  if (!art) return null;
  return (
    <svg className="tech-art" viewBox="0 0 120 112" role="img" aria-label={label ? `Illustration: ${label}` : undefined}>
      <Defs />
      {art}
    </svg>
  );
}