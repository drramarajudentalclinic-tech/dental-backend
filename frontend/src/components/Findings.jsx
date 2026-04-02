import { useEffect, useState, useRef } from "react";
import api from "../api/api";

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

  .of-root * { box-sizing: border-box; margin: 0; padding: 0; }
  .of-root {
    font-family: 'DM Sans', sans-serif;
    background: #f8fafc;
    border-radius: 16px;
    padding: 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    max-width: 700px;
  }

  /* Header */
  .of-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e9eef4;
  }
  .of-header-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #dbeafe, #bfdbfe);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 17px;
  }
  .of-header-title { font-size: 15px; font-weight: 600; color: #1e293b; }
  .of-header-sub { font-size: 12px; color: #94a3b8; margin-top: 1px; }
  .of-header-right { margin-left: auto; }

  /* Add button */
  .of-add-btn {
    padding: 7px 14px;
    background: #eff6ff;
    color: #3b82f6;
    border: 1.5px solid #bfdbfe;
    border-radius: 8px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    font-family: 'DM Sans', sans-serif;
    transition: all 0.15s;
    display: flex;
    align-items: center;
    gap: 5px;
  }
  .of-add-btn:hover { background: #dbeafe; border-color: #93c5fd; }

  /* Input area */
  .of-input-box {
    background: #fff;
    border: 1.5px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 14px;
    animation: fadeIn 0.2s ease;
  }
  .of-textarea {
    width: 100%;
    min-height: 80px;
    padding: 12px 14px;
    border: 1.5px solid #e2e8f0;
    border-radius: 10px;
    font-family: 'DM Sans', sans-serif;
    font-size: 13.5px;
    color: #1e293b;
    resize: vertical;
    background: #f8fafc;
    transition: border-color 0.2s, box-shadow 0.2s;
    outline: none;
    box-sizing: border-box;
    margin-bottom: 10px;
  }
  .of-textarea:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
    background: #fff;
  }
  .of-textarea::placeholder { color: #cbd5e1; }

  /* Date row */
  .of-date-row {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 12px;
  }
  .of-date-label {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
    white-space: nowrap;
  }
  .of-date-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    background: #f1f5f9;
    border: 1.5px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12.5px;
    color: #475569;
    font-family: 'DM Mono', monospace;
    cursor: pointer;
    transition: all 0.15s;
    position: relative;
  }
  .of-date-chip:hover { border-color: #3b82f6; background: #eff6ff; }
  .of-date-chip .icon { font-size: 13px; }
  .of-date-input {
    position: absolute;
    opacity: 0;
    width: 100%;
    height: 100%;
    top: 0; left: 0;
    cursor: pointer;
    font-size: 0;
  }
  .of-date-input::-webkit-calendar-picker-indicator { cursor: pointer; opacity: 0; width: 100%; height: 100%; position: absolute; top:0; left:0; }

  /* Action buttons */
  .of-actions { display: flex; gap: 8px; justify-content: flex-end; }
  .of-btn {
    padding: 8px 18px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    border: none;
    transition: all 0.15s;
    font-family: 'DM Sans', sans-serif;
  }
  .of-btn-cancel {
    background: #f1f5f9;
    color: #64748b;
  }
  .of-btn-cancel:hover { background: #e2e8f0; }
  .of-btn-ok {
    background: #3b82f6;
    color: #fff;
    box-shadow: 0 1px 3px rgba(59,130,246,0.3);
  }
  .of-btn-ok:hover { background: #2563eb; }
  .of-btn-ok:disabled { background: #93c5fd; cursor: not-allowed; }

  /* Findings list */
  .of-list { margin-top: 12px; display: flex; flex-direction: column; gap: 10px; }
  .of-list-header {
    font-size: 11.5px;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 4px;
  }

  .of-item {
    background: #fff;
    border: 1.5px solid #e9eef4;
    border-radius: 10px;
    padding: 12px 14px;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    transition: border-color 0.15s, box-shadow 0.15s;
    animation: fadeIn 0.2s ease;
  }
  .of-item:hover { border-color: #bfdbfe; box-shadow: 0 1px 6px rgba(59,130,246,0.07); }
  .of-item.editing { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.08); }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .of-item-body { flex: 1; min-width: 0; }
  .of-item-date {
    font-size: 11px;
    font-family: 'DM Mono', monospace;
    color: #94a3b8;
    margin-bottom: 4px;
    display: flex; align-items: center; gap: 4px;
  }
  .of-item-text { font-size: 13.5px; color: #1e293b; line-height: 1.5; word-break: break-word; }

  .of-item-btns { display: flex; gap: 6px; flex-shrink: 0; }
  .of-icon-btn {
    width: 30px; height: 30px;
    border: 1.5px solid #e2e8f0;
    border-radius: 7px;
    background: #fff;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.15s;
    color: #64748b;
  }
  .of-icon-btn:hover.edit { border-color: #3b82f6; color: #3b82f6; background: #eff6ff; }
  .of-icon-btn:hover.delete { border-color: #ef4444; color: #ef4444; background: #fef2f2; }

  /* Edit inline textarea */
  .of-edit-area {
    width: 100%;
    min-height: 60px;
    padding: 8px 10px;
    border: 1.5px solid #3b82f6;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-size: 13.5px;
    color: #1e293b;
    resize: vertical;
    outline: none;
    margin-top: 4px;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
    box-sizing: border-box;
  }
  .of-edit-actions { display: flex; gap: 6px; margin-top: 8px; }
  .of-edit-save {
    padding: 5px 14px;
    background: #3b82f6;
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    font-family: 'DM Sans', sans-serif;
  }
  .of-edit-save:hover { background: #2563eb; }
  .of-edit-cancel {
    padding: 5px 14px;
    background: #f1f5f9;
    color: #64748b;
    border: none;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    font-family: 'DM Sans', sans-serif;
  }
  .of-edit-cancel:hover { background: #e2e8f0; }

  .of-empty {
    text-align: center;
    color: #cbd5e1;
    font-size: 13px;
    padding: 18px 0;
    font-style: italic;
  }
`;

function todayStr() {
  return new Date().toISOString().split("T")[0];
}
function fmtDisplay(dateStr) {
  if (!dateStr) return "";
  const [y, m, d] = dateStr.split("-");
  return `${d}/${m}/${y}`;
}

export default function OtherFindings({ visitId, onFindingsChange }) {
  const [findings, setFindings] = useState([]);
  const [showAdd, setShowAdd] = useState(false);
  const [text, setText] = useState("");
  const [date, setDate] = useState(todayStr());
  const [editingId, setEditingId] = useState(null);
  const [editText, setEditText] = useState("");
  const dateRef = useRef();

  // Notify parent whenever findings list changes
  useEffect(() => {
    if (onFindingsChange) onFindingsChange(findings);
  }, [findings]);

  // Load existing findings
  useEffect(() => {
    if (!visitId) return;
    api.get(`/visits/${visitId}/findings`).then(res => {
      if (Array.isArray(res.data)) setFindings(res.data);
    }).catch(() => {});
  }, [visitId]);

  const handleAdd = async () => {
    if (!text.trim()) return;
    try {
      const payload = [{ finding_type: text.trim(), value: date, notes: null }];
      const res = await api.post(`/visits/${visitId}/findings`, payload);
      const saved = Array.isArray(res.data) ? res.data : [res.data];
      setFindings(prev => [...prev, ...saved.map(s => ({ ...s, _date: date }))]);
    } catch {
      // fallback: add locally
      setFindings(prev => [...prev, {
        id: Date.now(),
        finding_type: text.trim(),
        value: date,
        notes: null,
        _local: true,
      }]);
    }
    setText("");
    setDate(todayStr());
    setShowAdd(false);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this finding?")) return;
    try { await api.delete(`/findings/${id}`); } catch {}
    setFindings(prev => prev.filter(f => f.id !== id));
  };

  const startEdit = (f) => {
    setEditingId(f.id);
    setEditText(f.finding_type);
  };

  const saveEdit = async (f) => {
    try {
      await api.put(`/findings/${f.id}`, { finding_type: editText });
    } catch {}
    setFindings(prev => prev.map(x => x.id === f.id ? { ...x, finding_type: editText } : x));
    setEditingId(null);
  };

  return (
    <>
      <style>{styles}</style>
      <div className="of-root">
        {/* Header */}
        <div className="of-header">
          <div className="of-header-icon">🔍</div>
          <div>
            <div className="of-header-title">Other Findings</div>
            <div className="of-header-sub">Clinical examination findings</div>
          </div>
          <div className="of-header-right">
            <button className="of-add-btn" onClick={() => { setShowAdd(o => !o); setText(""); setDate(todayStr()); }}>
              + Add Finding
            </button>
          </div>
        </div>

        {/* Add Input Box */}
        {showAdd && (
          <div className="of-input-box">
            <textarea
              className="of-textarea"
              placeholder="Enter finding details…"
              value={text}
              onChange={e => setText(e.target.value)}
              autoFocus
            />
            <div className="of-date-row">
              <span className="of-date-label">Date:</span>
              <div className="of-date-chip" title="Auto date (today)">
                <span className="icon">📅</span>
                {fmtDisplay(todayStr())}
                <span style={{ fontSize: 10, color: "#94a3b8", marginLeft: 2 }}>auto</span>
              </div>
              <div className="of-date-chip" title="Pick a date manually">
                <span className="icon">🗓</span>
                {fmtDisplay(date)}
                <span style={{ fontSize: 10, color: "#94a3b8", marginLeft: 2 }}>manual</span>
                <input
                  type="date"
                  className="of-date-input"
                  value={date}
                  onChange={e => setDate(e.target.value)}
                  ref={dateRef}
                />
              </div>
            </div>
            <div className="of-actions">
              <button className="of-btn of-btn-cancel" onClick={() => { setShowAdd(false); setText(""); setDate(todayStr()); }}>
                Cancel
              </button>
              <button className="of-btn of-btn-ok" onClick={handleAdd} disabled={!text.trim()}>
                Save Finding
              </button>
            </div>
          </div>
        )}

        {/* Findings List */}
        {findings.length > 0 && (
          <div className="of-list">
            <div className="of-list-header">Recorded Findings ({findings.length})</div>
            {findings.map(f => (
              <div
                key={f.id}
                className={`of-item${editingId === f.id ? " editing" : ""}`}
              >
                <div className="of-item-body">
                  <div className="of-item-date">
                    <span>📅</span>
                    {fmtDisplay(f.value || f._date || todayStr())}
                  </div>

                  {editingId === f.id ? (
                    <>
                      <textarea
                        className="of-edit-area"
                        value={editText}
                        onChange={e => setEditText(e.target.value)}
                        autoFocus
                      />
                      <div className="of-edit-actions">
                        <button className="of-edit-save" onClick={() => saveEdit(f)}>Save</button>
                        <button className="of-edit-cancel" onClick={() => setEditingId(null)}>Cancel</button>
                      </div>
                    </>
                  ) : (
                    <div className="of-item-text">{f.finding_type}</div>
                  )}
                </div>

                {editingId !== f.id && (
                  <div className="of-item-btns">
                    <button
                      className="of-icon-btn edit"
                      title="Edit"
                      onClick={() => startEdit(f)}
                    >✏️</button>
                    <button
                      className="of-icon-btn delete"
                      title="Delete"
                      onClick={() => handleDelete(f.id)}
                    >🗑️</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {findings.length === 0 && !showAdd && (
          <div className="of-empty">No findings recorded yet. Click "+ Add Finding" to begin.</div>
        )}
      </div>
    </>
  );
}