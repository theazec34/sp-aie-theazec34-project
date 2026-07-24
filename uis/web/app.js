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
  const { protocol, hostname, port } = window.location;

  // Misma origen (UI servida por la API en :8000 o URL -8000 de Codespaces)
  if (port === "8000" || hostname.includes("-8000.")) {
    return window.location.origin;
  }

  // Codespaces / GitHub.dev: xxx-8080.app.github.dev -> xxx-8000.app.github.dev
  if (hostname.includes("github.dev") || hostname.includes("githubpreview.dev")) {
    const apiHost = hostname.replace(/-\d+(?=\.)/, "-8000");
    return `${protocol}//${apiHost}`;
  }

  return "http://localhost:8000";
}

apiUrlInput.value = defaultApiUrl();


const TOKEN_KEY = "brasaland_access_token";
const authEmail = document.getElementById("auth-email");
const authPassword = document.getElementById("auth-password");
const authToken = document.getElementById("auth-token");
const loginBtn = document.getElementById("login-btn");
const logoutBtn = document.getElementById("logout-btn");

function formatApiDetail(payload, fallback) {
  if (!payload) return fallback;
  if (typeof payload.detail === "string") return payload.detail;
  if (payload.detail && typeof payload.detail === "object" && payload.detail.message) {
    return payload.detail.message;
  }
  if (Array.isArray(payload.errors) && payload.errors.length) {
    return payload.errors.map((e) => e.message || "Error").join(" · ");
  }
  if (Array.isArray(payload.detail) && payload.detail.length) {
    return "Revisa los datos enviados e inténtalo de nuevo.";
  }
  return fallback;
}

function friendlyNetworkMessage(err, base) {
  const raw = err && err.message ? String(err.message) : String(err || "");
  if (/failed to fetch|networkerror|load failed/i.test(raw)) {
    return (
      `No hay conexión con la API en ${base}. En Ports marca el 8000 como Public, ` +
      "reinicia uvicorn y pulsa «Probar API»."
    );
  }
  return raw || "Error inesperado.";
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
  authToken.value = token;
}

function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  authToken.value = "";
}

function authHeaders(extra = {}) {
  const headers = { ...extra };
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

function handleUnauthorized(response) {
  if (response.status === 401) {
    clearToken();
    setStatus("Sesión no válida o expirada. Vuelve a iniciar sesión.", "error");
    return true;
  }
  return false;
}

authToken.value = getToken();

async function loginFromUi() {
  const base = getApiBase();
  setStatus("Iniciando sesión...");
  try {
    const body = new URLSearchParams();
    body.set("username", authEmail.value.trim());
    body.set("password", authPassword.value);
    const response = await fetch(`${base}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(
        formatApiDetail(error, "No se pudo iniciar sesión. Revisa email y contraseña.")
      );
    }
    const data = await response.json();
    setToken(data.access_token);
    setStatus("Sesión iniciada. Ya puedes analizar ficheros.", "success");
  } catch (error) {
    setStatus(`Login fallido: ${friendlyNetworkMessage(error, base)}`, "error");
  }
}

loginBtn.addEventListener("click", loginFromUi);
logoutBtn.addEventListener("click", () => {
  clearToken();
  setStatus("Sesión cerrada.", "success");
});


async function pingApi() {
  const base = getApiBase();
  try {
    const response = await fetch(`${base}/health`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    setStatus(`API conectada: ${data.service || "ok"} (${base})`, "success");
    return true;
  } catch (error) {
    setStatus(friendlyNetworkMessage(error, base), "error");
    return false;
  }
}

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

    if (!getToken()) {
      throw new Error("No autenticado. Inicia sesión arriba antes de analizar.");
    }

    const response = await fetch(
      `${getApiBase()}/api/v1/incidents/analyze`,
      { method: "POST", body: formData, headers: authHeaders() }
    );

    if (handleUnauthorized(response)) {
      return;
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(
        formatApiDetail(error, "No se pudo analizar el fichero. Revisa el CSV e inténtalo de nuevo.")
      );
    }

    const report = await response.json();
    renderReport(report);
    setStatus("Análisis completado.", "success");
  } catch (error) {
    setStatus(
      `No se pudo analizar el fichero. ${friendlyNetworkMessage(error, getApiBase())}`,
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

    if (!getToken()) {
      throw new Error("No autenticado. Inicia sesión arriba antes de exportar.");
    }

    const response = await fetch(
      `${getApiBase()}/api/v1/incidents/export`,
      { method: "POST", body: formData, headers: authHeaders() }
    );

    if (handleUnauthorized(response)) {
      return;
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(
        formatApiDetail(error, "No se pudo exportar el CSV. Reinténtalo en unos segundos.")
      );
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
    setStatus(
      `No se pudo exportar el CSV. ${friendlyNetworkMessage(error, getApiBase())}`,
      "error"
    );
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
document.getElementById("ping-btn").addEventListener("click", pingApi);

// Comprueba la API al cargar la página
pingApi();
