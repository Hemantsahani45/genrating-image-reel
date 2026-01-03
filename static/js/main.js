const sceneList = document.getElementById("sceneList");
const addSceneBtn = document.getElementById("addSceneBtn");
const generateBtn = document.getElementById("generateBtn");
const statusEl = document.getElementById("status");
const resultsSection = document.getElementById("results");
const resultsTimestamp = resultsSection.querySelector(".results__timestamp");
const downloadLink = document.getElementById("downloadLink");
const sceneTemplate = document.getElementById("sceneTemplate");
const toast = document.getElementById("toast");

const projectTitleInput = document.getElementById("projectTitle");
const tempoInput = document.getElementById("tempo");
const aspectSelect = document.getElementById("aspectRatio");

const demoScenes = [
  {
    text: "Hook viewers with a bold claim or irresistible teaser.",
    duration: 3,
    accent: "#FF9F1C",
    divider: "wave",
    backgroundStart: "#11001C",
    backgroundEnd: "#32004B",
  },
  {
    text: "Highlight the key benefit or transformation they'll experience.",
    duration: 3,
    accent: "#F94184",
    divider: "zigzag",
    backgroundStart: "#31005B",
    backgroundEnd: "#1F0439",
  },
  {
    text: "Close with a clear call to action that sparks urgency.",
    duration: 2.5,
    accent: "#70E4EF",
    divider: "line",
    backgroundStart: "#02111F",
    backgroundEnd: "#083753",
  },
];

function showToast(message, type = "neutral") {
  toast.textContent = message;
  toast.dataset.type = type;
  toast.hidden = false;
  requestAnimationFrame(() => toast.classList.add("toast--visible"));
  setTimeout(() => {
    toast.classList.remove("toast--visible");
    setTimeout(() => {
      toast.hidden = true;
      toast.textContent = "";
    }, 220);
  }, 4200);
}

function updateSceneIndices() {
  sceneList.querySelectorAll(".scene-card").forEach((card, index) => {
    card.querySelector(".scene-card__index").textContent = index + 1;
  });
}

function createSceneCard(scene = {}) {
  const fragment = sceneTemplate.content.cloneNode(true);
  const card = fragment.querySelector(".scene-card");

  card.querySelector(".scene-text").value = scene.text || "";
  card.querySelector(".scene-duration").value = scene.duration || 3;
  card.querySelector(".scene-accent").value = scene.accent || "#FF9F1C";
  card.querySelector(".scene-divider").value = scene.divider || "wave";
  card.querySelector(".scene-bg-start").value = scene.backgroundStart || "#11001C";
  card.querySelector(".scene-bg-end").value = scene.backgroundEnd || "#32004B";

  card.querySelector(".scene-card__remove").addEventListener("click", () => {
    card.remove();
    updateSceneIndices();
    statusEl.querySelector("p").textContent = `${sceneList.children.length} scene(s) queued.`;
  });

  sceneList.append(fragment);
  updateSceneIndices();
}

function collectScenes() {
  return Array.from(sceneList.querySelectorAll(".scene-card")).map((card) => ({
    text: card.querySelector(".scene-text").value.trim(),
    duration: parseFloat(card.querySelector(".scene-duration").value) || 3,
    accentColor: card.querySelector(".scene-accent").value,
    dividerShape: card.querySelector(".scene-divider").value,
    backgroundStart: card.querySelector(".scene-bg-start").value,
    backgroundEnd: card.querySelector(".scene-bg-end").value,
  }));
}

async function generateReel() {
  const title = projectTitleInput.value.trim();
  const tempo = parseInt(tempoInput.value, 10) || 100;
  const aspectRatio = aspectSelect.value;
  const scenes = collectScenes();

  if (!scenes.length) {
    showToast("Add at least one scene before generating.", "error");
    return;
  }

  const body = { title, tempo, aspectRatio, scenes };

  setGeneratingState(true);
  statusEl.querySelector("p").textContent = "Rendering reel… this may take a minute.";

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Failed to generate the reel.");
    }

    showToast("Reel generated successfully! Download ready.");
    renderResult(payload);
    statusEl.querySelector("p").textContent = "All done! Download your new reel.";
  } catch (error) {
    console.error(error);
    showToast(error.message || "Something went wrong while generating.", "error");
    statusEl.querySelector("p").textContent = "Generation failed — review the details and try again.";
  } finally {
    setGeneratingState(false);
  }
}

function renderResult(data) {
  resultsTimestamp.textContent = new Date(data.createdAt).toLocaleString();
  downloadLink.href = data.downloadUrl;
  downloadLink.setAttribute("download", data.filename);
  resultsSection.hidden = false;
}

function setGeneratingState(isGenerating) {
  generateBtn.disabled = isGenerating;
  generateBtn.textContent = isGenerating ? "Generating…" : "Generate Reel";
  generateBtn.classList.toggle("button--accent", !isGenerating);
  generateBtn.classList.toggle("button--primary", isGenerating);
}

addSceneBtn.addEventListener("click", () => {
  createSceneCard();
  showToast("Scene added. Keep stacking the story!");
  statusEl.querySelector("p").textContent = `${sceneList.children.length} scene(s) queued.`;
});

generateBtn.addEventListener("click", generateReel);

document.addEventListener("DOMContentLoaded", () => {
  demoScenes.forEach((scene) => createSceneCard(scene));
  statusEl.querySelector("p").textContent = `${sceneList.children.length} scene(s) queued.`;
});

