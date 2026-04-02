export default function DoctorWomenSummary({ data }) {
  if (!data || Object.keys(data).length === 0) return null;

  return (
    <section className="doctor-section">
      <h3>Women Health Details</h3>

      <p>Pregnant: {data.pregnant ? "Yes" : "No"}</p>

      {data.due_date && (
        <p>Due Date: {data.due_date}</p>
      )}

      <p>Lactating: {data.nursing_child ? "Yes" : "No"}</p>

      {data.menstrual_issues && (
        <p>Menstrual Issues: {data.menstrual_issues}</p>
      )}
    </section>
  );
}