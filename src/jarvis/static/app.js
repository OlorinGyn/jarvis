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
const analysisLabel = document.getElementById("analysis");

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
const SETTINGS_PARTS = ["notifications", "detection", "devices", "archive", "reports"];
const CONFIDENCE_KEYS = ["confidence_person", "confidence_dog", "confidence_animal"];

function currentTab() {
  const tab = location.hash.slice(1).split("/")[0];
  return TABS.includes(tab) ? tab : "live";
}

const PAGE_STEP = 24;

function paged(container, items, render, shown, key) {
  let count = Math.min(items.length, Math.max(PAGE_STEP, shown.get(key) || 0));
  container.replaceChildren(...items.slice(0, count).map((item, index) => render(item, index)));
  if (count >= items.length) return;
  const more = document.createElement("button");
  more.type = "button";
  more.className = "more";
  const label = () => {
    const left = items.length - count;
    more.textContent = `Show ${Math.min(PAGE_STEP, left)} more (${left} left)`;
  };
  more.addEventListener("click", () => {
    const next = Math.min(items.length, count + PAGE_STEP);
    more.before(...items.slice(count, next).map((item, index) => render(item, count + index)));
    count = next;
    shown.set(key, count);
    if (count >= items.length) more.remove(); else label();
  });
  label();
  container.append(more);
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
  const article = node.querySelector(".card");
  if (event.video) {
    article.classList.add("playable");
    article.title = "Play this recording";
    article.addEventListener("click", () => openPlayer(event));
  }
  const who = [];
  if (event.people.length) who.push(`People: ${event.people.join("; ")}`);
  if (event.animals.length) who.push(`Animals: ${event.animals.join(", ")}`);
  node.querySelector(".who").textContent = who.join(" · ");
  return node;
}

const player = document.getElementById("player");
const playerVideo = document.getElementById("player-video");
const playerSide = document.getElementById("player-side");
const playerReports = document.getElementById("player-reports");

function reportButton(event, label) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "report";
  button.textContent = `Not a ${label}`;
  button.title = `The detector was wrong: remove "${label}" from this recording and keep it as a report`;
  button.addEventListener("click", async () => {
    if (!confirm(`${button.title}?`)) return;
    try {
      await send(event.report, { label });
      button.replaceWith(`Reported: not a ${label}.`);
    } catch (problem) {
      button.replaceWith(`Not reported: ${problem.message}`);
    }
    loadEvents();
  });
  return button;
}

function openPlayer(event) {
  playerVideo.src = event.video;
  const parts = [`${event.camera} · ${event.time} · ${event.seconds} s`];
  if (event.people.length) parts.push(`People: ${event.people.join("; ")}`);
  if (event.animals.length) parts.push(`Animals: ${event.animals.join(", ")}`);
  document.getElementById("player-text").textContent = parts.join(" · ");
  playerSide.hidden = !event.side;
  if (event.side) playerSide.src = event.side;
  playerReports.replaceChildren(...event.labels.map((label) => reportButton(event, label)));
  player.hidden = false;
  playerVideo.play().catch(() => {});
}

function closePlayer() {
  playerVideo.pause();
  playerVideo.removeAttribute("src");
  playerVideo.load();
  player.hidden = true;
}

document.getElementById("player-close").addEventListener("click", closePlayer);
player.addEventListener("click", (clicked) => {
  if (clicked.target === player) closePlayer();
});
document.addEventListener("keydown", (pressed) => {
  if (pressed.key === "Escape" && !player.hidden) closePlayer();
});

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

function showAnalysis(state) {
  analysisLabel.textContent = state || "";
  analysisLabel.classList.toggle("off", state === "Off");
  analysisLabel.title = state === "Off"
    ? "Analysis is Off: nothing is recorded or sent. Click to switch it On."
    : "Analysis is On. Click to switch it Off (or /on and /off on the bot).";
}

analysisLabel.addEventListener("click", async () => {
  const wanted = analysisLabel.textContent === "Off";
  if (!wanted && !confirm("Switch analysis Off? Nothing is recorded or sent until it is switched On again; Live keeps working.")) return;
  analysisLabel.disabled = true;
  try {
    showAnalysis((await send("/api/analysis", { on: wanted })).analysis);
  } catch (problem) {
    alert(`Not done: ${problem.message}`);
  } finally {
    analysisLabel.disabled = false;
  }
});

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
    showAnalysis(status.analysis);
  }
  if (changed) {
    stopLive();
    syncLive();
  }
}

