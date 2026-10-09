const NOMES = {
  person: "pessoa",
  dog: "cachorro",
  cat: "gato",
  bird: "pássaro",
  horse: "cavalo",
  sheep: "ovelha",
  cow: "vaca",
};

const ATUALIZAR_MS = 15000;

const campoDia = document.getElementById("dia");
const lista = document.getElementById("eventos");
const resumo = document.getElementById("resumo");
const modelo = document.getElementById("cartao");
const botaoAnterior = document.getElementById("anterior");
const botaoProximo = document.getElementById("proximo");

let diasComGravacao = [];

function hojeISO() {
  const agora = new Date();
  const local = new Date(agora.getTime() - agora.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function plural(n, um, varios) {
  return `${n} ${n === 1 ? um : varios}`;
}

function cartao(evento) {
  const no = modelo.content.cloneNode(true);
  const imagem = no.querySelector("img");
  if (evento.thumbnail) {
    imagem.src = evento.thumbnail;
  } else {
    imagem.remove();
  }
  no.querySelector(".hora").textContent = evento.time;
  no.querySelector(".camera").textContent = evento.camera;
  const rotulos = no.querySelector(".rotulos");
  rotulos.textContent = evento.labels.map((r) => NOMES[r] || r).join(", ") || "?";
  rotulos.classList.toggle("pessoa", evento.labels.includes("person"));
  no.querySelector(".duracao").textContent =
    `${evento.seconds.toLocaleString("pt-BR")} s`;
  return no;
}

function contarPorCamera(eventos) {
  const contagem = {};
  for (const e of eventos) {
    contagem[e.camera] = (contagem[e.camera] || 0) + 1;
  }
  return Object.entries(contagem)
    .map(([camera, n]) => `${camera} ${n}`)
    .join(" · ");
}

function atualizarSetas() {
  const dia = campoDia.value;
  botaoAnterior.disabled = !diasComGravacao.some((d) => d < dia);
  botaoProximo.disabled = !diasComGravacao.some((d) => d > dia);
}

async function carregar() {
  const dia = campoDia.value;
  const resposta = await fetch(`/api/eventos?dia=${dia}`);
  if (!resposta.ok) {
    resumo.textContent = "Não consegui ler as gravações.";
    return;
  }
  const dados = await resposta.json();
  lista.replaceChildren(...dados.eventos.map(cartao));
  if (dados.eventos.length === 0) {
    const vazio = document.createElement("p");
    vazio.className = "vazio";
    vazio.textContent = "Nenhuma gravação neste dia.";
    lista.append(vazio);
    resumo.textContent = "";
  } else {
    resumo.textContent =
      `${plural(dados.eventos.length, "gravação", "gravações")} · ${contarPorCamera(dados.eventos)}`;
  }
  atualizarSetas();
}

async function carregarDias() {
  const resposta = await fetch("/api/dias");
  diasComGravacao = resposta.ok ? await resposta.json() : [];
  atualizarSetas();
}

function irPara(dia) {
  campoDia.value = dia;
  carregar();
}

botaoAnterior.addEventListener("click", () => {
  const antes = diasComGravacao.filter((d) => d < campoDia.value);
  if (antes.length) irPara(antes[0]);
});

botaoProximo.addEventListener("click", () => {
  const depois = diasComGravacao.filter((d) => d > campoDia.value);
  if (depois.length) irPara(depois[depois.length - 1]);
});

document.getElementById("hoje").addEventListener("click", () => irPara(hojeISO()));
campoDia.addEventListener("change", carregar);

const quadroCameras = document.getElementById("cameras");
let cameras = [];

function abaAtual() {
  return location.hash === "#gravacoes" ? "gravacoes" : "ao-vivo";
}

function ligarAoVivo(ligar) {
  if (!ligar) {
    for (const imagem of quadroCameras.querySelectorAll("img")) {
      imagem.removeAttribute("src");
    }
    quadroCameras.replaceChildren();
    return;
  }
  if (quadroCameras.children.length) return;
  if (cameras.length === 0) {
    const vazio = document.createElement("p");
    vazio.className = "vazio";
    vazio.textContent = "Nenhuma câmera ativa.";
    quadroCameras.append(vazio);
    return;
  }
  for (const nome of cameras) {
    const imagem = document.createElement("img");
    imagem.alt = nome;
    imagem.src = `/ao-vivo/${encodeURIComponent(nome)}`;
    quadroCameras.append(imagem);
  }
}

function mostrarAba() {
  const aba = abaAtual();
  for (const secao of document.querySelectorAll(".aba")) {
    secao.classList.toggle("ativa", secao.id === aba);
  }
  for (const link of document.querySelectorAll(".abas a")) {
    link.classList.toggle("ativa", link.dataset.aba === aba);
  }
  ligarAoVivo(aba === "ao-vivo" && !document.hidden);
  if (aba === "gravacoes") {
    carregarDias().then(carregar);
  }
}

window.addEventListener("hashchange", mostrarAba);
document.addEventListener("visibilitychange", () => {
  ligarAoVivo(abaAtual() === "ao-vivo" && !document.hidden);
});

setInterval(() => {
  if (abaAtual() === "gravacoes" && campoDia.value === hojeISO() && !document.hidden) {
    carregarDias();
    carregar();
  }
}, ATUALIZAR_MS);

campoDia.value = hojeISO();
fetch("/api/cameras")
  .then((resposta) => (resposta.ok ? resposta.json() : []))
  .then((lista) => {
    cameras = lista;
    mostrarAba();
  });
