const apiUrlInput = document.getElementById("api-url");
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const fileName = document.getElementById("file-name");
const analyzeBtn = document.getElementById("analyze-btn");
const exportBtn = document.getElementById("export-btn");
const statusEl = document.getElementById("status");
const resultsSection = document.getElementById("results");

let selectedFile = null;
let lastReport = null;

function defaultApiUrl() {
  const { protocol, hostname } = window.location;
  // Codespaces / GitHub.dev: xxx-8080.app.github.dev -> xxx-8000.app.github.dev
  if (hostname.includes("github.dev") || hostname.includes("githubpreview.dev")) {
    const apiHost = hostname.replace(/-\d+(?=\.)/, "-8000");
    return `${protocol}//${apiHost}`;
  }
  return "http://localhost:8000";
}

apiUrlInput.value = defaultApiUrl();

const INVALID_LABELS = {
  missing_location_id: "Falta location_id",
  invalid_category: "Categoría faltante o inválida",
  empty_description: "Descripción vacía o demasiado corta",
  closed_no_score: "Caso CLOSED sin puntaje",
  missing_reporter_id: "Falta reporter_id",
  score_out_of_range: "Puntaje fuera de rango",
};

function setStatus(message, type = "") {
  statusEl.textContent = message;
  statusEl.className = "status";
  if (type) {
    statusEl.classList.add(`is-${type}`);
  }
}

function getApiBase() {
  return apiUrlInput.value.trim().replace(/\/$/, "");
}

function setSelectedFile(file) {
  selectedFile = file;
  fileName.textContent = file ? file.name : "Ningún fichero seleccionado";
  analyzeBtn.disabled = !file;
  exportBtn.disabled = !file;
}

function renderReport(report) {
  lastReport = report;
  resultsSection.classList.remove("hidden");
  document.getElementById("results-source").textContent =
    `Fichero analizado: ${report.source_file}`;

  document.getElementById("metric-total").textContent = report.total_records;
  document.getElementById("metric-valid").textContent = report.valid_records;
  document.getElementById("metric-invalid").textContent = report.invalid_records;
  document.getElementById("metric-satisfaction").textContent =
    `${report.satisfaction.average.toFixed(2)} / 5`;

  const invalidBody = document.getElementById("invalid-body");
  invalidBody.innerHTML = "";
  for (const [key, label] of Object.entries(INVALID_LABELS)) {
    const count = report.invalid_breakdown[key] ?? 0;
    if (count === 0 && !["missing_location_id", "invalid_category", "empty_description", "closed_no_score"].includes(key)) {
      continue;
    }
    invalidBody.appendChild(createRow([label, count]));
  }

  const categoryBody = document.getElementById("category-body");
  categoryBody.innerHTML = "";
  for (const item of report.by_category) {
    categoryBody.appendChild(
      createRow([item.category, item.count, `${item.percentage}%`])
    );
  }

  const statusBody = document.getElementById("status-body");
  statusBody.innerHTML = "";
  for (const item of report.by_status) {
    statusBody.appendChild(
      createRow([item.status, item.count, `${item.percentage}%`])
    );
  }

  const scoresBody = document.getElementById("scores-body");
  scoresBody.innerHTML = "";
  for (const item of report.satisfaction.distribution) {
    scoresBody.appendChild(createRow([`Puntaje ${item.score}`, item.count]));
  }
}

function createRow(cells) {
  const row = document.createElement("tr");
  for (const value of cells) {
    const cell = document.createElement("td");
    cell.textContent = String(value);
    row.appendChild(cell);
  }
  return row;
}

async function analyzeFile() {
  if (!selectedFile) {
    return;
  }

  setStatus("Analizando fichero...");
  analyzeBtn.disabled = true;
  exportBtn.disabled = true;

  try {
    const formData = new FormData();
    formData.append("file", selectedFile);

    const response = await fetch(
      `${getApiBase()}/api/v1/incidents/analyze`,
      { method: "POST", body: formData }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Error HTTP ${response.status}`);
    }

    const report = await response.json();
    renderReport(report);
    setStatus("Análisis completado.", "success");
  } catch (error) {
    setStatus(
      `No se pudo analizar el fichero. ${error.message}. ¿Está la API en ejecución?`,
      "error"
    );
  } finally {
    analyzeBtn.disabled = !selectedFile;
    exportBtn.disabled = !selectedFile;
  }
}

async function exportFile() {
  if (!selectedFile) {
    return;
  }

  setStatus("Generando CSV de exportación...");
  exportBtn.disabled = true;

  try {
    const formData = new FormData();
    formData.append("file", selectedFile);

    const response = await fetch(
      `${getApiBase()}/api/v1/incidents/export`,
      { method: "POST", body: formData }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Error HTTP ${response.status}`);
    }

    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="([^"]+)"/);
    const filename = match?.[1] || `${selectedFile.name.replace(/\.csv$/i, "")}-analysis.csv`;

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);

    setStatus("CSV exportado correctamente.", "success");
  } catch (error) {
    setStatus(`No se pudo exportar el CSV. ${error.message}`, "error");
  } finally {
    exportBtn.disabled = !selectedFile;
  }
}

dropzone.addEventListener("click", () => fileInput.click());

dropzone.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    fileInput.click();
  }
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files?.[0];
  if (file) {
    setSelectedFile(file);
    setStatus(`Fichero listo: ${file.name}`);
  }
});

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("is-dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("is-dragover");
});

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("is-dragover");
  const file = event.dataTransfer?.files?.[0];
  if (file && file.name.toLowerCase().endsWith(".csv")) {
    setSelectedFile(file);
    setStatus(`Fichero listo: ${file.name}`);
  } else {
    setStatus("Selecciona un fichero con extensión .csv", "error");
  }
});

analyzeBtn.addEventListener("click", analyzeFile);
exportBtn.addEventListener("click", exportFile);
