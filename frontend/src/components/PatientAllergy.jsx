import { useEffect, useState } from "react";
import api from "../api/api";

/**
 * PatientAllergy
 * ---------------
 * Props:
 *  - patientId (number)  ✅ REQUIRED
 *  - readOnly (boolean)  optional (doctor view)
 */
export default function PatientAllergy({ patientId, readOnly = false }) {
  const [loading, setLoading] = useState(false);

  const [allergy, setAllergy] = useState({
    drug_allergy: false,
    food_allergy: false,
    latex_allergy: false,
    iodine_allergy: false,
    anesthesia_allergy: false,
    other_allergy: "",
  });

  /* -------------------------
     LOAD EXISTING ALLERGIES
  -------------------------- */
  useEffect(() => {
    if (!patientId) return;

    api
      .get(`/allergies/${patientId}`)
      .then((res) => {
        if (res.data) setAllergy(res.data);
      })
      .catch(() => {
        // no record yet → ignore
      });
  }, [patientId]);

  /* -------------------------
     HANDLE INPUT CHANGE
  -------------------------- */
  const handleChange = (e) => {
    const { name, type, checked, value } = e.target;

    setAllergy((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  /* -------------------------
     SAVE ALLERGIES
  -------------------------- */
  const saveAllergy = async () => {
    if (!patientId) return;

    setLoading(true);
    try {
      await api.put(`/allergies/${patientId}`, allergy);
      alert("Allergy details saved");
    } catch (err) {
      console.error("Allergy save failed", err);
      alert("Failed to save allergy details");
    } finally {
      setLoading(false);
    }
  };

  /* -------------------------
     UI
  -------------------------- */
  return (
    <div className="card">
      <h3>Allergy Information</h3>

      <label>
        <input
          type="checkbox"
          name="drug_allergy"
          checked={allergy.drug_allergy}
          onChange={handleChange}
          disabled={readOnly}
        />
        Drug Allergy
      </label>

      <label>
        <input
          type="checkbox"
          name="food_allergy"
          checked={allergy.food_allergy}
          onChange={handleChange}
          disabled={readOnly}
        />
        Food Allergy
      </label>

      <label>
        <input
          type="checkbox"
          name="latex_allergy"
          checked={allergy.latex_allergy}
          onChange={handleChange}
          disabled={readOnly}
        />
        Latex Allergy
      </label>

      <label>
        <input
          type="checkbox"
          name="iodine_allergy"
          checked={allergy.iodine_allergy}
          onChange={handleChange}
          disabled={readOnly}
        />
        Iodine Allergy
      </label>

      <label>
        <input
          type="checkbox"
          name="anesthesia_allergy"
          checked={allergy.anesthesia_allergy}
          onChange={handleChange}
          disabled={readOnly}
        />
        Anesthesia Allergy
      </label>

      <div>
        <label>Other Allergy</label>
        <input
          type="text"
          name="other_allergy"
          value={allergy.other_allergy}
          onChange={handleChange}
          disabled={readOnly}
        />
      </div>

      {!readOnly && (
        <button onClick={saveAllergy} disabled={loading}>
          {loading ? "Saving..." : "Save Allergy"}
        </button>
      )}
    </div>
  );
}
