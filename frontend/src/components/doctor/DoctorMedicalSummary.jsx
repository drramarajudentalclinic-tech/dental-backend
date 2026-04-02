import React from "react";

const MEDICAL_LABELS = {
  // SQLAlchemy column names (what DB returns)
  aids:                     "AIDS",
  asthma:                   "Asthma",
  arthritis_rheumatism:     "Arthritis / Rheumatism",
  blood_disease:            "Blood Disease",
  bp_high:                  "High Blood Pressure",
  bp_low:                   "Low Blood Pressure",
  corticosteroid_treatment: "Corticosteroid Treatment",
  cancer:                   "Cancer",
  diabetes:                 "Diabetes",
  epilepsy:                 "Epilepsy",
  heart_problems:           "Heart Problems",
  hepatitis:                "Hepatitis",
  herpes:                   "Herpes",
  jaundice:                 "Jaundice",
  liver_disease:            "Liver Disease",
  kidney_disease:           "Kidney Disease",
  psychiatric_treatment:    "Psychiatric Treatment",
  radiation_treatment:      "Radiation Treatment",
  respiratory_disease:      "Respiratory Disease",
  rheumatic_fever:          "Rheumatic Fever",
  tb:                       "Tuberculosis",
  thyroid_problems:         "Thyroid Problems",
  ulcer:                    "Ulcer",
  venereal_disease:         "Venereal Disease",
};

// Map reception form field names → DB column names
const ALIAS_MAP = {
  Blood_Pressure_High:       "bp_high",
  Blood_Pressure_Low:        "bp_low",
  Blood_Disease:             "blood_disease",
  Arthritis_Rheumatism:      "arthritis_rheumatism",
  Corticosteroid_Treatment:  "corticosteroid_treatment",
  Heart_Problems:            "heart_problems",
  Kidney_Disease:            "kidney_disease",
  Liver_Disease:             "liver_disease",
  Psychiatric_Treatment:     "psychiatric_treatment",
  Radiation_Treatment:       "radiation_treatment",
  Respiratory_Disease:       "respiratory_disease",
  Rheumatic_Fever:           "rheumatic_fever",
  Thyroid_Problems:          "thyroid_problems",
  Venereal_Disease:          "venereal_disease",
  // Simple ones that match except for capitalisation
  Aids:      "aids",
  Asthma:    "asthma",
  Cancer:    "cancer",
  Diabetes:  "diabetes",
  Epilepsy:  "epilepsy",
  Hepatitis: "hepatitis",
  Herpes:    "herpes",
  Jaundice:  "jaundice",
  Tb:        "tb",
  Ulcer:     "ulcer",
};

const CRITICAL = [
  "diabetes", "heart_problems", "bp_high", "aids",
  "hepatitis", "tb", "blood_disease", "kidney_disease",
  "liver_disease", "cancer",
];

// Normalise incoming data — convert any reception-form keys to DB keys
function normalise(data) {
  const out = { ...data };
  for (const [alias, canonical] of Object.entries(ALIAS_MAP)) {
    if (alias in out) {
      // Only set if canonical not already present
      if (!(canonical in out)) {
        const val = out[alias];
        out[canonical] = val === "YES" || val === true || val === 1;
      }
      delete out[alias];
    }
  }
  return out;
}

function isTruthy(val) {
  if (val === "YES" || val === "yes") return true;
  if (val === "NO"  || val === "no")  return false;
  return Boolean(Number(val) || val);
}

export default function DoctorMedicalSummary({ data }) {
  if (!data || typeof data !== "object") return null;

  const norm = normalise(data);

  const selected = Object.entries(MEDICAL_LABELS)
    .filter(([key]) => isTruthy(norm[key]))
    .map(([key, label]) => ({
      key,
      label,
      critical: CRITICAL.includes(key),
    }));

  const hasOther = Boolean(norm.other && String(norm.other).trim());

  if (selected.length === 0 && !hasOther) return null;

  const isHighRisk = selected.some(i => i.critical);

  return (
    <section style={{ marginTop: 20 }}>
      {isHighRisk && (
        <div style={{
          backgroundColor: "#b00020", color: "white",
          padding: "10px 14px", marginBottom: 14,
          fontWeight: "bold", borderRadius: 8,
          fontSize: 14, letterSpacing: 0.5,
        }}>
          🚨 HIGH RISK PATIENT – Review medical history carefully
        </div>
      )}

      <h3 style={{ marginBottom: 10 }}>Medical History</h3>
      <ul style={{ listStyle: "none", paddingLeft: 0, margin: 0 }}>
        {selected.map(item => (
          <li key={item.key} style={{
            color: item.critical ? "#b00020" : "#222",
            fontWeight: item.critical ? "bold" : "normal",
            marginBottom: 6, fontSize: 14,
          }}>
            {item.critical ? "🚨 " : ""}{item.label}
          </li>
        ))}
        {hasOther && (
          <li style={{ marginTop: 8, color: "#b00020", fontWeight: "bold", fontSize: 14 }}>
            🚨 Other: {norm.other}
          </li>
        )}
      </ul>
    </section>
  );
}