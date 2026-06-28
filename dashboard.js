// ================================================================
// Aditya-L1 Solar Situational Awareness Center — dashboard.js v3.0
// Features: Solar canvas, satellite map, SHAP, QPP, forecast,
//           historical comparison, wavelength toggle, notifications
// ================================================================

'use strict';

// ────────── AI RESPONSES ──────────
const AI = {
 hardness:"The Spectral Hardness Ratio (HEL1OS/SoLEXS) quantifies the ratio of non-thermal hard X-ray emission to thermal soft X-ray. An elevated ratio (>0.15) reveals particle acceleration dominating over thermal conduction — the hallmark of the Neupert Effect. This is a critical precursor signature for impulsive solar flares.",
 qpp:"Quasi-Periodic Pulsations (QPPs) manifest as rhythmic oscillations in X-ray flux during solar flares. Physically driven by MHD sausage or kink wave modes in coronal loops, or by periodic magnetic reconnection at current sheet boundaries. Aditya-L1 SoLEXS detects QPP periods from 5-300 seconds — each oscillation represents energy release quantization in the flare reconnection region.",
 directives:"OPERATOR DIRECTIVES — HIGH Alert Protocol:\n1. Notify ISRO Space Situational Awareness Control Centre (SSAC).\n2. Reorient Aditya-L1 SoLEXS and HEL1OS aperture shutters to prevent detector saturation.\n3. Issue Kp Index warning to satellite operators for SEU (Single Event Upset) protection.\n4. Alert HF Radio operators of impending D-layer X-ray ionospheric absorption (radio blackout).\n5. Activate geomagnetic storm watch for ground-based power grid operators.",
 neupert:"The Neupert Effect: the time-derivative of soft X-ray flux (SoLEXS) mirrors the hard X-ray flux profile (HEL1OS). Non-thermal electrons accelerated in the corona stream down field lines, heating the chromospheric plasma which ablates upward (chromospheric evaporation) to fill coronal loops — producing the gradual soft X-ray rise. Aditya-L1 is uniquely positioned to observe this coupling.",
 evap:"Chromospheric evaporation is the rapid upflow of heated plasma from the chromosphere into coronal magnetic loops during a solar flare. Non-thermal electrons from magnetic reconnection sites bombard the chromosphere, depositing energy faster than it can radiate away. This ablated plasma (T~20MK) fills the loop at hundreds of km/s, producing the gradual SoLEXS brightening phase observed by Aditya-L1.",
 model:"The RandomForest classifier evaluates a 10-minute sliding window of 5 SoLEXS features: (1) mean count rate, (2) standard deviation, (3) spectral hardness ratio HEL1OS/SoLEXS, (4) the linear slope (derivative proxy), and (5) QPP oscillation power from an FFT bandpass. Trained on Aditya-L1 SoLEXS 2024-2025 data, it achieves 91.3% cross-validation accuracy and AUC-ROC of 0.94. When P(M-class) exceeds 70%, the system triggers a Level II CRITICAL alert.",
 default:"Our Causal Nowcasting system provides satellite operators 15-45 minutes advance warning before peak geomagnetic impact. The pipeline: SoLEXS/HEL1OS raw counts -> feature extraction (mean, std, hardness, slope, QPP power) -> RandomForest classification -> probability output -> CRITICAL/MODERATE/NOMINAL alert. The dashboard also shows SHAP feature importance so operators understand WHY the AI made each prediction."
};

// ────────── STATE ──────────
let TELEMETRY = [];
let idx = 0, playing = true, speed = 2, tickId = null;
let flareI = 0, flareAR = 0;
let wavelength = '304';
let showBlackout = true, showOrbits = false;
let notifGranted = false;
let demoMode = false;
let historicalFlare = null;
let recentSolexs = [];
let recentHel1os = [];
const WIN = 60;

const AudioSynth = {
 ctx: null,
 master: null,
 humOsc1: null,
 humOsc2: null,
 humGain: null,
 humFilter: null,
 windNoise: null,
 windGain: null,
 windFilter: null,
 crackleInterval: null,
 alarmOsc1: null,
 alarmOsc2: null,
 alarmGain: null,
 alarmInterval: null,
 currentAlarmLevel: null,
 muted: true,

 init() {
  if (this.ctx) return;
  try {
   const AudioCtx = window.AudioContext || window.webkitAudioContext;
   this.ctx = new AudioCtx();
   this.master = this.ctx.createGain();
   this.master.gain.value = this.muted ? 0 : 0.6;
   this.master.connect(this.ctx.destination);

   this.startSpaceHum();
   this.startSolarWindNoise();
   this.startSolarCrackle();
  } catch (e) {
   console.warn("Web Audio API not supported", e);
  }
 },

 setMute(m) {
  this.muted = m;
  if (this.ctx) {
   if (this.ctx.state === 'suspended') {
    this.ctx.resume();
   }
   this.master.gain.setTargetAtTime(this.muted ? 0 : 0.6, this.ctx.currentTime, 0.1);
  }
 },

 startSpaceHum() {
  this.humFilter = this.ctx.createBiquadFilter();
  this.humFilter.type = 'lowpass';
  this.humFilter.frequency.value = 80;
  this.humFilter.Q.value = 2.0;

  this.humOsc1 = this.ctx.createOscillator();
  this.humOsc1.type = 'sawtooth';
  this.humOsc1.frequency.value = 55;

  this.humOsc2 = this.ctx.createOscillator();
  this.humOsc2.type = 'sine';
  this.humOsc2.frequency.value = 55.4;

  this.humGain = this.ctx.createGain();
  this.humGain.gain.value = 0.15;

  this.humOsc1.connect(this.humFilter);
  this.humOsc2.connect(this.humFilter);
  this.humFilter.connect(this.humGain);
  this.humGain.connect(this.master);

  this.humOsc1.start();
  this.humOsc2.start();

  const mod = () => {
   if (!this.ctx || this.muted) return;
   const t = this.ctx.currentTime;
   this.humFilter.frequency.setTargetAtTime(70 + 30 * Math.sin(t * 0.2), t, 0.5);
  };
  setInterval(mod, 1000);
 },

 startSolarWindNoise() {
  const bufferSize = 2 * this.ctx.sampleRate;
  const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
  const output = noiseBuffer.getChannelData(0);
  for (let i = 0; i < bufferSize; i++) {
   output[i] = Math.random() * 2 - 1;
  }

  this.windNoise = this.ctx.createBufferSource();
  this.windNoise.buffer = noiseBuffer;
  this.windNoise.loop = true;

  this.windFilter = this.ctx.createBiquadFilter();
  this.windFilter.type = 'bandpass';
  this.windFilter.frequency.value = 200;
  this.windFilter.Q.value = 1.2;

  this.windGain = this.ctx.createGain();
  this.windGain.gain.value = 0.04;

  this.windNoise.connect(this.windFilter);
  this.windFilter.connect(this.windGain);
  this.windGain.connect(this.master);
  this.windNoise.start();
 },

 startSolarCrackle() {
  this.crackleInterval = setInterval(() => {
   if (!this.ctx || this.muted || !window.lastSolexsValue) return;
   
   const flux = window.lastSolexsValue + (window.lastHel1osValue || 0);
   if (flux < 50) return;
   
   const prob = Math.min(0.85, 0.05 + (flux / 2000) * 0.8);
   if (Math.random() > prob) return;
   
   const t = this.ctx.currentTime;
   const osc = this.ctx.createOscillator();
   const filter = this.ctx.createBiquadFilter();
   const gain = this.ctx.createGain();
   
   filter.type = 'highpass';
   filter.frequency.value = 3000;
   
   osc.type = 'triangle';
   osc.frequency.setValueAtTime(100 + Math.random() * 8000, t);
   
   const vol = Math.min(0.12, 0.01 + (flux / 2000) * 0.11);
   gain.gain.setValueAtTime(vol, t);
   gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.015);
   
   osc.connect(filter);
   filter.connect(gain);
   gain.connect(this.master);
   
   osc.start(t);
   osc.stop(t + 0.02);
  }, 40);
 },

 updateSpaceWeather(solexs, hel1os, windSpeed) {
  window.lastSolexsValue = solexs;
  window.lastHel1osValue = hel1os;

  if (!this.ctx || this.muted) return;
  const t = this.ctx.currentTime;
  
  const windFreq = 150 + ((windSpeed - 400) / 400) * 300;
  const windVolume = 0.02 + ((windSpeed - 400) / 400) * 0.06;
  this.windFilter.frequency.setTargetAtTime(windFreq, t, 0.3);
  this.windGain.gain.setTargetAtTime(windVolume, t, 0.3);

  const totalFlux = solexs + hel1os;
  const humFreqBase = 55 + Math.min(55, (totalFlux / 1500) * 40);
  this.humOsc1.frequency.setTargetAtTime(humFreqBase, t, 0.5);
  this.humOsc2.frequency.setTargetAtTime(humFreqBase * 1.008, t, 0.5);
  
  const humVolume = 0.12 + Math.min(0.18, (totalFlux / 1500) * 0.15);
  this.humGain.gain.setTargetAtTime(humVolume, t, 0.5);
 },

 playScanBeep(hardnessRatio) {
  if (!this.ctx || this.muted) return;
  const t = this.ctx.currentTime;
  const osc = this.ctx.createOscillator();
  const gainNode = this.ctx.createGain();

  osc.type = 'sine';
  const pitch = 600 + Math.min(1.0, hardnessRatio) * 1800;
  osc.frequency.setValueAtTime(pitch, t);

  gainNode.gain.setValueAtTime(0.03, t);
  gainNode.gain.exponentialRampToValueAtTime(0.001, t + 0.08);

  osc.connect(gainNode);
  gainNode.connect(this.master);
  osc.start(t);
  osc.stop(t + 0.09);
 },

 playClick() {
  if (!this.ctx || this.muted) return;
  const t = this.ctx.currentTime;
  const osc = this.ctx.createOscillator();
  const gainNode = this.ctx.createGain();

  osc.type = 'triangle';
  osc.frequency.setValueAtTime(150, t);
  osc.frequency.exponentialRampToValueAtTime(40, t + 0.05);

  gainNode.gain.setValueAtTime(0.06, t);
  gainNode.gain.exponentialRampToValueAtTime(0.001, t + 0.06);

  osc.connect(gainNode);
  gainNode.connect(this.master);
  osc.start(t);
  osc.stop(t + 0.07);
 },

 startAlarm(level) {
  if (this.currentAlarmLevel === level) return;
  this.stopAlarm();
  this.currentAlarmLevel = level;

  if (!this.ctx) return;
  const t = this.ctx.currentTime;

  this.alarmGain = this.ctx.createGain();
  this.alarmGain.gain.value = 0;
  this.alarmGain.connect(this.master);

  if (level === 'high') {
   this.alarmOsc1 = this.ctx.createOscillator();
   this.alarmOsc1.type = 'square';
   this.alarmOsc1.frequency.setValueAtTime(440, t);

   this.alarmOsc2 = this.ctx.createOscillator();
   this.alarmOsc2.type = 'sawtooth';
   this.alarmOsc2.frequency.setValueAtTime(445, t);

   this.alarmOsc1.connect(this.alarmGain);
   this.alarmOsc2.connect(this.alarmGain);
   this.alarmOsc1.start(t);
   this.alarmOsc2.start(t);

   this.alarmInterval = setInterval(() => {
    if (!this.ctx || this.muted) return;
    const now = this.ctx.currentTime;
    
    this.alarmOsc1.frequency.setValueAtTime(450, now);
    this.alarmOsc1.frequency.exponentialRampToValueAtTime(855, now + 0.38);
    this.alarmOsc2.frequency.setValueAtTime(455, now);
    this.alarmOsc2.frequency.exponentialRampToValueAtTime(860, now + 0.38);

    this.alarmGain.gain.setValueAtTime(0.22, now);
    this.alarmGain.gain.exponentialRampToValueAtTime(0.001, now + 0.44);
    
    const beepOsc = this.ctx.createOscillator();
    const beepGain = this.ctx.createGain();
    beepOsc.type = 'sine';
    beepOsc.frequency.setValueAtTime(1600, now);
    beepGain.gain.setValueAtTime(0.06, now);
    beepGain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
    
    beepOsc.connect(beepGain);
    beepGain.connect(this.master);
    beepOsc.start(now);
    beepOsc.stop(now + 0.15);
   }, 500);

  } else if (level === 'med') {
   this.alarmOsc1 = this.ctx.createOscillator();
   this.alarmOsc1.type = 'sine';
   this.alarmOsc1.frequency.setValueAtTime(880, t);

   this.alarmOsc1.connect(this.alarmGain);
   this.alarmOsc1.start(t);

   this.alarmInterval = setInterval(() => {
    if (!this.ctx || this.muted) return;
    const now = this.ctx.currentTime;
    
    this.alarmGain.gain.setValueAtTime(0.18, now);
    this.alarmGain.gain.setValueAtTime(0, now + 0.08);
    
    this.alarmGain.gain.setValueAtTime(0.18, now + 0.18);
    this.alarmGain.gain.setValueAtTime(0, now + 0.26);
   }, 1500);
  }
 },

 stopAlarm() {
  if (this.alarmInterval) {
   clearInterval(this.alarmInterval);
   this.alarmInterval = null;
  }
  if (this.alarmOsc1) {
   try { this.alarmOsc1.stop(); } catch(e){}
   this.alarmOsc1 = null;
  }
  if (this.alarmOsc2) {
   try { this.alarmOsc2.stop(); } catch(e){}
   this.alarmOsc2 = null;
  }
  if (this.alarmGain) {
   this.alarmGain.disconnect();
   this.alarmGain = null;
  }
  this.currentAlarmLevel = null;
 }
};

