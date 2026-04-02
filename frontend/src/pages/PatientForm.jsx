import { useState, useEffect } from "react";
import api from "../api/api";

export default function PatientForm({ existingPatient = null, onSaved }) {
  const [form, setForm] = useState({
    case_number: "",
    name: "",
    age: "",
    gender: "",
    mobile: "",
    address: "",
    email: "",
    referred_by: "",
    profession: "",
    dob: "",
  });

  // 🔹 Load existing patient data (Edit Mode)
  useEffect(() => {
    if (existingPatient) {
      setForm({
        ...existingPatient,
        age: calculateAge(existingPatient.dob),
      });
    }
  }, [existingPatient]);

  // 🔹 Age calculation logic
  const calculateAge = (dob) => {
    if (!dob) return "";
    const birthDate = new Date(dob);
    const today = new Date();

    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();

    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  // 🔹 Handle input changes
  const handleChange = (e) => {
    const { name, value } = e.target;

    if (name === "dob") {
      const age = calculateAge(value);
      setForm({ ...form, dob: value, age });
    } else {
      setForm({ ...form, [name]: value });
    }
  };

  // 🔹 Save patient
  const savePatient = async () => {
    try {
      const payload = {
        ...form,
        age: calculateAge(form.dob), // Always recalc before save
      };

      if (existingPatient) {
        await api.put(`/api/patients/${existingPatient.id}`, payload);
        alert("Patient updated successfully");
      } else {
        await api.post("/api/patients", payload);
        alert("Patient created successfully");
      }

      if (onSaved) onSaved();
    } catch (err) {
      console.error(err);
      alert("Error saving patient");
    }
  };

  return (
    <div style={{ border: "1px solid #ccc", padding: 20, marginTop: 20 }}>
      <h3>{existingPatient ? "Edit Patient" : "New Patient Registration"}</h3>

      <input
        name="case_number"
        placeholder="Case Number"
        value={form.case_number}
        onChange={handleChange}
      /><br /><br />

      <input
        name="name"
        placeholder="Patient Name"
        value={form.name}
        onChange={handleChange}
      /><br /><br />

      <input
        name="age"
        placeholder="Age (Auto)"
        value={form.age}
        readOnly
        style={{ backgroundColor: "#f2f2f2" }}
      /><br /><br />

      <input
        name="gender"
        placeholder="Gender"
        value={form.gender}
        onChange={handleChange}
      /><br /><br />

      <input
        name="mobile"
        placeholder="Mobile"
        value={form.mobile}
        onChange={handleChange}
      /><br /><br />

      <input
        name="address"
        placeholder="Address"
        value={form.address}
        onChange={handleChange}
      /><br /><br />

      <input
        name="email"
        placeholder="Email"
        value={form.email}
        onChange={handleChange}
      /><br /><br />

      <input
        name="profession"
        placeholder="Profession"
        value={form.profession}
        onChange={handleChange}
      /><br /><br />

      <input
        name="referred_by"
        placeholder="Referred By"
        value={form.referred_by}
        onChange={handleChange}
      /><br /><br />

      <label>DOB:</label><br />
      <input
        type="date"
        name="dob"
        value={form.dob || ""}
        onChange={handleChange}
      /><br /><br />

      <button onClick={savePatient}>
        {existingPatient ? "Update Patient" : "Save Patient"}
      </button>
    </div>
  );
}
