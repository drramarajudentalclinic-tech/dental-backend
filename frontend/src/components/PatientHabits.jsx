export default function PatientHabits({ data = {}, setData }) {
  return (
    <fieldset>
      <legend>Habits</legend>

      <label>
        Smoking:
        <input
          value={data.smoking || ""}
          onChange={(e) =>
            setData({ ...data, smoking: e.target.value })
          }
          placeholder="Yes / No / Years"
        />
      </label>

      <br />

      <label>
        Alcohol:
        <input
          value={data.alcohol || ""}
          onChange={(e) =>
            setData({ ...data, alcohol: e.target.value })
          }
          placeholder="Occasional / Daily"
        />
      </label>

      <br />

      <label>
        Tobacco:
        <input
          value={data.tobacco || ""}
          onChange={(e) =>
            setData({ ...data, tobacco: e.target.value })
          }
          placeholder="Chewing / Smoking"
        />
      </label>
    </fieldset>
  );
}