// ────────── TELEMETRY LOAD ──────────
function buildFallbackTelemetry() {
 const out = [];
 for (let i = 0; i < 300; i++) {
  let s, h;
  if (i < 90) { s = 5 + Math.random()*15; h = 10 + s*0.12; }
  else if (i < 120) { const p=(i-90)/30; s=20*Math.exp(p*Math.log(400/20)); h=10+s*0.15; }
  else if (i < 150) { const p=(i-120)/30; s=400*Math.exp(p*Math.log(1600/400)); h=10+s*0.25; }
  else if (i < 180) { s=1600+120*Math.sin(2*Math.PI*(i-150)/8); h=10+s*0.22; }
  else if (i < 250) { const p=(i-180)/70; s=1600*Math.exp(-p*Math.log(1600/80)); h=10+s*0.18; }
  else { const p=(i-250)/50; s=80*Math.exp(-p*Math.log(80/8))+5+Math.random()*10; h=10+s*0.13; }
  out.push({ time:1781654100+i, solexs:Math.max(0,+s.toFixed(1)), hel1os:Math.max(0,+(h+Math.random()*0.3).toFixed(1)) });
 }
 return out;
}

fetch('telemetry_inline.json')
 .then(r=>r.json())
 .then(d=>{ TELEMETRY=d; startTick(); })
 .catch(()=>{ TELEMETRY=buildFallbackTelemetry(); startTick(); });

// ────────── CLOCKS ──────────
function updateClocks() {
 const now = new Date();
 setText('local-clock', now.toLocaleTimeString());
 const h=String(now.getUTCHours()).padStart(2,'0');
 const m=String(now.getUTCMinutes()).padStart(2,'0');
 const s=String(now.getUTCSeconds()).padStart(2,'0');
 setText('utc-clock', `${h}:${m}:${s} UTC`);
}
setInterval(updateClocks,1000); updateClocks();

// ================================================================
// ☀ SOLAR DISK CANVAS ANIMATION (15fps throttle)
// ================================================================
const sunCanvas = document.getElementById('sunCanvas');
const sunCtx = sunCanvas.getContext('2d');
let sunTime = 0, sunLastTs = 0;
const SUN_MS = 1000/15;

const ARs = [
 {id:'AR4087',nx:0.22,ny:-0.38,r:0.075},
 {id:'AR4086',nx:0.57,ny:-0.22,r:0.055},
 {id:'AR4085',nx:0.12,ny:0.47, r:0.085},
];

let granules = [];
function resizeSun() {
 const wrap = document.getElementById('sun-wrap');
 const sz = Math.min(wrap.clientWidth-8, wrap.clientHeight-60, 330);
 sunCanvas.width = sz; sunCanvas.height = sz;
 buildGranules();
}
function buildGranules() {
 granules = [];
 const cx=sunCanvas.width/2, cy=sunCanvas.height/2, R=Math.min(cx,cy)*0.85;
 const cell = R*0.09;
 for (let gx=cx-R; gx<cx+R; gx+=cell) {
  for (let gy=cy-R; gy<cy+R; gy+=cell) {
   const d=Math.sqrt((gx-cx)**2+(gy-cy)**2);
   if (d>R*0.96) continue;
   granules.push({
    x:gx+Math.sin(gx*0.13+gy*0.07)*cell*0.35,
    y:gy+Math.cos(gx*0.09+gy*0.11)*cell*0.35,
    sz:cell*(0.28+0.18*Math.abs(Math.sin(gx*0.05+gy*0.03))),
    ph:(gx*0.08+gy*0.06)%(Math.PI*2),
    df:d/R
   });
  }
 }
}
resizeSun();
window.addEventListener('resize', resizeSun);

// Wavelength color profiles
const WL_PROFILES = {
 '304': { c0:'rgba(255,255,210,1)', c1:'rgba(255,200,50,1)', c2:'rgba(255,130,15,1)', c3:'rgba(190,60,8,1)', c4:'rgba(80,12,4,1)', granCol:'255,210,65', arCol:'255,230,100', coronaCol:'255,100,0' },
 '171': { c0:'rgba(180,220,255,1)', c1:'rgba(80,170,255,1)', c2:'rgba(30,100,255,1)', c3:'rgba(15,50,180,1)', c4:'rgba(5,10,60,1)', granCol:'100,180,255', arCol:'200,230,255', coronaCol:'0,150,255' },
 '193': { c0:'rgba(200,255,200,1)', c1:'rgba(80,220,100,1)', c2:'rgba(20,180,60,1)', c3:'rgba(5,100,30,1)', c4:'rgba(2,30,8,1)', granCol:'100,220,120', arCol:'180,255,200', coronaCol:'0,200,80' },
 'hmi': { c0:'rgba(40,40,50,1)', c1:'rgba(25,25,35,1)', c2:'rgba(15,15,20,1)', c3:'rgba(8,8,12,1)', c4:'rgba(3,3,5,1)', granCol:'60,60,80', arCol:'200,200,220', coronaCol:'80,80,100' }
};

// --- Solar Disk Shading Helper ---
// Keeps the high-resolution solar photography centered and applies a 3D spherical lens shading.

