const REFRESH_MS = 15000;
const HEALTH_MS = 5000;

const dayInput = document.getElementById("day");
const eventList = document.getElementById("events");
const summary = document.getElementById("summary");
const cardTemplate = document.getElementById("card");
const previousButton = document.getElementById("previous");
const nextButton = document.getElementById("next");
const cameraGrid = document.getElementById("cameras");
const connectionBanner = document.getElementById("connection");
const versionLabel = document.getElementById("version");

let daysWithRecordings = [];
let cameras = [];
let online = true;
let serverStarted = null;

function todayISO() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function plural(n, one, many) {
  return `${n} ${n === 1 ? one : many}`;
}

const TABS = ["live", "recordings", "people", "settings"];

function currentTab() {
  const tab = location.hash.slice(1);
  return TABS.includes(tab) ? tab : "live";
}

function showNotice(parent, text) {
  const notice = document.createElement("p");
  notice.className = "empty";
  notice.textContent = text;
  parent.replaceChildren(notice);
}

function card(event) {
  const node = cardTemplate.content.cloneNode(true);
  const image = node.querySelector("img");
  if (event.thumbnail) {
    image.src = event.thumbnail;
  } else {
    image.remove();
  }
  node.querySelector(".time").textContent = event.time;
  node.querySelector(".camera").textContent = event.camera;
  const labels = node.querySelector(".labels");
  labels.textContent = event.labels.join(", ") || "?";
  labels.classList.toggle("person", event.labels.includes("person"));
  node.querySelector(".duration").textContent = `${event.seconds} s`;
  return node;
}

function countByCamera(events) {
  const counts = {};
  for (const e of events) {
    counts[e.camera] = (counts[e.camera] || 0) + 1;
  }
  return Object.entries(counts).map(([camera, n]) => `${camera} ${n}`).join(" · ");
}

function updateArrows() {
  const day = dayInput.value;
  previousButton.disabled = !daysWithRecordings.some((d) => d < day);
  nextButton.disabled = !daysWithRecordings.some((d) => d > day);
}

async function loadEvents() {
  let data;
  try {
    const response = await fetch(`/api/events?day=${dayInput.value}`);
    if (!response.ok) throw new Error(response.status);
    data = await response.json();
  } catch {
    summary.textContent = "Could not read the recordings.";
    return;
  }
  eventList.replaceChildren(...data.events.map(card));
  if (data.events.length === 0) {
    showNotice(eventList, "No recordings on this day.");
    summary.textContent = "";
  } else {
    summary.textContent =
      `${plural(data.events.length, "recording", "recordings")} · ${countByCamera(data.events)}`;
  }
  updateArrows();
}

async function loadDays() {
  try {
    const response = await fetch("/api/days");
    daysWithRecordings = response.ok ? await response.json() : [];
  } catch {
    daysWithRecordings = [];
  }
  updateArrows();
}

function goTo(day) {
  dayInput.value = day;
  loadEvents();
}

function stopLive() {
  for (const image of cameraGrid.querySelectorAll("img")) {
    image.removeAttribute("src");
  }
  cameraGrid.replaceChildren();
}

function startLive() {
  if (cameraGrid.querySelector("img")) return;
  if (!online) {
    showNotice(cameraGrid, "No connection to J.A.R.V.I.S.");
    return;
  }
  if (cameras.length === 0) {
    showNotice(cameraGrid, "Cameras are starting...");
    return;
  }
  const stamp = Date.now();
  cameraGrid.replaceChildren(...cameras.map((name) => {
    const image = document.createElement("img");
    image.alt = name;
    image.src = `/live/${encodeURIComponent(name)}?t=${stamp}`;
    return image;
  }));
}

function syncLive() {
  if (currentTab() === "live" && !document.hidden) {
    startLive();
  } else {
    stopLive();
  }
}

async function checkHealth() {
  let status = null;
  try {
    const response = await fetch("/api/status", { cache: "no-store" });
    if (response.ok) status = await response.json();
  } catch {
    status = null;
  }
  const nowOnline = status !== null;
  const changed = nowOnline !== online || (nowOnline && (
    status.started !== serverStarted || status.cameras.join() !== cameras.join()));
  online = nowOnline;
  connectionBanner.hidden = online;
  if (online) {
    cameras = status.cameras;
    serverStarted = status.started;
    versionLabel.textContent = status.version || "";
  }
  if (changed) {
    stopLive();
    syncLive();
  }
}

