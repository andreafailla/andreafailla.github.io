/* Pix2Beats browser edition */

const SAMPLE_RATE = 22050;
const FADE_DURATION = 0.015;

const NOTES = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"];

const PIANO_NOTES = {
  A0: 27.5,
  "A#0": 29.13523509488062,
  B0: 30.86770632850775,
  C0: 32.70319566257483,
  "C#0": 34.64782887210901,
  D0: 36.70809598967594,
  "D#0": 38.890872965260115,
  E0: 41.20344461410875,
  F0: 43.653528929125486,
  "F#0": 46.2493028389543,
  G0: 48.999429497718666,
  "G#0": 51.91308719749314,
  A1: 55.0,
  "A#1": 58.27047018976124,
  B1: 61.7354126570155,
  C1: 65.40639132514966,
  "C#1": 69.29565774421802,
  D1: 73.41619197935188,
  "D#1": 77.78174593052023,
  E1: 82.4068892282175,
  F1: 87.30705785825097,
  "F#1": 92.4986056779086,
  G1: 97.99885899543733,
  "G#1": 103.82617439498628,
  A2: 110.0,
  "A#2": 116.54094037952248,
  B2: 123.47082531403103,
  C2: 130.8127826502993,
  "C#2": 138.59131548843604,
  D2: 146.8323839587038,
  "D#2": 155.56349186104046,
  E2: 164.81377845643496,
  F2: 174.61411571650194,
  "F#2": 184.9972113558172,
  G2: 195.99771799087463,
  "G#2": 207.65234878997256,
  A3: 220.0,
  "A#3": 233.08188075904496,
  B3: 246.94165062806206,
  C3: 261.6255653005986,
  "C#3": 277.1826309768721,
  D3: 293.6647679174076,
  "D#3": 311.1269837220809,
  E3: 329.6275569128699,
  F3: 349.2282314330039,
  "F#3": 369.9944227116344,
  G3: 391.99543598174927,
  "G#3": 415.3046975799451,
  A4: 440.0,
  "A#4": 466.1637615180899,
  B4: 493.8833012561241,
  C4: 523.2511306011972,
  "C#4": 554.3652619537442,
  D4: 587.3295358348151,
  "D#4": 622.2539674441618,
  E4: 659.2551138257398,
  F4: 698.4564628660078,
  "F#4": 739.9888454232688,
  G4: 783.9908719634985,
  "G#4": 830.6093951598903,
  A5: 880.0,
  "A#5": 932.3275230361799,
  B5: 987.7666025122483,
  C5: 1046.5022612023945,
  "C#5": 1108.7305239074883,
  D5: 1174.6590716696303,
  "D#5": 1244.5079348883237,
  E5: 1318.5102276514797,
  F5: 1396.9129257320155,
  "F#5": 1479.9776908465376,
  G5: 1567.981743926997,
  "G#5": 1661.2187903197805,
  A6: 1760.0,
  "A#6": 1864.6550460723597,
  B6: 1975.533205024496,
  C6: 2093.004522404789,
  "C#6": 2217.4610478149766,
  D6: 2349.31814333926,
  "D#6": 2489.0158697766474,
  E6: 2637.02045530296,
  F6: 2793.825851464031,
  "F#6": 2959.955381693075,
  G6: 3135.9634878539946,
  "G#6": 3322.437580639561,
  A7: 3520.0,
  "A#7": 3729.3100921447194,
  B7: 3951.066410048992,
  C7: 4186.009044809578,
  "C#7": 4434.922095629953,
  D7: 4698.63628667852,
  "D#7": 4978.031739553295,
  E7: 5274.04091060592,
  F7: 5587.651702928062,
  "F#7": 5919.91076338615,
  G7: 6271.926975707989,
  "G#7": 6644.875161279122,
  A8: 7040.0,
  "A#8": 7458.620184289437,
  B8: 7902.132820097988,
  C8: 8372.018089619156,
  "": 0.0,
};