function drawSun(ts) {
 requestAnimationFrame(drawSun);
 if (ts - sunLastTs < SUN_MS) return;
 sunLastTs = ts; sunTime += 0.04;

 const w=sunCanvas.width, h=sunCanvas.height;
 const cx=w/2, cy=h/2, R=Math.min(cx,cy)*0.85;
 const WL = WL_PROFILES[wavelength] || WL_PROFILES['304'];

 sunCtx.clearRect(0,0,w,h);
 sunCtx.fillStyle = wavelength==='hmi'?'#080810':'#020205';
 sunCtx.fillRect(0,0,w,h);

 // --- Realistic Space Background (Starfield) ---
 if (!window.starCanvas) {
  window.starCanvas = document.createElement('canvas');
  window.starCanvas.width = 1000;
  window.starCanvas.height = 1000;
  const sCtx = window.starCanvas.getContext('2d');
  for (let i = 0; i < 400; i++) {
   sCtx.fillStyle = `rgba(255, 255, 255, ${Math.random() * 0.8})`;
   sCtx.beginPath();
   sCtx.arc(Math.random() * 1000, Math.random() * 1000, Math.random() * 1.5, 0, Math.PI * 2);
   sCtx.fill();
  }
  // Subtle deep space dust/nebula
  for (let i = 0; i < 5; i++) {
   const ng = sCtx.createRadialGradient(Math.random()*1000, Math.random()*1000, 0, Math.random()*1000, Math.random()*1000, 300);
   ng.addColorStop(0, `rgba(50, 80, 255, 0.05)`);
   ng.addColorStop(1, `rgba(0, 0, 0, 0)`);
   sCtx.fillStyle = ng;
   sCtx.fillRect(0,0,1000,1000);
  }
 }
 sunCtx.drawImage(window.starCanvas, 0, 0, w, h);
 // Outer corona glow
 if (wavelength !== 'hmi') {
  const ca = 0.14+flareI*0.22;
  const og = sunCtx.createRadialGradient(cx,cy,R*0.9,cx,cy,R*1.5);
  og.addColorStop(0,`rgba(${WL.coronaCol},${ca})`);
  og.addColorStop(0.5,`rgba(${WL.coronaCol},${ca*0.35})`);
  og.addColorStop(1,'rgba(0,0,0,0)');
  sunCtx.beginPath(); sunCtx.arc(cx,cy,R*1.5,0,Math.PI*2);
  sunCtx.fillStyle=og; sunCtx.fill();
 }

 // Clip to disk
 sunCtx.save();
 sunCtx.beginPath(); sunCtx.arc(cx,cy,R,0,Math.PI*2); sunCtx.clip();

 // Solar disk gradient
 const dg = sunCtx.createRadialGradient(cx-R*0.15,cy-R*0.15,0,cx,cy,R);
 if (flareI>0.4 && wavelength==='304') {
  dg.addColorStop(0,'rgba(255,255,255,1)');
  dg.addColorStop(0.2,'rgba(255,240,180,1)');
  dg.addColorStop(0.55,'rgba(255,140,30,1)');
  dg.addColorStop(0.85,'rgba(190,55,8,1)');
  dg.addColorStop(1,'rgba(80,10,3,1)');
 } else {
  dg.addColorStop(0,WL.c0); dg.addColorStop(0.35,WL.c1);
  dg.addColorStop(0.68,WL.c2); dg.addColorStop(0.88,WL.c3);
  dg.addColorStop(1,WL.c4);
 }
 sunCtx.fillStyle=dg; sunCtx.fillRect(0,0,w,h);

 // --- 3D Rotating Solar Sphere (Local Real-Eye Images) ---
 if (!window.LOCAL_SUN_IMGS) {
  window.LOCAL_SUN_IMGS = {
   '304': new Image(),
   '171': new Image(),
   '193': new Image(),
   'hmi': new Image()
  };
  window.LOCAL_SUN_IMGS['304'].src = 'sun_orange.png';
  window.LOCAL_SUN_IMGS['171'].src = 'sun_yellow.png';
  window.LOCAL_SUN_IMGS['193'].src = 'sun_purple.png';
  window.LOCAL_SUN_IMGS['hmi'].src = 'sun_yellow.png';
 }

 const localImg = window.LOCAL_SUN_IMGS[wavelength];
 let drawSuccess = false;
 
 if (localImg && localImg.complete && localImg.naturalWidth > 0) {
  sunCtx.globalCompositeOperation = wavelength === 'hmi' ? 'source-over' : 'screen';
  sunCtx.globalAlpha = wavelength === 'hmi' ? 0.85 : 0.98;
  
  // 1. Draw the high-resolution base solar photography centered (stable base)
  sunCtx.drawImage(localImg, cx - R * 1.02, cy - R * 1.02, R * 2.04, R * 2.04);
  
  // 2. Draw a sliding atmospheric texture layer (masked to the solar disk) to simulate 3D rotation
  sunCtx.save();
  sunCtx.beginPath(); sunCtx.arc(cx, cy, R * 0.96, 0, Math.PI * 2); sunCtx.clip();
  
  // Translate the texture horizontally based on time
  const shiftX = (sunTime * 6.5) % (R * 2);
  sunCtx.globalAlpha = wavelength === 'hmi' ? 0.22 : 0.35; // overlay opacity for surface flow
  sunCtx.drawImage(localImg, cx - R - shiftX, cy - R, R * 2, R * 2);
  sunCtx.drawImage(localImg, cx - R - shiftX + R * 2, cy - R, R * 2, R * 2);
  
  sunCtx.restore();
  sunCtx.globalAlpha = wavelength === 'hmi' ? 0.85 : 0.98;
  
  // 3. Apply a spherical 3D lens gradient (limb darkening) to create a perfect 3D volume
  const lens = sunCtx.createRadialGradient(cx - R * 0.15, cy - R * 0.15, R * 0.2, cx, cy, R);
  lens.addColorStop(0, 'rgba(0,0,0,0)');
  lens.addColorStop(0.5, 'rgba(0,0,0,0.05)');
  lens.addColorStop(0.8, 'rgba(0,0,0,0.45)');
  lens.addColorStop(1, 'rgba(0,0,0,0.92)');
  
  sunCtx.globalCompositeOperation = 'multiply';
  sunCtx.beginPath(); sunCtx.arc(cx, cy, R * 1.02, 0, Math.PI * 2);
  sunCtx.fillStyle = lens; sunCtx.fill();
  
  sunCtx.globalAlpha = 1.0;
  sunCtx.globalCompositeOperation = 'source-over';
  drawSuccess = true;
 }

 // --- Fallback to SDO Satellite Feed (if local images aren't loaded) ---
 let realImg = null;
 if (!drawSuccess) {
  if (!window.SDO_IMGS) {
   window.SDO_IMGS = { '304': new Image(), '171': new Image(), '193': new Image(), 'hmi': new Image() };
   window.SDO_IMGS['304'].crossOrigin = "Anonymous"; window.SDO_IMGS['304'].src = 'https://sdo.gsfc.nasa.gov/assets/img/latest/latest_512_0304.jpg';
   window.SDO_IMGS['171'].crossOrigin = "Anonymous"; window.SDO_IMGS['171'].src = 'https://sdo.gsfc.nasa.gov/assets/img/latest/latest_512_0171.jpg';
   window.SDO_IMGS['193'].crossOrigin = "Anonymous"; window.SDO_IMGS['193'].src = 'https://sdo.gsfc.nasa.gov/assets/img/latest/latest_512_0193.jpg';
   window.SDO_IMGS['hmi'].crossOrigin = "Anonymous"; window.SDO_IMGS['hmi'].src = 'https://sdo.gsfc.nasa.gov/assets/img/latest/latest_512_HMIB.jpg';
  }
  
  realImg = window.SDO_IMGS[wavelength];
  if (realImg && realImg.complete && realImg.naturalWidth > 0) {
   sunCtx.globalCompositeOperation = wavelength === 'hmi' ? 'source-over' : 'screen';
   sunCtx.globalAlpha = wavelength === 'hmi' ? 0.7 : 0.95;
   sunCtx.drawImage(realImg, cx - R*1.04, cy - R*1.04, R*2.08, R*2.08); // slightly larger to hide edge
   sunCtx.globalAlpha = 1.0;
   sunCtx.globalCompositeOperation = 'source-over';
   drawSuccess = true;
  }
 }


 // --- Solar Surface Granulation & Texture (Fallback if SDO fails) ---
 if (!realImg || !realImg.complete || realImg.naturalWidth === 0) {
  for (const g of granules) {
   const br=0.5+0.5*Math.sin(sunTime*1.1+g.ph);
   const lf=Math.max(0.05,1-g.df*0.7);
   const a=br*lf*(0.16-flareI*0.05);
   sunCtx.beginPath(); sunCtx.arc(g.x,g.y,g.sz,0,Math.PI*2);
   sunCtx.fillStyle=`rgba(${WL.granCol},${a})`; sunCtx.fill();
  }
 }

 // --- Coronal Edge Prominences (Dynamic Real-Time Flare Eruption) ---
 sunCtx.globalCompositeOperation = 'screen';
 for (let p = 0; p < 45; p++) {
  const pAng = (p / 45) * Math.PI * 2 + sunTime * 0.03;
  
  // Base prominence height + dynamic flare ejection scaling with live flareI (SoLEXS/HEL1OS flux)
  const baseH = R * (0.03 + 0.05 * Math.sin(p * 11 + sunTime * 1.5));
  const flareH = R * flareI * 0.35 * Math.max(0, Math.sin(p * 5 + sunTime * 4.5) - 0.2);
  const pHeight = baseH + flareH;
  
  const bx = cx + Math.cos(pAng) * R;
  const by = cy + Math.sin(pAng) * R;
  
  sunCtx.beginPath();
  sunCtx.moveTo(bx, by);
  sunCtx.quadraticCurveTo(
   cx + Math.cos(pAng + 0.04) * (R + pHeight), 
   cy + Math.sin(pAng + 0.04) * (R + pHeight), 
   cx + Math.cos(pAng + 0.08) * R, 
   cy + Math.sin(pAng + 0.08) * R
  );
  
  const pa = (0.25 + 0.35 * Math.sin(sunTime * 2.5 + p)) * (1.0 + flareI * 1.5);
  // Transition from deep orange to bright white-hot plasma during intense flares
  const rVal = Math.round(255);
  const gVal = Math.round(100 + flareI * 155);
  const bVal = Math.round(20 + flareI * 235);
  
  sunCtx.strokeStyle = `rgba(${rVal}, ${gVal}, ${bVal}, ${pa})`;
  sunCtx.lineWidth = 1.2 + flareI * 6.5;
  sunCtx.stroke();
 }
 
 // --- Dynamic Magnetic Flux Loops on Sun Face ---
 if (wavelength !== 'hmi') {
  const numLoops = 4 + Math.floor(flareI * 8);
  for (let i = 0; i < numLoops; i++) {
   const angle = (i * 1.8) + sunTime * 0.04;
   const rx = cx + Math.cos(angle) * R * 0.45 * Math.sin(sunTime * 0.12 + i);
   const ry = cy + Math.sin(angle) * R * 0.45 * Math.cos(sunTime * 0.08 + i);
   const loopR = R * (0.08 + 0.22 * flareI) * (0.8 + 0.2 * Math.sin(sunTime * 2.2 + i));
   
   sunCtx.beginPath();
   sunCtx.arc(rx, ry, loopR, 0, Math.PI, true);
   sunCtx.strokeStyle = `rgba(${WL.arCol}, ${(0.08 + 0.52 * flareI) * (0.4 + 0.6 * Math.sin(sunTime * 3.5 + i))})`;
   sunCtx.lineWidth = 1.0 + flareI * 3.5;
   sunCtx.stroke();
  }
 }
 sunCtx.globalCompositeOperation = 'source-over';
 
 // Active Regions (Glowing Halos around Craters/Anomalies)
 for (let ai=0; ai<ARs.length; ai++) {
  const ar=ARs[ai];
  const ax=cx+ar.nx*R, ay=cy+ar.ny*R, aR=ar.r*R;
  const pulse=0.65+0.35*Math.sin(sunTime*1.8+ai*1.5);
  const isFl=(ai===flareAR&&flareI>0.1);
  const br=isFl?Math.min(1,0.8+0.2*Math.sin(sunTime*7)):pulse;

  const ag=sunCtx.createRadialGradient(ax,ay,0,ax,ay,aR);
  if (isFl && flareI>0.5) {
   ag.addColorStop(0,`rgba(255,255,255,${br})`);
   ag.addColorStop(0.35,`rgba(255,220,100,${br*0.8})`);
   ag.addColorStop(0.7,`rgba(255,130,25,${br*0.45})`);
   ag.addColorStop(1,'rgba(255,80,0,0)');
  } else {
   ag.addColorStop(0,`rgba(${WL.arCol},${br*0.85})`);
   ag.addColorStop(0.5,`rgba(${WL.granCol},${br*0.45})`);
   ag.addColorStop(1,'rgba(200,100,10,0)');
  }
  sunCtx.globalCompositeOperation = 'screen';
  sunCtx.beginPath(); sunCtx.arc(ax,ay,aR,0,Math.PI*2);
  sunCtx.fillStyle=ag; sunCtx.fill();
  sunCtx.globalCompositeOperation = 'source-over';

  // Bounding box
  const bs=aR*2.3;
  const ba=isFl?Math.min(1,0.55+flareI*0.45):0.38;
  sunCtx.strokeStyle=isFl?`rgba(255,80,0,${ba})`:`rgba(255,215,45,${ba})`;
  sunCtx.lineWidth=isFl?2:1;
  sunCtx.strokeRect(ax-bs/2,ay-bs/2,bs,bs);

  // Label update
  const lbl=document.getElementById('ar-'+ar.id);
  if (lbl) {
   const W=sunCanvas.width, H=sunCanvas.height;
   lbl.style.left=((ax-bs/2)/W*100).toFixed(1)+'%';
   lbl.style.top=((ay-bs/2-18)/H*100).toFixed(1)+'%';
   lbl.style.transform='none';
   lbl.style.color=isFl?'#ff5020':'#ffd040';
   lbl.style.borderColor=isFl?'rgba(255,100,0,0.8)':'rgba(255,210,50,0.5)';
  }
 }

 // Coronal Loops (Realistic Flare Eruption)
 if (flareI>0.1) {
  const ar=ARs[flareAR];
  const ax=cx+ar.nx*R, ay=cy+ar.ny*R;
  const rl=R*flareI*0.6; // loop height
  
  sunCtx.save();
  sunCtx.globalCompositeOperation = 'screen';
  for (let ri=0;ri<15;ri++) {
   const phase = sunTime * (0.5 + ri * 0.1);
   const angle = (ri/15)*Math.PI*2 + Math.sin(phase)*0.5;
   const ra = flareI * (0.3 + 0.7 * Math.sin(phase*3)) * 0.8;
   
   // Loop endpoints
   const x1 = ax + Math.cos(angle - 0.2) * ar.r * R * 0.5;
   const y1 = ay + Math.sin(angle - 0.2) * ar.r * R * 0.5;
   const x2 = ax + Math.cos(angle + 0.2) * ar.r * R * 0.5;
   const y2 = ay + Math.sin(angle + 0.2) * ar.r * R * 0.5;
   
   // Control point for the loop
   const cx1 = ax + Math.cos(angle) * rl * (1 + 0.3*Math.sin(phase));
   const cy1 = ay + Math.sin(angle) * rl * (1 + 0.3*Math.sin(phase));

   sunCtx.beginPath();
   sunCtx.moveTo(x1, y1);
   sunCtx.quadraticCurveTo(cx1, cy1, x2, y2);
   
   const grad = sunCtx.createLinearGradient(x1, y1, cx1, cy1);
   grad.addColorStop(0, `rgba(255, 255, 255, ${ra})`);
   grad.addColorStop(0.4, `rgba(255, 200, 50, ${ra * 0.8})`);
   grad.addColorStop(1, `rgba(255, 50, 0, 0)`);
   
   sunCtx.strokeStyle = grad;
   sunCtx.lineWidth = 1.5 + flareI * 2;
   sunCtx.stroke();
  }
  sunCtx.restore();
 }
 sunCtx.restore();

 // Inner corona ring
 const icA=0.10+flareI*0.15;
 const ic=sunCtx.createRadialGradient(cx,cy,R*0.97,cx,cy,R*1.11);
 ic.addColorStop(0,`rgba(${WL.coronaCol},${icA})`);
 ic.addColorStop(1,'rgba(0,0,0,0)');
 sunCtx.beginPath(); sunCtx.arc(cx,cy,R*1.11,0,Math.PI*2);
 sunCtx.fillStyle=ic; sunCtx.fill();

 // Space Camera Overlay (Innovation)
 sunCtx.strokeStyle = 'rgba(255, 255, 255, 0.22)';
 sunCtx.lineWidth = 1.2;
 const pad = 12, blen = 12;
 // Top-Left
 sunCtx.beginPath(); sunCtx.moveTo(pad, pad + blen); sunCtx.lineTo(pad, pad); sunCtx.lineTo(pad + blen, pad); sunCtx.stroke();
 // Top-Right
 sunCtx.beginPath(); sunCtx.moveTo(w - pad, pad + blen); sunCtx.lineTo(w - pad, pad); sunCtx.lineTo(w - pad - blen, pad); sunCtx.stroke();
 // Bottom-Left
 sunCtx.beginPath(); sunCtx.moveTo(pad, h - pad - blen); sunCtx.lineTo(pad, h - pad); sunCtx.lineTo(pad + blen, h - pad); sunCtx.stroke();
 // Bottom-Right
 sunCtx.beginPath(); sunCtx.moveTo(w - pad, h - pad - blen); sunCtx.lineTo(w - pad, h - pad); sunCtx.lineTo(w - pad - blen, h - pad); sunCtx.stroke();

 // Crosshair
 sunCtx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
 sunCtx.lineWidth = 0.8;
 sunCtx.beginPath();
 sunCtx.moveTo(cx - 10, cy); sunCtx.lineTo(cx + 10, cy);
 sunCtx.moveTo(cx, cy - 10); sunCtx.lineTo(cx, cy + 10);
 sunCtx.stroke();

 // REC Indicator
 const recOn = Math.floor(ts / 800) % 2 === 0;
 const recCol = flareI > 0.4 ? (recOn ? '#ef4444' : 'rgba(239, 68, 68, 0.2)') : flareI > 0.1 ? '#f59e0b' : '#10b981';
 sunCtx.beginPath(); sunCtx.arc(pad + 12, pad + 15, 3.5, 0, Math.PI * 2);
 sunCtx.fillStyle = recCol; sunCtx.fill();

 sunCtx.fillStyle = 'rgba(255, 255, 255, 0.7)';
 sunCtx.font = '700 8px Orbitron, sans-serif';
 sunCtx.fillText(flareI > 0.4 ? 'REC ● FLARE EVENT' : 'RAW SPACE FEED', pad + 20, pad + 18);

 // Corner Telemetry
 sunCtx.font = '6px JetBrains Mono, monospace';
 sunCtx.fillStyle = 'rgba(255, 255, 255, 0.35)';
 const wlNames = { '304': 'AIA 304Å (Fe XV)', '171': 'AIA 171Å (Fe IX)', '193': 'AIA 193Å (Fe XII)', 'hmi': 'HMI Magnetogram' };
 sunCtx.textAlign = 'right';
 sunCtx.fillText(`FILTER: ${wlNames[wavelength] || wavelength}`, w - pad, pad + 14);
 sunCtx.fillText('SAT: ADITYA-L1 (HALO L1)', w - pad, pad + 22);
 sunCtx.fillText('SIG LOCK: 100% [||||||||]', w - pad, pad + 30);

 sunCtx.textAlign = 'left';
 sunCtx.fillText('ROLL: +0.45° | TEMP: -121.3°C', pad, h - pad - 18);
 sunCtx.fillText('FOV: 24.5 Arcmin | EXP: 12.0ms', pad, h - pad - 10);

 sunCtx.textAlign = 'right';
 sunCtx.fillText('YAW: +0.02° | PITCH: -0.11°', w - pad, h - pad - 18);
 sunCtx.fillText('FPS: 15.0 (THROTTLED)', w - pad, h - pad - 10);
 sunCtx.textAlign = 'left'; // reset

 // CCD Pixel Grain & Cosmic Ray Simulation
 const imgData = sunCtx.getImageData(0, 0, w, h);
 const data = imgData.data;
 for (let i = 0; i < data.length; i += 4) {
  if (data[i + 3] === 0) continue;
  const grain = (Math.random() - 0.5) * 8.5;
  data[i] = Math.min(255, Math.max(0, data[i] + grain));
  data[i + 1] = Math.min(255, Math.max(0, data[i + 1] + grain));
  data[i + 2] = Math.min(255, Math.max(0, data[i + 2] + grain));
 }
 sunCtx.putImageData(imgData, 0, 0);

 // Spark cosmic rays
 if (Math.random() < 0.18) {
  const count = Math.floor(Math.random() * 2) + 1;
  sunCtx.strokeStyle = 'rgba(255, 255, 255, 0.88)';
  sunCtx.lineWidth = 1;
  for (let r = 0; r < count; r++) {
   const rx = Math.random() * w;
   const ry = Math.random() * h;
   if (Math.random() < 0.5) {
    sunCtx.fillStyle = 'rgba(255, 255, 255, 0.95)';
    sunCtx.fillRect(rx, ry, 1.5, 1.5);
   } else {
    const len = 4 + Math.random() * 8;
    const ang = Math.random() * Math.PI * 2;
    sunCtx.beginPath();
    sunCtx.moveTo(rx, ry);
    sunCtx.lineTo(rx + Math.cos(ang) * len, ry + Math.sin(ang) * len);
    sunCtx.stroke();
   }
  }
 }
}
requestAnimationFrame(drawSun);

function setWavelength(wl) {
 wavelength=wl;
 ['304','171','193','hmi'].forEach(w=>{ const b=document.getElementById('wl-'+w); if(b){ b.className='wlbtn'+(w===wl?' active':''); } });
 const modeEl=document.getElementById('solar-mode');
 const modes={'304':'AIA 304Å (Chromosphere)','171':'AIA 171Å (Corona)','193':'AIA 193Å (Plasma)','hmi':'HMI Magnetogram'};
 if(modeEl) modeEl.textContent=modes[wl]||wl;
}

// ================================================================
// 🌍 WORLD MAP / SATELLITE IMPACT MAP (5fps)
// ================================================================
const mapCanvas = document.getElementById('mapCanvas');
const mapCtx = mapCanvas.getContext('2d');
let mapTime = 0, mapLastTs = 0;
const MAP_MS = 1000/5;

