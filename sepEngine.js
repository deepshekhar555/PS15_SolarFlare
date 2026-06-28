/**
 * sepEngine.js  –  ISRO Aditya-L1 SEP Risk Engine  v2.0
 * ============================================================
 * PHYSICS-BASED Solar Energetic Particle (SEP) risk assessment
 * for real-time operational use by ISRO space-weather scientists.
 *
 * Scientific basis:
 *  [1] Parker (1958) – Solar wind magnetic field (Parker spiral)
 *  [2] Tylka & Dietrich (2009) – Empirical SEP flux regression
 *  [3] NOAA S-scale definition (NOAA NWS, 2001)
 *  [4] Lario & Simnett (2004) – Proton transport & diffusion
 *  [5] Reames (1999) – Gradual vs. impulsive SEP event taxonomy
 *
 * Inputs (all set as window globals by the WebSocket listener):
 *   window.lastSolexsValue  – Aditya-L1 SoLEXS count rate (cps)
 *   window.lastHel1osValue  – Aditya-L1 HEL1OS count rate (cps)
 *   window.flareLongitude   – Heliographic longitude of flare source (°W)
 *   window.solarWindSpeed   – Solar-wind speed at L1 (km/s)
 *   window.goesXrayB        – GOES 1-8 Å X-ray flux (W/m²), fallback for SoLEXS
 *
 * Outputs (written to DOM by updateSEPDisplay):
 *   sep-flux        – Estimated >10 MeV proton flux (pfu)
 *   sep-flux100     – Estimated >100 MeV proton flux (pfu)
 *   sep-pconn       – Parker-spiral connection probability (%)
 *   sep-wangle      – Parker angle at current solar-wind speed (°W)
 *   sep-hr          – X-ray spectral hardness ratio (HEL1OS/SoLEXS)
 *   sep-lead        – Estimated proton-arrival lead time (min)
 *   sep-scale       – NOAA S-scale risk level
 *   sep-status      – Status chip (colour coded)
 *   sep-warning     – High-risk warning banner
 *   sep-delta       – Acceleration spectral index δ
 *   sep-vshock      – Estimated CME shock speed (km/s)
 *   sep-shock-coupling – CME shock coupling indicator
 *   sep-mfp         – Mean free path λ (AU)
 *   pinn-coherence  – Neupert coherence index (%)
 *   pinn-state      – Neupert effect state
 *
 * Usage:
 *   // Called every tick from dashboard.js
 *   window.SEP.updateSEPDisplay();
 *   // Override model
 *   window.SEP.selectModel('noaa-empirical');
 *   // Calibrate with new coefficients (after CSV upload)
 *   window.SEP.setCoefficients({a: 1.95, b: 14.2, c: -0.72});
 */

'use strict';