const SCALES = {
  Major: [0, 2, 4, 5, 7, 9, 11],
  "Natural Minor": [0, 2, 3, 5, 7, 8, 10],
  Dorian: [0, 2, 3, 5, 7, 9, 10],
  Mixolydian: [0, 2, 4, 5, 7, 9, 10],
  Aeolian: [0, 2, 3, 5, 7, 8, 10],
  Phrygian: [0, 1, 3, 5, 7, 8, 10],
  Lydian: [0, 2, 4, 6, 7, 9, 11],
  "Harmonic Minor": [0, 2, 3, 5, 7, 8, 11],
  "Melodic Minor": [0, 2, 3, 5, 7, 8, 9, 10, 11],
  Locrian: [0, 1, 3, 5, 6, 8, 10],
  Blues: [0, 2, 3, 4, 5, 7, 9, 10, 11],
  Chromatic: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
};

const HARMONIES = {
  None: 1,
  "Major second": 9 / 8,
  "Minor third": 6 / 5,
  "Major third": 5 / 4,
  "Perfect fourth": 4 / 3,
  "Diatonic tritone": 45 / 32,
  "Perfect fifth": 3 / 2,
  "Minor sixth": 8 / 5,
  "Major sixth": 5 / 3,
  "Minor seventh": 9 / 5,
  "Major seventh": 15 / 8,
};

const HSV_THRESHOLDS = [26, 52, 78, 104, 128, 154, 180];

const SAMPLE_IMAGES = [
  { label: "Mona Lisa", file: "mona_lisa.png" },
  { label: "Pixel Landscape", file: "pixel_art_landscape.png" },
  { label: "Sunflower", file: "sunflower.png" },
];
const UPLOAD_OPTION = "__upload__";

const PRESETS = {
  None: {
    scale: "Major",
    key: "A",
    octave: 2,
    harmony: "None",
    randomize_octaves: true,
    resize_to_n_pixels: false,
    t_value: 0.2,
    n_pixels: 64,
    gain_db: 0.0,
    drive_db: 0.0,
    cutoff_hz: 0.0,
    resonance_lad: 0.0,
    drive_lad: 1.0,
    delay_seconds: 0.0,
    room_size: 0.0,
    damping: 0.0,
    wet_level: 0.0,
    dry_level: 0.1,
    width: 0.0,
    rate_hz_chorus: 0.0,
  },
  Bitcrusher: {
    scale: "Natural Minor",
    key: "G",
    octave: 2,
    harmony: "Perfect fifth",
    randomize_octaves: true,
    resize_to_n_pixels: false,
    t_value: 0.1,
    n_pixels: 100,
    gain_db: 9.0,
    drive_db: 14.0,
    cutoff_hz: 81.0,
    resonance_lad: 0.4,
    drive_lad: 5.8,
    delay_seconds: 0.0,
    room_size: 0.1,
    damping: 0.0,
    wet_level: 0.0,
    dry_level: 0.3,
    width: 0.0,
    rate_hz_chorus: 0.0,
  },
  "Sleepy Silly Penguin": {
    scale: "Dorian",
    key: "F",
    octave: 3,
    harmony: "Major third",
    randomize_octaves: false,
    resize_to_n_pixels: false,
    t_value: 0.22,
    n_pixels: 143,
    gain_db: 0.0,
    drive_db: 0.0,
    cutoff_hz: 0.0,
    resonance_lad: 0.0,
    drive_lad: 1.0,
    delay_seconds: 0.0,
    room_size: 0.0,
    damping: 0.0,
    wet_level: 0.0,
    dry_level: 0.1,
    width: 0.0,
    rate_hz_chorus: 0.3,
  },
  "Underground Cave": {
    scale: "Mixolydian",
    key: "C",
    octave: 2,
    harmony: "Major sixth",
    randomize_octaves: false,
    resize_to_n_pixels: false,
    t_value: 0.2,
    n_pixels: 219,
    gain_db: 0.0,
    drive_db: 0.0,
    cutoff_hz: 0.0,
    resonance_lad: 0.2,
    drive_lad: 1.0,
    delay_seconds: 0.1,
    room_size: 0.2,
    damping: 0.3,
    wet_level: 0.0,
    dry_level: 0.1,
    width: 0.0,
    rate_hz_chorus: 1.4,
  },
  "Distorted Bass": {
    scale: "Aeolian",
    key: "A#",
    octave: 1,
    harmony: "None",
    randomize_octaves: false,
    resize_to_n_pixels: false,
    t_value: 0.3,
    n_pixels: 64,
    gain_db: 12.0,
    drive_db: 4.0,
    cutoff_hz: 0.0,
    resonance_lad: 0.2,
    drive_lad: 1.0,
    delay_seconds: 0.0,
    room_size: 0.1,
    damping: 0.0,
    wet_level: 0.0,
    dry_level: 0.6,
    width: 0.0,
    rate_hz_chorus: 0.0,
  },
  "Bitcrusher (re:)": {
    scale: "Natural Minor",
    key: "G",
    octave: 3,
    harmony: "Major seventh",
    randomize_octaves: true,
    resize_to_n_pixels: false,
    t_value: 0.1,
    n_pixels: 100,
    gain_db: 9.0,
    drive_db: 14.0,
    cutoff_hz: 81.0,
    resonance_lad: 0.4,
    drive_lad: 5.8,
    delay_seconds: 0.0,
    room_size: 0.1,
    damping: 0.0,
    wet_level: 0.0,
    dry_level: 0.3,
    width: 0.0,
    rate_hz_chorus: 0.0,
  },
};