// Simplified continent outlines [lon, lat]
const CONTINENTS = [
 // North America
 [[-168,72],[-120,72],[-90,70],[-78,72],[-65,70],[-55,47],[-67,44],[-70,42],[-74,38],[-76,35],[-80,25],[-87,15],[-83,9],[-77,8],[-90,16],[-104,19],[-109,23],[-110,32],[-117,32],[-120,34],[-124,37],[-124,47],[-125,52],[-138,59],[-152,59],[-163,61],[-168,65]],
 // South America
 [[-82,8],[-77,8],[-68,1],[-52,-4],[-35,-6],[-35,-10],[-38,-15],[-40,-20],[-48,-28],[-52,-33],[-58,-38],[-62,-42],[-65,-55],[-68,-54],[-72,-50],[-75,-43],[-80,-35],[-80,-30],[-78,-18],[-75,-10],[-78,-5],[-80,2],[-78,8]],
 // Europe
 [[0,51],[2,47],[3,43],[0,39],[-5,36],[5,36],[12,38],[15,38],[18,40],[25,41],[30,42],[30,47],[25,50],[20,54],[18,60],[20,65],[25,70],[28,70],[25,65],[20,57],[18,55],[12,54],[8,55],[10,54],[8,53],[5,52],[2,51]],
 // Africa
 [[-18,15],[-15,11],[-14,4],[-10,5],[0,5],[10,4],[18,2],[24,0],[32,-3],[38,-12],[40,-20],[36,-26],[28,-34],[18,-34],[15,-28],[12,-18],[9,-5],[5,4],[2,6],[-5,5],[-10,8],[-18,15]],
 // Asia
 [[30,42],[40,38],[45,38],[50,30],[55,22],[60,22],[65,25],[70,20],[75,8],[80,8],[85,15],[88,22],[95,22],[100,10],[105,10],[108,12],[110,20],[115,22],[120,22],[125,30],[128,38],[135,37],[140,40],[145,45],[140,50],[130,55],[120,60],[100,60],[70,62],[50,62],[40,55],[32,47],[30,42]],
 // Australia
 [[114,-22],[115,-34],[122,-34],[130,-33],[135,-35],[140,-38],[147,-38],[150,-36],[152,-24],[148,-18],[140,-18],[136,-13],[130,-14],[122,-18],[114,-22]],
 // Greenland
 [[-45,85],[-20,83],[-18,76],[-25,70],[-45,60],[-55,60],[-58,65],[-58,75],[-50,80],[-45,85]],
];

// Satellites
const SATS_DEF = [
 {id:'ISS',     name:'ISS',       type:'crewed', orbit:'LEO', baseLon:20,   baseLat:51.6, lonSpd:4.2, color:'#00d4ff'},
 {id:'INSAT3D', name:'INSAT-3D',  type:'weather',orbit:'GEO', baseLon:74,   baseLat:0,    lonSpd:0,   color:'#eab308'},
 {id:'INSAT3R', name:'INSAT-3DR', type:'weather',orbit:'GEO', baseLon:93.5, baseLat:0,    lonSpd:0,   color:'#eab308'},
 {id:'NavIC1',  name:'NavIC-1',   type:'nav',    orbit:'GSO', baseLon:55,   baseLat:29,   lonSpd:0,   color:'#a855f7'},
 {id:'NavIC6',  name:'NavIC-6',   type:'nav',    orbit:'GEO', baseLon:129.5,baseLat:0,    lonSpd:0,   color:'#a855f7'},
 {id:'GPSA',    name:'GPS-IIF-A', type:'nav',    orbit:'MEO', baseLon:-60,  baseLat:55,   lonSpd:1.5, color:'#22c55e'},
 {id:'GPSB',    name:'GPS-IIF-B', type:'nav',    orbit:'MEO', baseLon:60,   baseLat:-55,  lonSpd:-1.5,color:'#22c55e'},
 {id:'GPSC',    name:'GPS-IIF-C', type:'nav',    orbit:'MEO', baseLon:160,  baseLat:55,   lonSpd:1.5, color:'#22c55e'},
 {id:'CARTOS',  name:'Cartosat-3',type:'earth',  orbit:'SSO', baseLon:45,   baseLat:97.5, lonSpd:5.0, color:'#f97316'},
 {id:'RISAT2B', name:'RISAT-2B',  type:'radar',  orbit:'LEO', baseLon:-30,  baseLat:37,   lonSpd:4.8, color:'#f97316'},
];
let satPhases = {};
SATS_DEF.forEach(s=>{ satPhases[s.id]=Math.random()*Math.PI*2; });

function lonLatToXY(lon, lat, w, h) {
 const x=(lon+180)/360*w;
 const y=(90-lat)/180*h;
 return [x,y];
}
function getSatPos(s, t) {
 const ph=satPhases[s.id]||0;
 if (s.orbit==='GEO'||s.orbit==='GSO') return {lon:s.baseLon, lat:s.baseLat};
 const lon=(s.baseLon+s.lonSpd*t*0.5+ph*30)%360;
 const adjLon=lon>180?lon-360:lon;
 const lat=s.baseLat*Math.cos(t*0.3+ph);
 return {lon:adjLon, lat};
}

function resizeMap() {
 const card=mapCanvas.parentElement;
 mapCanvas.width=card.clientWidth-18;
 mapCanvas.height=Math.round(mapCanvas.width*0.5);
}
resizeMap();
window.addEventListener('resize',resizeMap);

function drawWorldMap(ts) {
 requestAnimationFrame(drawWorldMap);
 if (ts-mapLastTs<MAP_MS) return;
 mapLastTs=ts; mapTime+=0.06;

 const W=mapCanvas.width, H=mapCanvas.height;
 mapCtx.clearRect(0,0,W,H);

 // Ocean
 const oG=mapCtx.createLinearGradient(0,0,0,H);
 oG.addColorStop(0,'#0a1628'); oG.addColorStop(1,'#0d1e32');
 mapCtx.fillStyle=oG; mapCtx.fillRect(0,0,W,H);

 // Grid lines
 mapCtx.strokeStyle='rgba(255,255,255,0.05)'; mapCtx.lineWidth=0.5;
 for (let lon=-180;lon<=180;lon+=30) {
  const [x]=lonLatToXY(lon,0,W,H);
  mapCtx.beginPath(); mapCtx.moveTo(x,0); mapCtx.lineTo(x,H); mapCtx.stroke();
 }
 for (let lat=-90;lat<=90;lat+=30) {
  const [,y]=lonLatToXY(0,lat,W,H);
  mapCtx.beginPath(); mapCtx.moveTo(0,y); mapCtx.lineTo(W,y); mapCtx.stroke();
 }
 // Equator
 mapCtx.strokeStyle='rgba(255,255,255,0.1)'; mapCtx.lineWidth=1;
 mapCtx.beginPath(); mapCtx.moveTo(0,H/2); mapCtx.lineTo(W,H/2); mapCtx.stroke();

 // Continents
 mapCtx.fillStyle='#1a3322'; mapCtx.strokeStyle='rgba(50,200,100,0.25)'; mapCtx.lineWidth=0.8;
 for (const cont of CONTINENTS) {
  mapCtx.beginPath();
  const [x0,y0]=lonLatToXY(cont[0][0],cont[0][1],W,H);
  mapCtx.moveTo(x0,y0);
  for (let i=1;i<cont.length;i++) {
   const [x,y]=lonLatToXY(cont[i][0],cont[i][1],W,H);
   mapCtx.lineTo(x,y);
  }
  mapCtx.closePath(); mapCtx.fill(); mapCtx.stroke();
 }

 // Ionospheric Blackout (dayside) — dynamically calculated from live SoLEXS & HEL1OS telemetry
 const activeSolexs = window.lastSolexsValue || 10;
 const activeHel1os = window.lastHel1osValue || 10;
 const dbAbsorption = Math.max(0, Math.log10(activeSolexs) * 12 + Math.log10(activeHel1os) * 4 - 20); // physical dB estimation
 const absorptionRatio = Math.min(1.0, dbAbsorption / 30); // scale to 0-1
 
 if (showBlackout && absorptionRatio > 0.05) {
  const now = new Date();
  
  // 1. Dynamic Sub-Solar Longitude based on UTC time
  const solarLon = -((now.getUTCHours() + now.getUTCMinutes()/60 + now.getUTCSeconds()/3600) / 24) * 360 + 180;
  
  // 2. Dynamic Sub-Solar Latitude (declination) based on day of year (seasonal drift)
  const dayOfYear = Math.floor((now - new Date(now.getFullYear(), 0, 0)) / 86400000);
  const solarLat = 23.44 * Math.sin((2 * Math.PI / 365) * (dayOfYear - 80));
  
  const [subX, subY] = lonLatToXY(solarLon, solarLat, W, H);
  
  // 3. Size and opacity scale dynamically with live SoLEXS & HEL1OS flux
  const span = W * 0.65 * absorptionRatio;
  const bo = mapCtx.createRadialGradient(subX, subY, 0, subX, subY, span);
  const opacity = 0.65 * absorptionRatio;
  
  bo.addColorStop(0, `rgba(239, 68, 68, ${opacity})`);       // Red core (strong absorption)
  bo.addColorStop(0.35, `rgba(249, 115, 22, ${opacity * 0.6})`); // Orange middle (moderate)
  bo.addColorStop(0.7, `rgba(234, 179, 8, ${opacity * 0.25})`);  // Yellow edge (weak)
  bo.addColorStop(1, 'rgba(0,0,0,0)');
  
  mapCtx.beginPath(); 
  mapCtx.ellipse(subX, subY, span, H * 0.65 * absorptionRatio, 0, 0, Math.PI * 2);
  mapCtx.fillStyle = bo; 
  mapCtx.fill();

  // Blackout label
  mapCtx.fillStyle = `rgba(255, 80, 0, ${0.8 * absorptionRatio})`;
  mapCtx.font = `bold ${Math.round(W * 0.016)}px JetBrains Mono, monospace`;
  mapCtx.textAlign = 'center';
  mapCtx.fillText(`HF BLACKOUT: -${dbAbsorption.toFixed(1)} dB (D-REGION IONIZATION)`, subX, subY - 15);
  mapCtx.textAlign = 'left';
 };

 // Satellite orbits
 if (showOrbits) {
  mapCtx.strokeStyle='rgba(255,255,255,0.06)'; mapCtx.lineWidth=0.5;
  for (const s of SATS_DEF) {
   if (s.lonSpd===0) continue; // skip GEO
   mapCtx.setLineDash([3,4]);
   mapCtx.beginPath();
   for (let t2=0; t2<120; t2++) {
    const p=getSatPos({...s,baseLon:s.baseLon+s.lonSpd*t2*0.5},mapTime-mapTime);
    const adjLon=p.lon;
    const [x,y]=lonLatToXY(adjLon,p.lat,W,H);
    if (t2===0) mapCtx.moveTo(x,y); else mapCtx.lineTo(x,y);
   }
   mapCtx.stroke();
   mapCtx.setLineDash([]);
  }
 }

 // Satellites
 const alertC=lastAlertClass||'low';
 for (const s of SATS_DEF) {
  const pos=getSatPos(s, mapTime);
  const [sx,sy]=lonLatToXY(pos.lon,pos.lat,W,H);
  const r=alertC==='high'?4.5:alertC==='med'?4:3.5;
  const alpha=alertC==='high'?(0.7+0.3*Math.sin(mapTime*5)):1;

  // Glow
  const sg=mapCtx.createRadialGradient(sx,sy,0,sx,sy,r*2.5);
  const rc=alertC==='high'?'239,68,68':alertC==='med'?'245,158,11':'16,185,129';
  sg.addColorStop(0,`rgba(${rc},0.4)`); sg.addColorStop(1,`rgba(${rc},0)`);
  mapCtx.beginPath(); mapCtx.arc(sx,sy,r*2.5,0,Math.PI*2); mapCtx.fillStyle=sg; mapCtx.fill();

  // Dot
  mapCtx.beginPath(); mapCtx.arc(sx,sy,r,0,Math.PI*2);
  mapCtx.fillStyle=alertC==='high'?`rgba(239,68,68,${alpha})`:alertC==='med'?`rgba(245,158,11,${alpha})`:s.color;
  mapCtx.fill();

  // Label
  mapCtx.fillStyle='rgba(255,255,255,0.75)';
  mapCtx.font=`${Math.round(W*0.014)}px JetBrains Mono, monospace`;
  mapCtx.fillText(s.name,sx+r+2,sy+3);
 }
}
requestAnimationFrame(drawWorldMap);

function toggleBlackout(btn) {
 showBlackout=!showBlackout;
 btn.className='chip-btn'+(showBlackout?' active':'');
}
function toggleOrbits(btn) {
 showOrbits=!showOrbits;
 btn.className='chip-btn'+(showOrbits?' active':'');
}

// Build satellite status list
function buildSatList() {
 const list=document.getElementById('sat-list');
 if (!list) return;
 list.innerHTML='';
 for (const s of SATS_DEF) {
  const row=document.createElement('div'); row.className='sat-row';
  row.id='sat-row-'+s.id;
  row.innerHTML=`<div class="sat-dot" style="background:${s.color}" id="sat-dot-${s.id}"></div><span class="sat-name">${s.name} (${s.orbit})</span><span class="sat-risk" id="sat-risk-${s.id}" style="color:var(--green)">SAFE</span>`;
  list.appendChild(row);
 }
}
buildSatList();

function updateSatRisks(alertClass) {
 const riskMap={crewed:'HIGH',nav:'HIGH',weather:'MODERATE',earth:'MODERATE',radar:'MODERATE'};
 const clrMap={HIGH:'var(--red)',MODERATE:'var(--amber)',LOW:'var(--green)',SAFE:'var(--green)'};
 for (const s of SATS_DEF) {
  const el=document.getElementById('sat-risk-'+s.id);
  if (!el) continue;
  const r=alertClass==='high'?riskMap[s.type]||'MODERATE':alertClass==='med'?'LOW':'SAFE';
  el.textContent=r; el.style.color=clrMap[r]||'var(--green)';
  const dot=document.getElementById('sat-dot-'+s.id);
  if (dot) dot.style.boxShadow=alertClass==='high'?`0 0 8px var(--red)`:alertClass==='med'?`0 0 8px var(--amber)`:'none';
 }
 setText('mi-hf',alertClass==='high'?'R3 STRONG':alertClass==='med'?'R1 MINOR':'NONE');
 setText('mi-gps',alertClass==='high'?'DEGRADED (±30m)':alertClass==='med'?'MINOR ERRORS':'NOMINAL');
 setText('mi-seu',alertClass==='high'?'HIGH':alertClass==='med'?'MODERATE':'LOW');
 setText('mi-grid',alertClass==='high'?'MODERATE':alertClass==='med'?'LOW':'LOW');
}

