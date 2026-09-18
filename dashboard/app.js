const fileInput = document.getElementById("fileInput");
const dropzone = document.getElementById("dropzone");
const sampleBtn = document.getElementById("sampleBtn");
const gallerySection = document.querySelector(".gallery-panel");
const galleryGrid = document.getElementById("galleryGrid");
const gallerySummary = document.getElementById("gallerySummary");
const jobCount = document.getElementById("jobCount");
const stageLabel = document.getElementById("stageLabel");
const progressFill = document.getElementById("progressFill");
const pipelineSteps = Array.from(document.querySelectorAll(".pipeline-step"));

const stages = ["File Ingested", "Frame Extraction", "Face Cropping", "Data Normalization"];

const sampleFaces = [
  { label: "Face #01", confidence: 0.99, tint: [90, 200, 250] },
  { label: "Face #04", confidence: 0.96, tint: [47, 129, 247] },
  { label: "Face #07", confidence: 0.94, tint: [70, 211, 154] },
  { label: "Face #12", confidence: 0.98, tint: [126, 160, 255] },
  { label: "Face #18", confidence: 0.92, tint: [255, 212, 120] },
  { label: "Face #22", confidence: 0.97, tint: [190, 120, 255] },
];

function updatePipeline(stageIndex) {
  pipelineSteps.forEach((step, index) => {
    step.classList.toggle("active", index === stageIndex);
    step.classList.toggle("done", index < stageIndex);
  });

  const progress = ((stageIndex + 1) / stages.length) * 100;
  progressFill.style.width = `${progress}%`;
  stageLabel.textContent = stages[stageIndex] || "Idle";
}

function makeFaceSvg(index, label, confidence, tint) {
  const [r, g, b] = tint;
  const pct = Math.round(confidence * 100);
  const eyeOffset = index % 2 === 0 ? 42 : 52;
  const mouthY = index % 3 === 0 ? 94 : 100;

  return `data:image/svg+xml;utf8,${encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 224 224">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="rgb(${r}, ${g}, ${b})" stop-opacity="0.95"/>
          <stop offset="100%" stop-color="#09111f" stop-opacity="1"/>
        </linearGradient>
      </defs>
      <rect width="224" height="224" rx="24" fill="url(#g)"/>
      <circle cx="112" cy="114" r="58" fill="#e7edf8" fill-opacity="0.92"/>
      <circle cx="${eyeOffset}" cy="98" r="7" fill="#08111f"/>
      <circle cx="${224 - eyeOffset}" cy="98" r="7" fill="#08111f"/>
      <path d="M82 ${mouthY} Q112 122 142 ${mouthY}" fill="none" stroke="#08111f" stroke-width="6" stroke-linecap="round"/>
      <rect x="0" y="0" width="224" height="224" rx="24" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="2"/>
      <text x="18" y="28" fill="#eaf3ff" font-family="Inter, Arial, sans-serif" font-size="16" font-weight="700">${label}</text>
      <text x="18" y="206" fill="#dce9ff" font-family="Inter, Arial, sans-serif" font-size="14">Confidence ${pct}%</text>
    </svg>
  `)}`;
}

function renderGallery() {
  galleryGrid.innerHTML = "";
  sampleFaces.forEach((face, index) => {
    const card = document.createElement("article");
    card.className = "face-card";
    card.innerHTML = `
      <div class="face-thumb">
        <img alt="${face.label} cropped face preview" src="${makeFaceSvg(index, face.label, face.confidence, face.tint)}" />
      </div>
      <div class="face-meta">
        <div>
          <strong>${face.label} (${Math.round(face.confidence * 100)}%)</strong>
          <span>224 x 224 extracted crop</span>
        </div>
        <span class="mini-badge success">Verified</span>
      </div>
    `;
    galleryGrid.appendChild(card);
  });

  gallerySummary.textContent = `${sampleFaces.length} crops`;
  gallerySection.classList.remove("hidden");
}

function simulatePipeline() {
  gallerySection.classList.add("hidden");
  let currentStage = 0;
  updatePipeline(currentStage);
  jobCount.textContent = "1 running";
  gallerySummary.textContent = "0 crops";

  const runNext = () => {
    updatePipeline(currentStage);
    if (currentStage < stages.length - 1) {
      currentStage += 1;
      window.setTimeout(runNext, 700);
    } else {
      window.setTimeout(() => {
        renderGallery();
        jobCount.textContent = "0 running";
      }, 450);
    }
  };

  runNext();
}

function handleFileSelection(file) {
  if (!file) {
    return;
  }

  fileInput.dataset.filename = file.name;
  dropzone.querySelector(".dropzone-title").textContent = file.name;
  dropzone.querySelector(".dropzone-copy").textContent = file.type.startsWith("video/")
    ? "Video received. Sampling frames for face analysis."
    : "Image received. Cropping the primary face region.";
  simulatePipeline();
}

fileInput.addEventListener("change", (event) => {
  handleFileSelection(event.target.files?.[0]);
});

["dragenter", "dragover"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove("dragover");
  });
});

dropzone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files?.[0];
  handleFileSelection(file);
});

sampleBtn.addEventListener("click", () => {
  const fakeFile = new File(["sample"], "sample_case.mp4", { type: "video/mp4" });
  handleFileSelection(fakeFile);
});

updatePipeline(0);
renderGallery();
gallerySection.classList.add("hidden");