function showSettingsPart() {
  const wanted = location.hash.slice(1).split("/")[1];
  const part = SETTINGS_PARTS.includes(wanted) ? wanted : SETTINGS_PARTS[0];
  for (const box of document.querySelectorAll("#settings .settings")) {
    box.hidden = box.dataset.part !== part;
  }
  for (const link of document.querySelectorAll("#settings .subtabs a")) {
    link.classList.toggle("active", link.dataset.part === part);
  }
  loadSettings();
  if (part === "reports") loadReports();
}

function showTab() {
  if (location.hash.split("/")[0] === "#notifications") {
    location.replace("#settings/notifications");
    return;
  }
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
    showSettingsPart();
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

async function send(url, payload, extraHeaders = {}) {
  const headers = { "Content-Type": "application/json", "X-Jarvis-Request": "1" };
  const pin = storedPin();
  if (pin) headers["X-Jarvis-Pin"] = pin;
  Object.assign(headers, extraHeaders);
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

function drawCalendar(box, appearances, shown = new Map(), key = "") {
  const counts = {};
  for (const seen of appearances) counts[seen.day] = (counts[seen.day] || 0) + 1;
  const months = [...new Set(Object.keys(counts).map((day) => day.slice(0, 7)))].sort().reverse();
  if (months.length === 0) {
    showNotice(box, "Not seen in any recording yet.");
    return;
  }
  paged(box, months, (month) => monthGrid(month, counts), shown, key);
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
  const viewsGrid = section.querySelector(".chosen-grid");
  const waitingGrid = section.querySelector(".waiting-grid");
  const calendarBox = section.querySelector(".calendar");
  const cardTemplate = document.getElementById("person-card");
  const analyse = section.querySelector(".analyse");
  const spreadBox = section.querySelector(".spread");
  const residentToggle = section.querySelector(".resident-toggle");
  const residentBox = residentToggle.querySelector("input");
  const selectBar = section.querySelector(".select-bar");
  const selectTo = selectBar.querySelector(".select-to");
  const selectName = selectBar.querySelector(".select-name");
  const chosen = new Set();
  const shown = new Map();
  let named = [];
  let order = [];
  let anchor = null;
  let proposal = null;

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
    node.querySelector(".badge").hidden = !entry.resident;
    const form = node.querySelector("form");
    const select = node.querySelector("select");
    if (entry.name) {
      form.remove();
      select.remove();
      return node;
    }
    const article = node.querySelector("article");
    article.dataset.id = entry.id;
    article.classList.toggle("selected", chosen.has(entry.id));
    link.addEventListener("click", (clicked) => {
      clicked.preventDefault();
      pick(entry.id, clicked.shiftKey);
    });
    const input = form.querySelector("input");
    input.placeholder = section.querySelector(".rename-form input").placeholder;
    const report = document.createElement("button");
    report.type = "button";
    report.className = "report";
    report.textContent = "Bad detection";
    report.title = `Not a ${kind === "dog" ? "dog" : "face"}: remove it and keep it as a report`;
    report.addEventListener("click", async () => {
      if (!confirm(`${report.title}?`)) return;
      try {
        await send(`${api}/${entry.id}/report`);
        listResult.textContent = "Reported: it is kept as an example of a bad detection.";
      } catch (problem) {
        listResult.textContent = `Not reported: ${problem.message}`;
      }
      loadList();
    });
    form.after(report);
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

  function showSelection() {
    for (const article of unnamedGrid.querySelectorAll("article")) {
      article.classList.toggle("selected", chosen.has(article.dataset.id));
    }
    selectBar.hidden = chosen.size === 0;
    list.classList.toggle("selecting", chosen.size > 0);
    selectBar.querySelector(".select-count").textContent = `${chosen.size} selected`;
    selectTo.hidden = named.length === 0;
  }

  function pick(id, range) {
    if (range && anchor !== null && order.includes(anchor)) {
      const [from, to] = [order.indexOf(anchor), order.indexOf(id)].sort((a, b) => a - b);
      for (const other of order.slice(from, to + 1)) chosen.add(other);
    } else if (chosen.has(id)) {
      chosen.delete(id);
    } else {
      chosen.add(id);
    }
    anchor = id;
    showSelection();
  }

  function clearSelection() {
    chosen.clear();
    anchor = null;
    showSelection();
  }

  function guessGroups(unnamed) {
    const names = new Map(named.map((entry) => [entry.id, entry.name]));
    const groups = new Map();
    for (const entry of unnamed) {
      const key = names.has(entry.guess) ? entry.guess : "";
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(entry);
    }
    return [...groups].sort(([a, first], [b, second]) =>
      (a === "") - (b === "") || second.length - first.length
    ).map(([key, entries]) => ({
      title: key ? `Looks like ${names.get(key)}` : "No guess",
      entries,
    }));
  }

  function groupBox(group) {
    const box = document.createElement("div");
    box.className = "guess-group";
    const heading = document.createElement("h3");
    heading.className = "heading guess-heading";
    heading.textContent = `${group.title} (${group.entries.length}) `;
    const all = document.createElement("button");
    all.type = "button";
    all.className = "select-all";
    all.textContent = "Select all";
    all.addEventListener("click", () => {
      for (const entry of group.entries) chosen.add(entry.id);
      showSelection();
    });
    heading.append(all);
    const grid = document.createElement("div");
    grid.className = "people-grid";
    paged(grid, group.entries, card, shown, `group:${group.title}`);
    box.append(heading, grid);
    return box;
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
    const groups = guessGroups(data.unnamed);
    order = groups.flatMap((group) => group.entries.map((entry) => entry.id));
    for (const id of [...chosen]) if (!order.includes(id)) chosen.delete(id);
    unnamedGrid.replaceChildren(...groups.map(groupBox));
    if (data.unnamed.length === 0) showNotice(unnamedGrid, "Nothing unnamed.");
    section.querySelector(".unnamed-count").textContent =
      data.unnamed.length ? `(${data.unnamed.length})` : "";
    selectTo.replaceChildren(new Option("Assign to…", ""),
      ...named.map((entry) => new Option(entry.name, entry.id)));
    showSelection();
  }

  function describeBatch(result) {
    const parts = [`${result.name}: ${plural(result.joined.length, "photo", "photos")} joined`];
    if (result.absorbed) parts.push(`${plural(result.absorbed, "look-alike", "look-alikes")} gathered`);
    if (result.gone.length) parts.push(`${result.gone.length} already gone`);
    return parts.join(", ");
  }

  async function assign(payload, target) {
    const count = plural(chosen.size, "photo", "photos");
    if (!confirm(`Join ${count} to ${target}? A merge cannot be undone.`)) return false;
    try {
      listResult.textContent = describeBatch(await send(`${api}/assign`, { ids: [...chosen], ...payload }));
      clearSelection();
    } catch (problem) {
      listResult.textContent = `Not saved: ${problem.message}`;
    }
    loadList();
    return true;
  }

  selectTo.addEventListener("change", async () => {
    const target = selectTo.value;
    if (!target) return;
    await assign({ to: target }, selectTo.selectedOptions[0].textContent);
    selectTo.value = "";
  });

  selectName.addEventListener("submit", async (submitted) => {
    submitted.preventDefault();
    const input = selectName.querySelector("input");
    const name = input.value.trim();
    if (!name) return;
    if (await assign({ name }, name)) input.value = "";
  });

  selectBar.querySelector(".select-report").addEventListener("click", async () => {
    const what = kind === "dog" ? "dog" : "face";
    const count = plural(chosen.size, "photo", "photos");
    if (!confirm(`Report ${count} as bad detections? Each is not a ${what}: it leaves the gallery and is kept as a report.`)) return;
    try {
      const result = await send(`${api}/report`, { ids: [...chosen] });
      listResult.textContent = `Reported ${plural(result.reported.length, "photo", "photos")}` +
        (result.gone.length ? `, ${result.gone.length} already gone` : "") +
        ": each is kept as an example of a bad detection.";
      clearSelection();
    } catch (problem) {
      listResult.textContent = `Not reported: ${problem.message}`;
    }
    loadList();
  });

  selectBar.querySelector(".select-clear").addEventListener("click", clearSelection);

  function tileButton(tile, className, symbol, title, action) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.title = title;
    button.textContent = symbol;
    button.addEventListener("click", action);
    tile.append(button);
    return button;
  }

  function photoTile(photo) {
    const tile = document.createElement("figure");
    tile.className = "view";
    if (photo) {
      const image = document.createElement("img");
      image.src = photo;
      image.alt = "";
      image.loading = "lazy";
      tile.append(image);
    } else {
      const missing = document.createElement("span");
      missing.className = "no-photo";
      missing.textContent = "no photo";
      tile.append(missing);
    }
    return tile;
  }

  async function change(route, done, question, photo) {
    if (question && !confirm(question)) return;
    try {
      showEntry(await send(`${api}/${selected()}/${route}`, { view: photoName(photo) }));
      pageResult.textContent = done;
    } catch (problem) {
      pageResult.textContent = `Not done: ${problem.message}`;
      if (problem.status === 409) loadEntry(selected());
    }
  }

  function photoName(photo) {
    return photo ? photo.split("/").pop() : "";
  }

  function viewTile(photo, index, entry) {
    const tile = photoTile(photo);
    if (photo) {
      const chosen = entry.cover_index === index;
      const favourite = tileButton(tile, "cover", "★",
        chosen ? "The photo shown on the grid" : "Show this photo on the grid",
        () => change(`views/${index}/cover`, "Favourite photo saved.", null, photo));
      favourite.classList.toggle("chosen", chosen);
    }
    if (entry.views > 1) {
      tileButton(tile, "", "×", "Delete this view",
        () => change(`views/${index}/remove`, "View deleted.",
          "Delete this view? It will no longer be used to recognise them.", photo));
      tileButton(tile, "move", "↓", "Move this view to Waiting",
        () => change(`views/${index}/demote`, "View moved to Waiting.", null, photo));
    }
    return tile;
  }

  function waitingTile(photo, index, entry) {
    const tile = photoTile(photo);
    tileButton(tile, "", "×", "Delete this waiting view",
      () => change(`pending/${index}/remove`, "Waiting view deleted.", "Delete this waiting view?", photo));
    const full = entry.views >= 40;
    tileButton(tile, "move", "↑",
      full ? "Chosen is full: move one down or delete one first" : "Move this view into Chosen",
      () => change(`pending/${index}/promote`, "View moved into Chosen.", null, photo));
    return tile;
  }

  function spreadTile(photo, kept) {
    const tile = photoTile(photo);
    tile.classList.toggle("moved", !kept);
    return tile;
  }

  function showProposal() {
    const kept = new Set(proposal.keep);
    const moved = proposal.photos.length - kept.size;
    const distance = (value) => (value === null ? "?" : value.toFixed(2));
    spreadBox.querySelector(".spread-text").textContent =
      `Proposal: keep the ${kept.size} most different views; ${plural(moved, "view", "views")} ` +
      `(faded) wait, or are discarded. The two most alike views kept are ${distance(proposal.closest_now)} ` +
      `apart now and ${distance(proposal.closest_after)} after: higher means more varied.`;
    spreadBox.querySelector(".spread-grid").replaceChildren(
      ...proposal.photos.map((photo, index) => spreadTile(photo, kept.has(index))));
    spreadBox.hidden = false;
  }

  analyse.addEventListener("click", async () => {
    try {
      proposal = await getJSON(`${api}/${selected()}/spread`);
      showProposal();
    } catch (problem) {
      pageResult.textContent = `Not analysed: ${problem.message}`;
    }
  });

  async function keepSpread(discard) {
    const moved = proposal.photos.length - proposal.keep.length;
    if (discard && !confirm(`Delete the other ${plural(moved, "view", "views")} for good?`)) return;
    try {
      showEntry(await send(`${api}/${selected()}/spread`,
        { keep: proposal.keep, signature: proposal.signature, discard }));
      pageResult.textContent = discard
        ? "Kept the most different views; the others were deleted."
        : "Kept the most different views; the others wait.";
    } catch (problem) {
      pageResult.textContent = `Not kept: ${problem.message}`;
    }
  }

  spreadBox.querySelector(".spread-keep").addEventListener("click", () => keepSpread(false));
  spreadBox.querySelector(".spread-discard").addEventListener("click", () => keepSpread(true));

  spreadBox.querySelector(".spread-cancel").addEventListener("click", () => {
    spreadBox.hidden = true;
  });

  function showEntry(entry) {
    analyse.hidden = entry.views + entry.pending <= 40;
    spreadBox.hidden = true;
    section.querySelector(".page-name").textContent = entry.name || unnamedLabel;
    renameForm.querySelector("input").value = entry.name;
    renameForm.querySelector("button").textContent = entry.name ? "Rename" : "Save name";
    residentToggle.hidden = !entry.name;
    residentBox.checked = entry.resident;
    section.querySelector(".views-count").textContent = `(${entry.views} of 40)`;
    section.querySelector(".waiting-count").textContent = entry.pending ? `(${entry.pending})` : "";
    viewsGrid.replaceChildren(...entry.view_photos.map((photo, index) => viewTile(photo, index, entry)));
    const newest = entry.pending_photos.map((photo, index) => ({ photo, index })).reverse();
    paged(waitingGrid, newest, (item) => waitingTile(item.photo, item.index, entry), shown, `waiting:${entry.id}`);
    if (entry.pending === 0) showNotice(waitingGrid, "Nothing waiting.");
    drawCalendar(calendarBox, entry.appearances, shown, `days:${entry.id}`);
  }

  async function loadEntry(id) {
    try {
      showEntry(await getJSON(`${api}/${id}`));
    } catch {
      section.querySelector(".page-name").textContent = "Not found";
      viewsGrid.replaceChildren();
      waitingGrid.replaceChildren();
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

  residentBox.addEventListener("change", async () => {
    const wanted = residentBox.checked;
    try {
      showEntry(await send(`${api}/${selected()}/resident`, { resident: wanted }));
      pageResult.textContent = wanted ? "Marked as a resident." : "No longer a resident.";
    } catch (problem) {
      residentBox.checked = !wanted;
      pageResult.textContent = `Not saved: ${problem.message}`;
    }
  });

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
const detectionForm = document.getElementById("detection-form");
const detectionResult = document.getElementById("detection-result");

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

const modesResult = document.getElementById("modes-result");

function modeButton(mode, name, active) {
  const option = document.createElement("label");
  option.className = "mode-option";
  const radio = document.createElement("input");
  radio.type = "radio";
  radio.name = "notify_mode";
  radio.value = mode;
  radio.checked = mode === active;
  radio.addEventListener("change", async () => {
    try {
      fillSettings(await send("/api/settings", { notify_mode: mode }));
      modesResult.textContent = `${name} is now the active mode.`;
    } catch (problem) {
      modesResult.textContent = `Not changed: ${problem.message}`;
      loadSettings();
    }
  });
  const text = document.createElement("span");
  text.textContent = name;
  option.append(radio, text);
  return option;
}

function modeSwitch(mode, modeName, caseKey, caseName, on) {
  const box = document.createElement("input");
  box.type = "checkbox";
  box.setAttribute("role", "switch");
  box.checked = on;
  box.setAttribute("aria-label", `${caseName} in ${modeName}`);
  box.addEventListener("change", async () => {
    const wanted = box.checked;
    try {
      fillSettings(await send("/api/settings", { notify_modes: { [mode]: { [caseKey]: wanted } } }));
      modesResult.textContent = `${modeName}: ${caseName} ${wanted ? "on" : "off"}.`;
    } catch (problem) {
      box.checked = !wanted;
      modesResult.textContent = `Not saved: ${problem.message}`;
    }
  });
  return box;
}

function showModes(values) {
  document.getElementById("mode-choice").replaceChildren(
    ...values.notify_mode_names.map(([mode, name]) => modeButton(mode, name, values.notify_mode)));
  const table = document.getElementById("modes-table");
  const head = table.querySelector("thead tr");
  head.replaceChildren(head.firstElementChild, ...values.notify_mode_names.map(([mode, name]) => {
    const cell = document.createElement("th");
    cell.scope = "col";
    cell.textContent = name;
    cell.classList.toggle("active", mode === values.notify_mode);
    return cell;
  }));
  table.querySelector("tbody").replaceChildren(...values.notify_cases.map(([caseKey, caseName]) => {
    const row = document.createElement("tr");
    const label = document.createElement("th");
    label.scope = "row";
    label.textContent = caseName;
    row.append(label, ...values.notify_mode_names.map(([mode, modeName]) => {
      const cell = document.createElement("td");
      cell.classList.toggle("active", mode === values.notify_mode);
      cell.append(modeSwitch(mode, modeName, caseKey, caseName, values.notify_modes[mode][caseKey]));
      return cell;
    }));
    return row;
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
  showModes(values);
  showPairing(values);
  archiveForm.archive_path.value = values.archive_path || "";
  archiveForm.archive_after_days.value = values.archive_after_days;
  archiveForm.archive_min_free_gb.value = values.archive_min_free_gb;
  showArchive(values.archive);
  showDetection(values);
}

let confidenceDefaults = {};

const CONFIDENCE_NAMES = { confidence_person: "Person", confidence_dog: "Dog", confidence_animal: "Other animals" };

function showDetection(values) {
  confidenceDefaults = values.confidence_defaults;
  const [low, high] = values.confidence_range;
  detectionForm.querySelector(".confidence-low").textContent = low.toFixed(2);
  detectionForm.querySelector(".confidence-high").textContent = high.toFixed(2);
  const now = document.getElementById("confidence-now");
  now.replaceChildren();
  for (const key of CONFIDENCE_KEYS) {
    const slider = detectionForm[key];
    slider.min = 0;
    slider.max = values.slider_steps;
    slider.step = 1;
    slider.value = values.confidence_positions[key];
    const line = document.createElement("li");
    line.textContent = `${CONFIDENCE_NAMES[key]}: minimum ${values[key].toFixed(2)} now, default ${confidenceDefaults[key].toFixed(2)}.`;
    now.append(line);
  }
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

detectionForm.addEventListener("submit", (submitted) => {
  submitted.preventDefault();
  saveSettings({ confidence_positions: Object.fromEntries(
    CONFIDENCE_KEYS.map((key) => [key, Number(detectionForm[key].value)])) }, detectionResult);
});

document.getElementById("detection-defaults").addEventListener("click", () => {
  saveSettings({ ...confidenceDefaults }, detectionResult);
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
    state = values.paired
      ? "This device is paired for 30 days, renewed with every change made from it."
      : "Enter the PIN set on the M900 once to pair this device.";
  }
  document.getElementById("pin-state").textContent = state;
  const list = document.getElementById("device-list");
  list.replaceChildren(...(values.devices || []).map((device) => {
    const item = document.createElement("li");
    const text = document.createElement("span");
    text.textContent = `${device.label} · last used ${device.last_used.replace("T", " ").slice(0, 16)}`;
    const forget = document.createElement("button");
    forget.type = "button";
    forget.textContent = "Forget";
    forget.addEventListener("click", async () => {
      try {
        await send(`/api/devices/${device.id}/forget`);
        pinResult.textContent = "Device forgotten: it must be paired again.";
      } catch (problem) {
        pinResult.textContent = `Not done: ${problem.message}`;
      }
      loadSettings();
    });
    item.append(text, forget);
    return item;
  }));
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
      await send("/api/pair", {}, { "X-Jarvis-Pin": pin });
      rememberPin("");
      pinResult.textContent = "This device is paired for 30 days, renewed with use.";
    }
    loadSettings();
  } catch (problem) {
    pinResult.textContent = `Not done: ${problem.message}`;
  }
});

const reportsResult = document.getElementById("reports-result");

function reportItem(report) {
  const item = document.createElement("li");
  if (report.photo) {
    const image = document.createElement("img");
    image.src = report.photo;
    image.alt = "";
    image.loading = "lazy";
    item.append(image);
  }
  const text = document.createElement("span");
  const where = report.source === "event" ? "recording" : `${report.kind} tab`;
  text.textContent = `${report.verdict} · ${report.camera} · ${report.at.replace("T", " ").slice(0, 16)} · from the ${where}`;
  const undo = document.createElement("button");
  undo.type = "button";
  undo.textContent = "Undo";
  undo.addEventListener("click", async () => {
    try {
      await send(report.undo);
      reportsResult.textContent = report.source === "event"
        ? "Undone: the label is back on its recording."
        : `Undone: the crop is back in the ${report.kind === "dog" ? "Dogs" : "People"} tab.`;
    } catch (problem) {
      reportsResult.textContent = `Not undone: ${problem.message}`;
    }
    loadReports();
  });
  const actually = document.createElement("select");
  actually.title = "What it actually was";
  actually.append(new Option("Actually…", ""), ...report.choices.map((choice) => new Option(choice, choice)));
  actually.value = report.actually;
  actually.addEventListener("change", async () => {
    try {
      await send(report.describe, { actually: actually.value });
      report.actually = actually.value;
      reportsResult.textContent = actually.value ? `Saved: actually ${actually.value}.` : "Cleared.";
    } catch (problem) {
      reportsResult.textContent = `Not saved: ${problem.message}`;
      actually.value = report.actually;
    }
  });
  item.append(text, actually, undo);
  return item;
}

async function loadReports() {
  const list = document.getElementById("report-list");
  try {
    const found = await getJSON("/api/reports");
    list.replaceChildren(...found.map(reportItem));
    if (found.length === 0) showNotice(list, "No reports.");
  } catch {
    showNotice(list, "Could not read the reports.");
  }
}

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