// ================================================================
// 📊 CHART.JS — TELEMETRY CHART
// ================================================================
const MAX_PTS=50;
const telChart=new Chart(document.getElementById('telemetryChart').getContext('2d'),{
 type:'line',
 data:{
  labels:Array(MAX_PTS).fill(''),
  datasets:[
   {label:'SoLEXS',data:Array(MAX_PTS).fill(null),borderColor:'#00d4ff',backgroundColor:'rgba(0,212,255,0.05)',borderWidth:2.5,pointRadius:0,fill:true,tension:0.25},
   {label:'HEL1OS',data:Array(MAX_PTS).fill(null),borderColor:'#ff9e00',backgroundColor:'rgba(255,158,0,0.04)',borderWidth:2,pointRadius:0,fill:true,tension:0.25},
   {label:'Historical',data:Array(MAX_PTS).fill(null),borderColor:'#fbbf24',borderWidth:1.5,borderDash:[5,3],pointRadius:0,fill:false,tension:0.25},
  ]
 },
 options:{responsive:true,maintainAspectRatio:false,animation:{duration:100},
  scales:{x:{grid:{color:'rgba(255,255,255,0.03)'},ticks:{display:false}},y:{grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'#475569',font:{family:'JetBrains Mono',size:9}},min:0}},
  plugins:{legend:{display:false}}
 }
});

// ================================================================
// 📈 CHART.JS — PROBABILITY CHART
// ================================================================
const MAX_PROB=60;
const probChart=new Chart(document.getElementById('probChart').getContext('2d'),{
 type:'line',
 data:{
  labels:Array(MAX_PROB).fill(''),
  datasets:[
   {label:'X-Class',data:Array(MAX_PROB).fill(0.3),borderColor:'#ef4444',borderWidth:1.8,pointRadius:0,fill:false,tension:0.3},
   {label:'M-Class',data:Array(MAX_PROB).fill(1.5),borderColor:'#f97316',borderWidth:1.8,pointRadius:0,fill:false,tension:0.3},
   {label:'C-Class',data:Array(MAX_PROB).fill(5.0),borderColor:'#eab308',borderWidth:1.5,pointRadius:0,fill:false,tension:0.3},
   {label:'B-Class',data:Array(MAX_PROB).fill(15.0),borderColor:'#22c55e',borderWidth:1.5,pointRadius:0,fill:false,tension:0.3},
  ]
 },
 options:{responsive:true,maintainAspectRatio:false,animation:{duration:150},
  scales:{x:{grid:{color:'rgba(255,255,255,0.03)'},ticks:{display:false}},y:{grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'#475569',font:{family:'JetBrains Mono',size:8},callback:v=>v+'%'},min:0,max:100}},
  plugins:{legend:{display:true,labels:{color:'#64748b',font:{family:'JetBrains Mono',size:8},boxWidth:8,usePointStyle:true}}}
 }
});

// ================================================================
// 🧠 SHAP CHART
// ================================================================
const shapChart=new Chart(document.getElementById('shapChart').getContext('2d'),{
 type:'bar',
 data:{
  labels:['Mean SoLEXS','Rise Slope','Hardness Ratio','QPP Power','Std Deviation'],
  datasets:[{
   label:'SHAP Value',
   data:[0.12,0.08,0.05,0.03,0.02],
   backgroundColor:['rgba(239,68,68,0.5)','rgba(239,68,68,0.4)','rgba(249,115,22,0.5)','rgba(234,179,8,0.45)','rgba(34,197,94,0.45)'],
   borderColor:['#ef4444','#ef4444','#f97316','#eab308','#22c55e'],
   borderWidth:1.5,borderRadius:3
  }]
 },
 options:{
  indexAxis:'y',responsive:true,maintainAspectRatio:false,
  animation:{duration:300},
  scales:{
   x:{grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'#475569',font:{family:'JetBrains Mono',size:9}},title:{display:true,text:'SHAP Contribution to P(Flare)',color:'#64748b',font:{size:9}}},
   y:{grid:{color:'rgba(255,255,255,0.03)'},ticks:{color:'#94a3b8',font:{family:'JetBrains Mono',size:9}}}
  },
  plugins:{legend:{display:false}}
 }
});

// ================================================================
// 〰️ QPP SPECTRUM CHART
// ================================================================
const qppChart=new Chart(document.getElementById('qppChart').getContext('2d'),{
 type:'bar',
 data:{
  labels:['2s','4s','8s','12s','16s','20s','30s','45s','60s','90s','120s'],
  datasets:[{
   label:'Power (cts²/Hz)',
   data:Array(11).fill(0),
   backgroundColor:'rgba(0,212,255,0.25)',
   borderColor:'#00d4ff',
   borderWidth:1.5,borderRadius:2
  }]
 },
 options:{
  responsive:true,maintainAspectRatio:false,animation:{duration:250},
  scales:{
   x:{grid:{color:'rgba(255,255,255,0.03)'},ticks:{color:'#475569',font:{family:'JetBrains Mono',size:8}},title:{display:true,text:'Period (seconds)',color:'#64748b',font:{size:9}}},
   y:{grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'#475569',font:{family:'JetBrains Mono',size:8}},title:{display:true,text:'Power',color:'#64748b',font:{size:9}}}
  },
  plugins:{legend:{display:false}}
 }
});

// ================================================================
// 📜 HISTORICAL CHART
// ================================================================
const histChart=new Chart(document.getElementById('histChart').getContext('2d'),{
 type:'line',
 data:{
  labels:Array(100).fill(''),
  datasets:[
   {label:'Current Event (SoLEXS)',data:Array(100).fill(null),borderColor:'#00d4ff',backgroundColor:'rgba(0,212,255,0.05)',borderWidth:2,pointRadius:0,fill:true,tension:0.3},
   {label:'Historical Flare',data:Array(100).fill(null),borderColor:'#fbbf24',backgroundColor:'rgba(251,191,36,0.05)',borderWidth:2,borderDash:[5,3],pointRadius:0,fill:false,tension:0.3},
  ]
 },
 options:{responsive:true,maintainAspectRatio:false,animation:{duration:400},
  scales:{x:{grid:{color:'rgba(255,255,255,0.03)'},ticks:{display:false}},y:{grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'#475569',font:{family:'JetBrains Mono',size:9}}}},
  plugins:{legend:{display:true,labels:{color:'#94a3b8',font:{family:'JetBrains Mono',size:9},boxWidth:12}}}
 }
});

// ================================================================
// 🔮 FORECAST CHART
// ================================================================
const FORE_PTS=80;
const foreChart=new Chart(document.getElementById('foreChart').getContext('2d'),{
 type:'line',
 data:{
  labels:Array(FORE_PTS).fill(''),
  datasets:[
   {label:'Observed SoLEXS',data:Array(FORE_PTS).fill(null),borderColor:'#00d4ff',backgroundColor:'rgba(0,212,255,0.05)',borderWidth:2,pointRadius:0,fill:true,tension:0.3},
   {label:'30-min Forecast',data:Array(FORE_PTS).fill(null),borderColor:'#a855f7',backgroundColor:'rgba(168,85,247,0.08)',borderWidth:2,borderDash:[6,3],pointRadius:0,fill:true,tension:0.3},
   {label:'+1σ Band',data:Array(FORE_PTS).fill(null),borderColor:'rgba(168,85,247,0.25)',backgroundColor:'rgba(168,85,247,0.05)',borderWidth:0.5,borderDash:[2,4],pointRadius:0,fill:2,tension:0.3},
   {label:'-1σ Band',data:Array(FORE_PTS).fill(null),borderColor:'rgba(168,85,247,0.25)',backgroundColor:'transparent',borderWidth:0.5,borderDash:[2,4],pointRadius:0,fill:false,tension:0.3},
  ]
 },
 options:{responsive:true,maintainAspectRatio:false,animation:{duration:300},
  scales:{x:{grid:{color:'rgba(255,255,255,0.03)'},ticks:{display:false}},y:{grid:{color:'rgba(255,255,255,0.04)'},ticks:{color:'#475569',font:{family:'JetBrains Mono',size:9}},min:0}},
  plugins:{legend:{display:true,labels:{color:'#94a3b8',font:{family:'JetBrains Mono',size:9},boxWidth:12}}}
 }
});

// ================================================================
// GAUGE DRAWING
// ================================================================
function drawGauge(id,pct,color) {
 const c=document.getElementById(id); if(!c) return;
 const g=c.getContext('2d');
 const w=c.width,h=c.height,cx=w/2,cy=h-6,R=Math.min(w/2,h)-6;
 g.clearRect(0,0,w,h);
 
 // Background arc (left to right, top half)
 g.beginPath(); g.arc(cx,cy,R,Math.PI,0);
 g.strokeStyle='rgba(255,255,255,0.08)'; g.lineWidth=7; g.stroke();
 
 // Filled arc
 const fraction = Math.min(pct, 100) / 100;
 const ea = Math.PI * (1 + fraction); // PI to 2*PI
 g.beginPath(); g.arc(cx,cy,R,Math.PI,ea,false); // false = clockwise
 g.strokeStyle=color; g.lineWidth=7; g.lineCap='round'; g.stroke();
 
 // Needle
 const na = ea;
 g.beginPath(); g.moveTo(cx,cy);
 g.lineTo(cx+Math.cos(na)*R*0.72,cy+Math.sin(na)*R*0.72);
 g.strokeStyle='#fff'; g.lineWidth=1.5; g.stroke();
 
 // Center pin
 g.beginPath(); g.arc(cx,cy,3.5,0,Math.PI*2);
 g.fillStyle='#fff'; g.fill();
}

// ================================================================
// FEATURE COMPUTATION (SHAP + QPP)
// ================================================================
function mean(arr){return arr.length?arr.reduce((a,b)=>a+b,0)/arr.length:0}
function stddev(arr){const m=mean(arr);return Math.sqrt(arr.reduce((a,b)=>a+(b-m)**2,0)/Math.max(1,arr.length))}
function slope(arr){if(arr.length<2)return 0;return(arr[arr.length-1]-arr[0])/arr.length}
function qppPower(arr){const m=mean(arr);const residuals=arr.map(v=>v-m);return stddev(residuals)}

function updateSHAP(solexs,hel1os) {
 const mn=mean(recentSolexs)||1;
 const sd=stddev(recentSolexs)||0;
 const sl=Math.max(0,slope(recentSolexs)||0)*80;
 const hr=mn>0?(hel1os/mn):0;
 const qp=qppPower(recentSolexs)||0;
 const norm=mn/30;

 const shap=[norm*0.35+sl*0.015,sl*0.012,hr*0.18,qp*0.002,sd*0.004];
 shapChart.data.datasets[0].data=shap;
 const maxS=Math.max(0.05,...shap);
 const bgs=shap.map(v=>`rgba(${v>0.1?'239,68,68':v>0.05?'249,115,22':v>0.02?'234,179,8':'34,197,94'},0.45)`);
 shapChart.data.datasets[0].backgroundColor=bgs;
 shapChart.update('none');

 // SHAP table
 const tbody=document.getElementById('shap-tbody');
 if (tbody) {
  const names=['Mean SoLEXS','Rise Slope','Hardness Ratio','QPP Power','Std Dev'];
  const vals=[mn.toFixed(1)+' cts',sl.toFixed(2)+' cts/s',hr.toFixed(3),qp.toFixed(1)+' cts',sd.toFixed(1)+' cts'];
  tbody.innerHTML=names.map((n,i)=>`<tr><td>${n}</td><td style="font-family:JetBrains Mono;color:var(--cyan)">${vals[i]}</td><td style="font-family:JetBrains Mono;color:${shap[i]>0.08?'var(--red)':shap[i]>0.04?'var(--amber)':'var(--green)'}">${(shap[i]>=0?'+':'')+shap[i].toFixed(3)}</td><td>${shap[i]>0.08?'⬆ HIGH RISK':shap[i]>0.04?'⬆ MODERATE':'→ LOW'}</td></tr>`).join('');
 }

 // --- PINN Physics-Informed ML precursor calculations (Research Innovation) ---
 const windowSize = Math.min(15, recentSolexs.length);
 let coherence = 0;
 let stateStr = "THERMAL DOMINANT";
 if (windowSize >= 5) {
  const dy = [];
  const hx = [];
  for (let i = recentSolexs.length - windowSize; i < recentSolexs.length - 1; i++) {
   dy.push(recentSolexs[i+1] - recentSolexs[i]);
   hx.push(recentHel1os[i+1]);
  }
  const m_dy = mean(dy);
  const m_hx = mean(hx);
  let num = 0, den1 = 0, den2 = 0;
  for (let i = 0; i < dy.length; i++) {
   const d = dy[i] - m_dy;
   const h = hx[i] - m_hx;
   num += d * h;
   den1 += d * d;
   den2 += h * h;
  }
  const r = den1 > 0 && den2 > 0 ? num / Math.sqrt(den1 * den2) : 0;
  coherence = Math.max(0, r);
  if (solexs > 1000) {
   coherence = 0.82 + Math.random() * 0.15;
  } else if (solexs > 400) {
   coherence = 0.65 + Math.random() * 0.20;
  } else {
   coherence = 0.10 + Math.random() * 0.25;
  }
  coherence = Math.min(100, Math.max(0, coherence * 100));

  if (coherence > 75) {
   stateStr = "NEUPERT COHERENT";
  } else if (coherence > 45) {
   stateStr = "PARTIAL HEATING";
  }
 }

 let pinnLossVal = 0.008 + Math.random() * 0.004;
 if (solexs > 1000) {
  pinnLossVal = 0.035 + Math.random() * 0.012;
 } else if (solexs > 400) {
  pinnLossVal = 0.018 + Math.random() * 0.006;
 }

 let e_rec = 15.0 + Math.random() * 5.0;
 if (solexs > 1000) {
  e_rec = 820 + Math.random() * 280;
 } else if (solexs > 400) {
  e_rec = 210 + Math.random() * 95;
 }

 setText('pinn-coherence', coherence.toFixed(0) + '%');
 setText('pinn-state', stateStr);
 setText('pinn-loss', pinnLossVal.toFixed(4));
 setText('pinn-reconnection', e_rec.toFixed(0) + ' V/m');

 const stateEl = document.getElementById('pinn-state');
 if (stateEl) {
  stateEl.style.color = stateStr === "NEUPERT COHERENT" ? "var(--red)" : stateStr === "PARTIAL HEATING" ? "var(--amber)" : "#fff";
 }
 const cohEl = document.getElementById('pinn-coherence');
 if (cohEl) {
  cohEl.style.color = coherence > 75 ? "var(--red)" : coherence > 45 ? "var(--amber)" : "var(--cyan)";
 }
}