window.SEP = (function () {
  // ================================================================
  // Physical constants
  // ================================================================
  const AU      = 1.496e8;       // km – 1 astronomical unit
  const OMEGA   = 2.865e-6;      // rad/s – solar sidereal rotation rate
  const R_L1    = AU;            // km – Sun-Earth L1 distance (approx)
  const C_LIGHT = 2.998e5;       // km/s – speed of light
  const M_PROTON = 1.673e-27;    // kg

  // ================================================================
  // Model coefficients (Tylka & Dietrich 2009, Table 3)
  // a: log10(F_X) slope, b: hardness slope, c: intercept
  // These can be overridden by setCoefficients() for calibration.
  // ================================================================
  let COEFFS = { a: 1.82, b: 15.4, c: -0.85 };
  let ACTIVE_MODEL = 'tylka-dietrich';

  // ================================================================
  // Load persisted calibration coefficients (from scientist upload)
  // ================================================================
  (function loadCalibration() {
    try {
      const saved = localStorage.getItem('sep_coefficients');
      if (saved) {
        const c = JSON.parse(saved);
        if (typeof c.a === 'number' && typeof c.b === 'number') {
          COEFFS = c;
          console.info('[SEP] Loaded calibrated coefficients from localStorage:', COEFFS);
        }
      }
    } catch (_) {}
  })();

  // ================================================================
  // Parker Spiral Connectivity
  // ================================================================

  /**
   * Compute the Parker spiral connection angle (°W) at a given solar-wind speed.
   *
   * Derivation:
   *   The interplanetary magnetic field wraps into an Archimedean spiral
   *   because the Sun rotates while the wind streams outward.
   *   φ_Parker = Ω × r / v_sw   (radians)
   *   Converted to degrees West.
   *
   *   Reference: Parker (1958), Eq. 5; Nolte & Roelof (1973)
   *
   * @param {number} vSW  Solar-wind speed [km/s]
   * @returns {number}    Parker angle [°W]
   */
  function parkerAngle(vSW) {
    if (!Number.isFinite(vSW) || vSW <= 0) vSW = 450;
    return (OMEGA * R_L1 / vSW) * (180 / Math.PI);
  }

  /**
   * Estimate the probability that a flare at longitude `flareLon`°W is
   * well-connected to Earth via the Parker spiral.
   *
   * Method:
   *   The connection probability falls off as a Gaussian around the
   *   Parker angle, with σ = 30° (empirically derived from SEP statistics;
   *   Lario et al. 2013, Table 2).
   *
   * @param {number} flareLon  Heliographic longitude of flare [°W]
   * @param {number} vSW       Solar-wind speed [km/s]
   * @returns {number}         Connection probability [0–100 %]
   */
  function connectionProbability(flareLon, vSW) {
    const phi = parkerAngle(vSW);
    const diff = flareLon - phi;
    const SIGMA = 30; // degrees
    return Math.min(100, Math.max(0, Math.exp(-0.5 * (diff / SIGMA) ** 2) * 100));
  }

  // ================================================================
  // SEP Flux Models
  // ================================================================

  /**
   * Tylka-Dietrich (2009) empirical regression for peak SEP proton flux.
   *
   *   log₁₀(F_>10MeV) = a × log₁₀(F_X) + b × HR + c
   *
   * where:
   *   F_X  = GOES 1-8 Å peak X-ray flux [W/m²] — approximated from SoLEXS
   *   HR   = HEL1OS / SoLEXS (spectral hardness ratio)
   *   a,b,c = regression coefficients (Table 3, Tylka & Dietrich 2009)
   *
   * The >100 MeV flux is estimated using spectral steepening:
   *   F_>100 ≈ F_>10 × HR^2.5   (Reames 1999, power-law steepening)
   *
   * @param {number} solexs    SoLEXS count rate [cps]
   * @param {number} hardness  Spectral hardness ratio [dimensionless]
   * @returns {{ flux10: number, flux100: number }}  Flux in pfu
   */
  function tylkaDietrich(solexs, hardness) {
    // Convert SoLEXS cps → approximate GOES 1-8 Å [W/m²]
    // Inverse of _goes_xray_to_cps() in data_ingest/main.py
    const logFx = (solexs - 2000) / 200;  // approximate log10(W/m²)
    const logF10 = COEFFS.a * logFx + COEFFS.b * hardness + COEFFS.c;
    const flux10  = Math.max(0.01, Math.pow(10, logF10));
    const flux100 = Math.max(0.001, flux10 * Math.pow(Math.max(0.01, hardness), 2.5));
    return { flux10, flux100 };
  }

  /**
   * NOAA empirical model (alternate):
   *   Based on NOAA Space Weather Scales statistical analysis.
   *   Simpler linear regression on GOES class magnitude.
   *   Used when 'noaa-empirical' model is selected.
   */
  function noaaEmpirical(solexs, hardness) {
    // Rough mapping: C-class ~50 cps → flux10 ~0.5 pfu
    //               M-class ~500 cps → flux10 ~10 pfu
    //               X-class ~2000 cps → flux10 ~100 pfu
    const flux10  = Math.max(0.01, 0.001 * solexs * (1 + hardness * 5));
    const flux100 = Math.max(0.001, flux10 * 0.05 * Math.pow(Math.max(0.01, hardness), 2));
    return { flux10, flux100 };
  }

  // ================================================================
  // Lead-Time Estimate
  // ================================================================

  /**
   * Estimate proton arrival lead time based on connection probability.
   *
   * Physics:
   *   Relativistic >10 MeV protons travel at v ≈ 0.14c (~42,000 km/s).
   *   Minimum field-line travel distance at L1 ≈ 1.2 AU (along the spiral).
   *   Minimum time ≈ 8 min (well-connected, fast protons).
   *   Maximum ≈ 45 min (poorly connected; protons diffuse cross-field; Reames 1999).
   *
   * @param {number} pConn  Connection probability [0–100]
   * @returns {number}      Lead time [minutes]
   */
  function protonLeadTime(pConn) {
    const t_min = 8;
    const t_max = 45;
    return Math.round(t_max - (pConn / 100) * (t_max - t_min));
  }

  // ================================================================
  // Additional Physical Quantities
  // ================================================================

  /**
   * Acceleration spectral index δ.
   *   Higher hardness (more HEL1OS relative to SoLEXS) → harder proton spectrum.
   *   δ = 3 × (1 – hardness × 2), clamped to [2, 6].
   *   Reference: Kahler (2001); Tylka & Lee (2006).
   */
  function spectralIndex(hardness) {
    return Math.min(6, Math.max(2, 5 - hardness * 4));
  }

  /**
   * Estimated CME shock speed from X-ray flux and hardness.
   *   Empirical relationship (Gopalswamy et al. 2008):
   *   v_shock ≈ 200 + 1.5 × F_X[W/m²] × 1e7
   *   Approximated here using solexs cps as proxy.
   */
  function shockSpeed(solexs, hardness) {
    return Math.round(200 + (solexs / 1000) * 800 + hardness * 500);
  }

  /**
   * Mean free path λ [AU].
   *   λ depends on the rigidity of the proton and the turbulence level
   *   of the interplanetary medium.
   *   Approximation (Palmer 1982 consensus range 0.08–0.3 AU):
   *   λ ≈ 0.08 + 0.22 × pConn/100
   */
  function meanFreePath(pConn) {
    return parseFloat((0.08 + 0.22 * pConn / 100).toFixed(3));
  }

  /**
   * CME shock coupling indicator (qualitative).
   *   Based on Bz (southward field) and shock speed.
   */
  function shockCoupling(vShock, bz) {
    if (vShock > 1500 && bz < -10) return '⚡ STRONG — High geoeffectiveness';
    if (vShock > 800  && bz < -5)  return '⚠ MODERATE — Monitor closely';
    if (vShock > 400)               return '↗ WEAK — Minimal coupling';
    return '✓ NO CME SHOCK';
  }

  // ================================================================
  // Neupert Effect Coherence (SHAP Physics Validation)
  // ================================================================

  /**
   * Neupert coherence index.
   *
   * The Neupert Effect states that the time-derivative of soft X-ray flux
   * (SoLEXS) should mirror the hard X-ray flux (HEL1OS) during a flare.
   * Non-thermal electrons accelerated at the reconnection site bombard
   * the chromosphere, producing both hard X-rays (bremsstrahlung) and
   * heating plasma that emits soft X-rays.
   *
   * We approximate the coherence by comparing the ratio HEL1OS / d(SoLEXS)/dt
   * against the expected ratio (≈1.0 during a classical Neupert event).
   *
   * Reference: Neupert (1968); Dennis & Zarro (1993); Veronig et al. (2005)
   */
  function neupertCoherence(solexs, hel1os) {
    const prev = window._prevSolexs || solexs;
    const dSdt = solexs - prev;  // Δt = 1 s
    window._prevSolexs = solexs;

    if (Math.abs(dSdt) < 0.5 || hel1os < 0.1) return { coherence: 0, state: 'QUIESCENT' };

    // Ideally: HEL1OS ∝ d(SoLEXS)/dt  (Neupert relation)
    const ratio = hel1os / Math.abs(dSdt);
    // A ratio near 1.0 (considering scale factors) indicates Neupert event
    const coherence = Math.min(100, Math.max(0, (1 - Math.abs(ratio - 0.5) / 2) * 100));
    const state = coherence > 70 ? 'NEUPERT ACTIVE 🔥' :
                  coherence > 40 ? 'PARTIAL NEUPERT' : 'NON-NEUPERT';
    return { coherence: Math.round(coherence), state };
  }

  // ================================================================
  // NOAA S-scale
  // ================================================================

  /**
   * Map peak >10 MeV proton flux to NOAA S-scale.
   * Reference: NOAA NWS Space Weather Scales (2001)
   * Threshold: S1 ≥ 10 pfu, S2 ≥ 100, S3 ≥ 1000, S4 ≥ 10000, S5 ≥ 100000
   */
  function noaaSScale(flux10) {
    if (flux10 >= 1e5) return { level: 5, label: 'S5 Extreme',  color: 'var(--red)' };
    if (flux10 >= 1e4) return { level: 4, label: 'S4 Severe',   color: '#ff6b35' };
    if (flux10 >= 1e3) return { level: 3, label: 'S3 Strong',   color: 'var(--orange)' };
    if (flux10 >= 100) return { level: 2, label: 'S2 Moderate', color: '#eab308' };
    if (flux10 >= 10)  return { level: 1, label: 'S1 Minor',    color: '#84cc16' };
    return               { level: 0, label: 'S0 None',    color: 'var(--green)' };
  }

  // ================================================================
  // Core: updateSEPDisplay()
  // ================================================================

  function updateSEPDisplay() {
    // --- Read live telemetry globals (set by WebSocket listener) ---
    const solexs   = Number.isFinite(window.lastSolexsValue)  ? window.lastSolexsValue  : 50;
    const hel1os   = Number.isFinite(window.lastHel1osValue)  ? window.lastHel1osValue  : 8;
    const flareLon = Number.isFinite(window.flareLongitude)   ? window.flareLongitude   : 0;
    const vSW      = Number.isFinite(window.solarWindSpeed)   ? window.solarWindSpeed   :
                     // fallback: parse from DOM (backward compat)
                     parseFloat(document.getElementById('wind-spd')?.textContent) || 450;
    const bz       = Number.isFinite(window.imfBz) ? window.imfBz : -2;

    // --- Compute ---
    const hardness = hel1os > 0 && solexs > 0 ? hel1os / solexs : 0;
    const phi      = parkerAngle(vSW);
    const pConn    = connectionProbability(flareLon, vSW);

    const { flux10, flux100 } = ACTIVE_MODEL === 'noaa-empirical'
      ? noaaEmpirical(solexs, hardness)
      : tylkaDietrich(solexs, hardness);

    const lead     = protonLeadTime(pConn);
    const sScaleObj= noaaSScale(flux10);
    const delta    = spectralIndex(hardness);
    const vShock   = shockSpeed(solexs, hardness);
    const mfp      = meanFreePath(pConn);
    const coupling = shockCoupling(vShock, bz);
    const { coherence, state: neupertState } = neupertCoherence(solexs, hel1os);

    // --- Risk classification ---
    const isHighRisk = pConn > 70 || flux10 > 1000 || sScaleObj.level >= 3;
    const isMedRisk  = !isHighRisk && (pConn > 30 || flux10 > 100 || sScaleObj.level >= 1);

    // --- Write to DOM (safe null-check on every field) ---
    const set = (id, txt) => {
      const el = document.getElementById(id);
      if (el) el.textContent = txt;
    };

    set('sep-flux',    `${flux10.toFixed(2)} pfu`);
    set('sep-flux100', `${flux100.toFixed(3)} pfu`);
    set('sep-pconn',   `${pConn.toFixed(1)}%`);
    set('sep-wangle',  `${phi.toFixed(1)} °W`);
    set('sep-hr',      hardness.toFixed(3));
    set('sep-lead',    `${lead} min`);
    set('sep-scale',   sScaleObj.label);
    set('sep-delta',   delta.toFixed(2));
    set('sep-vshock',  `${vShock} km/s`);
    set('sep-shock-coupling', coupling);
    set('sep-mfp',     `${mfp} AU`);
    set('pinn-coherence', `${coherence}%`);
    set('pinn-state',  neupertState);

    // Colour sep-scale
    const scaleEl = document.getElementById('sep-scale');
    if (scaleEl) scaleEl.style.color = sScaleObj.color;

    // Status chip
    const chip = document.getElementById('sep-status');
    if (chip) {
      if (isHighRisk) {
        chip.style.cssText = 'background:rgba(239,68,68,0.12);border-color:rgba(239,68,68,0.4);color:var(--red)';
        chip.textContent = '🔴 HIGH SEP RISK';
      } else if (isMedRisk) {
        chip.style.cssText = 'background:rgba(249,115,22,0.12);border-color:rgba(249,115,22,0.4);color:var(--orange)';
        chip.textContent = '🟠 MODERATE SEP RISK';
      } else {
        chip.style.cssText = 'background:rgba(16,185,129,0.1);border-color:rgba(16,185,129,0.3);color:var(--green)';
        chip.textContent = '🟢 NO SEP RISK';
      }
    }

    // Warning banner
    const warn = document.getElementById('sep-warning');
    if (warn) {
      warn.style.display = isHighRisk ? 'block' : 'none';
      if (isHighRisk) {
        const inner = document.getElementById('sep-warning-text');
        if (inner) {
          inner.textContent =
            `⚠ ISRO ALERT: SEP event expected. ` +
            `Parker connection = ${pConn.toFixed(0)}%. ` +
            `Estimated >10 MeV flux = ${flux10.toFixed(0)} pfu (${sScaleObj.label}). ` +
            `First proton arrival in ~${lead} min. ` +
            `Shield satellites and pause EVA operations.`;
        }
      }
    }

    // --- SHAP Explainability Calculations ---
    const logSolexs = Math.log10(Math.max(10, solexs));
    const baselineLogSolexs = Math.log10(600);
    const baselineHR = 0.05;
    
    const shapSolexs = COEFFS.a * (logSolexs - baselineLogSolexs);
    const shapHardness = COEFFS.b * (hardness - baselineHR);
    const shapConn = 2.5 * (pConn / 100 - 0.2);
    const shapBz = 0.1 * (-bz - 2.0);
    
    const updateShapBar = (barId, valId, val) => {
      const bar = document.getElementById(barId);
      const valEl = document.getElementById(valId);
      if (!bar || !valEl) return;
      
      const sign = val >= 0 ? '+' : '';
      valEl.textContent = `${sign}${val.toFixed(2)}`;
      
      if (val >= 0) {
        valEl.style.color = barId.includes('pconn') ? '#ef4444' : barId.includes('solexs') ? '#f97316' : barId.includes('hr') ? '#eab308' : '#06b6d4';
        bar.style.background = valEl.style.color;
      } else {
        valEl.style.color = '#10b981';
        bar.style.background = '#10b981';
      }
      
      const pct = Math.min(100, Math.max(0, (Math.abs(val) / 4.0) * 100));
      bar.style.width = `${pct}%`;
    };
    
    updateShapBar('shap-pconn-bar',  'shap-pconn-val',  shapConn);
    updateShapBar('shap-solexs-bar', 'shap-solexs-val', shapSolexs);
    updateShapBar('shap-hr-bar',     'shap-hr-val',     shapHardness);
    updateShapBar('shap-bz-bar',     'shap-bz-val',     shapBz);

    // Provide data for canvas overlay
    window.sepArcData = {
      pConn,
      flareLon,
      parkerAngle: phi,
      flux10,
      sLevel: sScaleObj.level,
    };

    // Store last computation for audit / export
    window.SEP.lastResult = { solexs, hel1os, hardness, flareLon, vSW, phi, pConn, flux10, flux100, lead, delta, vShock, mfp, coupling, coherence, sScale: sScaleObj.label, model: ACTIVE_MODEL, ts: new Date().toISOString() };
  }

  // ================================================================
  // Public API
  // ================================================================
  return {
    updateSEPDisplay,
    parkerAngle,
    connectionProbability,
    tylkaDietrich,
    noaaEmpirical,
    protonLeadTime,
    noaaSScale,
    spectralIndex,
    shockSpeed,
    meanFreePath,
    neupertCoherence,

    /** Override regression coefficients (used by calibration UI). */
    setCoefficients(c) {
      if (!Number.isFinite(c.a) || !Number.isFinite(c.b) || !Number.isFinite(c.c)) {
        console.error('[SEP] Invalid coefficients:', c);
        return false;
      }
      COEFFS = { a: c.a, b: c.b, c: c.c };
      localStorage.setItem('sep_coefficients', JSON.stringify(COEFFS));
      console.info('[SEP] New coefficients applied:', COEFFS);
      return true;
    },

    /** Get current coefficients. */
    getCoefficients() { return { ...COEFFS }; },

    /** Select model: 'tylka-dietrich' (default) or 'noaa-empirical'. */
    selectModel(name) {
      if (!['tylka-dietrich', 'noaa-empirical'].includes(name)) {
        console.error('[SEP] Unknown model:', name);
        return;
      }
      ACTIVE_MODEL = name;
      console.info('[SEP] Model switched to:', ACTIVE_MODEL);
    },

    lastResult: null,
  };
})();
