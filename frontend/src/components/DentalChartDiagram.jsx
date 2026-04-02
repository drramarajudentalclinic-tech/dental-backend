import "./DentalChartDiagram.css";

const CONDITION_COLORS = {
  Caries: "#e53935",
  Missing: "#424242",
  RCT: "#1e88e5",
  Crown: "#fbc02d",
  Bridge: "#8e24aa",
  Implant: "#43a047",
  Attrition: "#fb8c00",
  Impaction: "#6d4c41",
  Other: "#546e7a"
};

const UPPER_RIGHT = [18,17,16,15,14,13,12,11];
const UPPER_LEFT  = [21,22,23,24,25,26,27,28];
const LOWER_LEFT  = [38,37,36,35,34,33,32,31];
const LOWER_RIGHT = [41,42,43,44,45,46,47,48];

export default function DentalChartDiagram({
  records = [],          // ✅ DEFAULT EMPTY ARRAY
  onToothClick = () => {} // ✅ SAFE DEFAULT
}) {

  // ✅ SAFE FIND
  const getRecord = (tooth) => {
    if (!Array.isArray(records)) return null;
    return records.find(r => r.tooth_number === tooth) || null;
  };

  const Tooth = ({ number }) => {
    const rec = getRecord(number);

    const surfaces =
      rec?.surface && typeof rec.surface === "string"
        ? rec.surface.split(",")
        : [];

    const bg = CONDITION_COLORS[rec?.condition] || "#ffffff";

    const tooltip = rec
      ? `Tooth ${number}
Condition: ${rec.condition || "—"}
Surfaces: ${surfaces.join(", ") || "—"}`
      : `Tooth ${number} – No findings`;

    return (
      <div
        className="tooth"
        style={{ backgroundColor: bg }}
        onClick={() => onToothClick(number)}
        title={tooltip}
      >
        {/* SURFACE OVERLAYS */}
        <div className={`surface top ${surfaces.includes("B") ? "active" : ""}`} />
        <div className={`surface left ${surfaces.includes("M") ? "active" : ""}`} />
        <div className={`surface center ${surfaces.includes("O") ? "active" : ""}`} />
        <div className={`surface right ${surfaces.includes("D") ? "active" : ""}`} />
        <div className={`surface bottom ${surfaces.includes("L") ? "active" : ""}`} />

        <span className="tooth-number">{number}</span>
      </div>
    );
  };

  return (
    <div className="chart-wrapper">
      <h3>🦷 Dental Chart</h3>

      <div className="arch">
        {UPPER_RIGHT.map(n => (
          <Tooth key={n} number={n} />
        ))}
        {UPPER_LEFT.map(n => (
          <Tooth key={n} number={n} />
        ))}
      </div>

      <div className="arch">
        {LOWER_LEFT.map(n => (
          <Tooth key={n} number={n} />
        ))}
        {LOWER_RIGHT.map(n => (
          <Tooth key={n} number={n} />
        ))}
      </div>
    </div>
  );
}