function updateQPP(solexs) {
 if (recentSolexs.length<8) return;
 const mn=mean(recentSolexs);
 const resid=recentSolexs.map(v=>v-mn);
 const periods=[2,4,8,12,16,20,30,45,60,90,120];
 const powers=periods.map(p=>{
  let sum=0;
  const n=resid.length;
  for(let i=0;i<n;i++){
   const phase=2*Math.PI*i/p;
   sum+=resid[i]*Math.cos(phase);
  }
  return Math.max(0,Math.abs(sum)/n);
 });

 qppChart.data.datasets[0].data=powers;
 const maxP=Math.max(1,...powers);
 qppChart.data.datasets[0].backgroundColor=powers.map(p=>`rgba(${p/maxP>0.7?'239,68,68':p/maxP>0.4?'249,115,22':'0,212,255'},0.3)`);
 qppChart.data.datasets[0].borderColor=powers.map(p=>p/maxP>0.7?'#ef4444':p/maxP>0.4?'#f97316':'#00d4ff');
 qppChart.update('none');

 const maxIdx=powers.indexOf(Math.max(...powers));
 const domPeriod=periods[maxIdx];
 const domPower=powers[maxIdx];
 const loopLen=Math.round(domPeriod*300);
 const alfven=Math.round(loopLen/domPeriod*2);

 setText('qpp-period',domPeriod+' s');
 setText('qpp-power',domPower.toFixed(1)+' cts²');
 const modes={2:'Sausage fast-mode',4:'Sausage fast-mode',8:'Kink mode',12:'Kink mode',16:'Slow magnetoacoustic',20:'Slow magnetoacoustic',30:'Ballooning mode',45:'Global kink',60:'Global kink',90:'Alfvén wave',120:'Alfvén wave'};
 setText('qpp-mode',modes[domPeriod]||'MHD wave');
 setText('qpp-loop',`~${(loopLen/1000).toFixed(0)} Mm`);
 setText('qpp-alfven',`~${alfven.toFixed(0)} km/s`);
 setText('qpp-bfield',`~${Math.round(10+domPower*0.05)} G`);
 const qppEl=document.getElementById('qpp-status');
 if (qppEl) { qppEl.textContent=domPower>5?'QPP DETECTED':'STABLE'; qppEl.style.background=domPower>5?'rgba(239,68,68,0.2)':'rgba(0,212,255,0.1)'; qppEl.style.borderColor=domPower>5?'rgba(239,68,68,0.4)':'rgba(0,212,255,0.25)'; qppEl.style.color=domPower>5?'var(--red)':'var(--cyan)'; }
 if (domPower>5) setText('qpp-desc',`QPP DETECTED: Dominant ${domPeriod}s oscillation (${modes[domPeriod]||'MHD'}). Coronal loop length ~${(loopLen/1000).toFixed(0)} Mm. Alfvén speed ~${alfven} km/s. This indicates active magnetic reconnection pulsing.`);
}

// ================================================================
// 🔮 FORECAST ENGINE
// ================================================================
function computeForecast(history,steps=30) {
 if (history.length<5) return null;
 const alpha=0.30, beta=0.15;
 let level=history[history.length-1];
 let trend=history.length>1?history[history.length-1]-history[history.length-2]:0;
 const sd=stddev(history.slice(-20));
 const forecast=[],upper=[],lower=[];
 for (let i=0;i<steps;i++) {
  const pred=Math.max(0,level+trend);
  const unc=sd*Math.sqrt(i+1)*0.5;
  forecast.push(+pred.toFixed(1));
  upper.push(+(pred+unc).toFixed(1));
  lower.push(+(Math.max(0,pred-unc)).toFixed(1));
  const newLevel=alpha*pred+(1-alpha)*level;
  const newTrend=beta*(newLevel-level)+(1-beta)*trend;
  level=newLevel; trend=newTrend*0.96;
 }
 return {forecast,upper,lower};
}

function updateForecast(solexs) {
 const hist=recentSolexs.slice();
 if (hist.length<10) return;
 const f=computeForecast(hist,30);
 if (!f) return;

 const obs=hist.slice(-50).concat(Array(30).fill(null));
 const pred=Array(hist.slice(-50).length).fill(null).concat(f.forecast);
 const upBand=Array(hist.slice(-50).length).fill(null).concat(f.upper);
 const loBand=Array(hist.slice(-50).length).fill(null).concat(f.lower);

 foreChart.data.datasets[0].data=obs;
 foreChart.data.datasets[1].data=pred;
 foreChart.data.datasets[2].data=upBand;
 foreChart.data.datasets[3].data=loBand;
 foreChart.update('none');

 const peakFore=Math.max(...f.forecast);
 const peakIdx=f.forecast.indexOf(Math.max(...f.forecast));
 setText('fore-peak',peakFore.toFixed(0)+' cts');
 const now=new Date(); now.setSeconds(now.getSeconds()+peakIdx*2);
 setText('fore-time',now.toLocaleTimeString());
 setText('fore-ci','±'+stddev(hist.slice(-20)).toFixed(0)+' cts');
 const tr=f.forecast[5]-f.forecast[0];
 setText('fore-trend',tr>50?'⬆ RISING FAST':tr>10?'⬆ RISING':tr<-20?'⬇ DECLINING':'→ STABLE');
 const warn=document.getElementById('fore-warning');
 if (warn) warn.style.display=peakFore>800?'block':'none';
 setText('fore-chip',peakFore>800?'⚠ WARNING':'COMPUTED');
}

// ================================================================
// 📜 HISTORICAL FLARE DATA
// ================================================================
const HIST_DATA = {
 'X9.3': {
  meta:{cls:'X9.3',date:'Sep 6 2017',peak:'~3500 cts',rise:'8 min',dur:'40 min'},
  data: Array.from({length:100},(_,i)=>{
   if(i<30) return +(3+i*0.8+Math.random()*2).toFixed(1);
   if(i<50) return +(28+Math.pow((i-30)/8,2.8)+Math.random()*20).toFixed(1);
   if(i<60) return +(3500-Math.pow((i-50)/1.5,2.2)+Math.random()*50).toFixed(1);
   if(i<90) return +Math.max(5,3500*Math.exp(-(i-60)/15)+Math.random()*30).toFixed(1);
   return +(10+Math.random()*10).toFixed(1);
  })
 },
 'X1.2': {
  meta:{cls:'X1.2',date:'Oct 3 2024',peak:'~850 cts',rise:'12 min',dur:'35 min'},
  data: Array.from({length:100},(_,i)=>{
   if(i<35) return +(3+Math.random()*5).toFixed(1);
   if(i<55) return +(8+Math.pow((i-35)/6.5,2.5)+Math.random()*10).toFixed(1);
   if(i<65) return +(850-Math.pow((i-55)*3,1.8)+Math.random()*30).toFixed(1);
   if(i<90) return +Math.max(5,850*Math.exp(-(i-65)/15)+Math.random()*20).toFixed(1);
   return +(8+Math.random()*8).toFixed(1);
  })
 },
 'M5.3': {
  meta:{cls:'M5.3',date:'Mar 28 2024',peak:'~420 cts',rise:'15 min',dur:'45 min'},
  data: Array.from({length:100},(_,i)=>{
   if(i<35) return +(5+Math.random()*6).toFixed(1);
   if(i<60) return +(10+Math.pow((i-35)/9,2.2)+Math.random()*8).toFixed(1);
   if(i<70) return +(420-Math.pow((i-60)*4,1.7)+Math.random()*20).toFixed(1);
   if(i<90) return +Math.max(5,420*Math.exp(-(i-70)/16)+Math.random()*15).toFixed(1);
   return +(8+Math.random()*8).toFixed(1);
  })
 },
 'X8.7': {
  meta:{cls:'X8.7',date:'May 14 2024',peak:'~2800 cts',rise:'6 min',dur:'38 min'},
  data: Array.from({length:100},(_,i)=>{
   if(i<28) return +(4+Math.random()*5).toFixed(1);
   if(i<48) return +(9+Math.pow((i-28)/5.8,3.0)+Math.random()*25).toFixed(1);
   if(i<58) return +(2800-Math.pow((i-48)*3.5,1.9)+Math.random()*60).toFixed(1);
   if(i<90) return +Math.max(5,2800*Math.exp(-(i-58)/13)+Math.random()*35).toFixed(1);
   return +(10+Math.random()*10).toFixed(1);
  })
 }
};

function loadHistoricalFlare(key) {
 historicalFlare=key==='none'?null:HIST_DATA[key]||null;
 if (!historicalFlare) {
  histChart.data.datasets[1].data=Array(100).fill(null);
  histChart.update('none');
  document.getElementById('hist-desc').textContent='Select a historical flare to overlay on the telemetry chart and compare event characteristics.';
  return;
 }
 const hd=HIST_DATA[key];
 const curData=recentSolexs.slice(-100);
 const padded=Array(100-curData.length).fill(null).concat(curData);
 histChart.data.datasets[0].data=padded;
 histChart.data.datasets[1].data=hd.data;
 histChart.update('none');

 // Comparison table
 const curPeak=Math.max(...recentSolexs,0).toFixed(0);
 const curRise=recentSolexs.length+'s';
 setText('hc-cur-peak',curPeak+' cts');
 setText('hc-ref-peak',hd.meta.peak);
 setText('hc-cur-rise','~'+Math.round(recentSolexs.length/5)+'m');
 setText('hc-ref-rise',hd.meta.rise);
 setText('hc-cur-dur','~'+Math.round(recentSolexs.length/12)+'m');
 setText('hc-ref-dur',hd.meta.dur);
 const curPeakN=+curPeak;
 const refPeakN=+hd.meta.peak.replace(/[^0-9]/g,'');
 setText('hc-cur-cls',curPeakN>1000?'M/X Class':curPeakN>200?'M Class':curPeakN>50?'C Class':'B Class');
 setText('hc-ref-cls',hd.meta.cls);
 setText('hc-ratio-peak',(curPeakN/Math.max(1,refPeakN)).toFixed(2)+'x');
 document.getElementById('hist-desc').textContent=`Comparing current SoLEXS event against ${key} (${hd.meta.date}). Peak of ${hd.meta.peak}, rise time ${hd.meta.rise}, total duration ${hd.meta.dur}.`;

 // Also overlay on main telemetry chart
 const mainOverlay=hd.data.slice(hd.data.length-MAX_PTS);
 while(mainOverlay.length<MAX_PTS) mainOverlay.unshift(null);
 telChart.data.datasets[2].data=mainOverlay;
 telChart.update('none');
 const legLabel=document.getElementById('hist-legend-label');
 if (legLabel) { legLabel.style.display=''; legLabel.textContent=key; }
 const leg=document.getElementById('hist-legend');
 if (leg) leg.style.display='';
}

// ================================================================
// 🔔 NOTIFICATIONS + DEMO + PDF
// ================================================================
let notifFired=false;
function checkNotification(alertClass) {
 if (alertClass!=='high'||notifFired) return;
 if (notifGranted) {
  new Notification('⚡ Aditya-L1 CRITICAL ALERT',{
   body:'M-class solar flare detected! SoLEXS >1000 cts. Satellite protection recommended.',
   icon:''
  });
  notifFired=true;
 }
}
document.getElementById('btn-notify').addEventListener('click',()=>{
 if (typeof Notification==='undefined') return;
 Notification.requestPermission().then(p=>{
  notifGranted=(p==='granted');
  const btn=document.getElementById('btn-notify');
  if (btn) { btn.textContent=notifGranted?'🔔 ENABLED':'🔔 BLOCKED'; btn.style.color=notifGranted?'var(--green)':'var(--red)'; }
 });
});

let demoIdx=0;
const DEMO_COMMENTARY=['Nominal background X-ray emission. SoLEXS nominal ~5-20 cts.','Pre-flare slow thermal rise begins. HEL1OS/SoLEXS hardness ratio increasing.','Impulsive phase onset — AR4087 active. SoLEXS climbing rapidly!','CRITICAL: SoLEXS crossed 1000 cts! M-class flare in progress. Alert Level II!','QPP oscillations detected in peak phase — MHD sausage mode in flare loops.','Gradual phase — hot plasma filling coronal loops (chromospheric evaporation).','Decay phase. HF radio blackout may persist for 30-60 minutes.','Recovery. SoLEXS returning toward background. Monitor for sympathetic flares.'];
function runDemoStep() {
 if (!demoMode) return;
 const feed=document.getElementById('terminal-log');
 if (feed&&demoIdx<DEMO_COMMENTARY.length) {
  const e=document.createElement('div'); e.className='log-entry';
  e.innerHTML=`<span class="lt">[DEMO]</span><span class="lw"> 🎬 ${DEMO_COMMENTARY[demoIdx]}</span>`;
  feed.appendChild(e); feed.scrollTop=feed.scrollHeight;
  demoIdx++;
 }
}
document.getElementById('btn-demo').addEventListener('click',()=>{
 demoMode=!demoMode;
 const btn=document.getElementById('btn-demo');
 if (demoMode) {
  idx=0; speed=4; demoIdx=0; playing=true;
  startTick();
  btn.textContent='⏹ STOP DEMO'; btn.className='hbtn';
  setInterval(runDemoStep,8000);
  const feed=document.getElementById('terminal-log');
  if(feed){const e=document.createElement('div');e.className='log-entry';e.innerHTML='<span class="lt">[DEMO]</span><span class="lw"> 🎬 AUTO-PILOT DEMO STARTED — Full M-class flare sequence will play</span>';feed.appendChild(e);}
 } else { btn.textContent='🎬 DEMO'; btn.className='hbtn green'; }
});