const ui = {
  sampleSelect: document.getElementById("sampleSelect"),
  uploadInput: document.getElementById("uploadInput"),
  presetSelect: document.getElementById("presetSelect"),
  presetExportBtn: document.getElementById("presetExportBtn"),
  presetImportInput: document.getElementById("presetImportInput"),
  scaleSelect: document.getElementById("scaleSelect"),
  keySelect: document.getElementById("keySelect"),
  octaveSelect: document.getElementById("octaveSelect"),
  harmonySelect: document.getElementById("harmonySelect"),
  tValueRange: document.getElementById("tValueRange"),
  tValue: document.getElementById("tValue"),
  nPixelsRange: document.getElementById("nPixelsRange"),
  nPixelsValue: document.getElementById("nPixelsValue"),
  randomizeOctaves: document.getElementById("randomizeOctaves"),
  resizeToPixels: document.getElementById("resizeToPixels"),
  gainDbRange: document.getElementById("gainDbRange"),
  gainDbValue: document.getElementById("gainDbValue"),
  driveDbRange: document.getElementById("driveDbRange"),
  driveDbValue: document.getElementById("driveDbValue"),
  cutoffHzRange: document.getElementById("cutoffHzRange"),
  cutoffHzValue: document.getElementById("cutoffHzValue"),
  resonanceRange: document.getElementById("resonanceRange"),
  resonanceValue: document.getElementById("resonanceValue"),
  driveLadRange: document.getElementById("driveLadRange"),
  driveLadValue: document.getElementById("driveLadValue"),
  delaySecondsRange: document.getElementById("delaySecondsRange"),
  delaySecondsValue: document.getElementById("delaySecondsValue"),
  roomSizeRange: document.getElementById("roomSizeRange"),
  roomSizeValue: document.getElementById("roomSizeValue"),
  dampingRange: document.getElementById("dampingRange"),
  dampingValue: document.getElementById("dampingValue"),
  wetLevelRange: document.getElementById("wetLevelRange"),
  wetLevelValue: document.getElementById("wetLevelValue"),
  dryLevelRange: document.getElementById("dryLevelRange"),
  dryLevelValue: document.getElementById("dryLevelValue"),
  widthRange: document.getElementById("widthRange"),
  widthValue: document.getElementById("widthValue"),
  rateHzRange: document.getElementById("rateHzRange"),
  rateHzValue: document.getElementById("rateHzValue"),
  generateBtn: document.getElementById("generateBtn"),
  downloadBtn: document.getElementById("downloadBtn"),
  player: document.getElementById("player"),
  status: document.getElementById("status"),
  imageCanvas: document.getElementById("imageCanvas"),
  durationValue: document.getElementById("durationValue"),
};

const sourceCanvas = document.createElement("canvas");
const sourceCtx = sourceCanvas.getContext("2d");
let currentImageName = "sample";
let currentObjectUrl = null;
const rangeUpdaters = [];

