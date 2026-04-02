const HABIT_LABELS = {
  smoking: "Smoking",
  alcohol: "Alcohol Consumption",
  tobacco: "Tobacco Chewing",
  pan:     "Pan / Betel Nut",
};

export default function DoctorHabitsSummary({ data }) {
  if (!data) return null;

  let habits = [];

  // ── Format 1: array of habit objects (DB format) ──────────────────
  // [ { habit_type: "smoking", frequency: "DAILY", duration_years: 10 }, ... ]
  if (Array.isArray(data)) {
    habits = data.filter(h => h.habit_type);
  }

  // ── Format 2: flat dict (reception form format) ───────────────────
  // { smoking: "yes/10/15", alcohol: "occasionally", tobacco: "chewing" }
  else if (typeof data === "object") {
    habits = Object.entries(data)
      .filter(([, val]) => val && val !== "no" && val !== false)
      .map(([key, val]) => {
        // Parse "yes/10/15" style values
        const parts = String(val).split("/");
        return {
          habit_type:     key,
          frequency:      parts[0] || val,
          duration_years: parts[1] || null,
          remarks:        parts[2] || null,
        };
      });
  }

  if (habits.length === 0) return null;

  return (
    <section className="doctor-section" style={{ marginTop: 16 }}>
      <h3>Habits</h3>
      <ul style={{ listStyle: "none", paddingLeft: 0, margin: 0 }}>
        {habits.map((habit, index) => (
          <li key={index} style={{ marginBottom: 6, fontSize: 14, color: "#222" }}>
            <strong>
              {HABIT_LABELS[habit.habit_type] || habit.habit_type}
            </strong>
            {habit.frequency && <> — {habit.frequency}</>}
            {habit.duration_years && <> ({habit.duration_years} yrs)</>}
            {habit.remarks && <> · {habit.remarks}</>}
          </li>
        ))}
      </ul>
    </section>
  );
}