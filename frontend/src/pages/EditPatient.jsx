import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/api";

import PatientMedical from "../components/PatientMedical";
import PatientAllergy from "../components/PatientAllergy";
import PatientHabits from "../components/PatientHabits";
import PatientWomen from "../components/PatientWomen";

export default function EditPatient() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [patient, setPatient] = useState({});
  const [medical, setMedical] = useState({});
  const [allergy, setAllergy] = useState({});
  const [habits, setHabits] = useState({});
  const [women, setWomen] = useState({});

  useEffect(() => {
    loadPatient();
  }, []);

  const loadPatient = async () => {
    try {
      const res = await api.get(`/patients/${id}`);
      setPatient(res.data.patient);
      setMedical(res.data.medical || {});
      setAllergy(res.data.allergy || {});
      setHabits(res.data.habits || {});
      setWomen(res.data.women || {});
    } catch {
      alert("Failed to load patient");
    }
  };

  const updatePatient = async () => {
    try {
      await api.put(`/patients/${id}`, patient);
      await api.put(`/patients/${id}/medical`, medical);
      await api.put(`/patients/${id}/allergy`, allergy);
      await api.put(`/patients/${id}/habits`, habits);

      if (patient.gender === "Female") {
        await api.put(`/patients/${id}/women`, women);
      }

      alert("Patient updated successfully");
      navigate("/reception");
    } catch {
      alert("Update failed");
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Edit Patient</h2>

      {Object.keys(patient).map(k =>
        k !== "gender" ? (
          <input
            key={k}
            value={patient[k] || ""}
            placeholder={k.replace("_", " ").toUpperCase()}
            onChange={e => setPatient({ ...patient, [k]: e.target.value })}
          />
        ) : (
          <select
            key="gender"
            value={patient.gender || ""}
            onChange={e => setPatient({ ...patient, gender: e.target.value })}
          >
            <option value="">Gender</option>
            <option>Male</option>
            <option>Female</option>
          </select>
        )
      )}

      <textarea
        placeholder="Main Complaint"
        value={patient.complaint || ""}
        onChange={e => setPatient({ ...patient, complaint: e.target.value })}
      />

      <PatientMedical data={medical} setData={setMedical} />
      <PatientAllergy data={allergy} setData={setAllergy} />
      <PatientHabits data={habits} setData={setHabits} />

      {patient.gender === "Female" && (
        <PatientWomen data={women} setData={setWomen} />
      )}

      <button onClick={updatePatient}>Update Patient</button>
      <button onClick={() => navigate(-1)}>Cancel</button>
    </div>
  );
}