function init() {
  SAMPLE_IMAGES.forEach((img) => {
    const option = document.createElement("option");
    option.value = img.file;
    option.textContent = img.label;
    ui.sampleSelect.appendChild(option);
  });
  const uploadOption = document.createElement("option");
  uploadOption.value = UPLOAD_OPTION;
  uploadOption.textContent = "Uploaded image";
  ui.sampleSelect.appendChild(uploadOption);

  Object.keys(SCALES).forEach((scale) => {
    const option = document.createElement("option");
    option.value = scale;
    option.textContent = scale;
    ui.scaleSelect.appendChild(option);
  });

  NOTES.forEach((note) => {
    const option = document.createElement("option");
    option.value = note;
    option.textContent = note;
    ui.keySelect.appendChild(option);
  });

  Object.keys(HARMONIES).forEach((harmony) => {
    const option = document.createElement("option");
    option.value = harmony;
    option.textContent = harmony;
    ui.harmonySelect.appendChild(option);
  });

  Object.keys(PRESETS).forEach((preset) => {
    const option = document.createElement("option");
    option.value = preset;
    option.textContent = preset;
    ui.presetSelect.appendChild(option);
  });

  registerRange(ui.tValueRange, ui.tValue, (v) => Number(v).toFixed(2));
  registerRange(ui.nPixelsRange, ui.nPixelsValue, (v) => v);
  registerRange(ui.gainDbRange, ui.gainDbValue, (v) => v);
  registerRange(ui.driveDbRange, ui.driveDbValue, (v) => v);
  registerRange(ui.cutoffHzRange, ui.cutoffHzValue, (v) => v);
  registerRange(ui.resonanceRange, ui.resonanceValue, (v) => Number(v).toFixed(1));
  registerRange(ui.driveLadRange, ui.driveLadValue, (v) => Number(v).toFixed(1));
  registerRange(ui.delaySecondsRange, ui.delaySecondsValue, (v) => Number(v).toFixed(1));
  registerRange(ui.roomSizeRange, ui.roomSizeValue, (v) => Number(v).toFixed(1));
  registerRange(ui.dampingRange, ui.dampingValue, (v) => Number(v).toFixed(1));
  registerRange(ui.wetLevelRange, ui.wetLevelValue, (v) => Number(v).toFixed(1));
  registerRange(ui.dryLevelRange, ui.dryLevelValue, (v) => Number(v).toFixed(1));
  registerRange(ui.widthRange, ui.widthValue, (v) => Number(v).toFixed(1));
  registerRange(ui.rateHzRange, ui.rateHzValue, (v) => Number(v).toFixed(1));

  ui.sampleSelect.addEventListener("change", () => {
    if (ui.sampleSelect.value === UPLOAD_OPTION) return;
    loadSample(ui.sampleSelect.value);
  });

  ui.uploadInput.addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    currentImageName = file.name.replace(/\.[^/.]+$/, "");
    const dataUrl = await readFileAsDataUrl(file);
    await loadImage(dataUrl);
    ui.sampleSelect.value = UPLOAD_OPTION;
  });

  ui.presetSelect.addEventListener("change", () => {
    const preset = PRESETS[ui.presetSelect.value];
    if (preset) {
      applyPreset(preset);
      syncDuration();
    }
  });

  ui.presetExportBtn.addEventListener("click", () => {
    const preset = readParams();
    downloadJson(preset, `${currentImageName || "pix2beats"}.json`);
  });

  ui.presetImportInput.addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const preset = JSON.parse(text);
      applyPreset(preset);
      syncDuration();
      setStatus(`Preset "${file.name}" loaded.`);
    } catch (error) {
      setStatus("Could not load preset JSON.");
    }
  });

  ui.generateBtn.addEventListener("click", async () => {
    await generateTrack();
  });

  ui.tValueRange.addEventListener("input", syncDuration);
  ui.nPixelsRange.addEventListener("input", syncDuration);

  ui.sampleSelect.value = SAMPLE_IMAGES[0].file;
  applyPreset(PRESETS["Distorted Bass"]);
  loadSample(SAMPLE_IMAGES[0].file);
  refreshRangeDisplays();
  syncDuration();
}

function registerRange(rangeEl, outputEl, formatter) {
  const update = () => {
    outputEl.textContent = formatter(rangeEl.value);
  };
  rangeEl.addEventListener("input", update);
  rangeUpdaters.push(update);
  update();
}

function refreshRangeDisplays() {
  rangeUpdaters.forEach((update) => update());
}