function showTab() {
  const tab = currentTab();
  for (const section of document.querySelectorAll(".tab")) {
    section.classList.toggle("active", section.id === tab);
  }
  for (const link of document.querySelectorAll(".tabs a")) {
    link.classList.toggle("active", link.dataset.tab === tab);
  }
  syncLive();
  if (tab === "recordings") {
    loadDays().then(loadEvents);
  } else if (tab === "people") {
    loadFaceDays().then(loadFaces);
  } else if (tab === "settings") {
    loadSettings();
  }
}

const peopleDay = document.getElementById("people-day");
const peoplePrevious = document.getElementById("people-previous");
const peopleNext = document.getElementById("people-next");
const peopleSummary = document.getElementById("people-summary");
const faceList = document.getElementById("faces");
const faceTemplate = document.getElementById("face-card");
let daysWithFaces = [];

async function send(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `error ${response.status}`);
  return data;
}

function faceCard(face) {
  const node = faceTemplate.content.cloneNode(true);
  const image = node.querySelector("img");
  if (face.thumbnail) {
    image.src = face.thumbnail;
  } else {
    image.remove();
  }
  const name = node.querySelector(".name");
  name.textContent = face.name;
  name.classList.toggle("person", face.named);
  node.querySelector(".camera").textContent = face.camera;
  node.querySelector(".time").textContent = face.time;
  node.querySelector(".score").textContent =
    face.reliable ? `match ${face.score.toFixed(2)}` : `${face.face_width} px face`;
  const form = node.querySelector("form");
  const input = form.querySelector("input");
  if (face.named) input.value = face.name;
  form.addEventListener("submit", async (submitted) => {
    submitted.preventDefault();
    try {
      const result = await send(`/api/people/${face.person_id}/name`, { name: input.value });
      await loadFaces(false);
      peopleSummary.textContent = `${result.name}: saved` +
        (result.merged ? `, ${plural(result.merged, "face", "faces")} merged` : "");
    } catch (problem) {
      peopleSummary.textContent = `Not saved: ${problem.message}`;
    }
  });
  return node;
}

function updateFaceArrows() {
  const day = peopleDay.value;
  peoplePrevious.disabled = !daysWithFaces.some((d) => d < day);
  peopleNext.disabled = !daysWithFaces.some((d) => d > day);
}

async function loadFaces(describe = true) {
  let data;
  try {
    const response = await fetch(`/api/people?day=${peopleDay.value}`);
    if (!response.ok) throw new Error(response.status);
    data = await response.json();
  } catch {
    peopleSummary.textContent = "Could not read the faces.";
    return;
  }
  faceList.replaceChildren(...data.faces.map(faceCard));
  if (data.faces.length === 0) {
    showNotice(faceList, "No faces seen on this day.");
  }
  if (describe) {
    const unnamed = data.faces.filter((f) => !f.named).length;
    peopleSummary.textContent = data.faces.length
      ? `${plural(data.faces.length, "face", "faces")} · ${unnamed} unnamed · ` +
        "the same name on two faces merges them"
      : "";
  }
  updateFaceArrows();
}

async function loadFaceDays() {
  try {
    const response = await fetch("/api/face-days");
    daysWithFaces = response.ok ? await response.json() : [];
  } catch {
    daysWithFaces = [];
  }
  updateFaceArrows();
}

function goToFaces(day) {
  peopleDay.value = day;
  loadFaces();
}

peoplePrevious.addEventListener("click", () => {
  const earlier = daysWithFaces.filter((d) => d < peopleDay.value);
  if (earlier.length) goToFaces(earlier[0]);
});

peopleNext.addEventListener("click", () => {
  const later = daysWithFaces.filter((d) => d > peopleDay.value);
  if (later.length) goToFaces(later[later.length - 1]);
});

document.getElementById("people-today").addEventListener("click", () => goToFaces(todayISO()));
peopleDay.addEventListener("change", () => loadFaces());

const notifyForm = document.getElementById("notify-form");
const archiveForm = document.getElementById("archive-form");
const notifyResult = document.getElementById("notify-result");
const archiveResult = document.getElementById("archive-result");

function gigabytes(bytes) {
  return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
}

