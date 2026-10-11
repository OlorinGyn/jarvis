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

const TABS = ["live", "recordings", "people", "dogs", "settings"];

function currentTab() {
  const tab = location.hash.slice(1).split("/")[0];
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
  const who = [];
  if (event.people.length) who.push(`People: ${event.people.join("; ")}`);
  if (event.animals.length) who.push(`Animals: ${event.animals.join(", ")}`);
  node.querySelector(".who").textContent = who.join(" · ");
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
    peopleTab.show();
  } else if (tab === "dogs") {
    dogsTab.show();
  } else if (tab === "settings") {
    loadSettings();
  }
}

const PIN_KEY = "jarvis-pin";

function storedPin() {
  try {
    return localStorage.getItem(PIN_KEY) || "";
  } catch {
    return "";
  }
}

function rememberPin(pin) {
  try {
    if (pin) localStorage.setItem(PIN_KEY, pin);
    else localStorage.removeItem(PIN_KEY);
  } catch {
    return;
  }
}

async function send(url, payload) {
  const headers = { "Content-Type": "application/json", "X-Jarvis-Request": "1" };
  const pin = storedPin();
  if (pin) headers["X-Jarvis-Pin"] = pin;
  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(payload || {}),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const problem = new Error(data.detail || `error ${response.status}`);
    problem.status = response.status;
    throw problem;
  }
  return data;
}

async function getJSON(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(response.status);
  return response.json();
}

function monthGrid(month, counts) {
  const [year, number] = month.split("-").map(Number);
  const box = document.createElement("div");
  box.className = "month";
  const title = document.createElement("h4");
  title.textContent = new Date(year, number - 1, 1)
    .toLocaleDateString("en", { month: "long", year: "numeric" });
  const grid = document.createElement("div");
  grid.className = "month-grid";
  for (const letter of ["S", "M", "T", "W", "T", "F", "S"]) {
    const head = document.createElement("span");
    head.className = "weekday";
    head.textContent = letter;
    grid.append(head);
  }
  for (let blank = new Date(year, number - 1, 1).getDay(); blank > 0; blank--) {
    grid.append(document.createElement("span"));
  }
  const last = new Date(year, number, 0).getDate();
  for (let day = 1; day <= last; day++) {
    const iso = `${month}-${String(day).padStart(2, "0")}`;
    const count = counts[iso];
    const cell = document.createElement(count ? "button" : "span");
    cell.className = count ? "day seen" : "day";
    cell.textContent = day;
    if (count) {
      cell.type = "button";
      cell.title = `seen ${plural(count, "time", "times")}: open the recordings`;
      cell.addEventListener("click", () => {
        dayInput.value = iso;
        location.hash = "#recordings";
      });
    }
    grid.append(cell);
  }
  box.append(title, grid);
  return box;
}

function drawCalendar(box, appearances) {
  const counts = {};
  for (const seen of appearances) counts[seen.day] = (counts[seen.day] || 0) + 1;
  const months = [...new Set(Object.keys(counts).map((day) => day.slice(0, 7)))].sort().reverse();
  if (months.length === 0) {
    showNotice(box, "Not seen in any recording yet.");
    return;
  }
  box.replaceChildren(...months.map((month) => monthGrid(month, counts)));
}