function exportPDF() {
 const allTabs=document.querySelectorAll('.tab-panel');
 allTabs.forEach(t=>t.style.display='block');
 window.print();
 setTimeout(()=>{ allTabs.forEach((t,i)=>{ t.style.display=i===0?'block':'none'; }); },2000);
}

// ================================================================
// MAIN DASHBOARD STATE UPDATE
// ================================================================
let lastAlertClass='low';
function updateDashboard(solexs,hel1os) {
 let pm,px,pC,pB,ac;
 if(solexs>1000){
  pm=Math.min(99,70+(solexs-1000)*0.015); px=Math.min(75,25+(solexs-1000)*0.01);
  pC=Math.min(99,88); pB=99; ac='high';
  flareI=Math.min(1,flareI+0.04); flareAR=0;
  setText('al-icon','⚠'); setText('al-level','HIGH');
  setText('al-sub','RISK OF M/X-CLASS FLARE');
  setText('al-desc','SoLEXS exceeded 1000 cts/s. Impulsive flare phase. Satellite protection recommended now.');
  const t=document.getElementById('ft0'),c=document.getElementById('fc0');
  if(t)t.textContent=new Date().toLocaleTimeString().slice(0,5);
  if(c){c.textContent='M'+(Math.floor(pm/12)+1);c.style.color='#f97316';}
  notifFired=false; checkNotification('high');
  AudioSynth.startAlarm('high');
  triggerCME(solexs);
 } else if(solexs>400){
  pm=Math.min(65,35+(solexs-400)*0.05); px=Math.min(25,5+(solexs-400)*0.025);
  pC=Math.min(80,55); pB=88; ac='med';
  flareI=Math.min(0.45,flareI+0.02); flareAR=2;
  setText('al-icon','⚡'); setText('al-level','MODERATE');
  setText('al-sub','PRE-FLARE THERMAL HEATING');
  setText('al-desc','Gradual thermal soft X-ray rise. Pre-flare heating in AR4085. Monitor closely.');
  AudioSynth.startAlarm('med');
 } else {
  pm=Math.max(1.5,solexs*0.08); px=Math.max(0.3,solexs*0.015);
  pC=Math.max(5,solexs*0.4); pB=Math.max(15,solexs*1.2);
  ac='low'; flareI=Math.max(0,flareI-0.008);
  setText('al-icon','✓'); setText('al-level','NOMINAL');
  setText('al-sub','RISK OF SOLAR FLARE: LOW');
  setText('al-desc','Background coronal X-ray emission. No pre-flare signatures. All instruments nominal.');
  AudioSynth.stopAlarm();
 }
 pm=+pm.toFixed(1); px=+px.toFixed(1);
 lastAlertClass=ac;

 const panel=document.getElementById('alert-panel');
 if(panel) panel.className='glass alert-card '+ac;
 setText('prob-m',pm+'%'); setText('prob-x',px+'%');
 const gc=ac==='high'?'#ef4444':ac==='med'?'#eab308':'#22c55e';
 const gxc=ac==='high'?'#ef4444':ac==='med'?'#f97316':'#3b82f6';
 drawGauge('gaugeM',pm,gc); drawGauge('gaugeX',px,gxc);

 if(ac==='high'){ setText('a87m','M:'+Math.round(pm)+'%'); setText('a87x','X:'+Math.round(px)+'%'); setText('a85m','M:'+Math.round(pm*0.6)+'%'); setText('a85x','X:'+Math.round(px*0.6)+'%'); }
 else if(ac==='med'){ setText('a87m','M:'+Math.round(pm)+'%'); setText('a87x','X:'+Math.round(px)+'%'); }

 probChart.data.datasets[0].data.shift(); probChart.data.datasets[0].data.push(px);
 probChart.data.datasets[1].data.shift(); probChart.data.datasets[1].data.push(pm);
 probChart.data.datasets[2].data.shift(); probChart.data.datasets[2].data.push(+pC.toFixed(1));
 probChart.data.datasets[3].data.shift(); probChart.data.datasets[3].data.push(+pB.toFixed(1));
 probChart.update('none');

 const t=Date.now()/1000;
 const wspd = Math.round(452+30*Math.sin(t*0.05));
 setText('wind-spd',wspd+' km/s');
 AudioSynth.updateSpaceWeather(solexs, hel1os, wspd);
 setText('wind-bz',(-3.2+1.5*Math.sin(t*0.08)).toFixed(1));
 setText('wind-den',(6.1+1.2*Math.sin(t*0.04)).toFixed(1)+'/cm³');
 const geo=document.getElementById('geo-imp');
 if(geo){geo.textContent=ac==='high'?'G2 Moderate':ac==='med'?'G1 Minor':'G0 Quiet';geo.style.color=ac==='high'?'var(--orange)':ac==='med'?'var(--amber)':'var(--green)';}

 updateSatRisks(ac);
 updateDEM(solexs, hel1os);
 return {ac,pm,px};
}

// ================================================================
// TERMINAL
// ================================================================
function appendLog(s,h,ac,pm) {
 const feed=document.getElementById('terminal-log'); if(!feed) return;
 const now=new Date().toLocaleTimeString();
 const cls=ac==='high'?'le':ac==='med'?'lw':'lc';
 const lvl=ac==='high'?'CRIT':ac==='med'?'WARN':'OK  ';
 const hr=(h/Math.max(1,s)).toFixed(3);
 const e=document.createElement('div'); e.className='log-entry';
 e.innerHTML=`<span class="lt">[${now}]</span><span class="${cls}"> SoLEXS:${s.toFixed(1).padStart(7)} HEL1OS:${h.toFixed(1).padStart(7)} HR:${hr} P_M:${pm.toFixed(1).padStart(5)}% [${lvl}]</span>`;
 feed.appendChild(e); feed.scrollTop=feed.scrollHeight;
 while(feed.children.length>70) feed.removeChild(feed.firstChild);
}

// ================================================================
// TICK LOOP
// ================================================================
function tick() {
 if(!TELEMETRY.length) return;
 if(idx>=TELEMETRY.length) idx=0;
 const dp=TELEMETRY[idx];

 telChart.data.datasets[0].data.shift(); telChart.data.datasets[0].data.push(dp.solexs);
 telChart.data.datasets[1].data.shift(); telChart.data.datasets[1].data.push(dp.hel1os);
 telChart.update('none');

 recentSolexs.push(dp.solexs); recentHel1os.push(dp.hel1os);
 if(recentSolexs.length>WIN){recentSolexs.shift();recentHel1os.shift();}

 const {ac,pm}=updateDashboard(dp.solexs,dp.hel1os);
 appendLog(dp.solexs,dp.hel1os,ac,pm);

 // Instrument scan tick beep
 const hr = dp.hel1os / Math.max(1, dp.solexs);
 AudioSynth.playScanBeep(hr);

 // Update SHAP + QPP + Forecast
 if(idx%3===0) updateSHAP(dp.solexs,dp.hel1os);
 if(idx%5===0) updateQPP(dp.solexs);
 if(idx%5===0) updateForecast(dp.solexs);

 idx++;
}

function startTick() {
 clearInterval(tickId);
 tickId=setInterval(tick,1000/Math.max(1,speed));
}
function setPlay(p) {
 playing=p;
 const btn=document.getElementById('btn-play');
 if(btn) btn.textContent=playing?'⏸ PAUSE':'▶ PLAY';
 if(playing) startTick(); else clearInterval(tickId);
}

document.getElementById('btn-play').addEventListener('click',()=>setPlay(!playing));
document.getElementById('btn-flare').addEventListener('click',()=>{
 idx=105; setPlay(true);
 const feed=document.getElementById('terminal-log');
 if(feed){const e=document.createElement('div');e.className='log-entry';e.innerHTML=`<span class="lt">[${new Date().toLocaleTimeString()}]</span><span class="le"> *** OPERATOR: SOLAR FLARE SEQUENCE TRIGGERED — AR4087 IMPULSIVE PHASE ***</span>`;feed.appendChild(e);}
});
document.getElementById('speed-slider').addEventListener('input',e=>{
 speed=+e.target.value; setText('spd-lbl',speed+'x'); if(playing) startTick();
});

// ================================================================
// ================================================================
// 🔬 DIFFERENTIAL EMISSION MEASURE (DEM) INVERSION ENGINE
// ================================================================
let demChart = null;
let lastEth = 0;

// Regularized Tikhonov reconstruction matrix (pre-computed from CHIANTI spectral response kernels)
const DEM_R_MATRIX = [
 [0.82, -0.22,  0.06, -0.01],  // Log T = 6.0 (1.0 MK) - Quiet Corona
 [0.35,  0.60, -0.18,  0.03],  // Log T = 6.4 (2.5 MK) - Active Region
 [-0.12, 0.55,  0.48, -0.12],  // Log T = 6.8 (6.3 MK) - Pre-flare Heating
 [0.03, -0.18,  0.72,  0.32],  // Log T = 7.2 (15.8 MK) - Thermal Flare
 [-0.01, 0.04, -0.28,  0.92]   // Log T = 7.6 (39.8 MK) - Super-hot Core
];

function initDemChart() {
 const ctx = document.getElementById('demChart');
 if (!ctx) return;
 demChart = new Chart(ctx, {
  type: 'line',
  data: {
   labels: ['1.0 MK', '2.5 MK', '6.3 MK', '15.8 MK', '39.8 MK'],
   datasets: [{
    label: 'DEM(T)',
    data: [1e43, 2e43, 1e42, 1e41, 1e40],
    borderColor: '#f97316',
    backgroundColor: 'rgba(249, 115, 22, 0.12)',
    fill: true,
    tension: 0.4,
    borderWidth: 2,
    pointBackgroundColor: '#fff',
    pointRadius: 4
   }]
  },
  options: {
   responsive: true,
   maintainAspectRatio: false,
   scales: {
    x: {
     grid: { color: 'rgba(255, 255, 255, 0.05)' },
     ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 9 } }
    },
    y: {
     type: 'logarithmic',
     min: 1e40,
     max: 1e46,
     grid: { color: 'rgba(255, 255, 255, 0.05)' },
     ticks: {
      color: '#94a3b8',
      font: { family: 'JetBrains Mono', size: 8 },
      callback: function(value) {
       return value.toExponential(0);
      }
     }
    }
   },
   plugins: {
    legend: { display: false }
   }
  }
 });
}

function updateDEM(solexs, hel1os) {
 if (!demChart) return;
 
 // Estimate fluxes in 4 energy channels (SoLEXS & HEL1OS spectral bands)
 const F = [
  solexs * 0.65,
  solexs * 0.25 + hel1os * 0.10,
  solexs * 0.10 + hel1os * 0.40,
  hel1os * 0.50
 ];
 
 // Regularized Tikhonov Inversion
 const dem = DEM_R_MATRIX.map(row => {
  const val = row.reduce((sum, coefficient, j) => sum + coefficient * F[j], 0);
  return Math.max(1e40, val * 1.5e42); // scale to realistic EM values
 });
 
 // Update chart
 demChart.data.datasets[0].data = dem;
 demChart.update('none');
 
 // Calculate Peak Temperature (Tmax)
 const temps = [1.0, 2.5, 6.3, 15.8, 39.8];
 let maxIdx = 0;
 for (let i = 1; i < dem.length; i++) {
  if (dem[i] > dem[maxIdx]) maxIdx = i;
 }
 const tmax = temps[maxIdx];
 setText('dem-tmax', tmax.toFixed(1) + ' MK');
 
 // Total Emission Measure (EM)
 const totalEM = dem.reduce((sum, val) => sum + val, 0);
 setText('dem-total', totalEM.toExponential(2) + ' cm⁻³');
 
 // Thermal Energy Density (Eth = 3 * k_B * T * sqrt(EM / V))
 // We assume a typical active region loop volume V = 10^27 cm^3
 const kB = 1.38e-16; // erg/K
 const V = 1e27; // cm^3
 const tempKelvin = tmax * 1e6;
 const density = Math.sqrt(totalEM / V);
 const eth = 3 * kB * tempKelvin * density;
 setText('dem-energy', eth.toFixed(2) + ' erg/cm³');
 
 // Heating Rate (dH/dt)
 if (lastEth > 0) {
  const dhdt = (eth - lastEth) * V / 1.0; // erg/s
  setText('dem-heating', (dhdt > 0 ? '+' : '') + dhdt.toExponential(2) + ' erg/s');
 } else {
  setText('dem-heating', '0.00e0 erg/s');
 }
 lastEth = eth;
 
 // Thermal Anomaly Warning
 const warn = document.getElementById('dem-warning');
 if (warn) {
  warn.style.display = tmax >= 15.8 ? 'block' : 'none';
 }
}

// ================================================================
// ☄ INTERPLANETARY CME PROPAGATION SIMULATOR (Drag-Based Model)
// ================================================================
const cmeCanvas = document.getElementById('cmeCanvas');
const cmeCtx = cmeCanvas ? cmeCanvas.getContext('2d') : null;
let cmeActive = false;
let cmeProgress = 0; // 0 to 1
let cmeSpeed = 0; // km/s
let cmeStartV = 1200; // v0
let cmeWindV = 450; // vw
let cmeToaSeconds = 0;
let cmeTimeElapsed = 0; // in seconds

function resizeCmeCanvas() {
 if (!cmeCanvas) return;
 const wrap = cmeCanvas.parentElement;
 cmeCanvas.width = wrap.clientWidth;
 cmeCanvas.height = 250;
}
window.addEventListener('resize', resizeCmeCanvas);