function applyPreset(preset) {
  ui.scaleSelect.value = preset.scale ?? ui.scaleSelect.value;
  ui.keySelect.value = preset.key ?? ui.keySelect.value;
  ui.octaveSelect.value = String(preset.octave ?? 2);
  ui.harmonySelect.value = preset.harmony ?? ui.harmonySelect.value;
  ui.randomizeOctaves.checked =
    preset.randomize_octaves ?? ui.randomizeOctaves.checked;
  ui.resizeToPixels.checked =
    preset.resize_to_n_pixels ?? ui.resizeToPixels.checked;
  ui.tValueRange.value = preset.t_value ?? ui.tValueRange.value;
  ui.nPixelsRange.value = preset.n_pixels ?? ui.nPixelsRange.value;
  ui.gainDbRange.value = preset.gain_db ?? ui.gainDbRange.value;
  ui.driveDbRange.value = preset.drive_db ?? ui.driveDbRange.value;
  ui.cutoffHzRange.value = preset.cutoff_hz ?? ui.cutoffHzRange.value;
  ui.resonanceRange.value = preset.resonance_lad ?? ui.resonanceRange.value;
  ui.driveLadRange.value = preset.drive_lad ?? ui.driveLadRange.value;
  ui.delaySecondsRange.value = preset.delay_seconds ?? ui.delaySecondsRange.value;
  ui.roomSizeRange.value = preset.room_size ?? ui.roomSizeRange.value;
  ui.dampingRange.value = preset.damping ?? ui.dampingRange.value;
  ui.wetLevelRange.value = preset.wet_level ?? ui.wetLevelRange.value;
  ui.dryLevelRange.value = preset.dry_level ?? ui.dryLevelRange.value;
  ui.widthRange.value = preset.width ?? ui.widthRange.value;
  ui.rateHzRange.value = preset.rate_hz_chorus ?? ui.rateHzRange.value;

  refreshRangeDisplays();
}

async function loadSample(filename) {
  currentImageName = filename.replace(/\.[^/.]+$/, "");
  await loadImage(`assets/${filename}`);
}

async function loadImage(src) {
  const img = new Image();
  img.crossOrigin = "anonymous";
  await new Promise((resolve, reject) => {
    img.onload = () => resolve();
    img.onerror = () => reject(new Error("Failed to load image"));
    img.src = src;
  });

  sourceCanvas.width = img.width;
  sourceCanvas.height = img.height;
  sourceCtx.clearRect(0, 0, img.width, img.height);
  sourceCtx.drawImage(img, 0, 0);

  renderPreview(img);
}

function renderPreview(img) {
  const canvas = ui.imageCanvas;
  const ctx = canvas.getContext("2d");
  const maxWidth = canvas.clientWidth || 520;
  const maxHeight = 360;
  const ratio = Math.min(maxWidth / img.width, maxHeight / img.height);
  const width = Math.max(1, Math.floor(img.width * ratio));
  const height = Math.max(1, Math.floor(img.height * ratio));
  canvas.width = width;
  canvas.height = height;
  ctx.clearRect(0, 0, width, height);
  ctx.drawImage(img, 0, 0, width, height);
}

function readParams() {
  return {
    scale: ui.scaleSelect.value,
    key: ui.keySelect.value,
    octave: Number(ui.octaveSelect.value),
    harmony: ui.harmonySelect.value,
    randomize_octaves: ui.randomizeOctaves.checked,
    resize_to_n_pixels: ui.resizeToPixels.checked,
    t_value: Number(ui.tValueRange.value),
    n_pixels: Number(ui.nPixelsRange.value),
    gain_db: Number(ui.gainDbRange.value),
    drive_db: Number(ui.driveDbRange.value),
    cutoff_hz: Number(ui.cutoffHzRange.value),
    resonance_lad: Number(ui.resonanceRange.value),
    drive_lad: Number(ui.driveLadRange.value),
    delay_seconds: Number(ui.delaySecondsRange.value),
    room_size: Number(ui.roomSizeRange.value),
    damping: Number(ui.dampingRange.value),
    wet_level: Number(ui.wetLevelRange.value),
    dry_level: Number(ui.dryLevelRange.value),
    width: Number(ui.widthRange.value),
    rate_hz_chorus: Number(ui.rateHzRange.value),
  };
}

function syncDuration() {
  const tValue = Number(ui.tValueRange.value);
  const nPixels = Number(ui.nPixelsRange.value);
  const duration = tValue * nPixels;
  ui.durationValue.textContent = `${duration.toFixed(1)}s`;
}

