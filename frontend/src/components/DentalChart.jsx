import { useEffect, useState, useRef, useCallback } from "react";
import api from "../api/api";

/* ═══════════════════════════════════════════════════════
   INJECT STYLES
═══════════════════════════════════════════════════════ */
const injectStyles = () => {
  if (document.getElementById("dc-pro-styles")) return;
  const s = document.createElement("style");
  s.id = "dc-pro-styles";
  s.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

    :root {
      --dc-bg: #f0f2f5;
      --dc-surface: #ffffff;
      --dc-surface2: #f7f8fa;
      --dc-border: #e4e8ef;
      --dc-border2: #d1d8e4;
      --dc-text: #0d1b2a;
      --dc-text2: #4a5568;
      --dc-text3: #8a96a8;
      --dc-accent: #1a56db;
      --dc-accent2: #1046c4;
      --dc-accent-soft: #e8effe;
      --dc-shadow: 0 1px 3px rgba(13,27,42,0.08), 0 4px 16px rgba(13,27,42,0.06);
      --dc-shadow-lg: 0 8px 32px rgba(13,27,42,0.14), 0 2px 8px rgba(13,27,42,0.08);
      --dc-radius: 14px;
      --dc-radius-sm: 8px;
      --dc-font: 'DM Sans', sans-serif;
      --dc-mono: 'DM Mono', monospace;
    }

    * { box-sizing: border-box; }

    .dc-root {
      font-family: var(--dc-font);
      color: var(--dc-text);
      background: var(--dc-bg);
      padding: 0;
    }

    /* ── HEADER PANEL ── */
    .dc-header {
      background: var(--dc-surface);
      border: 1px solid var(--dc-border);
      border-radius: var(--dc-radius);
      padding: 18px 22px;
      margin-bottom: 14px;
      box-shadow: var(--dc-shadow);
      display: flex;
      align-items: center;
      gap: 20px;
      flex-wrap: wrap;
    }
    .dc-header-title {
      font-size: 16px;
      font-weight: 700;
      color: var(--dc-text);
      letter-spacing: -0.3px;
      display: flex;
      align-items: center;
      gap: 9px;
    }
    .dc-header-title-icon {
      width: 34px; height: 34px;
      background: linear-gradient(135deg, #1a56db, #2e70f0);
      border-radius: 9px;
      display: flex; align-items: center; justify-content: center;
      font-size: 17px;
      box-shadow: 0 3px 10px rgba(26,86,219,.30);
    }
    .dc-tab-group {
      display: flex;
      background: var(--dc-surface2);
      border: 1px solid var(--dc-border);
      border-radius: 10px;
      padding: 3px;
      gap: 2px;
    }
    .dc-tab {
      padding: 7px 18px;
      border-radius: 8px;
      border: none;
      background: transparent;
      font-family: var(--dc-font);
      font-size: 12.5px;
      font-weight: 600;
      color: var(--dc-text3);
      cursor: pointer;
      transition: all .18s;
      white-space: nowrap;
    }
    .dc-tab.active {
      background: var(--dc-surface);
      color: var(--dc-accent);
      box-shadow: 0 1px 4px rgba(0,0,0,.10);
    }
    .dc-stats-row {
      display: flex;
      gap: 10px;
      margin-left: auto;
      flex-wrap: wrap;
    }
    .dc-stat-chip {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 13px;
      border-radius: 20px;
      font-size: 11.5px;
      font-weight: 600;
      border: 1.5px solid;
    }
    .dc-stat-dot {
      width: 7px; height: 7px;
      border-radius: 50%;
    }

    /* ── CHART PANEL ── */
    .dc-chart-panel {
      background: var(--dc-surface);
      border: 1px solid var(--dc-border);
      border-radius: var(--dc-radius);
      box-shadow: var(--dc-shadow);
      overflow: hidden;
      margin-bottom: 14px;
    }
    .dc-chart-inner {
      background: #f8fafd;
      background-image:
        radial-gradient(circle at 50% 50%, rgba(26,86,219,0.03) 0%, transparent 70%);
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 28px 16px 20px;
    }

    /* ── TOOTH ── */
    .dc-tooth-g { cursor: pointer; transition: filter .15s; }
    .dc-tooth-g:hover .dc-tooth-body {
      filter: brightness(0.9) drop-shadow(0 3px 8px rgba(0,0,0,.22));
    }
    .dc-tooth-g.selected .dc-tooth-body {
      filter: drop-shadow(0 0 6px rgba(26,86,219,.7));
    }
    .dc-tooth-g.disabled { cursor: default; pointer-events: none; }

    /* ── QUADRANT LABEL ── */
    .dc-qlabel {
      font-family: var(--dc-mono);
      font-size: 8.5px;
      font-weight: 500;
      fill: rgba(26,86,219,0.30);
      letter-spacing: .5px;
    }

    /* ── LEGEND BAR ── */
    .dc-legend-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
      padding: 12px 18px;
      border-top: 1px solid var(--dc-border);
      background: var(--dc-surface2);
    }
    .dc-legend-item {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
      background: var(--dc-surface);
      border: 1px solid var(--dc-border);
      color: var(--dc-text2);
      cursor: default;
    }
    .dc-legend-dot {
      width: 8px; height: 8px;
      border-radius: 3px;
      flex-shrink: 0;
    }

    /* ── MODAL OVERLAY ── */
    .dc-overlay {
      position: fixed; inset: 0;
      background: rgba(8,15,30,.60);
      backdrop-filter: blur(14px) saturate(0.8);
      display: flex; align-items: center; justify-content: center;
      z-index: 9000;
      animation: dcFadeIn .16s ease both;
    }
    @keyframes dcFadeIn { from { opacity:0 } to { opacity:1 } }
    @keyframes dcSlideUp {
      from { opacity:0; transform: translateY(24px) scale(0.96) }
      to   { opacity:1; transform: none }
    }

    .dc-modal {
      background: var(--dc-surface);
      border-radius: 20px;
      width: 96%;
      max-width: 520px;
      max-height: 90vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: 0 40px 100px rgba(8,15,30,.40), 0 0 0 1px rgba(255,255,255,.08);
      animation: dcSlideUp .22s cubic-bezier(.22,.68,0,1.15) both;
    }
    .dc-modal-top {
      padding: 22px 24px 18px;
      border-bottom: 1px solid var(--dc-border);
      flex-shrink: 0;
      background: linear-gradient(160deg, #f8faff 0%, var(--dc-surface) 100%);
    }
    .dc-modal-scroll { overflow-y: auto; flex: 1; padding: 20px 24px 24px; }

    .dc-modal-head-row {
      display: flex; align-items: center; gap: 14px; margin-bottom: 0;
    }
    .dc-modal-badge {
      width: 52px; height: 52px;
      border-radius: 14px;
      display: flex; align-items: center; justify-content: center;
      font-weight: 800; font-size: 17px;
      flex-shrink: 0;
      font-family: var(--dc-mono);
      transition: all .2s;
    }
    .dc-modal-title { font-size: 18px; font-weight: 700; color: var(--dc-text); }
    .dc-modal-sub { font-size: 12px; color: var(--dc-text3); margin-top: 2px; font-weight: 500; }
    .dc-close-btn {
      margin-left: auto;
      width: 34px; height: 34px;
      border-radius: 9px;
      border: 1px solid var(--dc-border);
      background: var(--dc-surface);
      color: var(--dc-text3);
      font-size: 16px;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
      transition: all .12s;
    }
    .dc-close-btn:hover { background: #fee2e2; color: #dc2626; border-color: #fecdd3; }

    /* ── FORM ELEMENTS ── */
    .dc-field-label {
      font-size: 10.5px;
      font-weight: 700;
      color: var(--dc-text3);
      letter-spacing: .8px;
      text-transform: uppercase;
      display: block;
      margin-bottom: 9px;
    }
    .dc-field-group { margin-bottom: 20px; }

    /* Condition grid */
    .dc-cond-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(148px, 1fr));
      gap: 7px;
    }
    .dc-cond-btn {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 9px 11px;
      border-radius: 10px;
      border: 1.5px solid transparent;
      background: var(--dc-surface2);
      font-family: var(--dc-font);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all .14s;
      text-align: left;
      line-height: 1.3;
      word-break: break-word;
    }
    .dc-cond-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(0,0,0,.10); }
    .dc-cond-btn.active {
      box-shadow: 0 3px 12px rgba(0,0,0,.18), inset 0 1px 0 rgba(255,255,255,.20);
    }
    .dc-cond-dot {
      width: 10px; height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    /* Severity */
    .dc-severity-row { display: flex; gap: 6px; }
    .dc-sev-btn {
      flex: 1; padding: 9px 6px;
      border-radius: 9px;
      border: 1.5px solid var(--dc-border);
      background: var(--dc-surface2);
      font-family: var(--dc-font);
      font-size: 11.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all .13s;
      text-align: center;
      color: var(--dc-text2);
    }
    .dc-sev-btn.s1.active { background:#dcfce7; border-color:#16a34a; color:#15803d; }
    .dc-sev-btn.s2.active { background:#fef9c3; border-color:#ca8a04; color:#a16207; }
    .dc-sev-btn.s3.active { background:#ffedd5; border-color:#ea580c; color:#c2410c; }
    .dc-sev-btn.s4.active { background:#fee2e2; border-color:#dc2626; color:#b91c1c; }

    /* Surface map */
    .dc-surface-map { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .dc-surf-key {
      width: 42px; height: 42px;
      border-radius: 9px;
      border: 1.5px solid var(--dc-border);
      background: var(--dc-surface2);
      font-family: var(--dc-mono);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      color: var(--dc-text2);
      transition: all .12s;
      display: flex; align-items: center; justify-content: center;
    }
    .dc-surf-key:hover { border-color: #93c5fd; background: #eff6ff; }
    .dc-surf-key.on {
      background: linear-gradient(135deg,#1a56db,#2e70f0);
      color: #fff;
      border-color: #1046c4;
      box-shadow: 0 2px 8px rgba(26,86,219,.30);
    }
    .dc-surf-key:disabled { opacity:.35; cursor:not-allowed; }

    /* Other panel */
    .dc-other-panel {
      background: linear-gradient(135deg,#f5f7ff,#eff1ff);
      border: 1.5px solid #c7d2fe;
      border-radius: 13px;
      padding: 16px;
      margin-top: 10px;
    }
    .dc-other-ta {
      width: 100%; padding: 10px 13px;
      border: 1.5px solid #c7d2fe;
      border-radius: 9px;
      font-family: var(--dc-font);
      font-size: 13px;
      color: var(--dc-text);
      background: #fff;
      outline: none;
      resize: none;
      height: 68px;
      line-height: 1.5;
      transition: border-color .14s;
    }
    .dc-other-ta:focus { border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,.12); }
    .dc-other-ta::placeholder { color: #a5b4fc; font-style: italic; }
    .dc-palette { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 10px; }
    .dc-pdot {
      width: 26px; height: 26px;
      border-radius: 50%;
      cursor: pointer;
      border: 3px solid transparent;
      transition: all .13s;
    }
    .dc-pdot:hover { transform: scale(1.25); }
    .dc-pdot.sel { box-shadow: 0 0 0 2px #fff, 0 0 0 4px #0f172a; }

    /* Notes textarea */
    .dc-notes-ta {
      width: 100%; padding: 10px 13px;
      border: 1.5px solid var(--dc-border);
      border-radius: 9px;
      font-family: var(--dc-font);
      font-size: 13px;
      color: var(--dc-text);
      background: var(--dc-surface2);
      outline: none;
      resize: vertical;
      min-height: 64px;
      line-height: 1.5;
    }
    .dc-notes-ta:focus { border-color: var(--dc-accent); box-shadow: 0 0 0 3px rgba(26,86,219,.10); }

    /* Divider */
    .dc-divider { border: none; border-top: 1px solid var(--dc-border); margin: 18px 0; }

    /* Action buttons */
    .dc-actions { display: flex; gap: 8px; margin-top: 22px; }
    .dc-btn-primary {
      flex: 2; padding: 12px;
      border-radius: 11px;
      background: linear-gradient(135deg,#1a56db,#2e70f0);
      color: #fff; border: none;
      font-family: var(--dc-font);
      font-size: 13.5px; font-weight: 700;
      cursor: pointer;
      box-shadow: 0 4px 16px rgba(26,86,219,.28);
      transition: all .14s;
    }
    .dc-btn-primary:hover { box-shadow: 0 6px 22px rgba(26,86,219,.40); transform: translateY(-1px); }
    .dc-btn-primary:disabled { opacity:.45; cursor:not-allowed; transform:none; }
    .dc-btn-danger {
      flex: 1; padding: 12px;
      border-radius: 11px;
      background: #fff1f2; color: #be123c;
      border: 1.5px solid #fecdd3;
      font-family: var(--dc-font);
      font-size: 13px; font-weight: 700; cursor: pointer;
      transition: all .13s;
    }
    .dc-btn-danger:hover { background: #ffe4e6; border-color: #fda4af; }
    .dc-btn-ghost {
      flex: 1; padding: 12px;
      border-radius: 11px;
      background: var(--dc-surface2); color: var(--dc-text2);
      border: 1.5px solid var(--dc-border);
      font-family: var(--dc-font);
      font-size: 13px; font-weight: 600; cursor: pointer;
      transition: all .13s;
    }
    .dc-btn-ghost:hover { background: var(--dc-border); }

    /* ── SELECTED TOOTH INFO PANEL ── */
    .dc-info-panel {
      background: var(--dc-surface);
      border: 1px solid var(--dc-border);
      border-radius: var(--dc-radius);
      box-shadow: var(--dc-shadow);
      overflow: hidden;
      margin-bottom: 14px;
      transition: all .25s ease;
    }
    .dc-info-panel-head {
      padding: 14px 18px;
      display: flex;
      align-items: center;
      gap: 12px;
      border-bottom: 1px solid var(--dc-border);
      background: var(--dc-surface2);
    }
    .dc-info-panel-body { padding: 16px 18px; }

    /* ── CONDITIONS LOG ── */
    .dc-log-panel {
      background: var(--dc-surface);
      border: 1px solid var(--dc-border);
      border-radius: var(--dc-radius);
      box-shadow: var(--dc-shadow);
      overflow: hidden;
    }
    .dc-log-head {
      padding: 14px 18px;
      border-bottom: 1px solid var(--dc-border);
      background: var(--dc-surface2);
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .dc-log-title {
      font-size: 13px;
      font-weight: 700;
      color: var(--dc-text);
    }
    .dc-count-badge {
      padding: 2px 9px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 700;
    }
    .dc-filter-row {
      display: flex;
      gap: 6px;
      padding: 10px 18px;
      border-bottom: 1px solid var(--dc-border);
      flex-wrap: wrap;
      background: #fafbfd;
    }
    .dc-filter-btn {
      padding: 4px 12px;
      border-radius: 20px;
      border: 1.5px solid var(--dc-border);
      background: var(--dc-surface);
      font-family: var(--dc-font);
      font-size: 11px;
      font-weight: 600;
      color: var(--dc-text2);
      cursor: pointer;
      transition: all .12s;
    }
    .dc-filter-btn.active {
      background: var(--dc-accent-soft);
      border-color: var(--dc-accent);
      color: var(--dc-accent);
    }
    .dc-log-empty {
      padding: 36px 20px;
      text-align: center;
      color: var(--dc-text3);
      font-size: 13px;
    }
    /* ── TABLE HEADER ── */
    .dc-log-table-head {
      display: grid;
      grid-template-columns: 52px 190px 1fr 110px 96px 76px;
      align-items: center;
      padding: 9px 20px;
      background: #f4f6fa;
      border-bottom: 1.5px solid var(--dc-border);
      gap: 16px;
    }
    .dc-log-th {
      font-size: 9.5px;
      font-weight: 700;
      color: var(--dc-text3);
      letter-spacing: .9px;
      text-transform: uppercase;
      padding: 0 2px;
    }
    .dc-log-row {
      display: grid;
      grid-template-columns: 52px 190px 1fr 110px 96px 76px;
      align-items: center;
      gap: 16px;
      padding: 9px 20px;
      border-bottom: 1px solid var(--dc-border);
      transition: background .12s;
      cursor: default;
      min-height: 50px;
    }
    .dc-log-row:last-child { border-bottom: none; }
    .dc-log-row:hover { background: #f8fafd; }
    .dc-log-num {
      width: 36px; height: 36px;
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      font-family: var(--dc-mono);
      font-weight: 700; font-size: 13px;
      flex-shrink: 0;
    }
    .dc-log-cond-pill {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      transition: all .12s;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: 100%;
    }
    .dc-log-cond-pill:hover { opacity: .85; transform: translateY(-1px); }
    .dc-sev-tag {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 5px;
      font-size: 10px;
      font-weight: 700;
      font-family: var(--dc-mono);
      letter-spacing: .3px;
      white-space: nowrap;
    }
    .dc-log-surf {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 5px;
      font-family: var(--dc-mono);
      font-size: 10.5px;
      font-weight: 500;
      background: var(--dc-surface2);
      border: 1px solid var(--dc-border);
      color: var(--dc-text2);
      white-space: nowrap;
    }
    .dc-log-notes-cell {
      font-size: 12px;
      color: var(--dc-text2);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-style: italic;
    }
    .dc-log-date {
      font-family: var(--dc-mono);
      font-size: 10.5px;
      color: var(--dc-text3);
      white-space: nowrap;
      text-align: right;
    }
    .dc-log-actions {
      display: flex;
      gap: 4px;
      justify-content: flex-end;
    }
    .dc-del-btn {
      width: 30px; height: 30px;
      border-radius: 8px;
      background: transparent;
      border: 1.5px solid transparent;
      color: var(--dc-text3);
      font-size: 13px;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      transition: all .12s;
      flex-shrink: 0;
    }
    .dc-del-btn:hover { background: #fee2e2; border-color: #fecdd3; color: #dc2626; }
    .dc-edit-btn {
      width: 30px; height: 30px;
      border-radius: 8px;
      background: transparent;
      border: 1.5px solid transparent;
      color: var(--dc-text3);
      font-size: 13px;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      transition: all .12s;
      flex-shrink: 0;
    }
    .dc-edit-btn:hover { background: var(--dc-accent-soft); border-color: #93c5fd; color: var(--dc-accent); }

    /* ── TOOLTIP ── */
    .dc-tooltip-wrap { position: relative; }
    .dc-tooltip-content {
      position: absolute;
      bottom: calc(100% + 8px);
      left: 50%;
      transform: translateX(-50%);
      background: var(--dc-text);
      color: #fff;
      font-size: 10.5px;
      font-weight: 600;
      padding: 5px 10px;
      border-radius: 7px;
      white-space: nowrap;
      pointer-events: none;
      opacity: 0;
      transition: opacity .12s;
      z-index: 100;
    }
    .dc-tooltip-wrap:hover .dc-tooltip-content { opacity: 1; }

    /* ── SCROLLBAR ── */
    .dc-modal-scroll::-webkit-scrollbar { width: 5px; }
    .dc-modal-scroll::-webkit-scrollbar-track { background: transparent; }
    .dc-modal-scroll::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 99px; }
  `;
  document.head.appendChild(s);
};

/* ═══════════════════════════════════════════════════════
   DATA
═══════════════════════════════════════════════════════ */
const CONDITIONS = [
  "Caries","Missing","RC Treated","Crown","Bridge","Implant","Attrition","Impacted",
  "Fracture","Restored","Cervical Abrasion","Mobility I","Mobility II","Mobility III",
  "Gum Recession","Pockets","Other"
];
const SEVERITY_LEVELS = [
  { key:"mild",   label:"Mild",     cls:"s1" },
  { key:"moderate",label:"Moderate",cls:"s2" },
  { key:"severe", label:"Severe",   cls:"s3" },
  { key:"critical",label:"Critical",cls:"s4" },
];
const CMAP = {
  "Caries":           { a:"#dc2626", dark:"#7f1d1d", hi:"rgba(220,38,38,.15)",   emoji:"🔴", short:"CAR" },
  "Missing":          { a:"#475569", dark:"#1e293b", hi:"rgba(71,85,105,.15)",   emoji:"✖",  short:"MIS" },
  "RC Treated":       { a:"#7c3aed", dark:"#4c1d95", hi:"rgba(124,58,237,.15)",  emoji:"🔩", short:"RCT" },
  "Crown":            { a:"#b45309", dark:"#78350f", hi:"rgba(180,83,9,.15)",    emoji:"👑", short:"CRW" },
  "Bridge":           { a:"#c2410c", dark:"#7c2d12", hi:"rgba(194,65,12,.15)",   emoji:"🌉", short:"BRG" },
  "Implant":          { a:"#1d4ed8", dark:"#1e3a8a", hi:"rgba(29,78,216,.15)",   emoji:"🔧", short:"IMP" },
  "Attrition":        { a:"#065f46", dark:"#022c22", hi:"rgba(6,95,70,.15)",     emoji:"⚡", short:"ATT" },
  "Impacted":         { a:"#9d174d", dark:"#500724", hi:"rgba(157,23,77,.15)",   emoji:"⬇", short:"IMP" },
  "Fracture":         { a:"#d97706", dark:"#78350f", hi:"rgba(217,119,6,.15)",   emoji:"💥", short:"FRC" },
  "Restored":         { a:"#0369a1", dark:"#0c4a6e", hi:"rgba(3,105,161,.15)",   emoji:"🛡", short:"RST" },
  "Cervical Abrasion":{ a:"#0891b2", dark:"#164e63", hi:"rgba(8,145,178,.15)",   emoji:"🪥", short:"CAB" },
  "Mobility I":       { a:"#d97706", dark:"#92400e", hi:"rgba(217,119,6,.15)",   emoji:"Ⅰ",  short:"M-I" },
  "Mobility II":      { a:"#ea580c", dark:"#7c2d12", hi:"rgba(234,88,12,.15)",   emoji:"Ⅱ",  short:"M-II"},
  "Mobility III":     { a:"#dc2626", dark:"#7f1d1d", hi:"rgba(220,38,38,.15)",   emoji:"Ⅲ",  short:"M-III"},
  "Gum Recession":    { a:"#be185d", dark:"#831843", hi:"rgba(190,24,93,.15)",   emoji:"📉", short:"GRC" },
  "Pockets":          { a:"#7e22ce", dark:"#4a044e", hi:"rgba(126,34,206,.15)",  emoji:"🫧", short:"PKT" },
  "Other":            { a:"#6366f1", dark:"#312e81", hi:"rgba(99,102,241,.15)",  emoji:"📋", short:"OTH" },
};
const OTHER_PALETTE = [
  "#ef4444","#f97316","#eab308","#84cc16","#22c55e",
  "#14b8a6","#06b6d4","#3b82f6","#6366f1","#8b5cf6",
  "#ec4899","#f43f5e","#d97706","#7c3aed","#0ea5e9",
  "#10b981","#64748b","#dc2626","#0f172a","#374151",
];
const SURFACES = ["M","D","O","B","L","I"];
const SURF_FULL = {M:"Mesial",D:"Distal",O:"Occlusal",B:"Buccal",L:"Lingual",I:"Incisal"};

function hexToRgba(hex,a){
  const r=parseInt(hex.slice(1,3),16),g=parseInt(hex.slice(3,5),16),b=parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${a})`;
}
function colorEntryFromHex(hex){
  return { a:hex, dark:hexToRgba(hex,.88), hi:hexToRgba(hex,.15), emoji:"📋", short:"OTH" };
}
function resolveColor(condition,customColor){
  if(!condition) return null;
  if(condition==="Other"&&customColor) return { ...colorEntryFromHex(customColor), emoji:"📋", short:"OTH" };
  return CMAP[condition]||CMAP["Other"];
}

/* ═══════════════════════════════════════════════════════
   TOOTH PATHS
═══════════════════════════════════════════════════════ */
function pathMolar(w,h,r){
  return [`M ${-w/2+r} ${-h/2}`,`L ${w/2-r} ${-h/2} Q ${w/2} ${-h/2} ${w/2} ${-h/2+r}`,
    `L ${w/2} ${h/2-r} Q ${w/2} ${h/2} ${w/2-r} ${h/2}`,
    `L ${-w/2+r} ${h/2} Q ${-w/2} ${h/2} ${-w/2} ${h/2-r}`,
    `L ${-w/2} ${-h/2+r} Q ${-w/2} ${-h/2} ${-w/2+r} ${-h/2} Z`].join(' ');
}
function pathCentral(w,h){
  const hw=w/2,hh=h/2;
  return [`M ${-hw+3} ${hh}`,`C ${-hw} ${hh} ${-hw} ${-hh+8} ${-hw+2} ${-hh+2}`,
    `C ${-hw+5} ${-hh} ${-3} ${-hh-1} 0 ${-hh-1}`,`C ${3} ${-hh-1} ${hw-5} ${-hh} ${hw-2} ${-hh+2}`,
    `C ${hw} ${-hh+8} ${hw} ${hh} ${hw-3} ${hh}`,'Z'].join(' ');
}
function pathLateral(w,h){
  const hw=w/2,hh=h/2;
  return [`M ${-hw+3} ${hh}`,`C ${-hw} ${hh} ${-hw} ${-hh+7} ${-hw+3} ${-hh+1}`,
    `C ${-hw+6} ${-hh-1} ${hw-6} ${-hh-1} ${hw-3} ${-hh+1}`,
    `C ${hw} ${-hh+7} ${hw} ${hh} ${hw-3} ${hh}`,'Z'].join(' ');
}
function pathCanine(w,h){
  const hw=w/2,hh=h/2;
  return [`M ${-hw+3} ${hh}`,`C ${-hw} ${hh} ${-hw} ${-hh+12} ${-hw+3} ${-hh+4}`,
    `C ${-hw+5} ${-hh+1} ${-3} ${-hh-3} 0 ${-hh-4}`,`C ${3} ${-hh-3} ${hw-5} ${-hh+1} ${hw-3} ${-hh+4}`,
    `C ${hw} ${-hh+12} ${hw} ${hh} ${hw-3} ${hh}`,'Z'].join(' ');
}
function pathPremolar(w,h){
  const hw=w/2,hh=h/2;
  return [`M ${-hw+4} ${hh}`,`C ${-hw} ${hh} ${-hw} ${-hh+9} ${-hw+3} ${-hh+2}`,
    `C ${-hw+7} ${-hh-2} ${-3} ${-hh-3} 0 ${-hh-3}`,`C ${3} ${-hh-3} ${hw-7} ${-hh-2} ${hw-3} ${-hh+2}`,
    `C ${hw} ${-hh+9} ${hw} ${hh} ${hw-4} ${hh}`,'Z'].join(' ');
}
function toothShape(num){
  const n=num%10;
  if(num>=51&&num<=85){
    const s=n>=4?{w:38,h:34,r:12}:n===3?{w:30,h:36,r:12}:{w:25,h:30,r:10};
    return { path:pathMolar(s.w,s.h,s.r), w:s.w, h:s.h };
  }
  if(n===1){const w=31,h=42;return{path:pathCentral(w,h),w,h};}
  if(n===2){const w=26,h=38;return{path:pathLateral(w,h),w,h};}
  if(n===3){const w=29,h=44;return{path:pathCanine(w,h),w,h};}
  if(n===4||n===5){const w=34,h=37;return{path:pathPremolar(w,h),w,h};}
  const ms=n===8?{w:44,h:36,r:13}:n===7?{w:43,h:35,r:13}:{w:42,h:34,r:12};
  return{path:pathMolar(ms.w,ms.h,ms.r),w:ms.w,h:ms.h};
}

/* ═══════════════════════════════════════════════════════
   ARCH LAYOUT — pronounced U-shape
═══════════════════════════════════════════════════════ */
function buildArch(isDeciduous){
  const W=680, CX=W/2;
  const A=isDeciduous?180:228;
  const B=isDeciduous?178:222;
  const P=isDeciduous?1.28:1.22;

  const cv=t=>B*Math.pow(Math.sin(t*Math.PI),1/P);
  const cxAt=t=>CX-A*Math.cos(t*Math.PI);

  function radialDeg(t,ySign){
    const dxdt=A*Math.PI*Math.sin(t*Math.PI);
    const sa=Math.sin(t*Math.PI);
    const dcdt=sa<1e-9?0:B*Math.PI*(1/P)*Math.pow(sa,1/P-1)*Math.cos(t*Math.PI);
    const dydt=ySign*dcdt;
    return Math.atan2(dxdt,-dydt)*180/Math.PI-90;
  }

  function placeTeeth(nums,ySign,GAP){
    const K=1200,lens=[0];
    for(let i=1;i<=K;i++){
      const t0=(i-1)/K,t1=i/K;
      const dx=cxAt(t1)-cxAt(t0),dy=ySign*cv(t1)-ySign*cv(t0);
      lens.push(lens[i-1]+Math.hypot(dx,dy));
    }
    const N=nums.length;
    const widths=nums.map(n=>toothShape(n).w);
    const totalW=widths.reduce((a,b)=>a+b,0);
    const gapEach=Math.max(GAP,(lens[K]-totalW)/(N-1));
    const tAt=s=>{
      let lo=0,hi=K;
      while(lo<hi-1){const m=(lo+hi)>>1;lens[m]<=s?(lo=m):(hi=m);}
      const f=lens[lo+1]>lens[lo]?(s-lens[lo])/(lens[lo+1]-lens[lo]):0;
      return Math.min(1,Math.max(0,(lo+f)/K));
    };
    const ts=[];let cursor=widths[0]/2;
    for(let j=0;j<N;j++){
      ts.push(tAt(cursor));
      if(j<N-1)cursor+=widths[j]/2+gapEach+widths[j+1]/2;
    }
    return ts;
  }

  const BASE_U=isDeciduous?210:268;
  const SEP=isDeciduous?62:82;
  const BASE_L=BASE_U+SEP;

  const upNums=isDeciduous?[55,54,53,52,51,61,62,63,64,65]:[18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28];
  const loNums=isDeciduous?[85,84,83,82,81,71,72,73,74,75]:[48,47,46,45,44,43,42,41,31,32,33,34,35,36,37,38];

  const teeth=[];
  placeTeeth(upNums,-1,5).forEach((t,i)=>{
    teeth.push({num:upNums[i],x:cxAt(t),y:BASE_U-cv(t),rot:radialDeg(t,-1),isUpper:true});
  });
  placeTeeth(loNums,+1,5).forEach((t,i)=>{
    teeth.push({num:loNums[i],x:cxAt(t),y:BASE_L+cv(t),rot:radialDeg(t,+1)+180,isUpper:false});
  });

  const ys=teeth.map(t=>t.y),minY=Math.min(...ys),shift=minY<30?30-minY:0;
  teeth.forEach(t=>{t.y+=shift;});
  return{teeth,W,H:Math.max(...teeth.map(t=>t.y))+58,CX};
}

/* ═══════════════════════════════════════════════════════
   TOOTH SVG
═══════════════════════════════════════════════════════ */
function ToothSVG({num,x,y,rot,condition,customColor,severity,onClick,disabled,isSelected}){
  const{path,w,h}=toothShape(num);
  const cm=resolveColor(condition,customColor);
  const fill=cm?cm.a:"#cdd2db";
  const stroke=cm?cm.dark:"#9aa3b2";
  const txtC=cm?"#fff":"#2d3748";
  const fs=w>30?11:w>22?10:9;

  // Severity pulse ring
  const sevColor=
    severity==="critical"?"#dc2626":
    severity==="severe"?"#ea580c":
    severity==="moderate"?"#ca8a04":null;

  return(
    <g className={`dc-tooth-g${disabled?" disabled":""}${isSelected?" selected":""}`}
      transform={`translate(${x.toFixed(1)},${y.toFixed(1)}) rotate(${rot.toFixed(1)})`}
      onClick={()=>!disabled&&onClick(num)}>

      {/* Severity ring */}
      {sevColor&&(
        <ellipse rx={w/2+5} ry={h/2+5} fill="none"
          stroke={sevColor} strokeWidth={2} strokeDasharray="4 3" opacity={0.7}/>
      )}

      {/* Selection ring */}
      {isSelected&&(
        <ellipse rx={w/2+7} ry={h/2+7} fill="none"
          stroke="#1a56db" strokeWidth={2.5} opacity={0.8}/>
      )}

      {/* Shadow */}
      <path d={path} transform="translate(0.5,1.5)" fill="rgba(0,0,0,0.09)"/>

      {/* Body */}
      <path className="dc-tooth-body" d={path}
        fill={fill} stroke={stroke} strokeWidth={0.9} strokeLinejoin="round"/>

      {/* Gloss on healthy */}
      {!cm&&<path d={path} fill="rgba(255,255,255,0.28)" transform="scale(0.68) translate(0,-3)" stroke="none"/>}

      {/* Missing X */}
      {condition==="Missing"&&(
        <g opacity={0.65}>
          <line x1={-w*.22} y1={-h*.22} x2={w*.22} y2={h*.22} stroke={stroke} strokeWidth={1.6} strokeLinecap="round"/>
          <line x1={w*.22}  y1={-h*.22} x2={-w*.22} y2={h*.22} stroke={stroke} strokeWidth={1.6} strokeLinecap="round"/>
        </g>
      )}

      {/* Number */}
      <text x={0} y={0} textAnchor="middle" dominantBaseline="middle"
        fontSize={fs} fontWeight="600"
        fontFamily="'DM Mono','Courier New',monospace"
        fill={txtC}
        transform={`rotate(${(-rot).toFixed(1)})`}
        pointerEvents="none" style={{userSelect:"none"}}>{num}</text>

      {/* Condition short code */}
      {cm&&cm.short&&(
        <text x={0} y={h*0.27} textAnchor="middle" dominantBaseline="middle"
          fontSize={7} fontWeight="700"
          fontFamily="'DM Mono','Courier New',monospace"
          fill="rgba(255,255,255,0.75)"
          transform={`rotate(${(-rot).toFixed(1)})`}
          pointerEvents="none" style={{userSelect:"none"}}>{cm.short}</text>
      )}
    </g>
  );
}

/* ═══════════════════════════════════════════════════════
   DENTAL DIAGRAM
═══════════════════════════════════════════════════════ */
function DentalDiagram({records,chartType,onToothClick,disabled,selectedTooth}){
  const isDeciduous=chartType==="deciduous";
  const{teeth,W,H,CX}=buildArch(isDeciduous);

  const condMap={},colorMap={},sevMap={};
  records.forEach(r=>{
    condMap[r.tooth_number]=r.condition;
    if(r.custom_color)colorMap[r.tooth_number]=r.custom_color;
    if(r.severity)sevMap[r.tooth_number]=r.severity;
  });

  // selectedTooth can be a number or null — highlight it
  const selSet=selectedTooth!=null?new Set([selectedTooth]):new Set();

  return(
    <div className="dc-chart-inner">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} style={{display:"block",maxWidth:W}}>
        {/* Arch guide line */}
        <line x1={CX} y1={10} x2={CX} y2={H-10}
          stroke="rgba(26,86,219,0.12)" strokeWidth={1} strokeDasharray="5 4"/>

        {/* Quadrant labels */}
        {[{t:"UR",x:CX-8,y:12,a:"end"},{t:"UL",x:CX+8,y:12,a:"start"},
          {t:"LR",x:CX-8,y:H-4,a:"end"},{t:"LL",x:CX+8,y:H-4,a:"start"}].map(q=>(
          <text key={q.t} x={q.x} y={q.y} textAnchor={q.a}
            className="dc-qlabel">{q.t}</text>
        ))}

        {teeth.map(({num,x,y,rot,isUpper})=>(
          <ToothSVG key={num} num={num} x={x} y={y} rot={rot} isUpper={isUpper}
            condition={condMap[num]||null}
            customColor={colorMap[num]||null}
            severity={sevMap[num]||null}
            onClick={onToothClick}
            disabled={disabled}
            isSelected={selSet.has(num)}/>
        ))}
      </svg>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   TOOTH MODAL
═══════════════════════════════════════════════════════ */
function ToothModal({tooth,existing,disabled,onSave,onDelete,onClose,saving,deleting}){
  const[condition,setCondition]=useState(existing?.condition||"");
  const[severity,setSeverity]=useState(existing?.severity||"");
  const[otherText,setOtherText]=useState(existing?.other_text||"");
  const[otherColor,setOtherColor]=useState(existing?.custom_color||OTHER_PALETTE[8]);
  const[surfaces,setSurfaces]=useState(existing?.surface?existing.surface.split(",").filter(Boolean):[]);
  const[notes,setNotes]=useState(existing?.notes||"");
  const taRef=useRef(null);

  const isOther=condition==="Other";
  const cm=resolveColor(condition,isOther?otherColor:null);
  const canSave=condition&&(!isOther||otherText.trim().length>0);

  useEffect(()=>{if(isOther&&taRef.current)setTimeout(()=>taRef.current?.focus(),80);},[isOther]);

  const togSurf=s=>{if(disabled)return;setSurfaces(p=>p.includes(s)?p.filter(x=>x!==s):[...p,s]);};

  const badgeBg=cm?cm.a:"#e2d0b0";
  const badgeBorder=cm?cm.dark:"#8c6030";

  return(
    <div className="dc-overlay" onClick={onClose}>
      <div className="dc-modal" onClick={e=>e.stopPropagation()}>

        {/* Header */}
        <div className="dc-modal-top">
          <div className="dc-modal-head-row">
            <div className="dc-modal-badge"
              style={{background:badgeBg,border:`2px solid ${badgeBorder}`,color:"#fff",
                boxShadow:`0 4px 16px ${badgeBg}55`}}>
              {tooth}
            </div>
            <div>
              <div className="dc-modal-title">Tooth #{tooth}</div>
              <div className="dc-modal-sub">
                {existing?"Edit existing condition":"Record new condition"}
                {existing?.updated_at&&` · Last updated ${new Date(existing.updated_at).toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"numeric"})}`}
              </div>
            </div>
            <button className="dc-close-btn" onClick={onClose}>✕</button>
          </div>
        </div>

        {/* Scrollable body */}
        <div className="dc-modal-scroll">

          {/* Condition */}
          <div className="dc-field-group">
            <label className="dc-field-label">Diagnosis / Condition</label>
            <div className="dc-cond-grid">
              {CONDITIONS.map(c=>{
                const cm2=CMAP[c];
                const sel=condition===c;
                return(
                  <button key={c} className={`dc-cond-btn${sel?" active":""}`}
                    disabled={disabled}
                    style={sel?{background:cm2.a,color:"#fff",borderColor:cm2.dark}:
                      {borderColor:`${cm2.a}33`,color:cm2.dark}}
                    onClick={()=>setCondition(c)}>
                    <span className="dc-cond-dot"
                      style={{background:cm2.a,boxShadow:sel?`0 0 0 2px rgba(255,255,255,.4)`:""}}/>
                    <span style={{fontSize:11.5}}>{cm2.emoji}</span>
                    {c}
                  </button>
                );
              })}
            </div>

            {/* Other panel */}
            {isOther&&(
              <div className="dc-other-panel">
                <label className="dc-field-label" style={{color:"#6366f1"}}>Custom description</label>
                <textarea ref={taRef} className="dc-other-ta"
                  placeholder="e.g. Fracture, Erosion, Fluorosis, Hypersensitivity…"
                  value={otherText} disabled={disabled}
                  onChange={e=>setOtherText(e.target.value)}/>
                <div style={{fontSize:10,fontWeight:700,color:"#6366f1",letterSpacing:".7px",
                  textTransform:"uppercase",margin:"12px 0 8px"}}>Highlight color</div>
                <div className="dc-palette">
                  {OTHER_PALETTE.map(hex=>(
                    <div key={hex} className={`dc-pdot${otherColor===hex?" sel":""}`}
                      style={{background:hex,borderColor:otherColor===hex?"#0f172a":"transparent"}}
                      onClick={()=>!disabled&&setOtherColor(hex)}/>
                  ))}
                </div>
                <div style={{marginTop:12,padding:"9px 12px",borderRadius:9,
                  background:`${otherColor}18`,border:`1.5px solid ${otherColor}44`,
                  display:"flex",gap:10,alignItems:"center"}}>
                  <div style={{width:28,height:28,borderRadius:8,background:otherColor,flexShrink:0,
                    border:`2px solid ${otherColor}cc`,boxShadow:`0 2px 8px ${otherColor}66`}}/>
                  <div style={{fontSize:12,fontWeight:600,color:otherColor}}>
                    {otherText.trim()||"Custom condition"}
                    <div style={{fontSize:10,color:"#94a3b8",fontWeight:400,marginTop:1}}>Preview color</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <hr className="dc-divider"/>

          {/* Severity */}
          <div className="dc-field-group">
            <label className="dc-field-label">Severity Level</label>
            <div className="dc-severity-row">
              {SEVERITY_LEVELS.map(sv=>(
                <button key={sv.key}
                  className={`dc-sev-btn ${sv.cls}${severity===sv.key?" active":""}`}
                  disabled={disabled}
                  onClick={()=>setSeverity(p=>p===sv.key?"":sv.key)}>
                  {sv.label}
                </button>
              ))}
            </div>
          </div>

          {/* Surfaces */}
          <div className="dc-field-group">
            <label className="dc-field-label">Affected Surfaces</label>
            <div className="dc-surface-map">
              {SURFACES.map(s=>(
                <div key={s} className="dc-tooltip-wrap">
                  <button className={`dc-surf-key${surfaces.includes(s)?" on":""}`}
                    disabled={disabled} onClick={()=>togSurf(s)}>
                    {s}
                  </button>
                  <span className="dc-tooltip-content">{SURF_FULL[s]}</span>
                </div>
              ))}
              {surfaces.length>0&&(
                <span style={{fontSize:11.5,color:"#64748b",fontWeight:500,marginLeft:4}}>
                  {surfaces.map(s=>SURF_FULL[s]).join(", ")}
                </span>
              )}
            </div>
          </div>

          {/* Notes */}
          <div className="dc-field-group">
            <label className="dc-field-label">Clinical Notes</label>
            <textarea className="dc-notes-ta"
              placeholder="Observations, treatment plan, follow-up instructions, referrals…"
              value={notes} disabled={disabled}
              onChange={e=>setNotes(e.target.value)}/>
          </div>

          {/* Actions */}
          {!disabled?(
            <div className="dc-actions">
              <button className="dc-btn-ghost" onClick={onClose}>Cancel</button>
              {existing&&(
                <button className="dc-btn-danger" onClick={onDelete} disabled={deleting}>
                  {deleting?"…":"🗑 Delete"}
                </button>
              )}
              <button className="dc-btn-primary"
                disabled={!canSave||saving}
                onClick={()=>onSave({
                  condition,severity,surface:surfaces.join(","),notes,
                  other_text:isOther?otherText:"",
                  custom_color:isOther?otherColor:"",
                })}>
                {saving?"Saving…":existing?"✔ Update Record":"✔ Save Record"}
              </button>
            </div>
          ):(
            <div className="dc-actions">
              <button className="dc-btn-ghost" onClick={onClose} style={{flex:1}}>Close</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   SELECTED TOOTH INFO PANEL
═══════════════════════════════════════════════════════ */
function SelectedToothPanel({tooth,record,onEdit,onDeselect,disabled}){
  if(!tooth) return(
    <div className="dc-info-panel" style={{padding:"22px 20px",textAlign:"center"}}>
      <div style={{fontSize:28,marginBottom:8,opacity:.35}}>🦷</div>
      <div style={{fontSize:13,color:"var(--dc-text3)",fontWeight:500}}>
        Select any tooth on the chart to view or record its condition
      </div>
    </div>
  );

  const cm=record?resolveColor(record.condition,record.custom_color):null;
  const condLabel=record?(record.condition==="Other"&&record.other_text?record.other_text:record.condition):null;

  return(
    <div className="dc-info-panel">
      <div className="dc-info-panel-head" style={cm?{borderLeft:`4px solid ${cm.a}`}:{}}>
        <div style={{
          width:40,height:40,borderRadius:11,flexShrink:0,
          background:cm?cm.a:"#e2e8f0",
          border:`2px solid ${cm?cm.dark:"#cbd5e1"}`,
          display:"flex",alignItems:"center",justifyContent:"center",
          fontFamily:"'DM Mono',monospace",fontWeight:700,fontSize:14,
          color:cm?"#fff":"#64748b",
          boxShadow:cm?`0 3px 12px ${cm.a}44`:"none",
        }}>{tooth}</div>

        <div style={{flex:1,minWidth:0}}>
          <div style={{fontSize:11,fontWeight:700,color:"var(--dc-text3)",textTransform:"uppercase",letterSpacing:".7px",marginBottom:2}}>
            Selected Tooth
          </div>
          <div style={{fontSize:15,fontWeight:700,color:"var(--dc-text)",display:"flex",alignItems:"center",gap:8,flexWrap:"wrap"}}>
            Tooth #{tooth}
            {condLabel&&cm&&(
              <span style={{display:"inline-flex",alignItems:"center",gap:5,padding:"3px 11px",
                borderRadius:20,background:cm.a,color:"#fff",fontSize:12,fontWeight:700,
                boxShadow:`0 2px 8px ${cm.a}44`}}>
                {CMAP[record.condition]?.emoji||"📋"} {condLabel}
              </span>
            )}
            {!condLabel&&<span style={{fontSize:12,fontWeight:500,color:"var(--dc-text3)",fontStyle:"italic"}}>No condition recorded</span>}
          </div>
          {record?.surface&&(
            <div style={{fontSize:11,color:"var(--dc-text3)",marginTop:3,fontFamily:"'DM Mono',monospace"}}>
              Surfaces: {record.surface}
            </div>
          )}
        </div>

        <div style={{display:"flex",gap:6,flexShrink:0}}>
          {!disabled&&(
            <button onClick={()=>onEdit(tooth)}
              style={{padding:"6px 14px",borderRadius:8,background:"var(--dc-accent-soft)",
                color:"var(--dc-accent)",border:"1.5px solid #93c5fd",fontFamily:"var(--dc-font)",
                fontSize:12,fontWeight:700,cursor:"pointer",transition:"all .12s"}}>
              ✏️ Edit
            </button>
          )}
          <button onClick={onDeselect}
            style={{width:32,height:32,borderRadius:8,border:"1px solid var(--dc-border)",
              background:"var(--dc-surface)",color:"var(--dc-text3)",fontSize:15,cursor:"pointer",
              display:"flex",alignItems:"center",justifyContent:"center",transition:"all .12s"}}>✕</button>
        </div>
      </div>

      {record&&(
        <div className="dc-info-panel-body">
          <div style={{display:"flex",gap:16,flexWrap:"wrap"}}>
            {record.severity&&(
              <div>
                <div style={{fontSize:10,fontWeight:700,color:"var(--dc-text3)",textTransform:"uppercase",letterSpacing:".7px",marginBottom:4}}>Severity</div>
                <span style={{padding:"3px 10px",borderRadius:6,fontSize:11.5,fontWeight:700,
                  background:record.severity==="critical"?"#fee2e2":record.severity==="severe"?"#ffedd5":record.severity==="moderate"?"#fef9c3":"#dcfce7",
                  color:record.severity==="critical"?"#b91c1c":record.severity==="severe"?"#c2410c":record.severity==="moderate"?"#a16207":"#15803d",
                  border:`1px solid ${record.severity==="critical"?"#fca5a5":record.severity==="severe"?"#fdba74":record.severity==="moderate"?"#fde047":"#86efac"}`,
                }}>
                  {record.severity.charAt(0).toUpperCase()+record.severity.slice(1)}
                </span>
              </div>
            )}
            {record.notes&&(
              <div style={{flex:1,minWidth:160}}>
                <div style={{fontSize:10,fontWeight:700,color:"var(--dc-text3)",textTransform:"uppercase",letterSpacing:".7px",marginBottom:4}}>Clinical Notes</div>
                <div style={{fontSize:12.5,color:"var(--dc-text2)",lineHeight:1.5,fontStyle:"italic"}}>
                  "{record.notes}"
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   CONDITIONS LOG
═══════════════════════════════════════════════════════ */
function ConditionsLog({records,chartType,disabled,onEdit,onDelete,deleting}){
  const[filter,setFilter]=useState("all");

  const affected=records.filter(r=>{
    const n=r.tooth_number;
    return chartType==="permanent"?(n>=11&&n<=48):(n>=51&&n<=85);
  }).slice().sort((a,b)=>a.tooth_number-b.tooth_number);

  const conditionTypes=[...new Set(affected.map(r=>r.condition))];

  const filtered=filter==="all"?affected:affected.filter(r=>r.condition===filter);

  const formatDate=d=>{
    const dt = d ? new Date(d) : new Date();
    try{return dt.toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"numeric"});}
    catch{return d||"Today";}
  };

  const sevStyle=s=>({
    critical:{bg:"#fee2e2",col:"#b91c1c",bdr:"#fca5a5"},
    severe:  {bg:"#ffedd5",col:"#c2410c",bdr:"#fdba74"},
    moderate:{bg:"#fef9c3",col:"#a16207",bdr:"#fde047"},
    mild:    {bg:"#dcfce7",col:"#15803d",bdr:"#86efac"},
  }[s]||null);

  return(
    <div className="dc-log-panel">
      <div className="dc-log-head">
        <span style={{fontSize:14,marginRight:2}}>📋</span>
        <span className="dc-log-title">Conditions Log</span>
        <span className="dc-count-badge"
          style={{background:"#fee2e2",color:"#b91c1c",border:"1px solid #fecaca"}}>
          {affected.length}
        </span>
        <div style={{marginLeft:"auto",fontSize:11,color:"var(--dc-text3)",fontWeight:500}}>
          {affected.length} tooth{affected.length!==1?"s":""} marked
        </div>
      </div>

      {/* Filters */}
      {conditionTypes.length>1&&(
        <div className="dc-filter-row">
          <span style={{fontSize:10,fontWeight:700,color:"var(--dc-text3)",textTransform:"uppercase",
            letterSpacing:".7px",alignSelf:"center",marginRight:4}}>Filter:</span>
          <button className={`dc-filter-btn${filter==="all"?" active":""}`} onClick={()=>setFilter("all")}>
            All ({affected.length})
          </button>
          {conditionTypes.map(c=>(
            <button key={c} className={`dc-filter-btn${filter===c?" active":""}`} onClick={()=>setFilter(c)}>
              {CMAP[c]?.emoji} {c} ({affected.filter(r=>r.condition===c).length})
            </button>
          ))}
        </div>
      )}

      {filtered.length===0?(
        <div className="dc-log-empty">
          <div style={{fontSize:24,marginBottom:8}}>🦷</div>
          No conditions recorded yet.<br/>Click on any tooth to start.
        </div>
      ):(
        <div>
          {/* Column headers */}
          <div className="dc-log-table-head">
            <span className="dc-log-th">Tooth</span>
            <span className="dc-log-th">Condition</span>
            <span className="dc-log-th">Notes</span>
            <span className="dc-log-th">Surfaces</span>
            <span className="dc-log-th">Date</span>
            {!disabled&&<span className="dc-log-th" style={{textAlign:"right"}}>Actions</span>}
          </div>

          {filtered.map((r,idx)=>{
            const cm=r.custom_color?colorEntryFromHex(r.custom_color):(CMAP[r.condition]||CMAP["Other"]);
            const isOther=r.condition==="Other";
            // For "Other": show the custom text as the label; pill still uses condition color
            const condLabel=isOther&&r.other_text?r.other_text:r.condition;
            const emoji=isOther?"📋":(CMAP[r.condition]?.emoji||"");
            const sv=sevStyle(r.severity);
            return(
              <div key={r.id||r.tooth_number} className="dc-log-row">

                {/* ── Col 1: Tooth badge ── */}
                <div className="dc-log-num"
                  style={{background:cm.hi,border:`1.5px solid ${cm.a}55`,color:cm.dark}}>
                  {r.tooth_number}
                </div>

                {/* ── Col 2: Condition pill + severity tag ── */}
                <div style={{display:"flex",flexDirection:"column",gap:3,minWidth:0}}>
                  <span className="dc-log-cond-pill"
                    style={{background:cm.a,color:"#fff",boxShadow:`0 2px 8px ${cm.a}44`}}
                    onClick={()=>!disabled&&onEdit(r.tooth_number)}
                    title={isOther&&r.other_text?`Other: ${r.other_text}`:r.condition}>
                    {emoji} {condLabel}
                  </span>
                  {sv&&(
                    <span className="dc-sev-tag"
                      style={{background:sv.bg,color:sv.col,border:`1px solid ${sv.bdr}`,
                        alignSelf:"flex-start"}}>
                      {r.severity.toUpperCase()}
                    </span>
                  )}
                </div>

                {/* ── Col 3: Notes (italic, truncated) ── */}
                <div className="dc-log-notes-cell">
                  {r.notes
                    ? <span title={r.notes}>{r.notes}</span>
                    : <span style={{color:"var(--dc-text3)",fontStyle:"normal",fontSize:11}}>—</span>
                  }
                </div>

                {/* ── Col 4: Surfaces ── */}
                <div>
                  {r.surface
                    ? <span className="dc-log-surf">{r.surface}</span>
                    : <span style={{color:"var(--dc-text3)",fontSize:11}}>—</span>
                  }
                </div>

                {/* ── Col 5: Date ── */}
                <span className="dc-log-date">{formatDate(r.created_at||r.updated_at)}</span>

                {/* ── Col 6: Actions ── */}
                {!disabled&&(
                  <div className="dc-log-actions">
                    <button className="dc-edit-btn" title="Edit condition"
                      onClick={()=>onEdit(r.tooth_number)}>✏️</button>
                    <button className="dc-del-btn" title={`Delete tooth #${r.tooth_number}`}
                      disabled={deleting}
                      onClick={()=>{
                        if(window.confirm(`Remove condition from Tooth #${r.tooth_number}?`))
                          onDelete(r.id,r.tooth_number);
                      }}>🗑</button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


/* ═══════════════════════════════════════════════════════
   ADD CONDITION MODAL — pick tooth + condition directly
═══════════════════════════════════════════════════════ */
function AddConditionModal({ chartType, onSave, onClose, saving }) {
  const PERM_NUMS = [
    11,12,13,14,15,16,17,18,
    21,22,23,24,25,26,27,28,
    31,32,33,34,35,36,37,38,
    41,42,43,44,45,46,47,48,
  ];
  const DEC_NUMS = [51,52,53,54,55,61,62,63,64,65,71,72,73,74,75,81,82,83,84,85];
  const nums = chartType === "deciduous" ? DEC_NUMS : PERM_NUMS;

  const [selectedTeeth, setSelectedTeeth] = useState(new Set());
  const [condition,     setCondition]     = useState("");
  const [severity,      setSeverity]      = useState("");
  const [surfaces,      setSurfaces]      = useState([]);
  const [notes,         setNotes]         = useState("");
  const [otherText,     setOtherText]     = useState("");
  const [otherColor,    setOtherColor]    = useState(OTHER_PALETTE[8]);

  const toggle = n => setSelectedTeeth(p => {
    const s = new Set(p); s.has(n) ? s.delete(n) : s.add(n); return s;
  });
  const isOther = condition === "Other";
  const cm = condition ? resolveColor(condition, isOther ? otherColor : null) : null;
  const canSave = condition && selectedTeeth.size > 0 && (!isOther || otherText.trim());

  // Group teeth by row of 8 for display
  const rows = [];
  for (let i = 0; i < nums.length; i += 8) rows.push(nums.slice(i, i + 8));

  return (
    <div className="dc-overlay" onClick={onClose}>
      <div className="dc-modal" style={{ maxWidth: 560 }} onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="dc-modal-top">
          <div className="dc-modal-head-row">
            <div className="dc-modal-badge"
              style={{ background: cm ? cm.a : "#e2e8f0", border: `2px solid ${cm ? cm.dark : "#cbd5e1"}`, color: "#fff" }}>
              🦷
            </div>
            <div>
              <div className="dc-modal-title">Add Condition</div>
              <div className="dc-modal-sub">Select teeth, then pick a condition</div>
            </div>
            <button className="dc-close-btn" onClick={onClose}>✕</button>
          </div>
        </div>

        <div className="dc-modal-scroll">

          {/* Step 1 — Teeth picker */}
          <div className="dc-field-group">
            <label className="dc-field-label">Step 1 — Select Teeth</label>
            <div style={{ background: "var(--dc-surface2)", border: "1.5px solid var(--dc-border)", borderRadius: 10, padding: "10px 12px", marginBottom: 8 }}>
              {rows.map((row, ri) => (
                <div key={ri} style={{ display: "flex", gap: 5, marginBottom: ri < rows.length - 1 ? 6 : 0, flexWrap: "wrap" }}>
                  {row.map(n => (
                    <button key={n}
                      onClick={() => toggle(n)}
                      style={{
                        width: 36, height: 36, borderRadius: 8,
                        border: selectedTeeth.has(n) ? `2px solid ${cm ? cm.dark : "#1a56db"}` : "1.5px solid var(--dc-border)",
                        background: selectedTeeth.has(n) ? (cm ? cm.a : "#1a56db") : "var(--dc-surface)",
                        color: selectedTeeth.has(n) ? "#fff" : "var(--dc-text2)",
                        fontSize: 11, fontWeight: 700, cursor: "pointer",
                        fontFamily: "'DM Mono',monospace",
                        transition: "all .12s",
                        transform: selectedTeeth.has(n) ? "scale(1.12)" : "scale(1)",
                      }}>
                      {n}
                    </button>
                  ))}
                </div>
              ))}
            </div>
            {selectedTeeth.size > 0 && (
              <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "6px 10px", background: cm ? `${cm.a}12` : "var(--dc-accent-soft)", border: `1px solid ${cm ? cm.a + "44" : "#93c5fd"}`, borderRadius: 7 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: cm ? cm.dark : "var(--dc-accent)" }}>Selected IRT:</span>
                <span style={{ fontFamily: "'DM Mono',monospace", fontWeight: 700, color: cm ? cm.dark : "var(--dc-accent)", fontSize: 12 }}>
                  {[...selectedTeeth].sort((a, b) => a - b).join(", ")}
                </span>
                <button onClick={() => setSelectedTeeth(new Set())} style={{ marginLeft: "auto", border: "none", background: "none", color: "#ef4444", cursor: "pointer", fontSize: 11, fontWeight: 600 }}>✕ Clear</button>
              </div>
            )}
          </div>

          <hr className="dc-divider" />

          {/* Step 2 — Condition */}
          <div className="dc-field-group">
            <label className="dc-field-label">Step 2 — Choose Condition</label>
            <div className="dc-cond-grid">
              {CONDITIONS.map(c => {
                const cm2 = CMAP[c];
                const sel = condition === c;
                return (
                  <button key={c} className={`dc-cond-btn${sel ? " active" : ""}`}
                    style={sel ? { background: cm2.a, color: "#fff", borderColor: cm2.dark } : { borderColor: `${cm2.a}33`, color: cm2.dark }}
                    onClick={() => setCondition(c === condition ? "" : c)}>
                    <span className="dc-cond-dot" style={{ background: cm2.a, boxShadow: sel ? "0 0 0 2px rgba(255,255,255,.4)" : "" }} />
                    <span style={{ fontSize: 11.5 }}>{cm2.emoji}</span>
                    {c}
                  </button>
                );
              })}
            </div>
            {isOther && (
              <div className="dc-other-panel">
                <label className="dc-field-label" style={{ color: "#6366f1" }}>Custom description</label>
                <textarea className="dc-other-ta" placeholder="e.g. Erosion, Fluorosis…"
                  value={otherText} onChange={e => setOtherText(e.target.value)} />
                <div className="dc-palette">
                  {OTHER_PALETTE.map(hex => (
                    <div key={hex} className={`dc-pdot${otherColor === hex ? " sel" : ""}`}
                      style={{ background: hex, borderColor: otherColor === hex ? "#0f172a" : "transparent" }}
                      onClick={() => setOtherColor(hex)} />
                  ))}
                </div>
              </div>
            )}
          </div>

          {condition && (
            <>
              <hr className="dc-divider" />
              {/* Severity */}
              <div className="dc-field-group">
                <label className="dc-field-label">Severity (optional)</label>
                <div className="dc-severity-row">
                  {SEVERITY_LEVELS.map(sv => (
                    <button key={sv.key} className={`dc-sev-btn ${sv.cls}${severity === sv.key ? " active" : ""}`}
                      onClick={() => setSeverity(p => p === sv.key ? "" : sv.key)}>
                      {sv.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Surfaces */}
              <div className="dc-field-group">
                <label className="dc-field-label">Surfaces (optional)</label>
                <div className="dc-surface-map">
                  {SURFACES.map(s => (
                    <div key={s} className="dc-tooltip-wrap">
                      <button className={`dc-surf-key${surfaces.includes(s) ? " on" : ""}`}
                        onClick={() => setSurfaces(p => p.includes(s) ? p.filter(x => x !== s) : [...p, s])}>
                        {s}
                      </button>
                      <span className="dc-tooltip-content">{SURF_FULL[s]}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Notes */}
              <div className="dc-field-group">
                <label className="dc-field-label">Clinical Notes (optional)</label>
                <textarea className="dc-notes-ta" placeholder="Observations…"
                  value={notes} onChange={e => setNotes(e.target.value)} />
              </div>
            </>
          )}

          {/* Actions */}
          <div className="dc-actions">
            <button className="dc-btn-ghost" onClick={onClose}>Cancel</button>
            <button className="dc-btn-primary" disabled={!canSave || saving}
              onClick={() => onSave({
                teeth: [...selectedTeeth].sort((a, b) => a - b),
                condition, severity,
                surface: surfaces.join(","),
                notes,
                other_text: isOther ? otherText : "",
                custom_color: isOther ? otherColor : "",
              })}>
              {saving ? "Saving…" : `✔ Add ${selectedTeeth.size > 1 ? selectedTeeth.size + " teeth" : "condition"}`}
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   MAIN EXPORT
═══════════════════════════════════════════════════════ */
/* ═══════════════════════════════════════════════════════
   GROUPED CONDITIONS LOG (new format)
═══════════════════════════════════════════════════════ */
function GroupedConditionsLog({records,chartType,disabled,onEditGroup,onDeleteTooth,deleting,onAdd}){
  const affected=records.filter(r=>{
    const n=r.tooth_number;
    return chartType==="permanent"?(n>=11&&n<=48):(n>=51&&n<=85);
  });

  // Group by condition
  const groups={};
  affected.forEach(r=>{
    const key=r.condition==="Other"&&r.other_text?r.other_text:r.condition;
    if(!groups[key])groups[key]={condition:r.condition,label:key,rows:[]};
    groups[key].rows.push(r);
  });

  const formatDate=d=>{
    try{return new Date(d||Date.now()).toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"numeric"});}
    catch{return "Today";}
  };

  if(!Object.keys(groups).length) return(
    <div className="dc-log-panel">
      <div className="dc-log-head">
        <span style={{fontSize:14,marginRight:2}}>📋</span>
        <span className="dc-log-title">Conditions Log</span>
        <span className="dc-count-badge" style={{background:"#fee2e2",color:"#b91c1c",border:"1px solid #fecaca"}}>0</span>
        {!disabled&&(
          <button onClick={onAdd}
            style={{marginLeft:"auto",padding:"5px 13px",borderRadius:8,
              background:"linear-gradient(135deg,#1a56db,#2e70f0)",color:"#fff",border:"none",
              fontSize:12,fontWeight:700,cursor:"pointer",display:"flex",alignItems:"center",gap:5,
              fontFamily:"var(--dc-font)",boxShadow:"0 2px 8px rgba(26,86,219,.28)"}}>
            + Add Condition
          </button>
        )}
      </div>
      <div className="dc-log-empty"><div style={{fontSize:24,marginBottom:8}}>🦷</div>No conditions recorded yet. Click "+ Add Condition" to start.</div>
    </div>
  );

  return(
    <div className="dc-log-panel">
      <div className="dc-log-head">
        <span style={{fontSize:14,marginRight:2}}>📋</span>
        <span className="dc-log-title">Conditions Log</span>
        <span className="dc-count-badge" style={{background:"#fee2e2",color:"#b91c1c",border:"1px solid #fecaca"}}>
          {affected.length}
        </span>
        <div style={{marginLeft:"auto",display:"flex",alignItems:"center",gap:10}}>
          <span style={{fontSize:11,color:"var(--dc-text3)",fontWeight:500}}>
            {affected.length} tooth{affected.length!==1?"s":""} marked
          </span>
          {!disabled&&(
            <button
              onClick={onAdd}
              style={{
                padding:"5px 13px",borderRadius:8,
                background:"linear-gradient(135deg,#1a56db,#2e70f0)",
                color:"#fff",border:"none",fontSize:12,fontWeight:700,
                cursor:"pointer",display:"flex",alignItems:"center",gap:5,
                fontFamily:"var(--dc-font)",
                boxShadow:"0 2px 8px rgba(26,86,219,.28)",
                transition:"all .14s",
              }}>
              + Add Condition
            </button>
          )}
        </div>
      </div>

      <div style={{display:"flex",flexDirection:"column",gap:10,padding:"4px 0"}}>
        {Object.values(groups).map(({condition,label,rows})=>{
          const cm=CMAP[condition]||CMAP["Other"];
          const emoji=cm.emoji||"📋";
          const sortedRows=[...rows].sort((a,b)=>a.tooth_number-b.tooth_number);
          return(
            <div key={label} style={{
              background:"#fff",border:`1.5px solid ${cm.a}33`,borderRadius:12,
              padding:"12px 14px",boxShadow:`0 1px 4px ${cm.a}14`}}>
              {/* Group header */}
              <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:10}}>
                <span style={{
                  display:"inline-flex",alignItems:"center",gap:5,
                  padding:"4px 12px",borderRadius:20,background:cm.a,color:"#fff",
                  fontSize:12,fontWeight:700,boxShadow:`0 2px 8px ${cm.a}44`}}>
                  {emoji} {label}
                </span>
                <span style={{fontSize:11,color:"var(--dc-text3)"}}>
                  IRT:&nbsp;
                  <span style={{fontFamily:"'DM Mono',monospace",fontWeight:600,color:cm.dark}}>
                    {sortedRows.map(r=>r.tooth_number).join(", ")}
                  </span>
                </span>
                {!disabled&&(
                  <button
                    title={`Edit all ${label} teeth`}
                    onClick={()=>onEditGroup(condition,sortedRows)}
                    style={{marginLeft:"auto",padding:"4px 10px",borderRadius:7,border:`1.5px solid ${cm.a}55`,
                      background:cm.hi,color:cm.dark,fontSize:11,fontWeight:600,cursor:"pointer",
                      fontFamily:"var(--dc-font)",transition:"all .12s"}}>
                    ✏️ Edit
                  </button>
                )}
              </div>

              {/* Each tooth row */}
              <div style={{display:"flex",flexDirection:"column",gap:6}}>
                {sortedRows.map(r=>(
                  <div key={r.id||r.tooth_number} style={{
                    display:"flex",alignItems:"center",gap:8,
                    padding:"6px 10px",borderRadius:8,
                    background:"var(--dc-surface2)",border:"1px solid var(--dc-border)"}}>
                    {/* Tooth badge */}
                    <div style={{
                      width:32,height:32,borderRadius:8,flexShrink:0,
                      background:cm.hi,border:`1.5px solid ${cm.a}55`,
                      display:"flex",alignItems:"center",justifyContent:"center",
                      fontFamily:"'DM Mono',monospace",fontWeight:700,fontSize:12,color:cm.dark}}>
                      {r.tooth_number}
                    </div>
                    {/* Notes / surfaces */}
                    <div style={{flex:1,minWidth:0}}>
                      {r.notes&&<div style={{fontSize:11.5,color:"var(--dc-text2)",fontStyle:"italic",lineHeight:1.4}}>"{r.notes}"</div>}
                      {r.surface&&<div style={{fontSize:10,color:"var(--dc-text3)",marginTop:2,fontFamily:"'DM Mono',monospace"}}>Surfaces: {r.surface}</div>}
                      {!r.notes&&!r.surface&&<div style={{fontSize:11,color:"var(--dc-text3)"}}>—</div>}
                    </div>
                    {/* Date */}
                    <span style={{fontSize:11,color:"var(--dc-text3)",fontFamily:"'DM Mono',monospace",whiteSpace:"nowrap"}}>
                      {formatDate(r.created_at||r.updated_at)}
                    </span>
                    {/* Per-tooth edit & delete */}
                    {!disabled&&(
                      <div style={{display:"flex",gap:4,flexShrink:0}}>
                        <button className="dc-edit-btn" title={`Edit tooth #${r.tooth_number}`}
                          onClick={()=>onEditGroup(condition,[r])}>✏️</button>
                        <button className="dc-del-btn" title={`Delete tooth #${r.tooth_number}`}
                          disabled={deleting}
                          onClick={()=>onDeleteTooth(r.id,r.tooth_number,label)}>🗑</button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   CONDITION SELECTOR PANEL (select condition first)
═══════════════════════════════════════════════════════ */
function ConditionSelectorPanel({activeCondition,onSelect,onClear,selectedTeeth,onClearTeeth}){
  const [otherText,setOtherText]=useState("");
  const [otherColor,setOtherColor]=useState(OTHER_PALETTE[8]);
  const [severity,setSeverity]=useState("");
  const [surfaces,setSurfaces]=useState([]);
  const [notes,setNotes]=useState("");

  // Reset extras when condition changes
  useEffect(()=>{setSeverity("");setSurfaces([]);setNotes("");},[activeCondition]);

  const togSurf=s=>setSurfaces(p=>p.includes(s)?p.filter(x=>x!==s):[...p,s]);
  const isOther=activeCondition==="Other";
  const cm=activeCondition?resolveColor(activeCondition,isOther?otherColor:null):null;

  return(
    <div style={{
      background:"#fff",border:"1.5px solid var(--dc-border)",borderRadius:14,
      padding:"16px 18px",marginBottom:14,boxShadow:"var(--dc-shadow)"}}>

      <div style={{fontSize:12,fontWeight:700,color:"var(--dc-text3)",textTransform:"uppercase",
        letterSpacing:".7px",marginBottom:12}}>
        Step 1 — Select Condition
      </div>

      {/* Condition grid */}
      <div className="dc-cond-grid" style={{marginBottom:12}}>
        {CONDITIONS.map(c=>{
          const cm2=CMAP[c];
          const sel=activeCondition===c;
          return(
            <button key={c} className={`dc-cond-btn${sel?" active":""}`}
              style={sel?{background:cm2.a,color:"#fff",borderColor:cm2.dark}:
                {borderColor:`${cm2.a}33`,color:cm2.dark}}
              onClick={()=>onSelect(c===activeCondition?null:c,{otherText,otherColor,severity,surfaces,notes})}>
              <span className="dc-cond-dot" style={{background:cm2.a,boxShadow:sel?"0 0 0 2px rgba(255,255,255,.4)":""}}/>
              <span style={{fontSize:11.5}}>{cm2.emoji}</span>
              {c}
            </button>
          );
        })}
      </div>

      {/* Other custom */}
      {isOther&&(
        <div className="dc-other-panel" style={{marginBottom:10}}>
          <label className="dc-field-label" style={{color:"#6366f1"}}>Custom description</label>
          <textarea className="dc-other-ta" placeholder="e.g. Fracture, Erosion…"
            value={otherText} onChange={e=>{setOtherText(e.target.value);onSelect("Other",{otherText:e.target.value,otherColor,severity,surfaces,notes});}}/>
          <div className="dc-palette">
            {OTHER_PALETTE.map(hex=>(
              <div key={hex} className={`dc-pdot${otherColor===hex?" sel":""}`}
                style={{background:hex,borderColor:otherColor===hex?"#0f172a":"transparent"}}
                onClick={()=>{setOtherColor(hex);onSelect("Other",{otherText,otherColor:hex,severity,surfaces,notes});}}/>
            ))}
          </div>
        </div>
      )}

      {activeCondition&&(
        <>
          {/* Severity */}
          <div style={{marginBottom:10}}>
            <div className="dc-field-label">Severity (optional)</div>
            <div className="dc-severity-row">
              {SEVERITY_LEVELS.map(sv=>(
                <button key={sv.key} className={`dc-sev-btn ${sv.cls}${severity===sv.key?" active":""}`}
                  onClick={()=>setSeverity(p=>p===sv.key?"":sv.key)}>
                  {sv.label}
                </button>
              ))}
            </div>
          </div>

          {/* Surfaces */}
          <div style={{marginBottom:10}}>
            <div className="dc-field-label">Surfaces (optional)</div>
            <div className="dc-surface-map">
              {SURFACES.map(s=>(
                <div key={s} className="dc-tooltip-wrap">
                  <button className={`dc-surf-key${surfaces.includes(s)?" on":""}`} onClick={()=>togSurf(s)}>{s}</button>
                  <span className="dc-tooltip-content">{SURF_FULL[s]}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div style={{marginBottom:10}}>
            <div className="dc-field-label">Notes (optional)</div>
            <textarea className="dc-notes-ta" placeholder="Clinical observations…"
              value={notes} onChange={e=>setNotes(e.target.value)}/>
          </div>
        </>
      )}

      {/* Step 2 instruction */}
      <div style={{
        marginTop:8,padding:"10px 14px",borderRadius:9,
        background:activeCondition?(cm?`${cm.a}10`:"#f0fdf4"):"#f8fafc",
        border:`1.5px dashed ${activeCondition&&cm?cm.a:"#cbd5e1"}`,
        fontSize:12,color:activeCondition&&cm?cm.dark:"#94a3b8",fontWeight:500}}>
        {activeCondition?(
          <>
            <span style={{fontWeight:700}}>Step 2 — Click teeth on the chart</span> to mark as{" "}
            <span style={{fontWeight:700}}>{activeCondition}</span>
            {selectedTeeth.length>0&&(
              <span style={{marginLeft:8}}>
                ·{" "}
                <span style={{fontFamily:"'DM Mono',monospace",fontWeight:700,color:cm?.dark}}>
                  {selectedTeeth.sort((a,b)=>a-b).join(", ")}
                </span>
                {" "}selected
                <button onClick={onClearTeeth} style={{marginLeft:6,border:"none",background:"none",
                  color:"#ef4444",cursor:"pointer",fontSize:11,fontWeight:600}}>✕ Clear</button>
              </span>
            )}
          </>
        ):"Select a condition above, then click teeth on the chart"}
      </div>

      {/* Extras state exposed via ref-style callback */}
      <input type="hidden" id="dc-extras"
        value={JSON.stringify({severity,surfaces,notes,otherText,otherColor})}/>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   EDIT MODE OVERLAY (highlight teeth of a condition)
═══════════════════════════════════════════════════════ */
function EditModeBar({condition,rows,onClose}){
  const cm=CMAP[condition]||CMAP["Other"];
  const nums=rows.map(r=>r.tooth_number).sort((a,b)=>a-b);
  return(
    <div style={{
      background:`${cm.a}14`,border:`2px solid ${cm.a}55`,borderRadius:12,
      padding:"10px 16px",marginBottom:12,display:"flex",alignItems:"center",gap:10,flexWrap:"wrap"}}>
      <span style={{
        padding:"3px 12px",borderRadius:20,background:cm.a,color:"#fff",
        fontSize:12,fontWeight:700}}>
        {cm.emoji} {condition}
      </span>
      <span style={{fontSize:12,color:cm.dark,fontWeight:600}}>
        Click a highlighted tooth to change its condition
      </span>
      <span style={{fontSize:11,color:"var(--dc-text3)",fontFamily:"'DM Mono',monospace"}}>
        Teeth: {nums.join(", ")}
      </span>
      <button onClick={onClose} style={{marginLeft:"auto",padding:"4px 12px",borderRadius:7,
        border:"1.5px solid var(--dc-border)",background:"#fff",fontSize:11,fontWeight:600,
        cursor:"pointer",color:"var(--dc-text2)"}}>
        ✕ Exit edit mode
      </button>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   MAIN EXPORT
═══════════════════════════════════════════════════════ */
export default function DentalChart({visitId,disabled=false,onRecordsChange}){
  const[records,setRecords]=useState([]);
  const[chartType,setChartType]=useState("permanent");
  const[saving,setSaving]=useState(false);
  const[deleting,setDeleting]=useState(false);

  // Condition-first selection state
  const[activeCondition,setActiveCondition]=useState(null);
  const[condExtras,setCondExtras]=useState({severity:"",surfaces:[],notes:"",otherText:"",otherColor:OTHER_PALETTE[8]});
  const[pendingTeeth,setPendingTeeth]=useState(new Set());

  // Edit mode: highlight a condition's teeth
  const[editMode,setEditMode]=useState(null); // {condition, rows:[]}
  const[editModalTooth,setEditModalTooth]=useState(null);

  // Add modal (direct add from conditions log)
  const[showAddModal,setShowAddModal]=useState(false);

  useEffect(()=>{injectStyles();if(visitId)load();},[visitId]);

  const load=async()=>{
    try{
      const r=await api.get(`/visits/${visitId}/dental-chart`);
      const data=r.data||[];
      setRecords(data);
      if(onRecordsChange)onRecordsChange(data);
    }catch(e){console.error(e);}
  };

  const getRecord=n=>records.find(r=>r.tooth_number===n)||null;

  // When a condition is selected in the panel
  const handleConditionSelect=(cond,extras)=>{
    setActiveCondition(cond);
    setCondExtras(extras||{severity:"",surfaces:[],notes:"",otherText:"",otherColor:OTHER_PALETTE[8]});
    setPendingTeeth(new Set());
    setEditMode(null);
  };

  // Clicking a tooth on the chart
  const handleToothClick=async n=>{
    if(disabled)return;

    // ── Edit mode: open modal for that tooth ──
    if(editMode){
      const isInGroup=editMode.rows.some(r=>r.tooth_number===n);
      if(isInGroup) setEditModalTooth(n);
      return;
    }

    // ── Condition-first mode ──
    if(!activeCondition)return;

    const existing=getRecord(n);
    setSaving(true);
    try{
      const fd={
        condition:activeCondition,
        severity:condExtras.severity||"",
        surface:(condExtras.surfaces||[]).join(","),
        notes:condExtras.notes||"",
        other_text:activeCondition==="Other"?(condExtras.otherText||""):"",
        custom_color:activeCondition==="Other"?(condExtras.otherColor||""):"",
      };
      if(existing){
        await api.put(`/visits/${visitId}/dental-chart/${existing.id}`,fd);
      } else {
        await api.post(`/visits/${visitId}/dental-chart`,{tooth_number:n,...fd});
      }
      // Optimistic update
      setPendingTeeth(p=>{const s=new Set(p);s.add(n);return s;});
      await load();
    }catch(e){console.error(e);alert("Failed to save.");}
    finally{setSaving(false);}
  };

  // Edit modal save
  const handleEditSave=async fd=>{
    if(!editModalTooth)return;
    setSaving(true);
    const ex=getRecord(editModalTooth);
    try{
      if(ex)await api.put(`/visits/${visitId}/dental-chart/${ex.id}`,fd);
      else  await api.post(`/visits/${visitId}/dental-chart`,{tooth_number:editModalTooth,...fd});
      setEditModalTooth(null);
      await load();
      // Refresh edit mode rows
      setEditMode(null);
    }catch(e){console.error(e);alert("Failed to save.");}
    finally{setSaving(false);}
  };

  // Save from AddConditionModal (multiple teeth at once)
  const handleAddModalSave=async(data)=>{
    setSaving(true);
    try{
      for(const toothNum of data.teeth){
        const fd={
          condition:data.condition,
          severity:data.severity||"",
          surface:data.surface||"",
          notes:data.notes||"",
          other_text:data.condition==="Other"?(data.other_text||""):"",
          custom_color:data.condition==="Other"?(data.custom_color||""):"",
        };
        const existing=getRecord(toothNum);
        if(existing){
          await api.put(`/visits/${visitId}/dental-chart/${existing.id}`,fd);
        } else {
          await api.post(`/visits/${visitId}/dental-chart`,{tooth_number:toothNum,...fd});
        }
      }
      setShowAddModal(false);
      await load();
    }catch(e){console.error(e);alert("Failed to save conditions.");}
    finally{setSaving(false);}
  };

  // Delete from conditions log
  const handleDeleteTooth=async(id,num,label)=>{
    if(!window.confirm(`Remove ${label} from Tooth #${num}?`))return;
    setDeleting(true);
    try{
      await api.delete(`/visits/${visitId}/dental-chart/${id}`);
      const updated=records.filter(r=>r.id!==id);
      setRecords(updated);
      if(onRecordsChange)onRecordsChange(updated);
    }catch(e){console.error(e);alert("Failed to delete.");}
    finally{setDeleting(false);}
  };

  // Enter edit group mode from log
  const handleEditGroup=(condition,rows)=>{
    setActiveCondition(null);
    setPendingTeeth(new Set());
    setEditMode({condition,rows});
  };

  const affected=records.filter(r=>{
    const n=r.tooth_number;
    return chartType==="permanent"?(n>=11&&n<=48):(n>=51&&n<=85);
  });
  const condCounts={};
  affected.forEach(r=>{condCounts[r.condition]=(condCounts[r.condition]||0)+1;});
  const topConds=Object.entries(condCounts).sort((a,b)=>b[1]-a[1]).slice(0,3);

  // Highlighted teeth: pending (just clicked) + edit mode group
  const highlightSet=new Set([
    ...pendingTeeth,
    ...(editMode?editMode.rows.map(r=>r.tooth_number):[]),
  ]);

  return(
    <div className="dc-root">

      {/* ── HEADER ── */}
      <div className="dc-header">
        <div className="dc-header-title">
          <div className="dc-header-title-icon">🦷</div>
          Dental Chart
        </div>
        <div className="dc-tab-group">
          {[{key:"permanent",label:"Permanent (FDI)"},{key:"deciduous",label:"Deciduous"}].map(o=>(
            <button key={o.key} className={`dc-tab${chartType===o.key?" active":""}`}
              onClick={()=>{setChartType(o.key);setActiveCondition(null);setPendingTeeth(new Set());setEditMode(null);}}>
              {o.label}
            </button>
          ))}
        </div>
        <div className="dc-stats-row">
          <div className="dc-stat-chip"
            style={{background:affected.length>0?"#fef2f2":"var(--dc-surface2)",
              borderColor:affected.length>0?"#fecaca":"var(--dc-border)",
              color:affected.length>0?"#991b1b":"var(--dc-text3)"}}>
            <span className="dc-stat-dot" style={{background:affected.length>0?"#ef4444":"#cbd5e1"}}/>
            {affected.length} marked
          </div>
          {topConds.map(([c,n])=>{
            const cm=CMAP[c]||CMAP["Other"];
            return(
              <div key={c} className="dc-stat-chip"
                style={{background:`${cm.a}14`,borderColor:`${cm.a}44`,color:cm.dark}}>
                <span className="dc-stat-dot" style={{background:cm.a}}/>
                {cm.emoji} {c}: {n}
              </div>
            );
          })}
          {saving&&<div className="dc-stat-chip" style={{color:"#3b82f6",borderColor:"#bfdbfe",background:"#eff6ff"}}>⏳ Saving…</div>}
        </div>
      </div>

      {/* ── CONDITION SELECTOR (Step 1) ── */}
      {!disabled&&(
        <ConditionSelectorPanel
          activeCondition={activeCondition}
          onSelect={handleConditionSelect}
          onClear={()=>{setActiveCondition(null);setPendingTeeth(new Set());}}
          selectedTeeth={[...pendingTeeth]}
          onClearTeeth={()=>setPendingTeeth(new Set())}
        />
      )}

      {/* ── EDIT MODE BAR ── */}
      {editMode&&(
        <EditModeBar
          condition={editMode.condition}
          rows={editMode.rows}
          onClose={()=>{setEditMode(null);setEditModalTooth(null);}}/>
      )}

      {/* ── CHART ── */}
      <div className="dc-chart-panel">
        <DentalDiagram records={records} chartType={chartType}
          onToothClick={handleToothClick} disabled={disabled}
          selectedTooth={highlightSet.size>0?[...highlightSet][highlightSet.size-1]:null}/>

        {/* Legend */}
        <div className="dc-legend-bar">
          <span style={{fontSize:10,fontWeight:700,color:"var(--dc-text3)",textTransform:"uppercase",
            letterSpacing:".8px",marginRight:4}}>Legend:</span>
          <div className="dc-legend-item">
            <span className="dc-legend-dot" style={{background:"#cdd2db",border:"1px solid #9aa3b2"}}/>
            Healthy
          </div>
          {CONDITIONS.map(c=>{
            const cm=CMAP[c];
            return(
              <div key={c} className="dc-legend-item">
                <span className="dc-legend-dot" style={{background:cm.a}}/>
                {cm.emoji} {c}
              </div>
            );
          })}
        </div>
      </div>

      {/* ── GROUPED CONDITIONS LOG ── */}
      <GroupedConditionsLog
        records={records}
        chartType={chartType}
        disabled={disabled}
        onEditGroup={handleEditGroup}
        onDeleteTooth={handleDeleteTooth}
        deleting={deleting}
        onAdd={()=>setShowAddModal(true)}/>

      {/* ── ADD CONDITION MODAL ── */}
      {showAddModal&&!disabled&&(
        <AddConditionModal
          chartType={chartType}
          onSave={handleAddModalSave}
          onClose={()=>setShowAddModal(false)}
          saving={saving}/>
      )}

      {/* ── EDIT MODAL (shown when tooth clicked in edit mode) ── */}
      {editModalTooth&&(
        <ToothModal
          tooth={editModalTooth}
          existing={getRecord(editModalTooth)}
          disabled={false}
          onSave={handleEditSave}
          onDelete={async()=>{
            const ex=getRecord(editModalTooth);
            if(!ex)return;
            if(!window.confirm(`Delete condition from Tooth #${editModalTooth}?`))return;
            setDeleting(true);
            try{
              await api.delete(`/visits/${visitId}/dental-chart/${ex.id}`);
              const updated=records.filter(r=>r.id!==ex.id);
              setRecords(updated);
              if(onRecordsChange)onRecordsChange(updated);
              setEditModalTooth(null);
              setEditMode(null);
            }catch(e){console.error(e);}
            finally{setDeleting(false);}
          }}
          onClose={()=>setEditModalTooth(null)}
          saving={saving}
          deleting={deleting}/>
      )}
    </div>
  );
}