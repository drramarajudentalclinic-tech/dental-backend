export default function PatientMedical({ data = {}, setData }) {
  const MEDICAL_FIELDS = [
    { key: "AIDS", label: "AIDS" },
    { key: "Asthma", label: "Asthma" },
    { key: "Arthritis_Rheumatism", label: "Arthritis / Rheumatism" },
    { key: "Blood_Disease", label: "Blood Disease" },
    { key: "Blood_Pressure_High", label: "High Blood Pressure" },
    { key: "Blood_Pressure_Low", label: "Low Blood Pressure" },
    { key: "Corticosteroid_Treatment", label: "Corticosteroid Treatment" },
    { key: "Cancer", label: "Cancer" },
    { key: "Diabetes", label: "Diabetes" },
    { key: "Epilepsy", label: "Epilepsy" },
    { key: "Heart_Problems", label: "Heart Problems" },
    { key: "Hepatitis", label: "Hepatitis" },
    { key: "Herpes", label: "Herpes" },
    { key: "Jaundice", label: "Jaundice" },
    { key: "Liver_Disease", label: "Liver Disease" },
    { key: "Kidney_Disease", label: "Kidney Disease" },
    { key: "Psychiatric_Treatment", label: "Psychiatric Treatment" },
    { key: "Radiation_Treatment", label: "Radiation Treatment" },
    { key: "Respiratory_Disease", label: "Respiratory Disease" },
    { key: "Rheumatic_Fever", label: "Rheumatic Fever" },
    { key: "TB", label: "Tuberculosis (TB)" },
    { key: "Thyroid_Problems", label: "Thyroid Problems" },
    { key: "Ulcer", label: "Ulcer" },
    { key: "Venereal_Disease", label: "Venereal Disease" }
  ];

  const toggle = (key) => {
    setData({
      ...data,
      [key]: data[key] === "YES" ? "NO" : "YES"
    });
  };

  // 🔎 Detect risk
  const hasMedicalRisk = MEDICAL_FIELDS.some(
    (item) => data[item.key] === "YES"
  );

  const hasOtherRisk = data.Other && data.Other.trim() !== "";

  const showRiskAlert = hasMedicalRisk || hasOtherRisk;

  return (
    <fieldset
      style={{
        border: showRiskAlert ? "2px solid red" : "1px solid #ccc",
        padding: 12,
        borderRadius: 6
      }}
    >
      <legend
        style={{
          color: showRiskAlert ? "red" : "black",
          fontWeight: "bold"
        }}
      >
        Medical History
      </legend>

      {/* 🚨 RISK ALERT */}
      {showRiskAlert && (
        <div
          style={{
            backgroundColor: "#ffe5e5",
            border: "1px solid red",
            padding: 8,
            marginBottom: 12,
            borderRadius: 6,
            color: "red",
            fontWeight: "bold"
          }}
        >
          🚨 MEDICAL RISK DETECTED – Please Review Carefully
        </div>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "8px"
        }}
      >
        {MEDICAL_FIELDS.map((item) => (
          <label key={item.key} style={{ display: "flex", gap: 6 }}>
            <input
              type="checkbox"
              checked={data[item.key] === "YES"}
              onChange={() => toggle(item.key)}
            />
            {item.label}
          </label>
        ))}
      </div>

      <br />

      <textarea
        placeholder="Other medical conditions"
        value={data.Other || ""}
        onChange={(e) =>
          setData({ ...data, Other: e.target.value })
        }
        style={{
          width: "100%",
          minHeight: 60,
          border: hasOtherRisk ? "1px solid red" : "1px solid #ccc"
        }}
      />
    </fieldset>
  );
}