function galleryTab(section, api, kind, unnamedLabel) {
  const tab = section.id;
  const list = section.querySelector(".list");
  const page = section.querySelector(".page");
  const namedGrid = section.querySelector(".named-grid");
  const unnamedGrid = section.querySelector(".unnamed-grid");
  const listResult = section.querySelector(".list-result");
  const pageResult = section.querySelector(".page-result");
  const renameForm = section.querySelector(".rename-form");
  const viewsGrid = section.querySelector(".views-grid");
  const calendarBox = section.querySelector(".calendar");
  const cardTemplate = document.getElementById("person-card");
  let named = [];

  function selected() {
    const parts = location.hash.slice(1).split("/");
    return parts[0] === tab ? parts[1] || "" : "";
  }

  async function nameEntry(id, name, merge) {
    try {
      return await send(`${api}/${id}/name`, { name, merge });
    } catch (problem) {
      if (!merge && problem.status === 409 && confirm(`${problem.message}. Merge them?`)) {
        return send(`${api}/${id}/name`, { name, merge: true });
      }
      throw problem;
    }
  }

  function describeNaming(result) {
    return `${result.name}: saved` +
      (result.merged ? `, ${plural(result.merged, "entry", "entries")} merged into it` : "");
  }

  async function applyName(id, name, merge) {
    try {
      listResult.textContent = describeNaming(await nameEntry(id, name, merge));
    } catch (problem) {
      listResult.textContent = `Not saved: ${problem.message}`;
    }
    loadList();
  }

  function card(entry) {
    const node = cardTemplate.content.cloneNode(true);
    const link = node.querySelector("a.photo");
    link.setAttribute("href", `#${tab}/${entry.id}`);
    const image = node.querySelector("img");
    if (entry.photo) {
      image.src = entry.photo;
    } else {
      image.remove();
    }
    const name = node.querySelector(".name");
    name.setAttribute("href", `#${tab}/${entry.id}`);
    name.textContent = entry.name || unnamedLabel;
    name.classList.toggle("person", Boolean(entry.name));
    node.querySelector(".count").textContent =
      plural(entry.views, "view", "views") + (entry.pending ? ` +${entry.pending}` : "");
    const form = node.querySelector("form");
    const select = node.querySelector("select");
    if (entry.name) {
      form.remove();
      select.remove();
      return node;
    }
    const input = form.querySelector("input");
    input.placeholder = section.querySelector(".rename-form input").placeholder;
    if (kind === "dog") {
      const dismiss = document.createElement("button");
      dismiss.type = "button";
      dismiss.className = "dismiss";
      dismiss.textContent = "Dismiss";
      dismiss.title = "Not a dog worth naming: forget this crop";
      dismiss.addEventListener("click", async () => {
        try {
          await send(`${api}/${entry.id}/dismiss`);
          listResult.textContent = "Crop dismissed.";
        } catch (problem) {
          listResult.textContent = `Not dismissed: ${problem.message}`;
        }
        loadList();
      });
      form.after(dismiss);
    }
    form.addEventListener("submit", (submitted) => {
      submitted.preventDefault();
      applyName(entry.id, input.value, false);
    });
    if (named.length === 0) {
      select.remove();
      return node;
    }
    for (const other of named) {
      const option = document.createElement("option");
      option.value = other.name;
      option.textContent = other.name;
      select.append(option);
    }
    select.addEventListener("change", () => {
      if (!select.value) return;
      if (confirm(`This ${kind} is ${select.value}? It merges into them, which cannot be undone.`)) {
        applyName(entry.id, select.value, true);
      } else {
        select.value = "";
      }
    });
    return node;
  }

  async function loadList() {
    let data;
    try {
      data = await getJSON(api);
    } catch {
      showNotice(namedGrid, "Could not read the gallery.");
      return;
    }
    named = data.named;
    namedGrid.replaceChildren(...data.named.map(card));
    if (data.named.length === 0) showNotice(namedGrid, `No ${kind} is named yet: name one below.`);
    unnamedGrid.replaceChildren(...data.unnamed.map(card));
    if (data.unnamed.length === 0) showNotice(unnamedGrid, "Nothing unnamed.");
    section.querySelector(".unnamed-count").textContent =
      data.unnamed.length ? `(${data.unnamed.length})` : "";
  }

  function viewTile(id, photo, index, entry) {
    const tile = document.createElement("figure");
    tile.className = "view";
    if (photo) {
      const image = document.createElement("img");
      image.src = photo;
      image.alt = "";
      image.loading = "lazy";
      tile.append(image);
      const favourite = document.createElement("button");
      favourite.type = "button";
      favourite.className = "cover";
      const chosen = entry.cover_index === index;
      favourite.classList.toggle("chosen", chosen);
      favourite.title = chosen ? "The photo shown on the grid" : "Show this photo on the grid";
      favourite.textContent = "★";
      favourite.addEventListener("click", async () => {
        try {
          showEntry(await send(`${api}/${id}/views/${index}/cover`));
          pageResult.textContent = "Favourite photo saved.";
        } catch (problem) {
          pageResult.textContent = `Not saved: ${problem.message}`;
        }
      });
      tile.append(favourite);
    } else {
      const missing = document.createElement("span");
      missing.className = "no-photo";
      missing.textContent = "no photo";
      tile.append(missing);
    }
    if (entry.views > 1 || entry.pending > 0) {
      const remove = document.createElement("button");
      remove.type = "button";
      remove.title = "Remove this view";
      remove.textContent = "×";
      remove.addEventListener("click", async () => {
        if (!confirm("Remove this view? It will no longer be used to recognise them.")) return;
        try {
          showEntry(await send(`${api}/${id}/views/${index}/remove`));
          pageResult.textContent = "View removed.";
        } catch (problem) {
          pageResult.textContent = `Not removed: ${problem.message}`;
        }
      });
      tile.append(remove);
    }
    return tile;
  }

  function showEntry(entry) {
    section.querySelector(".page-name").textContent = entry.name || unnamedLabel;
    renameForm.querySelector("input").value = entry.name;
    renameForm.querySelector("button").textContent = entry.name ? "Rename" : "Save name";
    section.querySelector(".views-count").textContent =
      `(${entry.views} of 40${entry.pending ? `, ${entry.pending} waiting` : ""})`;
    viewsGrid.replaceChildren(...entry.view_photos.map((photo, index) =>
      viewTile(entry.id, photo, index, entry)));
    drawCalendar(calendarBox, entry.appearances);
  }

  async function loadEntry(id) {
    try {
      showEntry(await getJSON(`${api}/${id}`));
    } catch {
      section.querySelector(".page-name").textContent = "Not found";
      viewsGrid.replaceChildren();
      calendarBox.replaceChildren();
      pageResult.textContent = `This ${kind} no longer exists; it may have been merged.`;
    }
  }

  function show() {
    const id = selected();
    list.hidden = Boolean(id);
    page.hidden = !id;
    pageResult.textContent = "";
    if (id) {
      loadEntry(id);
    } else {
      loadList();
    }
  }

  renameForm.addEventListener("submit", async (submitted) => {
    submitted.preventDefault();
    const id = selected();
    try {
      const result = await nameEntry(id, renameForm.querySelector("input").value, false);
      pageResult.textContent = describeNaming(result);
      if (result.id !== id) {
        location.hash = `#${tab}/${result.id}`;
      } else {
        loadEntry(id);
      }
    } catch (problem) {
      pageResult.textContent = `Not saved: ${problem.message}`;
    }
  });

  return { show };
}