function showArchive(state) {
  const rows = [
    ["Events on this computer", state.local_events],
    ["Using", gigabytes(state.local_bytes)],
    ["Free on this computer", gigabytes(state.local_free)],
    ["Oldest recording", state.oldest ? state.oldest.replace("T", " ").slice(0, 16) : "none"],
    ["Archive", state.archive_ready ? "connected" : state.archive_reason],
  ];
  if (state.archive_ready) {
    rows.push(["Archived events", state.archive_events],
              ["Free on the drive", gigabytes(state.archive_free)]);
  }
  document.getElementById("archive-state").replaceChildren(...rows.flatMap(([term, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = value;
    return [dt, dd];
  }));
}

function fillSettings(values) {
  notifyForm.notify_token.value = "";
  document.getElementById("token-state").textContent = values.notify_token_set
    ? "A token is set. It is never shown; paste a new one only to replace it."
    : "No token yet: paste the one BotFather gave you.";
  notifyForm.notify_chat.value = values.notify_chat || "";
  notifyForm.notify_cooldown.value = values.notify_cooldown;
  notifyForm.notify_prefix.value = values.notify_prefix || "";
  const choices = document.getElementById("label-choices");
  choices.replaceChildren(choices.querySelector("legend"), ...values.notify_label_choices.map((label) => {
    const option = document.createElement("label");
    option.className = "choice";
    const box = document.createElement("input");
    box.type = "checkbox";
    box.value = label;
    box.checked = values.notify_labels.includes(label);
    option.append(box, ` ${label}`);
    return option;
  }));
  archiveForm.archive_path.value = values.archive_path || "";
  archiveForm.archive_after_days.value = values.archive_after_days;
  archiveForm.archive_min_free_gb.value = values.archive_min_free_gb;
  showArchive(values.archive);
}

async function loadSettings() {
  try {
    const response = await fetch("/api/settings", { cache: "no-store" });
    if (!response.ok) throw new Error(response.status);
    fillSettings(await response.json());
  } catch {
    notifyResult.textContent = "Could not read the settings.";
  }
}

async function saveSettings(payload, result) {
  try {
    fillSettings(await send("/api/settings", payload));
    result.textContent = "Saved.";
  } catch (problem) {
    result.textContent = `Not saved: ${problem.message}`;
  }
}

notifyForm.addEventListener("submit", (submitted) => {
  submitted.preventDefault();
  const payload = {
    notify_chat: notifyForm.notify_chat.value,
    notify_cooldown: Number(notifyForm.notify_cooldown.value),
    notify_prefix: notifyForm.notify_prefix.value,
    notify_labels: [...document.querySelectorAll("#label-choices input:checked")].map((b) => b.value),
  };
  if (notifyForm.notify_token.value.trim()) payload.notify_token = notifyForm.notify_token.value;
  saveSettings(payload, notifyResult);
});

archiveForm.addEventListener("submit", (submitted) => {
  submitted.preventDefault();
  saveSettings({
    archive_path: archiveForm.archive_path.value,
    archive_after_days: Number(archiveForm.archive_after_days.value),
    archive_min_free_gb: Number(archiveForm.archive_min_free_gb.value),
  }, archiveResult);
});

document.getElementById("find-chat").addEventListener("click", async () => {
  try {
    const result = await send("/api/notify/discover");
    notifyResult.textContent = result.chat ? `Chat found: ${result.chat}` : `Not found: ${result.error}`;
    loadSettings();
  } catch (problem) {
    notifyResult.textContent = problem.message;
  }
});

document.getElementById("send-test").addEventListener("click", async () => {
  try {
    const result = await send("/api/notify/test");
    notifyResult.textContent = result.ok ? "Test sent." : `Failed: ${result.detail}`;
  } catch (problem) {
    notifyResult.textContent = problem.message;
  }
});

previousButton.addEventListener("click", () => {
  const earlier = daysWithRecordings.filter((d) => d < dayInput.value);
  if (earlier.length) goTo(earlier[0]);
});

nextButton.addEventListener("click", () => {
  const later = daysWithRecordings.filter((d) => d > dayInput.value);
  if (later.length) goTo(later[later.length - 1]);
});

document.getElementById("today").addEventListener("click", () => goTo(todayISO()));
dayInput.addEventListener("change", loadEvents);
window.addEventListener("hashchange", showTab);
document.addEventListener("visibilitychange", syncLive);

setInterval(() => {
  if (!document.hidden) checkHealth();
}, HEALTH_MS);

setInterval(() => {
  if (currentTab() === "recordings" && dayInput.value === todayISO() && !document.hidden) {
    loadDays();
    loadEvents();
  }
}, REFRESH_MS);

dayInput.value = todayISO();
peopleDay.value = todayISO();
checkHealth().then(showTab);
