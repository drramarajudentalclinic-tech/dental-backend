export default function PatientWomen({ data = {}, setData }) {
  return (
    <fieldset>
      <legend>Women History</legend>

      {/* Pregnant */}
      <label>
        <input
          type="checkbox"
          checked={Boolean(data.pregnant)}
          onChange={(e) =>
            setData({
              ...data,
              pregnant: e.target.checked,
              due_date: e.target.checked ? data.due_date || "" : ""
            })
          }
        />
        Are you pregnant?
      </label>

      {/* Due Date */}
      {data.pregnant && (
        <div style={{ marginTop: 8 }}>
          <label>Expected Due Date</label>
          <input
            type="date"
            value={data.due_date || ""}
            onChange={(e) =>
              setData({ ...data, due_date: e.target.value })
            }
          />
        </div>
      )}

      <br />

      {/* Nursing */}
      <label>
        <input
          type="checkbox"
          checked={Boolean(data.nursing_child)}
          onChange={(e) =>
            setData({
              ...data,
              nursing_child: e.target.checked
            })
          }
        />
        Are you nursing a child?
      </label>
    </fieldset>
  );
}