const peopleTab = galleryTab(document.getElementById("people"), "/api/persons", "person", "Unknown");
const dogsTab = galleryTab(document.getElementById("dogs"), "/api/dogs", "dog", "Unnamed dog");

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
  showPairing(values);
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

const pinForm = document.getElementById("pin-form");
const pinResult = document.getElementById("pin-result");
let localDevice = false;

function showPairing(values) {
  localDevice = values.local;
  pinForm.pin.value = "";
  let state;
  if (localDevice) {
    state = values.pin_set
      ? "This is the M900. A PIN is set: other devices need it once to change anything. " +
        "Save a new one to replace it, or save it empty to remove it."
      : "This is the M900. Set a PIN of 4 to 12 digits so other devices on the network " +
        "can change names and settings after entering it once.";
  } else if (!values.pin_set) {
    state = "Changes from this device are refused until a PIN is set on the M900 itself.";
  } else {
    state = storedPin()
      ? "This device is paired. Enter the PIN again only if it changed."
      : "Enter the PIN set on the M900 to pair this device.";
  }
  document.getElementById("pin-state").textContent = state;
  document.getElementById("pin-button").textContent = localDevice ? "Save PIN" : "Pair";
}

pinForm.addEventListener("submit", async (submitted) => {
  submitted.preventDefault();
  const pin = pinForm.pin.value.trim();
  try {
    if (localDevice) {
      const result = await send("/api/pin", { pin });
      pinResult.textContent = result.pin_set ? "PIN saved." : "PIN removed.";
    } else {
      const previous = storedPin();
      rememberPin(pin);
      try {
        await send("/api/pair");
        pinResult.textContent = "This device is paired.";
      } catch (problem) {
        rememberPin(previous);
        throw problem;
      }
    }
    loadSettings();
  } catch (problem) {
    pinResult.textContent = `Not done: ${problem.message}`;
  }
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
checkHealth().then(showTab);