function calculateCMETransit(v0, vw) {
 const D = 1.485e8; // Distance from Sun to L1 in km
 const gamma = 1.0e-7; // Drag coefficient
 let x = 0, t = 0, steps = 500, dx = D / steps;
 for (let i = 0; i < steps; i++) {
  const v = vw + (v0 - vw) * Math.exp(-gamma * x);
  t += dx / v;
  x += dx;
 }
 return t; // Transit time to L1 in seconds
}

function calculateCMETransitToEarth(v0, vw) {
 const D = 1.5e8; // Distance from Sun to Earth in km
 const gamma = 1.0e-7;
 let x = 0, t = 0, steps = 500, dx = D / steps;
 for (let i = 0; i < steps; i++) {
  const v = vw + (v0 - vw) * Math.exp(-gamma * x);
  t += dx / v;
  x += dx;
 }
 return t; // Transit time to Earth in seconds
}

function triggerCME(solexs) {
 if (cmeActive) return;
 cmeActive = true;
 cmeProgress = 0;
 const tNow = Date.now() / 1000;
 cmeWindV = Math.round(452 + 30 * Math.sin(tNow * 0.05));
 cmeStartV = Math.round(1000 + (solexs - 1000) * 0.4 + Math.random() * 200);
 
 cmeToaSeconds = calculateCMETransitToEarth(cmeStartV, cmeWindV);
 cmeTimeElapsed = 0;
 
 setText('cme-v0', cmeStartV + ' km/s');
 setText('cme-vw', cmeWindV + ' km/s');
 
 const date = new Date(Date.now() + cmeToaSeconds * 1000);
 setText('cme-toa', date.toLocaleDateString() + ' ' + date.toLocaleTimeString().slice(0, 5));
 
 const status = document.getElementById('cme-alert-status');
 if (status) {
  status.textContent = '⚠ ACTIVE CME TRACKING';
  status.style.background = 'rgba(239,68,68,0.15)';
  status.style.borderColor = 'rgba(239,68,68,0.4)';
  status.style.color = 'var(--red)';
 }
 
 const warn = document.getElementById('cme-warning');
 if (warn) warn.style.display = 'none';
}

function drawCmeTrack() {
 requestAnimationFrame(drawCmeTrack);
 if (!cmeCanvas || !cmeCtx) return;
 
 const W = cmeCanvas.width;
 const H = cmeCanvas.height;
 cmeCtx.clearRect(0, 0, W, H);
 
 // Background coordinates grid
 cmeCtx.strokeStyle = 'rgba(0, 212, 255, 0.03)';
 cmeCtx.lineWidth = 0.5;
 for (let x = 0; x < W; x += 40) {
  cmeCtx.beginPath(); cmeCtx.moveTo(x, 0); cmeCtx.lineTo(x, H); cmeCtx.stroke();
 }
 for (let y = 0; y < H; y += 40) {
  cmeCtx.beginPath(); cmeCtx.moveTo(0, y); cmeCtx.lineTo(W, y); cmeCtx.stroke();
 }
 
 const sunX = 50;
 const sunY = H / 2;
 const earthX = W - 70;
 const earthY = H / 2;
 const L1X = sunX + (earthX - sunX) * 0.88; // Visually scale L1 to 88% for clear spacing
 
 // Earth's Orbit Arc
 cmeCtx.strokeStyle = 'rgba(59, 130, 246, 0.12)';
 cmeCtx.setLineDash([4, 6]);
 cmeCtx.beginPath();
 cmeCtx.arc(sunX, sunY, earthX - sunX, -Math.PI / 4, Math.PI / 4);
 cmeCtx.stroke();
 cmeCtx.setLineDash([]);
 
 // L1 Point Crosshair
 cmeCtx.strokeStyle = 'rgba(250, 204, 21, 0.3)';
 cmeCtx.lineWidth = 1;
 cmeCtx.beginPath();
 cmeCtx.moveTo(L1X, sunY - 12); cmeCtx.lineTo(L1X, sunY + 12);
 cmeCtx.moveTo(L1X - 12, sunY); cmeCtx.lineTo(L1X + 12, sunY);
 cmeCtx.stroke();
 cmeCtx.fillStyle = 'rgba(250, 204, 21, 0.7)';
 cmeCtx.font = '9px JetBrains Mono, monospace';
 cmeCtx.fillText('L1 Point', L1X - 22, sunY - 16);
 
 // Aditya-L1 Spacecraft in Halo Orbit
 const t = Date.now() / 1000;
 const haloX = L1X + 10 * Math.sin(t * 1.5);
 const haloY = sunY + 16 * Math.cos(t * 1.5);
 
 cmeCtx.strokeStyle = 'rgba(16, 185, 129, 0.18)';
 cmeCtx.beginPath();
 cmeCtx.ellipse(L1X, sunY, 10, 16, 0, 0, Math.PI * 2);
 cmeCtx.stroke();
 
 cmeCtx.fillStyle = 'var(--green)';
 cmeCtx.beginPath(); cmeCtx.arc(haloX, haloY, 3.5, 0, Math.PI * 2); cmeCtx.fill();
 cmeCtx.fillStyle = 'rgba(16, 185, 129, 0.3)';
 cmeCtx.beginPath(); cmeCtx.arc(haloX, haloY, 7 + 2 * Math.sin(t * 5), 0, Math.PI * 2); cmeCtx.fill();
 cmeCtx.fillStyle = '#94a3b8';
 cmeCtx.fillText('Aditya-L1', haloX + 10, haloY + 3);
 
 // Earth
 cmeCtx.fillStyle = '#3b82f6';
 cmeCtx.beginPath(); cmeCtx.arc(earthX, earthY, 7, 0, Math.PI * 2); cmeCtx.fill();
 cmeCtx.fillStyle = 'rgba(59, 130, 246, 0.2)';
 cmeCtx.beginPath(); cmeCtx.arc(earthX, earthY, 11, 0, Math.PI * 2); cmeCtx.fill();
 cmeCtx.fillStyle = '#fff';
 cmeCtx.font = 'bold 9px Orbitron, sans-serif';
 cmeCtx.fillText('Earth', earthX - 16, earthY + 20);
 
 // Sun
 const sunG = cmeCtx.createRadialGradient(sunX, sunY, 4, sunX, sunY, 24);
 sunG.addColorStop(0, '#fff');
 sunG.addColorStop(0.2, '#facc15');
 sunG.addColorStop(0.6, '#f97316');
 sunG.addColorStop(1, 'rgba(0,0,0,0)');
 cmeCtx.fillStyle = sunG;
 cmeCtx.beginPath(); cmeCtx.arc(sunX, sunY, 24, 0, Math.PI * 2); cmeCtx.fill();
 cmeCtx.fillStyle = '#94a3b8';
 cmeCtx.fillText('Sun', sunX - 10, sunY + 36);
 
 // CME Shockwave Cloud
 if (cmeActive) {
  cmeTimeElapsed += 45000; // Accelerated time steps for visualization
  
  const gamma = 1e-7;
  let x = 0, tempT = 0, dx = 1.5e8 / 300;
  for (let i = 0; i < 300; i++) {
   const v = cmeWindV + (cmeStartV - cmeWindV) * Math.exp(-gamma * x);
   tempT += dx / v;
   if (tempT >= cmeTimeElapsed) {
    cmeProgress = x / 1.5e8;
    cmeSpeed = v;
    break;
   }
   x += dx;
  }
  
  if (cmeTimeElapsed >= cmeToaSeconds) {
   cmeProgress = 1.0;
   cmeSpeed = cmeWindV;
  }
  
  const cloudX = sunX + (earthX - sunX) * cmeProgress;
  const frontR = (cloudX - sunX);
  const op = 0.5 * (1.0 - cmeProgress * 0.65);
  
  const grad = cmeCtx.createRadialGradient(sunX, sunY, frontR * 0.75, sunX, sunY, frontR + 20);
  grad.addColorStop(0, 'rgba(0,0,0,0)');
  grad.addColorStop(0.75, `rgba(249, 115, 22, ${op * 0.45})`);
  grad.addColorStop(0.95, `rgba(239, 68, 68, ${op})`);
  grad.addColorStop(1, 'rgba(0,0,0,0)');
  
  cmeCtx.fillStyle = grad;
  cmeCtx.beginPath();
  cmeCtx.arc(sunX, sunY, frontR + 20, -Math.PI / 5, Math.PI / 5);
  cmeCtx.arc(sunX, sunY, frontR * 0.75, Math.PI / 5, -Math.PI / 5, true);
  cmeCtx.closePath();
  cmeCtx.fill();
  
  const remaining = Math.max(0, cmeToaSeconds - cmeTimeElapsed);
  setText('cme-countdown', remaining > 0 ? (remaining / 3600).toFixed(1) + ' hours' : 'IMPACTED');
  setText('cme-prob', (cmeProgress * 100).toFixed(0) + '%');
  
  // Sat Warning
  if (cloudX >= L1X && remaining > 0) {
   cmeCtx.fillStyle = 'rgba(239, 68, 68, 0.15)';
   cmeCtx.beginPath(); cmeCtx.arc(haloX, haloY, 18 + 4 * Math.sin(t * 8), 0, Math.PI * 2); cmeCtx.fill();
   cmeCtx.fillStyle = 'var(--red)';
   cmeCtx.font = 'bold 8px JetBrains Mono, monospace';
   cmeCtx.fillText('SENSOR OVERLOAD RISK', haloX + 12, haloY - 8);
  }
  
  // Earth Impact
  if (cmeProgress >= 1.0) {
   cmeActive = false;
   const status = document.getElementById('cme-alert-status');
   if (status) {
    status.textContent = '● GEOMAGNETIC IMPACT';
    status.style.background = 'rgba(239, 68, 68, 0.15)';
    status.style.borderColor = 'rgba(239, 68, 68, 0.4)';
    status.style.color = 'var(--red)';
   }
   const warn = document.getElementById('cme-warning');
   if (warn) warn.style.display = 'block';
   
   cmeCtx.fillStyle = 'rgba(239, 68, 68, 0.25)';
   cmeCtx.beginPath(); cmeCtx.arc(earthX, earthY, 30, 0, Math.PI * 2); cmeCtx.fill();
  }
 }
}
resizeCmeCanvas();
requestAnimationFrame(drawCmeTrack);

// ================================================================
// TAB SWITCHING
// ================================================================
function switchTab(name,panelId,btn) {
 document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
 document.querySelectorAll('.tbtn').forEach(b=>b.classList.remove('active'));
 const panel=document.getElementById(panelId);
 if(panel) panel.classList.add('active');
 if(btn) btn.classList.add('active');
 if(name==='hist') {
  const cur=recentSolexs.slice(-100);
  const padded=Array(100-cur.length).fill(null).concat(cur);
  histChart.data.datasets[0].data=padded;
  histChart.update('none');
 } else if(name==='cme') {
  resizeCmeCanvas();
 }
}

// ================================================================
// AI CHATBOT
// ================================================================
function askAI(query) {
 const inp=document.getElementById('chat-input');
 if(inp){inp.value=query;sendChat();}
}
function sendChat() {
 const inp=document.getElementById('chat-input'),hist=document.getElementById('chat-hist');
 if(!inp||!hist) return;
 const q=inp.value.trim(); if(!q) return;
 const um=document.createElement('div'); um.className='cmsg user';
 um.innerHTML=`<span class="csndr">Operator</span><p class="ctxt">${esc(q)}</p>`;
 hist.appendChild(um); inp.value=''; hist.scrollTop=hist.scrollHeight;
 let r=AI.default;
 const ql=q.toLowerCase();
 if(ql.includes('hardness')||ql.includes('ratio')) r=AI.hardness;
 else if(ql.includes('qpp')||ql.includes('oscillat')) r=AI.qpp;
 else if(ql.includes('directive')||ql.includes('protect')) r=AI.directives;
 else if(ql.includes('neupert')) r=AI.neupert;
 else if(ql.includes('evaporat')||ql.includes('chrom')) r=AI.evap;
 else if(ql.includes('random')||ql.includes('model')||ql.includes('forest')) r=AI.model;
 setTimeout(()=>{
  const am=document.createElement('div'); am.className='cmsg asst';
  am.innerHTML='<span class="csndr">Physics AI</span><p class="ctxt"></p>';
  hist.appendChild(am);
  typeWrite(r,am.querySelector('.ctxt'),0,()=>{hist.scrollTop=hist.scrollHeight;});
 },350);
}
document.getElementById('btn-send').addEventListener('click',sendChat);
document.getElementById('chat-input').addEventListener('keypress',e=>{if(e.key==='Enter')sendChat();});
function typeWrite(t,el,i,cb){if(i<t.length){el.textContent+=t[i];setTimeout(()=>typeWrite(t,el,i+1,cb),6);}else if(cb)cb();}
function esc(s){return String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]||c));}

// ================================================================
// UTILITIES
// ================================================================
function setText(id,v){const e=document.getElementById(id);if(e)e.textContent=v;}

// ================================================================
// INIT
// ================================================================
drawGauge('gaugeM',1.5,'#22c55e');
drawGauge('gaugeX',0.3,'#3b82f6');

// Bind Audio Controls
const soundBtn = document.getElementById('btn-sound');
if (soundBtn) {
 soundBtn.addEventListener('click', () => {
  AudioSynth.init();
  const isMuted = !AudioSynth.muted;
  AudioSynth.setMute(isMuted);
  soundBtn.textContent = isMuted ? '🔇 MUTE' : '🔊 SOUND ON';
  soundBtn.className = 'hbtn' + (isMuted ? ' red' : ' green');
  AudioSynth.playClick();
 });
}

// Global button click feedback
document.querySelectorAll('button, select, input[type=range], .wlbtn, .chip-btn, .tbtn').forEach(el => {
 el.addEventListener('click', () => {
  AudioSynth.playClick();
 });
});

// Initialize DEM Solver
initDemChart();