async function generateTrack() {
  if (!sourceCanvas.width || !sourceCanvas.height) {
    setStatus("Load an image first.");
    return;
  }

  const params = readParams();
  const duration = params.t_value * params.n_pixels;
  setStatus(`Rendering ${duration.toFixed(1)}s track...`);
  ui.generateBtn.disabled = true;

  try {
    const imageData = getSamplingImageData(
      params.n_pixels,
      params.resize_to_n_pixels
    );
    const buffer = buildTrackBuffer(imageData, params);
    const rendered = await renderWithEffects(buffer, params);
    const wavBlob = audioBufferToWav(rendered);
    setAudioOutput(wavBlob);
    setStatus("Track ready. Hit play or download.");
  } catch (error) {
    setStatus("Failed to generate audio. Try smaller settings.");
  } finally {
    ui.generateBtn.disabled = false;
  }
}

function getSamplingImageData(nPixels, resizeToPixels) {
  if (!resizeToPixels) {
    return sourceCtx.getImageData(0, 0, sourceCanvas.width, sourceCanvas.height);
  }

  const aspectRatio = sourceCanvas.width / sourceCanvas.height;
  const newWidth = Math.max(1, Math.floor(Math.sqrt(nPixels * aspectRatio)));
  const newHeight = Math.max(1, Math.floor(newWidth / aspectRatio));

  const tempCanvas = document.createElement("canvas");
  tempCanvas.width = newWidth;
  tempCanvas.height = newHeight;
  const tempCtx = tempCanvas.getContext("2d");
  tempCtx.drawImage(sourceCanvas, 0, 0, newWidth, newHeight);
  return tempCtx.getImageData(0, 0, newWidth, newHeight);
}

function buildTrackBuffer(imageData, params) {
  const scaleFreqs = getScale(params.octave, params.key, params.scale);
  const hues = sampleHues(imageData, params.n_pixels);
  const freqPool = hues.map((h) => hueToFreq(h, scaleFreqs));
  const noteSamples = Math.max(1, Math.floor(params.t_value * SAMPLE_RATE));
  const totalSamples = noteSamples * params.n_pixels;
  const fadeSamples = Math.min(
    Math.floor(FADE_DURATION * SAMPLE_RATE),
    Math.floor(noteSamples / 2)
  );

  const left = new Float32Array(totalSamples);
  const right = new Float32Array(totalSamples);
  const octaves = [0.5, 1, 2];

  let offset = 0;
  for (let k = 0; k < params.n_pixels; k += 1) {
    const freq = freqPool[Math.floor(Math.random() * freqPool.length)];
    const octaveMul = params.randomize_octaves
      ? octaves[Math.floor(Math.random() * octaves.length)]
      : 1;
    const baseFreq = freq * octaveMul;
    const harmonyRatio = HARMONIES[params.harmony] ?? 1;

    for (let i = 0; i < noteSamples; i += 1) {
      let amp = 1;
      if (i < fadeSamples) {
        amp = i / fadeSamples;
      } else if (i >= noteSamples - fadeSamples) {
        amp = (noteSamples - i) / fadeSamples;
      }

      const t = i / SAMPLE_RATE;
      left[offset + i] = 0.5 * Math.sin(2 * Math.PI * baseFreq * t) * amp;
      right[offset + i] =
        0.5 * Math.sin(2 * Math.PI * baseFreq * harmonyRatio * t) * amp;
    }

    offset += noteSamples;
  }

  const buffer = new AudioBuffer({
    length: totalSamples,
    numberOfChannels: 2,
    sampleRate: SAMPLE_RATE,
  });
  buffer.copyToChannel(left, 0);
  buffer.copyToChannel(right, 1);
  return buffer;
}

