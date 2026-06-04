const API_BASE = window.location.origin.includes("127.0.0.1:8000")
  ? ""
  : "http://127.0.0.1:8000";

/* ================= NAVIGATION ================= */
function showSection(id) {
  document.getElementById("home").style.display = "none";
  document.querySelectorAll(".section").forEach((s) => {
    s.style.display = "none";
  });
  document.getElementById(id).style.display = "block";
}

function goHome() {
  document.querySelectorAll(".section").forEach((s) => {
    s.style.display = "none";
  });
  document.getElementById("home").style.display = "grid";
}

/* ================= SHARED HELPERS ================= */
function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatError(message) {
  return `<span class="error">Error: ${escapeHtml(message)}</span>`;
}

async function postForm(path, formData) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body: formData
  });

  const raw = await response.text();
  let data = {};

  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch (error) {
      throw new Error(`Server returned an invalid response (${response.status}).`);
    }
  }

  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : `HTTP ${response.status}`;
    throw new Error(detail);
  }

  return data;
}

/* ================= LINK API ================= */
async function analyzeLink() {
  const url = document.getElementById("linkInput").value;
  const output = document.getElementById("linkResult");

  if (!url.trim()) {
    output.innerHTML = "<span class='error'>Error: URL is required.</span>";
    return;
  }

  output.innerHTML = "<span class='loading'>Analyzing link...</span>";

  const formData = new FormData();
  formData.append("url", url);

  try {
    const data = await postForm("/analyze/link", formData);
    displayResult(output, data);
  } catch (error) {
    output.innerHTML = formatError(error.message || "Server error.");
  }
}

/* ================= TEXT API ================= */
async function analyzeText() {
  const text = document.getElementById("textInput").value;
  const output = document.getElementById("textResult");

  if (!text.trim()) {
    output.innerHTML = "<span class='error'>Error: Text is required.</span>";
    return;
  }

  output.innerHTML = "<span class='loading'>Analyzing text...</span>";

  const formData = new FormData();
  formData.append("text", text);

  try {
    const data = await postForm("/analyze/text", formData);
    displayResult(output, data);
  } catch (error) {
    output.innerHTML = formatError(error.message || "Server error.");
  }
}

/* ================= IMAGE API ================= */
async function analyzeImage() {
  const file = document.getElementById("imageInput").files[0];
  const output = document.getElementById("imageResult");

  if (!file || !file.type.startsWith("image/")) {
    output.innerHTML = "<span class='error'>Error: Please choose a valid image file.</span>";
    return;
  }

  output.innerHTML = "<span class='loading'>Analyzing image...</span>";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const data = await postForm("/analyze/image", formData);
    displayResult(output, data);
  } catch (error) {
    output.innerHTML = formatError(error.message || "Server error.");
  }
}

/* ================= VIDEO API ================= */
async function analyzeVideo() {
  const file = document.getElementById("videoInput").files[0];
  const output = document.getElementById("videoResult");

  if (!file || !file.type.startsWith("video/")) {
    output.innerHTML = "<span class='error'>Error: Please choose a valid video file.</span>";
    return;
  }

  output.innerHTML = "<span class='loading'>Analyzing video...</span>";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const data = await postForm("/analyze/video", formData);
    displayResult(output, data);
  } catch (error) {
    output.innerHTML = formatError(error.message || "Server error.");
  }
}

/* ================= RESULT UI ================= */
function displayResult(container, data) {
  const verdictText = String(data?.verdict || "Uncertain");
  const verdictLower = verdictText.toLowerCase();

  const verdictClass =
    verdictLower.includes("true") || verdictLower.includes("real") || verdictLower.includes("supported")
      ? "verdict-real"
      : verdictLower.includes("false") || verdictLower.includes("fake") || verdictLower.includes("refuted")
        ? "verdict-fake"
        : "verdict-uncertain";

  const confidenceValue = Number(data?.confidence);
  const confidenceText = Number.isFinite(confidenceValue)
    ? `${(confidenceValue * 100).toFixed(2)}%`
    : "N/A";

  const claim = escapeHtml(data?.claim || "Not available.");
  const explanation = escapeHtml(data?.explanation || "No explanation returned.");

  container.innerHTML = `
    <div class="result-card">
      <div class="result-header">
        <span class="verdict ${verdictClass}">
          ${escapeHtml(verdictText)}
        </span>
        <span class="confidence">
          Confidence: ${confidenceText}
        </span>
      </div>
      <div class="result-section">
        <h4>Claim</h4>
        <p>${claim}</p>
      </div>
      <div class="result-section">
        <h4>Explanation</h4>
        <p>${explanation}</p>
      </div>
    </div>
  `;
}
