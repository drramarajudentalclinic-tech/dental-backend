import { useState } from "react";
import api from "../api/api";

export default function PatientSearch() {
  const [q, setQ] = useState([]);
  const [results, setResults] = useState([]);

  const search = async () => {
    const res = await api.get(`/api/patients/search?q=${q}`);
    setResults(res.data);
  };

  return (
    <>
      <input onChange={e => setQ(e.target.value)} placeholder="Search patient" />
      <button onClick={search}>Search</button>

      <ul>
        {results.map(p => (
          <li key={p.id}>{p.name} ({p.case_number})</li>
        ))}
      </ul>
    </>
  );
}