async function renderWithEffects(buffer, params) {
  const tailSeconds = Math.max(params.delay_seconds || 0, params.room_size * 2.5);
  const extraSamples = Math.floor(buffer.sampleRate * (tailSeconds + 0.5));
  const offline = new OfflineAudioContext(
    2,
    buffer.length + extraSamples,
    buffer.sampleRate
  );
  const source = offline.createBufferSource();
  source.buffer = buffer;

  const gain = offline.createGain();
  gain.gain.value = dbToGain(params.gain_db);

  const driveGain = offline.createGain();
  driveGain.gain.value = 1 + Math.max(0, params.drive_lad - 1) / 25;

  const distortion = offline.createWaveShaper();
  distortion.curve = makeDistortionCurve(params.drive_db);
  distortion.oversample = "2x";

  const filter = offline.createBiquadFilter();
  if (params.cutoff_hz > 0) {
    filter.type = "highpass";
    filter.frequency.value = params.cutoff_hz;
  } else {
    filter.type = "allpass";
    filter.frequency.value = 1000;
  }
  filter.Q.value = 0.1 + (params.resonance_lad || 0) * 18;

  const delay = offline.createDelay(2.0);
  delay.delayTime.value = params.delay_seconds;
  const delayWet = offline.createGain();
  delayWet.gain.value = params.delay_seconds > 0 ? 0.35 : 0.0;
  const delayDry = offline.createGain();
  delayDry.gain.value = 1.0;
  const delayMix = offline.createGain();

  const convolver = offline.createConvolver();
  convolver.buffer = makeImpulseResponse(
    offline,
    params.room_size,
    params.damping
  );
  const reverbWet = offline.createGain();
  reverbWet.gain.value = params.wet_level;
  const reverbDry = offline.createGain();
  reverbDry.gain.value = params.dry_level;
  const reverbMix = offline.createGain();

  const chorus = createChorus(offline, params.rate_hz_chorus);

  source.connect(gain);
  gain.connect(driveGain);
  driveGain.connect(distortion);
  distortion.connect(filter);

  filter.connect(delay);
  delay.connect(delayWet).connect(delayMix);
  filter.connect(delayDry).connect(delayMix);

  delayMix.connect(convolver);
  convolver.connect(reverbWet).connect(reverbMix);
  delayMix.connect(reverbDry).connect(reverbMix);

  reverbMix.connect(chorus.input);

  let finalNode = chorus.output;
  if (params.width < 1) {
    finalNode = applyWidth(offline, chorus.output, params.width);
  }
  finalNode.connect(offline.destination);

  source.start(0);
  return offline.startRendering();
}

function getScale(octave, key, scaleName) {
  const idx = NOTES.indexOf(key);
  const newScale = NOTES.slice(idx).concat(NOTES.slice(0, idx));
  const scale = SCALES[scaleName];
  if (!scale) return [];
  return scale.map((interval) => {
    const note = `${newScale[interval]}${octave}`;
    return PIANO_NOTES[note] || 0;
  });
}

function hueToFreq(hue, scaleFreqs) {
  for (let i = 0; i < HSV_THRESHOLDS.length; i += 1) {
    if (
      i === HSV_THRESHOLDS.length - 1 ||
      (HSV_THRESHOLDS[i] <= hue && hue < HSV_THRESHOLDS[i + 1])
    ) {
      return scaleFreqs[i] ?? scaleFreqs[0];
    }
  }
  return scaleFreqs[0];
}

function sampleHues(imageData, nPixels) {
  const { data, width, height } = imageData;
  const hues = new Array(nPixels);
  for (let i = 0; i < nPixels; i += 1) {
    const x = Math.floor(Math.random() * width);
    const y = Math.floor(Math.random() * height);
    const idx = (y * width + x) * 4;
    const r = data[idx];
    const g = data[idx + 1];
    const b = data[idx + 2];
    hues[i] = rgbToHue(r, g, b);
  }
  return hues;
}

function rgbToHue(r, g, b) {
  const rf = r / 255;
  const gf = g / 255;
  const bf = b / 255;
  const max = Math.max(rf, gf, bf);
  const min = Math.min(rf, gf, bf);
  const delta = max - min;
  let hue = 0;

  if (delta === 0) {
    hue = 0;
  } else if (max === rf) {
    hue = ((gf - bf) / delta) % 6;
  } else if (max === gf) {
    hue = (bf - rf) / delta + 2;
  } else {
    hue = (rf - gf) / delta + 4;
  }

  hue = Math.round(hue * 60);
  if (hue < 0) hue += 360;
  return hue / 2;
}

function dbToGain(db) {
  return Math.pow(10, db / 20);
}

function makeDistortionCurve(amount) {
  const k = Math.max(0, amount) * 6;
  const nSamples = 44100;
  const curve = new Float32Array(nSamples);
  const deg = Math.PI / 180;
  for (let i = 0; i < nSamples; i += 1) {
    const x = (i * 2) / nSamples - 1;
    curve[i] = ((3 + k) * x * 20 * deg) / (Math.PI + k * Math.abs(x));
  }
  return curve;
}

