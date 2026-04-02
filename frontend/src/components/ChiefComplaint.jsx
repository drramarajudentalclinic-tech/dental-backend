import { useEffect, useState } from "react";
import api from "../api/api";

export default function ChiefComplaint({ visitId }) {
  const [complaint, setComplaint] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.get(`/api/visit/${visitId}`).then(res => {
      if (res.data.chief_complaint) {
        setComplaint(res.data.chief_complaint);
        setSaved(true);
      }
    });
  }, [visitId]);

  const save = async () => {
    await api.put(`/api/visit/${visitId}`, {
      chief_complaint: complaint
    });
    setSaved(true);
  };

  return (
    <section>
      <h3>Chief Complaint</h3>
      <textarea
        rows={3}
        value={complaint}
        onChange={e => setComplaint(e.target.value)}
        placeholder="Enter patient's main complaint"
        style={{ width: "100%" }}
      />
      <button onClick={save}>
        {saved ? "Update" : "Save"}
      </button>
    </section>
  );
}
