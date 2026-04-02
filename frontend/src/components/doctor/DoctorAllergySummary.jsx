export default function DoctorAllergySummary({ data }) {
  // data can be:
  //   { rows: [ { type, allergen, reaction, severity, notes }, ... ] }  ← new format
  //   { drug_allergy: true, food_allergy: true, ... }                   ← old flat format

  // ── New row-based format ──────────────────────────────────────────
  const rows = data?.rows;
  if (Array.isArray(rows)) {
    if (rows.length === 0) return null;
    // Already rendered as a table in the parent (DoctorPatientView / VisitPage)
    // so we just return null here to avoid duplication.
    return null;
  }

  // ── Old flat format fallback ──────────────────────────────────────
  if (!data || typeof data !== "object" || Object.keys(data).length === 0) return null;

  const LABELS = {
    penicillin:        "Penicillin",
    sulfa:             "Sulfa Drugs",
    aspirin:           "Aspirin",
    iodine:            "Iodine",
    local_anaesthetic: "Local Anaesthetic",
    ibuprofen:         "Ibuprofen",
    latex:             "Latex",
    drug_allergy:      "Drug Allergy",
    food_allergy:      "Food Allergy",
    latex_allergy:     "Latex Allergy",
    iodine_allergy:    "Iodine Allergy",
    anesthesia_allergy:"Anesthesia Allergy",
  };

  const items = Object.entries(LABELS)
    .filter(([key]) => Boolean(data[key]))
    .map(([, label]) => label);

  if (data.food_allergy && typeof data.food_allergy === "string" && data.food_allergy.trim()) {
    items.push(`Food Allergy: ${data.food_allergy}`);
  }
  if (data.other_allergy && typeof data.other_allergy === "string" && data.other_allergy.trim()) {
    items.push(`Other: ${data.other_allergy}`);
  }

  if (items.length === 0) return null;

  return (
    <section className="doctor-section" style={{ marginTop: 16 }}>
      <h3>Allergies</h3>
      <ul>
        {items.map(item => <li key={item}>{item}</li>)}
      </ul>
    </section>
  );
}