function makeImpulseResponse(context, roomSize, damping) {
  const duration = 1.0 + roomSize * 2.5;
  const length = Math.floor(context.sampleRate * duration);
  const impulse = context.createBuffer(2, length, context.sampleRate);

  for (let channel = 0; channel < impulse.numberOfChannels; channel += 1) {
    const data = impulse.getChannelData(channel);
    for (let i = 0; i < length; i += 1) {
      const decay = Math.pow(1 - i / length, 2 + roomSize * 6);
      const damp = 1 - damping * (i / length);
      data[i] = (Math.random() * 2 - 1) * decay * damp;
    }
  }

  return impulse;
}

function createChorus(context, rateHz) {
  const input = context.createGain();
  const output = context.createGain();
  const delay = context.createDelay(0.03);
  delay.delayTime.value = 0.015;

  const lfo = context.createOscillator();
  const lfoGain = context.createGain();
  lfo.type = "sine";
  lfo.frequency.value = Math.max(0.1, rateHz || 0.1);
  lfoGain.gain.value = 0.004;
  lfo.connect(lfoGain).connect(delay.delayTime);
  lfo.start(0);

  const wet = context.createGain();
  wet.gain.value = rateHz > 0 ? 0.4 : 0.0;
  const dry = context.createGain();
  dry.gain.value = 1.0;

  input.connect(delay);
  delay.connect(wet).connect(output);
  input.connect(dry).connect(output);

  return { input, output };
}

function applyWidth(context, inputNode, width) {
  const splitter = context.createChannelSplitter(2);
  const merger = context.createChannelMerger(2);

  const leftGain = context.createGain();
  const rightGain = context.createGain();
  leftGain.gain.value = width;
  rightGain.gain.value = width;

  const monoGainL = context.createGain();
  const monoGainR = context.createGain();
  monoGainL.gain.value = (1 - width) * 0.5;
  monoGainR.gain.value = (1 - width) * 0.5;

  inputNode.connect(splitter);
  splitter.connect(leftGain, 0);
  splitter.connect(rightGain, 1);

  splitter.connect(monoGainL, 0);
  splitter.connect(monoGainL, 1);
  splitter.connect(monoGainR, 0);
  splitter.connect(monoGainR, 1);

  leftGain.connect(merger, 0, 0);
  rightGain.connect(merger, 0, 1);
  monoGainL.connect(merger, 0, 0);
  monoGainR.connect(merger, 0, 1);

  return merger;
}

function audioBufferToWav(buffer) {
  const numChannels = buffer.numberOfChannels;
  const sampleRate = buffer.sampleRate;
  const format = 1;
  const bitDepth = 16;
  const blockAlign = (numChannels * bitDepth) / 8;
  const byteRate = sampleRate * blockAlign;
  const dataSize = buffer.length * blockAlign;
  const bufferLength = 44 + dataSize;

  const arrayBuffer = new ArrayBuffer(bufferLength);
  const view = new DataView(arrayBuffer);

  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + dataSize, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, format, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitDepth, true);
  writeString(view, 36, "data");
  view.setUint32(40, dataSize, true);

  let offset = 44;
  for (let i = 0; i < buffer.length; i += 1) {
    for (let channel = 0; channel < numChannels; channel += 1) {
      const sample = buffer.getChannelData(channel)[i];
      const clamped = Math.max(-1, Math.min(1, sample));
      view.setInt16(
        offset,
        clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff,
        true
      );
      offset += 2;
    }
  }

  return new Blob([view], { type: "audio/wav" });
}

function writeString(view, offset, text) {
  for (let i = 0; i < text.length; i += 1) {
    view.setUint8(offset + i, text.charCodeAt(i));
  }
}

function setAudioOutput(blob) {
  if (currentObjectUrl) {
    URL.revokeObjectURL(currentObjectUrl);
  }
  currentObjectUrl = URL.createObjectURL(blob);
  ui.player.src = currentObjectUrl;
  ui.downloadBtn.href = currentObjectUrl;
  ui.downloadBtn.download = `${currentImageName || "pix2beats"}.wav`;
}

function setStatus(message) {
  ui.status.textContent = message;
}

function downloadJson(obj, filename) {
  const blob = new Blob([JSON.stringify(obj, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("Failed to read file"));
    reader.readAsDataURL(file);
  });
}

init();
