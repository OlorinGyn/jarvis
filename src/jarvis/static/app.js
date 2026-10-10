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

function currentTab() {
  return location.hash === "#recordings" ? "recordings" : "live";
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
  }
}

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
checkHealth().then(showTab);
