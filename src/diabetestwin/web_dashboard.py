# ruff: noqa: E501

DASHBOARD_HTML = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#f6f8fb" />
  <title>DiabetesTwin-AI · Predictive Digital Twin</title>
  <style>
    :root {
      --bg: #f6f8fb;
      --surface: #ffffff;
      --surface-soft: #f9fbfc;
      --ink: #14263d;
      --muted: #65758b;
      --line: #dfe6ec;
      --teal: #0b6976;
      --teal-soft: #e8f4f3;
      --blue: #0877b9;
      --orange: #c65318;
      --red: #b92b37;
      --green: #2f6b4f;
      --amber: #946200;
      --shadow: 0 12px 34px rgba(28, 48, 74, .08);
      --radius-lg: 22px;
      --radius-md: 15px;
      --radius-sm: 10px;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      background: radial-gradient(circle at 12% 5%, rgba(11, 105, 118, .08), transparent 28%),
        linear-gradient(180deg, #fbfcfd 0%, var(--bg) 42%);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      -webkit-font-smoothing: antialiased;
    }
    button, input, select { font: inherit; }
    button { cursor: pointer; }
    a { color: inherit; }
    .shell { min-height: 100vh; }
    .topbar {
      position: sticky; top: 0; z-index: 20; display: flex; align-items: center; justify-content: space-between;
      gap: 22px; height: 72px; padding: 0 max(24px, calc((100vw - 1480px) / 2));
      background: rgba(255, 255, 255, .9); backdrop-filter: blur(18px);
      border-bottom: 1px solid rgba(219, 227, 233, .88);
    }
    .brand { display: flex; align-items: center; gap: 12px; min-width: 260px; }
    .brand-mark {
      width: 38px; height: 38px; border-radius: 12px; display: grid; place-items: center; color: white;
      font-weight: 800; background: linear-gradient(145deg, #075a69, #0f8190);
      box-shadow: 0 8px 20px rgba(11, 105, 118, .22);
    }
    .brand strong { display: block; font-size: 15px; letter-spacing: -.01em; }
    .brand small { display: block; color: var(--muted); font-size: 11px; margin-top: 1px; }
    .nav { display: flex; align-items: center; gap: 5px; }
    .nav a { text-decoration: none; color: #52647a; font-size: 13px; font-weight: 650; padding: 9px 12px; border-radius: 9px; }
    .nav a:hover { color: var(--teal); background: var(--teal-soft); }
    .top-actions { display: flex; align-items: center; gap: 10px; min-width: 250px; justify-content: flex-end; }
    .badge {
      display: inline-flex; align-items: center; gap: 7px; padding: 7px 10px; border-radius: 999px;
      background: #fff8e7; color: #7b5700; border: 1px solid #f2dfae; font-size: 11px; font-weight: 700;
      white-space: nowrap;
    }
    .dot { width: 7px; height: 7px; border-radius: 50%; background: #c58b00; }
    .docs-link { text-decoration: none; border: 1px solid var(--line); border-radius: 10px; padding: 8px 11px; font-size: 12px; font-weight: 700; background: var(--surface); }
    main { max-width: 1480px; margin: 0 auto; padding: 34px 24px 64px; }
    .hero { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(340px, .65fr); gap: 22px; align-items: stretch; margin-bottom: 22px; }
    .hero-main, .hero-aside, .panel, .kpi { background: rgba(255, 255, 255, .96); border: 1px solid var(--line); box-shadow: var(--shadow); }
    .hero-main { border-radius: var(--radius-lg); padding: 30px 32px; position: relative; overflow: hidden; }
    .hero-main::after { content: ""; position: absolute; width: 300px; height: 300px; right: -95px; top: -130px; border-radius: 50%; background: radial-gradient(circle, rgba(11,105,118,.13), rgba(11,105,118,0)); pointer-events: none; }
    .eyebrow { color: var(--teal); font-size: 11px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; margin-bottom: 9px; }
    h1 { margin: 0; font-size: clamp(30px, 3.2vw, 46px); line-height: 1.05; letter-spacing: -.045em; }
    .hero-copy { max-width: 790px; color: var(--muted); font-size: 15px; line-height: 1.65; margin: 15px 0 21px; }
    .hero-tags { display: flex; flex-wrap: wrap; gap: 8px; }
    .hero-tag { padding: 7px 10px; border-radius: 999px; background: #f2f6f8; border: 1px solid #e4ebef; color: #496176; font-size: 11px; font-weight: 700; }
    .hero-aside { border-radius: var(--radius-lg); padding: 22px; }
    .aside-title { font-size: 12px; color: var(--muted); font-weight: 700; margin-bottom: 15px; }
    .status-row { display: flex; align-items: center; justify-content: space-between; padding: 11px 0; border-bottom: 1px solid #edf1f4; }
    .status-row:last-child { border-bottom: 0; }
    .status-key { font-size: 12px; color: var(--muted); }
    .status-value { font-size: 12px; font-weight: 800; display: flex; align-items: center; gap: 7px; }
    .status-ok { color: var(--green); }
    .notice { display: flex; gap: 12px; align-items: flex-start; padding: 13px 15px; margin: 0 0 22px; border-radius: 13px; background: #fff9eb; border: 1px solid #f0dfb5; color: #664b0a; font-size: 12px; line-height: 1.5; }
    .notice strong { color: #513a00; }
    .section-head { display: flex; align-items: end; justify-content: space-between; gap: 16px; margin: 30px 0 12px; }
    .section-head h2 { margin: 0; font-size: 20px; letter-spacing: -.02em; }
    .section-head p { margin: 5px 0 0; color: var(--muted); font-size: 12px; }
    .section-chip { color: var(--teal); font-size: 11px; font-weight: 800; background: var(--teal-soft); padding: 7px 10px; border-radius: 999px; }
    .kpi-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }
    .kpi { border-radius: var(--radius-md); padding: 16px 17px; min-height: 118px; box-shadow: 0 7px 22px rgba(24, 49, 73, .05); }
    .kpi-label { display: flex; align-items: center; justify-content: space-between; gap: 7px; color: var(--muted); font-size: 11px; font-weight: 750; }
    .kpi-value { margin-top: 13px; font-size: 26px; font-weight: 780; letter-spacing: -.035em; }
    .kpi-sub { margin-top: 6px; color: var(--muted); font-size: 10.5px; }
    .main-grid { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(330px, .72fr); gap: 14px; }
    .panel { border-radius: var(--radius-lg); overflow: hidden; box-shadow: 0 8px 26px rgba(28, 48, 74, .055); }
    .panel-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 17px 19px; border-bottom: 1px solid #edf1f4; }
    .panel-title { font-size: 13px; font-weight: 800; }
    .panel-sub { color: var(--muted); font-size: 10.5px; margin-top: 3px; }
    .legend { display: flex; align-items: center; gap: 13px; color: var(--muted); font-size: 10px; font-weight: 700; }
    .legend-item { display: flex; align-items: center; gap: 6px; }
    .legend-line { width: 21px; height: 2px; background: var(--blue); border-radius: 2px; }
    .legend-line.orange { background: var(--orange); border-top: 1px dashed var(--orange); }
    .chart-wrap { padding: 13px 13px 8px; min-height: 390px; }
    .chart-wrap svg { width: 100%; height: 365px; overflow: visible; }
    .chart-note { padding: 0 19px 16px; color: var(--muted); font-size: 10px; line-height: 1.45; }
    .controls { padding: 17px; }
    .control-group { margin-bottom: 18px; }
    .control-label { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 7px; color: #40556a; font-size: 11px; font-weight: 750; }
    .control-value { color: var(--teal); font-weight: 800; }
    input[type="range"] { width: 100%; accent-color: var(--teal); }
    select { width: 100%; padding: 10px 11px; border-radius: 10px; border: 1px solid #d9e2e8; color: var(--ink); background: white; outline: none; }
    select:focus { border-color: #4f97a0; box-shadow: 0 0 0 3px rgba(11,105,118,.1); }
    .btn-primary, .btn-secondary { border: 0; border-radius: 11px; padding: 11px 14px; font-weight: 800; font-size: 12px; transition: transform .15s ease, box-shadow .15s ease; }
    .btn-primary { width: 100%; color: white; background: linear-gradient(135deg, #075d6b, #0b7c8a); box-shadow: 0 9px 20px rgba(11,105,118,.2); }
    .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 12px 22px rgba(11,105,118,.25); }
    .btn-secondary { color: var(--teal); background: var(--teal-soft); border: 1px solid #cce2e2; }
    .btn-secondary:hover { background: #dcefee; }
    .impact-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 9px; margin-top: 15px; }
    .impact { background: #f7fafb; border: 1px solid #e4ebef; border-radius: 11px; padding: 11px; }
    .impact span { color: var(--muted); font-size: 9.5px; display: block; }
    .impact strong { display: block; margin-top: 4px; font-size: 15px; }
    .real-grid { display: grid; grid-template-columns: 280px minmax(0, 1fr); gap: 14px; }
    .patient-card { padding: 18px; }
    .patient-avatar { width: 48px; height: 48px; display: grid; place-items: center; border-radius: 15px; background: linear-gradient(145deg, #e7f3f3, #d7eeee); color: var(--teal); font-weight: 850; margin-bottom: 12px; }
    .patient-title { font-size: 16px; font-weight: 800; }
    .patient-meta { color: var(--muted); font-size: 10.5px; margin-top: 3px; }
    .patient-info { margin-top: 15px; }
    .patient-info-row { display: flex; justify-content: space-between; gap: 10px; padding: 9px 0; border-bottom: 1px solid #edf1f4; font-size: 11px; }
    .patient-info-row span:first-child { color: var(--muted); }
    .patient-info-row strong { text-align: right; }
    .model-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .model-card { padding: 17px; }
    .model-label { color: var(--muted); font-size: 10px; font-weight: 700; }
    .model-value { margin-top: 7px; font-size: 24px; font-weight: 800; letter-spacing: -.03em; }
    .model-foot { margin-top: 5px; color: var(--muted); font-size: 9.5px; line-height: 1.4; }
    .baseline-callout { margin-top: 12px; padding: 13px 15px; border-radius: 12px; background: #f7fafb; border: 1px solid var(--line); color: #445b70; font-size: 11px; line-height: 1.5; }
    .interop-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    .interop-card { padding: 18px; min-height: 176px; display: flex; flex-direction: column; }
    .interop-icon { width: 36px; height: 36px; border-radius: 11px; display: grid; place-items: center; background: #eef4f7; margin-bottom: 14px; }
    .interop-card h3 { font-size: 13px; margin: 0 0 7px; }
    .interop-card p { color: var(--muted); font-size: 10.5px; line-height: 1.5; margin: 0 0 14px; flex: 1; }
    code { background: #f1f5f7; padding: 2px 5px; border-radius: 5px; font-size: 10px; }
    .footer { margin-top: 34px; padding-top: 22px; border-top: 1px solid var(--line); display: flex; justify-content: space-between; gap: 18px; color: var(--muted); font-size: 10px; line-height: 1.55; }
    .footer strong { color: #3d5267; }
    .loading { opacity: .55; pointer-events: none; }
    .toast { position: fixed; right: 22px; bottom: 22px; z-index: 50; max-width: 340px; padding: 12px 14px; border-radius: 12px; color: white; background: #21374d; box-shadow: 0 12px 34px rgba(20, 38, 61, .25); font-size: 11px; transform: translateY(20px); opacity: 0; pointer-events: none; transition: .22s ease; }
    .toast.show { transform: translateY(0); opacity: 1; }
    @media (max-width: 1120px) { .nav { display: none; } .hero { grid-template-columns: 1fr; } .hero-aside { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0 22px; } .kpi-grid { grid-template-columns: repeat(3, 1fr); } .main-grid { grid-template-columns: 1fr; } .real-grid { grid-template-columns: 1fr; } .model-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 720px) { .topbar { height: 64px; padding: 0 14px; } .brand { min-width: auto; } .brand small, .docs-link { display: none; } .top-actions { min-width: auto; } main { padding: 22px 13px 50px; } .hero-main { padding: 22px 20px; } .hero-aside { display: block; } .kpi-grid { grid-template-columns: repeat(2, 1fr); } .kpi:last-child { grid-column: span 2; } .model-grid, .interop-grid { grid-template-columns: 1fr; } .chart-wrap svg { height: 300px; } .chart-wrap { min-height: 325px; } .legend { display: none; } .section-head { align-items: flex-start; } .section-chip { display: none; } .footer { flex-direction: column; } .impact-grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="shell">
    <header class="topbar">
      <div class="brand"><div class="brand-mark">DT</div><div><strong>DiabetesTwin-AI</strong><small>Predictive digital twin · Research prototype</small></div></div>
      <nav class="nav" aria-label="Primary navigation"><a href="#overview">Overview</a><a href="#simulation">Simulation</a><a href="#real-data">Real CGM</a><a href="#model">Model</a><a href="#interop">Interoperability</a></nav>
      <div class="top-actions"><span class="badge"><span class="dot"></span>Non-clinical demo</span><a class="docs-link" href="/docs">API docs</a></div>
    </header>
    <main>
      <section class="hero" id="overview">
        <div class="hero-main"><div class="eyebrow">Personalized diabetes monitoring twin</div><h1>One patient. One trajectory.<br />A safer way to explore what-if scenarios.</h1><p class="hero-copy">Interactive digital twin for glucose trajectory simulation, lifestyle scenario exploration, real CGMacros visualization and +30 minute forecasting research.</p><div class="hero-tags"><span class="hero-tag">24 h virtual patient</span><span class="hero-tag">5 min cadence</span><span class="hero-tag">CGMacros real data</span><span class="hero-tag">FHIR R5 export</span></div></div>
        <aside class="hero-aside"><div class="aside-title">Research environment</div><div class="status-row"><span class="status-key">API status</span><span class="status-value status-ok">● Online</span></div><div class="status-row"><span class="status-key">Simulation engine</span><span class="status-value">Deterministic seed 42</span></div><div class="status-row"><span class="status-key">Real dataset</span><span class="status-value">CGMacros v1.0.0</span></div><div class="status-row"><span class="status-key">Forecast horizon</span><span class="status-value">+30 minutes</span></div><div class="status-row"><span class="status-key">Clinical status</span><span class="status-value">Not validated</span></div></aside>
      </section>
      <div class="notice"><span aria-hidden="true">⚠</span><div><strong>Research and education only.</strong> Simulations and predictions are not medical advice, diagnosis, medication guidance or insulin-dosing recommendations. CGMacros dates are privacy-shifted.</div></div>
      <div class="section-head"><div><h2>Virtual patient overview</h2><p>Current simulated day compared with the reference lifestyle.</p></div><span class="section-chip">Target display band 70–180 mg/dL</span></div>
      <section class="kpi-grid" aria-label="Virtual patient metrics">
        <article class="kpi"><div class="kpi-label">Mean glucose <span>mg/dL</span></div><div class="kpi-value" id="meanGlucose">—</div><div class="kpi-sub" id="meanDelta">Loading simulation…</div></article>
        <article class="kpi"><div class="kpi-label">Time in range <span>70–180</span></div><div class="kpi-value" id="tir">—</div><div class="kpi-sub" id="tirDelta">Loading simulation…</div></article>
        <article class="kpi"><div class="kpi-label">Below range <span>&lt;70</span></div><div class="kpi-value" id="tbr">—</div><div class="kpi-sub">Share of simulated samples</div></article>
        <article class="kpi"><div class="kpi-label">Above range <span>&gt;180</span></div><div class="kpi-value" id="tar">—</div><div class="kpi-sub">Share of simulated samples</div></article>
        <article class="kpi"><div class="kpi-label">Variability <span>CV</span></div><div class="kpi-value" id="cv">—</div><div class="kpi-sub">Coefficient of variation</div></article>
      </section>
      <div class="section-head" id="simulation"><div><h2>Digital twin simulation</h2><p>Adjust lifestyle inputs and compare the new trajectory with the reference scenario.</p></div></div>
      <section class="main-grid">
        <article class="panel"><div class="panel-head"><div><div class="panel-title">Glucose trajectory · 24 hours</div><div class="panel-sub">Simulated personalized twin versus reference lifestyle</div></div><div class="legend"><span class="legend-item"><span class="legend-line"></span>Current</span><span class="legend-item"><span class="legend-line orange"></span>Reference</span></div></div><div class="chart-wrap" id="virtualChart" aria-label="Virtual glucose chart"></div><div class="chart-note">The shaded band is a standardized display range used for CGM reporting. It is not an individualized clinical target.</div></article>
        <aside class="panel"><div class="panel-head"><div><div class="panel-title">Scenario controls</div><div class="panel-sub">No medication or insulin controls are provided</div></div></div><div class="controls" id="controls">
          <div class="control-group"><div class="control-label"><span>Phenotype</span></div><select id="phenotype"><option value="balanced">Balanced</option><option value="insulin_resistant">Insulin resistant</option><option value="active">Active</option></select></div>
          <div class="control-group"><div class="control-label"><span>Breakfast carbs</span><span class="control-value" id="breakfastValue">45 g</span></div><input id="breakfast" type="range" min="0" max="120" step="5" value="45" /></div>
          <div class="control-group"><div class="control-label"><span>Lunch carbs</span><span class="control-value" id="lunchValue">65 g</span></div><input id="lunch" type="range" min="0" max="150" step="5" value="65" /></div>
          <div class="control-group"><div class="control-label"><span>Dinner carbs</span><span class="control-value" id="dinnerValue">70 g</span></div><input id="dinner" type="range" min="0" max="150" step="5" value="70" /></div>
          <div class="control-group"><div class="control-label"><span>Evening activity</span><span class="control-value" id="exerciseValue">35 min</span></div><input id="exercise" type="range" min="0" max="90" step="5" value="35" /></div>
          <div class="control-group"><div class="control-label"><span>Stress level</span><span class="control-value" id="stressValue">25%</span></div><input id="stress" type="range" min="0" max="100" step="5" value="25" /></div>
          <div class="control-group"><div class="control-label"><span>Sleep duration</span><span class="control-value" id="sleepValue">7.5 h</span></div><input id="sleep" type="range" min="4" max="10" step="0.25" value="7.5" /></div>
          <button class="btn-primary" id="simulateButton">Run what-if simulation</button><div class="impact-grid"><div class="impact"><span>Peak change</span><strong id="peakImpact">—</strong></div><div class="impact"><span>TIR change</span><strong id="tirImpact">—</strong></div><div class="impact"><span>Mean change</span><strong id="meanImpact">—</strong></div></div>
        </div></aside>
      </section>
      <div class="section-head" id="real-data"><div><h2>Real CGM explorer</h2><p>Small deployment subset derived from the official PhysioNet CGMacros release.</p></div><span class="section-chip">CC BY-NC-SA 4.0</span></div>
      <section class="real-grid">
        <article class="panel patient-card"><div class="patient-avatar" id="patientAvatar">001</div><div class="patient-title">CGMacros participant <span id="participantTitle">001</span></div><div class="patient-meta">Pseudonymous released participant ID</div><div class="control-group" style="margin-top:16px"><select id="participantSelect"><option value="001">Participant 001</option><option value="008">Participant 008</option><option value="003">Participant 003</option></select></div><div class="patient-info"><div class="patient-info-row"><span>Dataset group</span><strong id="realDiagnosis">—</strong></div><div class="patient-info-row"><span>HbA1c</span><strong id="realHba1c">—</strong></div><div class="patient-info-row"><span>Observed TIR</span><strong id="realTir">—</strong></div><div class="patient-info-row"><span>Displayed points</span><strong id="realPoints">—</strong></div></div></article>
        <article class="panel"><div class="panel-head"><div><div class="panel-title">Observed CGM trajectory</div><div class="panel-sub">Privacy-shifted timeline · deployment sample</div></div><div class="legend"><span class="legend-item"><span class="legend-line"></span>Observed CGM</span></div></div><div class="chart-wrap" id="realChart" aria-label="Observed real CGM chart"></div><div class="chart-note">The full CGMacros archive is not committed to the repository. This deployment uses a small licensed subset for demonstration only.</div></article>
      </section>
      <div class="section-head" id="model"><div><h2>Forecasting benchmark</h2><p>Verified full-dataset grouped holdout on unseen participants.</p></div><span class="section-chip">+30 min horizon</span></div>
      <section class="model-grid"><article class="panel model-card"><div class="model-label">Random Forest · MAE</div><div class="model-value">13.11</div><div class="model-foot">mg/dL · 9 unseen participants in grouped test set</div></article><article class="panel model-card"><div class="model-label">Random Forest · RMSE</div><div class="model-value">18.94</div><div class="model-foot">mg/dL · grouped participant holdout</div></article><article class="panel model-card"><div class="model-label">Persistence · MAE</div><div class="model-value">13.39</div><div class="model-foot">mg/dL · current glucose used as +30 min baseline</div></article><article class="panel model-card"><div class="model-label">Usable forecast rows</div><div class="model-value">621k</div><div class="model-foot">621,069 rows · 45 / 45 participants</div></article></section>
      <div class="baseline-callout"><strong>Interpretation:</strong> the Random Forest improves MAE by only about 0.28 mg/dL over persistence on the grouped holdout. The result is intentionally shown without overclaiming model performance; this is research validation, not clinical validation.</div>
      <div class="section-head" id="interop"><div><h2>Interoperability & developer tools</h2><p>Use the same digital twin engine from the web interface or via API.</p></div></div>
      <section class="interop-grid"><article class="panel interop-card"><div class="interop-icon">FHIR</div><h3>FHIR R5 observations</h3><p>Generate a demonstration Bundle of synthetic glucose observations from the current virtual-patient scenario.</p><button class="btn-secondary" id="fhirButton">Download FHIR JSON</button></article><article class="panel interop-card"><div class="interop-icon">API</div><h3>FastAPI endpoint</h3><p>Programmatic simulation is available at <code>POST /simulate</code> with typed Pydantic request and response models.</p><a class="btn-secondary" href="/docs" style="text-decoration:none;text-align:center">Open Swagger docs</a></article><article class="panel interop-card"><div class="interop-icon">CGM</div><h3>Real-data demo API</h3><p>Retrieve the bundled CGMacros participant trajectory through <code>GET /demo/cgmacros</code>.</p><a class="btn-secondary" href="/demo/cgmacros?participant_id=001" style="text-decoration:none;text-align:center">View JSON response</a></article></section>
      <footer class="footer"><div><strong>DiabetesTwin-AI</strong><br />Predictive digital twin for research and education · source code licensed MIT.</div><div><strong>Demo data</strong><br />Derived from PhysioNet CGMacros v1.0.0 · DOI 10.13026/3z8q-x658 · CC BY-NC-SA 4.0.</div></footer>
    </main>
  </div>
  <div class="toast" id="toast"></div>
  <script>
    const presets = { balanced: {baseline_glucose:112, carb_sensitivity:.72, activity_sensitivity:18, stress_sensitivity:16, circadian_amplitude:7}, insulin_resistant: {baseline_glucose:138, carb_sensitivity:1.05, activity_sensitivity:14, stress_sensitivity:22, circadian_amplitude:10}, active: {baseline_glucose:102, carb_sensitivity:.58, activity_sensitivity:24, stress_sensitivity:13, circadian_amplitude:6} };
    const refScenario = {breakfast:45, lunch:65, dinner:70, exercise:35, stress:.25, sleep:7.5}; let referenceResult = null; let currentResult = null;
    const $ = (id) => document.getElementById(id); const fmt = (n, digits=0) => Number(n).toFixed(digits); const pct = (n) => `${fmt(n,1)}%`; const signed = (n, digits=1, suffix='') => `${n >= 0 ? '+' : ''}${fmt(n,digits)}${suffix}`;
    function showToast(message) { const el = $('toast'); el.textContent = message; el.classList.add('show'); window.clearTimeout(showToast.timer); showToast.timer = window.setTimeout(() => el.classList.remove('show'), 2800); }
    function scenarioFromUI() { return { breakfast: Number($('breakfast').value), lunch: Number($('lunch').value), dinner: Number($('dinner').value), exercise: Number($('exercise').value), stress: Number($('stress').value) / 100, sleep: Number($('sleep').value) }; }
    function payload(scenario, phenotypeName = $('phenotype').value) { const p = presets[phenotypeName]; return { patient: {name:'Twin-01', age:45, phenotype:phenotypeName, ...p}, scenario: { meals: [{hour:8, carbs_g:scenario.breakfast, label:'Breakfast'},{hour:13, carbs_g:scenario.lunch, label:'Lunch'},{hour:19.5, carbs_g:scenario.dinner, label:'Dinner'}], exercise: scenario.exercise > 0 ? [{hour:18, duration_min:scenario.exercise, intensity:.55, label:'Activity'}] : [], stress: scenario.stress, sleep_hours:scenario.sleep, sleep_quality:.8 }, seed:42, step_minutes:5 }; }
    async function simulate(body) { const response = await fetch('/simulate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)}); if (!response.ok) throw new Error(`Simulation failed (${response.status})`); return response.json(); }
    function chartSvg(seriesA, seriesB=null, options={}) { if (!seriesA || !seriesA.length) return '<div style="padding:40px;color:#65758b">No data available.</div>'; const W=1000, H=350, L=52, R=18, T=18, B=40; const values = seriesA.map(d=>d.y).concat(seriesB ? seriesB.map(d=>d.y) : []); const yMin = Math.min(50, Math.floor((Math.min(...values)-15)/10)*10); const yMax = Math.max(220, Math.ceil((Math.max(...values)+18)/10)*10); const xMin = Math.min(...seriesA.map(d=>d.x)), xMax = Math.max(...seriesA.map(d=>d.x)); const x = v => L + (v-xMin)/(xMax-xMin || 1)*(W-L-R); const y = v => T + (yMax-v)/(yMax-yMin)*(H-T-B); const path = s => s.map((d,i)=>`${i?'L':'M'}${x(d.x).toFixed(1)},${y(d.y).toFixed(1)}`).join(' '); const ticks = [70,120,180,250].filter(v=>v>=yMin && v<=yMax); let html = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Glucose time-series chart">`; html += `<rect x="${L}" y="${y(180)}" width="${W-L-R}" height="${y(70)-y(180)}" fill="#e7f3ed" rx="4" />`; ticks.forEach(v=>{ html += `<line x1="${L}" x2="${W-R}" y1="${y(v)}" y2="${y(v)}" stroke="#e6ebef" stroke-width="1"/><text x="${L-9}" y="${y(v)+4}" text-anchor="end" font-size="10" fill="#748499">${v}</text>`; }); const xTicks = options.timeMode ? 5 : 7; for (let i=0;i<xTicks;i++) { const ratio=i/(xTicks-1); const xv=xMin+(xMax-xMin)*ratio; const xp=x(xv); const label=options.timeMode ? formatClockFromIndex(ratio, options.startLabel, options.endLabel) : `${Math.round(xv)}h`; html += `<line x1="${xp}" x2="${xp}" y1="${H-B}" y2="${H-B+5}" stroke="#aebbc6"/><text x="${xp}" y="${H-14}" text-anchor="middle" font-size="10" fill="#748499">${label}</text>`; } if (!options.timeMode) { [8,13,19.5].forEach((hour,idx)=>{ const xp=x(hour); html += `<line x1="${xp}" x2="${xp}" y1="${T}" y2="${H-B}" stroke="#b8c4cd" stroke-dasharray="3 5" opacity=".7"/><text x="${xp+4}" y="${T+12}" font-size="9" fill="#748499">${['Breakfast','Lunch','Dinner'][idx]}</text>`; }); const xp=x(18); html += `<line x1="${xp}" x2="${xp}" y1="${T}" y2="${H-B}" stroke="#0b6976" stroke-dasharray="6 5" opacity=".45"/>`; } if (seriesB) html += `<path d="${path(seriesB)}" fill="none" stroke="#c65318" stroke-width="2.2" stroke-dasharray="6 6" stroke-linejoin="round" stroke-linecap="round" opacity=".9"/>`; html += `<path d="${path(seriesA)}" fill="none" stroke="#0877b9" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>`; html += `<text x="${L}" y="12" font-size="9" fill="#748499">mg/dL</text></svg>`; return html; }
    function formatClockFromIndex(ratio, startLabel, endLabel) { if (!startLabel || !endLabel) return `${Math.round(ratio*48)}h`; const start = new Date(startLabel), end = new Date(endLabel); const t = new Date(start.getTime() + ratio*(end-start)); return t.toLocaleString([], {month:'short', day:'numeric', hour:'2-digit'}); }
    function updateMetrics() { if (!currentResult || !referenceResult) return; const m=currentResult.metrics, r=referenceResult.metrics; $('meanGlucose').textContent=`${fmt(m.mean_glucose)} mg/dL`; $('tir').textContent=pct(m.time_in_range_pct); $('tbr').textContent=pct(m.time_below_range_pct); $('tar').textContent=pct(m.time_above_range_pct); $('cv').textContent=pct(m.coefficient_of_variation_pct); const dMean=m.mean_glucose-r.mean_glucose, dTir=m.time_in_range_pct-r.time_in_range_pct; $('meanDelta').textContent=`${signed(dMean,1,' mg/dL')} vs reference`; $('tirDelta').textContent=`${signed(dTir,1,' pp')} vs reference`; $('peakImpact').textContent=signed(m.max_glucose-r.max_glucose,1,' mg/dL'); $('tirImpact').textContent=signed(dTir,1,' pp'); $('meanImpact').textContent=signed(dMean,1,' mg/dL'); }
    function updateVirtualChart() { if (!currentResult || !referenceResult) return; const a=currentResult.points.map(p=>({x:p.hour,y:p.glucose_mg_dl})); const b=referenceResult.points.map(p=>({x:p.hour,y:p.glucose_mg_dl})); $('virtualChart').innerHTML=chartSvg(a,b); }
    async function runSimulation(initial=false) { const controls=$('controls'); controls.classList.add('loading'); try { const phenotype=$('phenotype').value; referenceResult=await simulate(payload(refScenario,phenotype)); currentResult=await simulate(payload(scenarioFromUI(),phenotype)); updateMetrics(); updateVirtualChart(); if(!initial) showToast('Scenario updated successfully.'); } catch (err) { showToast(err.message); } finally { controls.classList.remove('loading'); } }
    async function loadRealData(participantId) { $('realChart').innerHTML='<div style="padding:40px;color:#65758b">Loading CGMacros sample…</div>'; try { const response=await fetch(`/demo/cgmacros?participant_id=${encodeURIComponent(participantId)}`); if(!response.ok) throw new Error('Real-data demo unavailable on this deployment.'); const data=await response.json(); $('patientAvatar').textContent=data.participant_id; $('participantTitle').textContent=data.participant_id; $('realDiagnosis').textContent=data.diagnosis_label; $('realHba1c').textContent=data.hba1c == null ? 'n/a' : `${Number(data.hba1c).toFixed(1)}%`; $('realTir').textContent=`${Number(data.metrics.time_in_range_pct).toFixed(1)}%`; $('realPoints').textContent=data.points.length.toLocaleString(); const series=data.points.map((p,i)=>({x:i,y:p.glucose_mg_dl})); $('realChart').innerHTML=chartSvg(series,null,{timeMode:true,startLabel:data.start,endLabel:data.end}); } catch(err) { $('realChart').innerHTML=`<div style="padding:40px;color:#b92b37">${err.message}</div>`; } }
    async function downloadFhir() { try { const response=await fetch('/fhir/observations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload(scenarioFromUI()))}); if(!response.ok) throw new Error('FHIR export failed.'); const data=await response.json(); const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/fhir+json'}); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download='diabetestwin_fhir_bundle.json'; a.click(); URL.revokeObjectURL(url); showToast('FHIR Bundle downloaded.'); } catch(err) { showToast(err.message); } }
    function bindRange(id, out, formatter) { const input=$(id), target=$(out); const sync=()=>target.textContent=formatter(Number(input.value)); input.addEventListener('input',sync); sync(); }
    bindRange('breakfast','breakfastValue',v=>`${v} g`); bindRange('lunch','lunchValue',v=>`${v} g`); bindRange('dinner','dinnerValue',v=>`${v} g`); bindRange('exercise','exerciseValue',v=>`${v} min`); bindRange('stress','stressValue',v=>`${v}%`); bindRange('sleep','sleepValue',v=>`${v.toFixed(2).replace(/0+$/,'').replace(/\.$/,'')} h`);
    $('simulateButton').addEventListener('click',()=>runSimulation(false)); $('phenotype').addEventListener('change',()=>runSimulation(false)); $('participantSelect').addEventListener('change',e=>loadRealData(e.target.value)); $('fhirButton').addEventListener('click',downloadFhir); Promise.all([runSimulation(true),loadRealData('001')]);
  </script>
</body>
</html>'''
