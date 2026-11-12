// Apresentação: Reatores de Coluna de Bolhas — seminário de Cinética (FEQ-UNICAMP)
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require(process.argv[2]);

const A = (f) => path.join(__dirname, "assets", f);
const DADOS = JSON.parse(fs.readFileSync(A("dados.json"), "utf8"));

const THEME = {
  name: "Coluna de Bolhas",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0B1F33", lt1: "FFFFFF", dk2: "1B3A57", lt2: "E8F4F7",
    accent1: "1A9BAE", accent2: "E8833A", accent3: "8FD6E1", accent4: "5B6B7B",
    accent5: "2E8B57", accent6: "C0392B", hlink: "1A9BAE", folHlink: "1B3A57",
  },
};
const HEX = THEME.colors;

async function icone(Comp, cor, tam = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + cor, size: tam }));
  const buf = await sharp(Buffer.from(svg)).resize(tam, tam).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

function tamanho(png) {
  // dimensões de um PNG (cabeçalho IHDR)
  const b = fs.readFileSync(png);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13,33 × 7,5 in
  pres.title = "Reatores de Coluna de Bolhas";
  pres.subject = "Seminário de Cinética e Reatores";
  pres.author = "FEQ-UNICAMP";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  const C = pres.SchemeColor;

  // ---------------- layouts ----------------
  pres.defineSlideMaster({
    title: "CONTEUDO",
    background: { color: C.background1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.9,
          fontFace: THEME.headFontFace, fontSize: 32, bold: true, color: C.text1, valign: "middle", align: "left", margin: 0 }, text: "" } },
      { text: { text: "Seminário de Cinética e Reatores · FEQ-UNICAMP", options: {
          x: 0.6, y: 7.0, w: 8, h: 0.3, fontSize: 10, color: C.accent4, margin: 0 } } },
    ],
    slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontSize: 10, color: C.accent4, align: "right" },
  });
  pres.defineSlideMaster({
    title: "SECAO",
    background: { color: C.text1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.6, w: 6.6, h: 1.4,
          fontFace: THEME.headFontFace, fontSize: 44, bold: true, color: C.background1, valign: "middle", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 4.05, w: 6.6, h: 1.2,
          fontSize: 18, color: C.accent3, valign: "top", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({ title: "ESCURO", background: { color: C.text1 }, objects: [] });


  // subscritos: "U_G" → U com G subscrito (em textos de caixas)
  function sub(texto, opts = {}) {
    const partes = [];
    const re = /([A-Za-zε])_([A-Za-z0-9]+)/g;
    let i = 0, m;
    const { breakLine, ...base } = opts;
    while ((m = re.exec(texto))) {
      if (m.index > i) partes.push({ text: texto.slice(i, m.index + 1), options: { ...base } });
      else partes.push({ text: m[1], options: { ...base } });
      partes.push({ text: m[2], options: { ...base, subscript: true } });
      i = m.index + m[0].length;
    }
    if (i < texto.length) partes.push({ text: texto.slice(i), options: { ...base } });
    if (breakLine) partes[partes.length - 1].options.breakLine = true;
    return partes;
  }
  function fixRuns(c) {
    if (typeof c === "string") return c.includes("_") ? sub(c) : c;
    if (Array.isArray(c)) return c.flatMap((r) => (typeof r.text === "string" && r.text.includes("_")) ? sub(r.text, r.options || {}) : [r]);
    return c;
  }
  function novo(opts) {
    const sl = pres.addSlide(opts);
    const add = sl.addText.bind(sl);
    sl.addText = (c, o) => add(fixRuns(c), o);
    return sl;
  }

  const notas = (s, t) => s.addNotes(t);
  const titulo = (s, t) => s.addText(t, { placeholder: "title" });

  function bolhaDeco(s, x, y, d, transp = 70) {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: C.accent3, transparency: transp },
      line: { color: C.accent3, width: 1, transparency: 40 }, objectName: "bolha" });
  }

  function cartao(s, x, y, w, h, nome) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: C.background2 },
      line: { color: C.background2 }, objectName: nome });
  }

  function circIcone(s, img, x, y, d, cor, nome) {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: cor }, line: { color: cor }, objectName: nome + "_c" });
    s.addImage({ data: img, x: x + d * 0.22, y: y + d * 0.22, w: d * 0.56, h: d * 0.56, objectName: nome + "_i" });
  }

  function equacao(s, arq, x, y, hAlvo, nome) {
    const t = tamanho(A(arq));
    const w = hAlvo * t.w / t.h;
    s.addImage({ path: A(arq), x, y, w, h: hAlvo, objectName: nome, altText: nome });
    return w;
  }

  const eixo = { catAxisLabelColor: HEX.accent4, valAxisLabelColor: HEX.accent4, catAxisLabelFontFace: "+mn-lt",
    valAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 12, valAxisLabelFontSize: 12,
    valGridLine: { color: "D9E3E8", size: 0.75 }, catGridLine: { style: "none" },
    legendFontFace: "+mn-lt", legendFontSize: 12, legendColor: HEX.dk1, titleFontFace: "+mn-lt",
    titleFontSize: 14, titleColor: HEX.dk1, dataLabelFontFace: "+mn-lt", dataLabelFontSize: 11,
    dataLabelColor: HEX.dk1, valAxisTitleFontFace: "+mn-lt", catAxisTitleFontFace: "+mn-lt",
    valAxisTitleFontSize: 12, catAxisTitleFontSize: 12, valAxisTitleColor: HEX.accent4, catAxisTitleColor: HEX.accent4 };

  // ícones
  const I = {};
  const lista = { ind: [fa.FaIndustry, HEX.lt1], fla: [fa.FaFlask, HEX.lt1], gas: [fa.FaGasPump, HEX.lt1],
    bio: [fa.FaSeedling, HEX.lt1], agua: [fa.FaWater, HEX.lt1], nuvem: [fa.FaCloud, HEX.lt1],
    ok: [fa.FaCheck, HEX.lt1], no: [fa.FaTimes, HEX.lt1], seta: [fa.FaArrowUp, HEX.lt1],
    cogs: [fa.FaCogs, HEX.lt1], chart: [fa.FaChartLine, HEX.lt1], ruler: [fa.FaRulerVertical, HEX.lt1],
    flask2: [fa.FaVial, HEX.lt1], bolhas: [fa.FaCircle, HEX.lt1], comp: [fa.FaDesktop, HEX.lt1],
    swarm: [fa.FaBraille, HEX.lt1], filtro: [fa.FaFilter, HEX.lt1], fire: [fa.FaFire, HEX.lt1] };
  for (const [k, [c, cor]] of Object.entries(lista)) I[k] = await icone(c, cor);

  // ================= 1. CAPA =================
  pres.addSection({ title: "Abertura" });
  let s = novo({ masterName: "ESCURO", sectionTitle: "Abertura" });
  s.addImage({ path: A("capa.jpg"), x: 0, y: 0, w: 13.333, h: 7.5, sizing: { type: "cover", w: 13.333, h: 7.5 }, objectName: "foto_capa", altText: "Coluna de bolhas em laboratório" });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 7.6, h: 7.5, fill: { color: C.text1, transparency: 15 }, line: { color: C.text1, transparency: 100 }, objectName: "veu" });
  s.addText("SEMINÁRIO DE CINÉTICA E REATORES · FEQ-UNICAMP", { x: 0.8, y: 1.7, w: 6.5, h: 0.4, fontSize: 14, bold: true, color: C.accent3, margin: 0, isTextBox: true, objectName: "kicker" });
  s.addText("Reatores de Coluna de Bolhas", { x: 0.8, y: 2.2, w: 6.5, h: 1.9, fontFace: THEME.headFontFace, fontSize: 48, bold: true, color: C.background1, margin: 0, valign: "top", isTextBox: true, objectName: "titulo_capa" });
  s.addText("Por que são tão usados, como se projetam e onde o CFD ajuda", { x: 0.8, y: 4.2, w: 6.3, h: 1.0, fontSize: 22, color: C.background1, margin: 0, valign: "top", isTextBox: true, objectName: "subtitulo" });
  s.addText("Novembro de 2026", { x: 0.8, y: 6.4, w: 6, h: 0.4, fontSize: 14, color: C.accent3, margin: 0, isTextBox: true, objectName: "data" });
  notas(s, "Abertura. Vamos falar de um reator muito simples por fora e complexo por dentro: a coluna de bolhas. Três perguntas guiam a apresentação: por que ela é tão usada, como se projeta usando cinética e transferência de massa, e onde a simulação computacional ajuda.");

  // ================= 2. GANCHO =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "Abertura" });
  titulo(s, "Uma pergunta para começar");
  s.addImage({ path: A("aspersor.jpg"), x: 7.6, y: 1.45, w: 5.1, h: 5.3, sizing: { type: "cover", w: 5.1, h: 5.3 }, objectName: "foto_aspersor", altText: "Aspersor de gás formando bolhas" });
  s.addText("Como fazer um gás reagir com um líquido, em escala industrial, sem nenhuma peça móvel?", { x: 0.6, y: 1.9, w: 6.6, h: 2.4, fontFace: THEME.headFontFace, fontSize: 30, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "pergunta" });
  s.addText("Soprando bolhas.", { x: 0.6, y: 4.6, w: 6.6, h: 0.8, fontFace: THEME.headFontFace, fontSize: 36, bold: true, italic: true, color: C.accent2, margin: 0, isTextBox: true, objectName: "resposta" });
  s.addText("O gás entra pelo fundo, sobe em bolhas e, no caminho, dissolve e reage no líquido.", { x: 0.6, y: 5.6, w: 6.6, h: 0.9, fontSize: 18, color: C.accent4, margin: 0, valign: "top", isTextBox: true, objectName: "explica" });
  notas(s, "Pergunta para prender a atenção. A resposta é surpreendentemente simples: soprar o gás por baixo. Não há agitador, não há rotor, e mesmo assim esse reator processa milhares de toneladas por dia em refinarias, indústrias químicas e estações de tratamento.");

  // ================= 3. ROTEIRO =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "Abertura" });
  titulo(s, "Roteiro");
  const partes = [["1", "O reator", "Como funciona, onde se usa, vantagens e desvantagens", "0–12 min"],
    ["2", "Cinética e projeto", "Do caminho da molécula de gás à altura do reator", "12–30 min"],
    ["3", "Onde entra o CFD", "O que simulamos, o que comparamos e o que aprendemos", "30–50 min"],
    ["4", "O que levar para casa", "Mensagens finais e perguntas", "50–60 min"]];
  partes.forEach(([n, t, d, m], i) => {
    const x = 0.6 + i * 3.08;
    cartao(s, x, 1.7, 2.8, 4.6, "parte" + n);
    s.addShape(pres.shapes.OVAL, { x: x + 0.3, y: 2.0, w: 1.0, h: 1.0, fill: { color: i === 2 ? C.accent2 : C.accent1 }, line: { color: i === 2 ? C.accent2 : C.accent1 }, objectName: "num" + n });
    s.addText(n, { x: x + 0.3, y: 2.0, w: 1.0, h: 1.0, fontSize: 30, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "numtxt" + n });
    s.addText(t, { x: x + 0.3, y: 3.25, w: 2.3, h: 0.9, fontFace: THEME.headFontFace, fontSize: 22, bold: true, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "pt" + n });
    s.addText(d, { x: x + 0.3, y: 4.2, w: 2.3, h: 1.3, fontSize: 15, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "pd" + n });
    s.addText(m, { x: x + 0.3, y: 5.65, w: 2.3, h: 0.4, fontSize: 14, bold: true, color: C.accent4, margin: 0, isTextBox: true, objectName: "pm" + n });
  });
  notas(s, "Quatro partes em uma hora. A terceira parte, em laranja, é o nosso estudo de caso com simulação.");

  // ================= SEÇÃO 1 =================
  pres.addSection({ title: "1. O reator" });
  s = novo({ masterName: "SECAO", sectionTitle: "1. O reator" });
  s.addImage({ path: A("bolhas.jpg"), x: 7.9, y: 0, w: 5.433, h: 7.5, sizing: { type: "cover", w: 5.433, h: 7.5 }, objectName: "foto_bolhas", altText: "Bolhas subindo em líquido" });
  s.addText("1 · O reator", { placeholder: "title" });
  s.addText("Simples por fora, complexo por dentro", { placeholder: "body" });
  notas(s, "Primeira parte: o equipamento.");

  // ================= 4. COMO FUNCIONA =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "1. O reator" });
  titulo(s, "Como funciona");
  // esquema da coluna
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 1.6, y: 1.55, w: 2.3, h: 5.1, rectRadius: 0.15, fill: { color: C.background1 }, line: { color: C.text2, width: 2.5 }, objectName: "coluna" });
  s.addShape(pres.shapes.RECTANGLE, { x: 1.66, y: 2.35, w: 2.18, h: 4.15, fill: { color: C.accent3, transparency: 55 }, line: { color: C.accent3, transparency: 100 }, objectName: "liquido" });
  const bs = [[1.9, 6.0, 0.18], [2.6, 5.7, 0.14], [3.3, 6.05, 0.16], [2.2, 5.2, 0.2], [3.0, 4.9, 0.15], [1.95, 4.4, 0.13], [2.75, 4.2, 0.19], [3.4, 3.8, 0.14], [2.3, 3.4, 0.17], [3.1, 3.1, 0.15], [2.0, 2.8, 0.14], [2.7, 2.6, 0.16]];
  bs.forEach(([x, y, d], i) => s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: C.background1 }, line: { color: C.accent1, width: 1.5 }, objectName: "b" + i }));
  s.addShape(pres.shapes.UP_ARROW, { x: 2.5, y: 6.65, w: 0.5, h: 0.32, fill: { color: C.accent2 }, line: { color: C.accent2 }, objectName: "seta_gas" });
  s.addShape(pres.shapes.UP_ARROW, { x: 2.5, y: 1.15, w: 0.5, h: 0.38, fill: { color: C.accent4 }, line: { color: C.accent4 }, objectName: "seta_saida" });
  s.addText("gás", { x: 3.05, y: 6.62, w: 0.8, h: 0.35, fontSize: 13, bold: true, color: C.accent2, margin: 0, isTextBox: true, objectName: "rot_gas" });
  s.addText("gás de saída", { x: 3.05, y: 1.15, w: 1.6, h: 0.35, fontSize: 13, color: C.accent4, margin: 0, isTextBox: true, objectName: "rot_saida" });
  s.addText("líquido", { x: 0.55, y: 4.1, w: 1.0, h: 0.35, fontSize: 13, color: C.accent1, bold: true, margin: 0, isTextBox: true, objectName: "rot_liq" });
  const passos = [["1", "O gás entra pelo aspersor, no fundo, e se divide em bolhas."],
    ["2", "As bolhas sobem; o reagente gasoso dissolve no líquido."],
    ["3", "A reação acontece no líquido, ou num catalisador sólido em suspensão."],
    ["4", "O gás não reagido sai pelo topo; o líquido pode ser batelada ou contínuo."]];
  passos.forEach(([n, t], i) => {
    const y = 1.75 + i * 1.22;
    s.addShape(pres.shapes.OVAL, { x: 5.2, y, w: 0.7, h: 0.7, fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: "pn" + n });
    s.addText(n, { x: 5.2, y, w: 0.7, h: 0.7, fontSize: 20, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "pnt" + n });
    s.addText(t, { x: 6.15, y: y - 0.05, w: 6.5, h: 0.8, fontSize: 20, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: "pt" + n });
  });
  notas(s, "Funcionamento em quatro passos. O ponto-chave para a cinética: o reagente precisa primeiro sair da bolha e dissolver no líquido; só então reage. Por isso a transferência de massa entra no projeto tanto quanto a cinética.");

  // ================= 5. ONDE SE USA =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "1. O reator" });
  titulo(s, "Onde se usa");
  const usos = [[I.ind, "Oxidações em fase líquida", "Ácido tereftálico, oxidação de cicloexano"],
    [I.fla, "Hidrogenações e clorações", "Química fina e intermediários"],
    [I.gas, "Fischer–Tropsch e metanol", "Coluna de lama, com catalisador sólido suspenso"],
    [I.bio, "Fermentações aeróbias", "Biorreatores de baixo cisalhamento"],
    [I.agua, "Tratamento de efluentes", "Aeração de lodos e águas residuais"],
    [I.nuvem, "Absorção de gases", "Remoção de CO₂ e H₂S com reação"]];
  usos.forEach(([img, t, d], i) => {
    const col = i % 3, lin = Math.floor(i / 3);
    const x = 0.6 + col * 4.1, y = 1.6 + lin * 2.6;
    cartao(s, x, y, 3.85, 2.3, "uso" + i);
    circIcone(s, img, x + 0.3, y + 0.35, 0.85, i === 2 ? C.accent2 : C.accent1, "uso" + i);
    s.addText(t, { x: x + 1.35, y: y + 0.3, w: 2.35, h: 0.95, fontFace: THEME.headFontFace, fontSize: 18, bold: true, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: "ut" + i });
    s.addText(d, { x: x + 0.3, y: y + 1.35, w: 3.35, h: 0.75, fontSize: 15, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "ud" + i });
  });
  s.addText("Fontes: Deckwer (1992); Kantarci et al. (2005).", { x: 0.6, y: 6.62, w: 8, h: 0.3, fontSize: 10, color: C.accent4, margin: 0, isTextBox: true, objectName: "fonte" });
  notas(s, "Aplicações. Em comum: um gás pouco solúvel precisa reagir no líquido, muitas vezes com calor liberado, o que favorece um reator bem misturado e fácil de resfriar. O Fischer–Tropsch, destacado, é o caso clássico de coluna de lama.");

  // ================= 6. VANTAGENS × DESVANTAGENS =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "1. O reator" });
  titulo(s, "Vantagens e desvantagens");
  const vant = ["Sem partes móveis: construção simples e barata",
    "Boa transferência de massa: muita área de bolha por volume",
    "Excelente troca de calor: opera quase isotérmica",
    "Aceita sólidos em suspensão (catalisador em lama)",
    "Operação e manutenção fáceis"];
  const desv = ["Retromistura intensa: o líquido se comporta quase como um CSTR",
    "Desempenho muito sensível ao aspersor, ao diâmetro e ao líquido",
    "Em vazões altas, as bolhas coalescem e a área interfacial cai",
    "Separar o catalisador do líquido dá trabalho",
    "Coluna alta de líquido: o gás precisa ser comprimido"];
  [[vant, "Vantagens", C.accent5, I.ok, 0.6], [desv, "Desvantagens", C.accent6, I.no, 6.85]].forEach(([itens, cab, cor, ic, x]) => {
    cartao(s, x, 1.55, 5.9, 5.2, "card_" + cab);
    circIcone(s, ic, x + 0.3, 1.8, 0.7, cor, "ic_" + cab);
    s.addText(cab, { x: x + 1.2, y: 1.8, w: 4.4, h: 0.7, fontFace: THEME.headFontFace, fontSize: 24, bold: true, color: cor, margin: 0, valign: "middle", isTextBox: true, objectName: "cab_" + cab });
    s.addText(itens.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < itens.length - 1, paraSpaceAfter: 10 } })),
      { x: x + 0.3, y: 2.75, w: 5.3, h: 3.8, fontSize: 17, color: C.text1, valign: "top", margin: 0, isTextBox: true, objectName: "lista_" + cab });
  });
  notas(s, "Vantagens e desvantagens. Para a cinética, a desvantagem mais importante é a primeira: a retromistura. O líquido circula muito, então a coluna se comporta quase como um tanque de mistura perfeita, o que reduz a conversão em relação a um reator pistonado do mesmo volume. A segunda desvantagem, a sensibilidade ao aspersor e à escala, é exatamente onde o CFD ajuda.");

  // ================= 7. COMPARAÇÃO =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "1. O reator" });
  titulo(s, "Frente a outros reatores gás–líquido");
  const H = (t) => ({ text: t, options: { bold: true, color: HEX.lt1, fill: { color: HEX.dk2 }, align: "center", valign: "middle" } });
  const R = (t, dest) => ({ text: t, options: { align: "center", valign: "middle", color: HEX.dk1, fill: { color: dest ? "D4EEF2" : HEX.lt1 }, bold: !!dest } });
  const L = (t) => ({ text: t, options: { bold: true, color: HEX.dk1, fill: { color: HEX.lt2 }, valign: "middle" } });
  const linhas = [["Partes móveis", "não", "sim (agitador)", "não", "não"],
    ["Consumo de energia", "baixo", "alto", "baixo", "baixo"],
    ["Transferência de massa", "boa", "muito boa", "moderada", "boa"],
    ["Retromistura do líquido", "alta", "total (CSTR)", "baixa (≈ PFR)", "moderada"],
    ["Troca de calor", "excelente", "boa", "ruim", "boa"],
    ["Sólidos em suspensão", "sim", "sim", "não (entope)", "sim"]];
  s.addTable([[H(""), H("Coluna de bolhas"), H("Tanque agitado"), H("Coluna recheada"), H("Airlift")],
    ...linhas.map(([a, ...r]) => [L(a), ...r.map((t, i) => R(t, i === 0))])],
    { x: 0.6, y: 1.6, w: 12.1, colW: [3.1, 2.25, 2.25, 2.25, 2.25], rowH: 0.62, fontSize: 16, fontFace: THEME.bodyFontFace,
      border: { type: "solid", color: "FFFFFF", pt: 2 }, objectName: "tabela_comparacao" });
  s.addText("Comparação qualitativa, ordem de grandeza típica (Deckwer, 1992; Kantarci et al., 2005).", { x: 0.6, y: 6.15, w: 12, h: 0.35, fontSize: 12, italic: true, color: C.accent4, margin: 0, isTextBox: true, objectName: "nota_tab" });
  notas(s, "A coluna de bolhas troca um pouco de eficiência de mistura por simplicidade e excelente troca de calor. O tanque agitado transfere melhor, mas gasta energia e é um CSTR perfeito. A coluna recheada se aproxima de um PFR, mas não aceita sólidos e troca mal calor.");

  // ================= 8. REGIMES =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "1. O reator" });
  titulo(s, "Dois regimes de escoamento");
  function miniColuna(x, tipo) {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.6, w: 1.9, h: 4.6, rectRadius: 0.12, fill: { color: C.background1 }, line: { color: C.text2, width: 2 }, objectName: "col_" + tipo });
    s.addShape(pres.shapes.RECTANGLE, { x: x + 0.05, y: 2.0, w: 1.8, h: 4.1, fill: { color: C.accent3, transparency: 55 }, line: { color: C.accent3, transparency: 100 }, objectName: "liq_" + tipo });
    const pts = tipo === "hom"
      ? [[0.3, 5.6, 0.12], [0.8, 5.5, 0.12], [1.3, 5.65, 0.12], [0.5, 4.9, 0.12], [1.1, 4.8, 0.12], [1.5, 4.3, 0.12], [0.3, 4.2, 0.12], [0.8, 3.7, 0.12], [1.3, 3.5, 0.12], [0.5, 3.0, 0.12], [1.1, 2.8, 0.12], [1.55, 2.4, 0.12], [0.25, 2.4, 0.12]]
      : [[0.6, 5.3, 0.45], [0.3, 5.9, 0.1], [1.4, 5.8, 0.12], [1.0, 4.4, 0.55], [0.3, 4.0, 0.1], [1.5, 3.7, 0.1], [0.45, 2.9, 0.5], [1.3, 2.6, 0.12], [1.55, 4.9, 0.1]];
    pts.forEach(([dx, y, d], i) => s.addShape(pres.shapes.OVAL, { x: x + dx, y, w: d, h: d, fill: { color: C.background1 }, line: { color: C.accent1, width: 1.5 }, objectName: tipo + "_b" + i }));
  }
  miniColuna(0.9, "hom");
  miniColuna(7.0, "het");
  s.addText([{ text: "Homogêneo", options: { fontFace: THEME.headFontFace, fontSize: 24, bold: true, color: HEX.accent1, breakLine: true } },
    { text: "U_G baixa (até ≈ 3–5 cm/s)", options: { fontSize: 15, color: HEX.accent4, breakLine: true } },
    { text: "Bolhas pequenas e uniformes, pouca circulação, muita área por volume de gás.", options: { fontSize: 17, color: HEX.dk1 } }],
    { x: 3.05, y: 2.2, w: 3.6, h: 3.2, valign: "top", margin: 0, paraSpaceAfter: 8, isTextBox: true, objectName: "txt_hom" });
  s.addText([{ text: "Heterogêneo", options: { fontFace: THEME.headFontFace, fontSize: 24, bold: true, color: HEX.accent2, breakLine: true } },
    { text: "U_G alta (acima de ≈ 5–8 cm/s)", options: { fontSize: 15, color: HEX.accent4, breakLine: true } },
    { text: "Bolhas grandes por coalescência, circulação forte, mais retromistura.", options: { fontSize: 17, color: HEX.dk1 } }],
    { x: 9.15, y: 2.2, w: 3.6, h: 3.2, valign: "top", margin: 0, paraSpaceAfter: 8, isTextBox: true, objectName: "txt_het" });
  s.addText("A transição depende do aspersor: furos grandes antecipam o regime heterogêneo (Besagni & Inzoli, 2016).", { x: 0.6, y: 6.4, w: 12.1, h: 0.4, fontSize: 14, italic: true, color: C.text2, margin: 0, isTextBox: true, objectName: "nota_reg" });
  notas(s, "Dois regimes. No homogêneo, as bolhas são pequenas e parecidas, e a retenção de gás cresce quase linearmente com a vazão. No heterogêneo, bolhas grandes sobem rápido pelo centro e arrastam o líquido. O nosso estudo de caso fica no regime homogêneo, a 2 cm/s.");

  // ================= SEÇÃO 2 =================
  pres.addSection({ title: "2. Cinética e projeto" });
  s = novo({ masterName: "SECAO", sectionTitle: "2. Cinética e projeto" });
  s.addImage({ path: A("industria.jpg"), x: 7.9, y: 0, w: 5.433, h: 7.5, sizing: { type: "cover", w: 5.433, h: 7.5 }, objectName: "foto_industria", altText: "Planta química" });
  s.addText("2 · Cinética e projeto", { placeholder: "title" });
  s.addText("Quem limita a reação: a química ou o transporte?", { placeholder: "body" });
  notas(s, "Segunda parte: como a cinética entra no projeto.");

  // ================= 9. CAMINHO DA MOLÉCULA =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "2. Cinética e projeto" });
  titulo(s, "O caminho de uma molécula de gás");
  const etapas = [["Bolha", "gás"], ["Filme gasoso", "difusão"], ["Interface", "dissolve (Henry)"], ["Filme líquido", "difusão (+ reação)"], ["Seio do líquido", "reação"]];
  etapas.forEach(([t, d], i) => {
    const x = 0.75 + i * 2.5;
    s.addShape(pres.shapes.OVAL, { x: x + 0.35, y: 1.65, w: 1.3, h: 1.3, fill: { color: i === 4 ? C.accent2 : C.accent1, transparency: i === 0 ? 0 : 10 }, line: { color: i === 4 ? C.accent2 : C.accent1 }, objectName: "et" + i });
    s.addText(String(i + 1), { x: x + 0.35, y: 1.65, w: 1.3, h: 1.3, fontSize: 30, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "etn" + i });
    s.addText(t, { x: x - 0.1, y: 3.1, w: 2.2, h: 0.5, fontFace: THEME.headFontFace, fontSize: 18, bold: true, color: C.text1, align: "center", margin: 0, isTextBox: true, objectName: "ett" + i });
    s.addText(d, { x: x - 0.1, y: 3.55, w: 2.2, h: 0.45, fontSize: 15, color: C.accent4, align: "center", margin: 0, isTextBox: true, objectName: "etd" + i });
    if (i < 4) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 1.82, y: 2.12, w: 0.55, h: 0.36, fill: { color: C.accent4 }, line: { color: C.accent4 }, objectName: "sa" + i });
  });
  cartao(s, 0.6, 4.4, 12.1, 2.25, "card_eq");
  const wK = equacao(s, "eq_K.png", 0.95, 4.75, 1.0, "eq_resistencias");
  s.addText([{ text: "Resistências em série: ", options: { bold: true } }, { text: "a etapa mais lenta controla a taxa. Para gases pouco solúveis (O₂, CO₂, H₂), o filme gasoso é desprezível." }],
    { x: 0.95 + wK + 0.4, y: 4.6, w: 12.1 - wK - 0.9, h: 1.9, fontSize: 17, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: "txt_resist" });
  notas(s, "Antes de reagir, a molécula percorre cinco etapas. Cada uma é uma resistência, e elas se somam como resistências elétricas em série. A constante global K junta transferência de massa (kL·a·E) e cinética (k1·εL). É essa equação que liga a cinética de laboratório ao reator.");

  // ================= 10. HATTA =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "2. Cinética e projeto" });
  titulo(s, "Reação ou difusão: quem é mais rápida?");
  const wHa = equacao(s, "eq_Ha.png", 0.6, 1.5, 0.95, "eq_hatta");
  s.addText("O número de Hatta compara a velocidade da reação com a da difusão no filme líquido.", { x: 0.6 + wHa + 0.4, y: 1.5, w: 12.1 - wHa - 0.4, h: 0.95, fontSize: 18, color: C.text2, valign: "middle", margin: 0, isTextBox: true, objectName: "txt_ha" });
  const regs = [["Lento", "Ha < 0,3", "A reação acontece no seio do líquido.", "O projeto depende de kLa e do volume de líquido.", C.accent5],
    ["Rápido", "Ha > 3", "A reação acontece dentro do filme líquido.", "O projeto depende só da área interfacial a (E ≈ Ha).", C.accent2],
    ["Instantâneo", "Ha ≫ Ei", "Reage no plano onde A e B se encontram.", "Limitado pela difusão do reagente líquido B (E = Ei).", C.accent6]];
  regs.forEach(([t, crit, a, b, cor], i) => {
    const x = 0.6 + i * 4.1;
    cartao(s, x, 2.85, 3.85, 3.85, "reg" + i);
    s.addText(t, { x: x + 0.3, y: 3.05, w: 3.3, h: 0.6, fontFace: THEME.headFontFace, fontSize: 26, bold: true, color: cor, margin: 0, isTextBox: true, objectName: "regt" + i });
    s.addText(crit, { x: x + 0.3, y: 3.65, w: 3.3, h: 0.45, fontSize: 18, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "regc" + i });
    s.addText([{ text: a, options: { breakLine: true } }, { text: b, options: { bold: true } }],
      { x: x + 0.3, y: 4.25, w: 3.3, h: 2.3, fontSize: 16, color: C.text2, valign: "top", margin: 0, paraSpaceAfter: 8, isTextBox: true, objectName: "regd" + i });
  });
  notas(s, "Este é o slide mais importante da parte de cinética. A cinética define o regime, e o regime define qual parâmetro hidrodinâmico precisa ser conhecido com precisão. No regime lento, importa o kLa. No rápido, a reação acontece no filme e o kL some da equação: só a área interfacial importa. Vamos usar dois exemplos: oxigênio consumido lentamente (Ha ≈ 0,03) e CO2 em soda (Ha ≈ 3,5).");

  // ================= 11. O QUE O PROJETO PRECISA =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "2. Cinética e projeto" });
  titulo(s, "O que o projeto precisa saber da hidrodinâmica");
  const stats = [["0,06–0,09", "εG", "fração do volume ocupada por gás"],
    ["50–125 m⁻¹", "a", "área de bolha por volume de reator"],
    ["0,02–0,05 s⁻¹", "kLa", "coeficiente de transferência de massa (O₂)"],
    ["≈ 0,015 m²/s", "D_L", "retromistura do líquido"]];
  stats.forEach(([v, sim, d], i) => {
    const x = 0.6 + i * 3.08;
    cartao(s, x, 1.6, 2.8, 3.4, "stat" + i);
    s.addText(sim, { x: x + 0.25, y: 1.8, w: 2.3, h: 0.6, fontFace: THEME.headFontFace, fontSize: 26, italic: true, bold: true, color: C.accent1, margin: 0, isTextBox: true, objectName: "sts" + i });
    s.addText(v, { x: x + 0.25, y: 2.45, w: 2.4, h: 0.9, fontSize: 30, bold: true, color: C.text1, margin: 0, valign: "middle", isTextBox: true, fit: "shrink", objectName: "stv" + i });
    s.addText(d, { x: x + 0.25, y: 3.45, w: 2.35, h: 1.3, fontSize: 15, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "std" + i });
  });
  const wa = equacao(s, "eq_a.png", 0.9, 5.35, 0.85, "eq_area");
  s.addText([{ text: "Na prática, esses números vêm de correlações empíricas ", options: {} }, { text: "(Akita & Yoshida, 1973; Shah et al., 1982; Deckwer, 1992). ", options: { color: HEX.accent4 } }, { text: "Valores para ar–água, U_G = 2 cm/s, D = 0,15 m.", options: { italic: true } }],
    { x: 0.9 + wa + 0.5, y: 5.25, w: 11.8 - wa - 0.6, h: 1.1, fontSize: 16, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: "txt_corr" });
  notas(s, "Quatro números que alimentam a equação de projeto. A área interfacial vem do holdup e do diâmetro das bolhas. Faixas calculadas por nós para a nossa coluna, a partir de correlações e dos dois experimentos de referência.");

  // ================= 12. DA CINÉTICA À ALTURA =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "2. Cinética e projeto" });
  titulo(s, "Da cinética à conversão");
  cartao(s, 0.6, 1.55, 5.2, 5.15, "card_proj");
  s.addText("Gás em escoamento pistonado", { x: 0.9, y: 1.75, w: 4.7, h: 0.5, fontFace: THEME.headFontFace, fontSize: 20, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "t_pfr" });
  equacao(s, "eq_X.png", 0.9, 2.35, 1.0, "eq_conversao");
  s.addText([{ text: "Mais altura H ou mais K → mais conversão.", options: { breakLine: true } },
    { text: "O líquido, porém, não é pistonado: ele circula. O grau de mistura é medido pelo Péclet:", options: {} }],
    { x: 0.9, y: 3.55, w: 4.7, h: 1.7, fontSize: 16, color: C.text2, valign: "top", margin: 0, paraSpaceAfter: 8, isTextBox: true, objectName: "txt_pfr" });
  equacao(s, "eq_Pe.png", 0.9, 5.35, 0.95, "eq_peclet");
  s.addChart(pres.charts.LINE, [
    { name: "PFR (Pe → ∞)", labels: ["0,5", "1", "2", "3", "5"], values: [39.3, 63.2, 86.5, 95.0, 99.3] },
    { name: "Pe = 5", labels: ["0,5", "1", "2", "3", "5"], values: [37.2, 58.3, 79.6, 88.9, 96.1] },
    { name: "Pe = 1", labels: ["0,5", "1", "2", "3", "5"], values: [34.8, 53.2, 72.1, 81.4, 90.2] },
    { name: "CSTR (Pe → 0)", labels: ["0,5", "1", "2", "3", "5"], values: [33.3, 50.0, 66.7, 75.0, 83.3] }],
    { x: 6.1, y: 1.55, w: 6.6, h: 5.15, ...eixo, chartColors: [HEX.accent1, "5FB8C6", HEX.accent2, HEX.accent6], lineSize: 3, lineDataSymbolSize: 8,
      showLegend: true, legendPos: "b", showTitle: true, title: "Conversão (%) × Damköhler (k₁·τ), reação de 1ª ordem",
      showCatAxisTitle: true, catAxisTitle: "Da = k₁·τ", showValAxisTitle: true, valAxisTitle: "Conversão X (%)", valAxisMinVal: 30, valAxisMaxVal: 100, objectName: "graf_ww" });
  notas(s, "Para o gás, a equação de projeto é uma exponencial simples: quanto maior a constante global K e a altura, maior a conversão. Para o líquido, a retromistura pesa: com Da = 3, um reator pistonado converte 95 %, mas uma coluna muito misturada (Pe = 1) só 81 %. Para atingir 95 % nessa condição, seria preciso 2,6 vezes mais volume (solução de Wehner & Wilhelm, 1956).");

  // ================= 13. CORRELAÇÕES DISCORDAM =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "2. Cinética e projeto" });
  titulo(s, "O problema: as previsões discordam");
  s.addChart(pres.charts.BAR, [{ name: "εG a 2 cm/s",
    labels: ["Akita & Yoshida (correlação)", "Hikita et al. (correlação)", "Besagni & Inzoli 2016 (experimento)", "Mudde et al. 2009 (experimento)", "Reilly et al. (correlação)"],
    values: [0.055, 0.062, 0.069, 0.089, 0.105] }],
    { x: 0.6, y: 1.5, w: 7.6, h: 5.2, barDir: "bar", ...eixo, chartColors: [HEX.accent4, HEX.accent4, HEX.accent1, HEX.accent1, HEX.accent4],
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000", valAxisMinVal: 0, valAxisMaxVal: 0.12, valAxisHidden: true,
      showLegend: false, showTitle: true, title: "Retenção de gás εG prevista para a mesma coluna (ar–água, 2 cm/s)", catAxisLabelFontSize: 13, objectName: "graf_discordam" });
  s.addText("≈ 2×", { x: 8.7, y: 1.8, w: 4.0, h: 1.4, fontFace: THEME.headFontFace, fontSize: 72, bold: true, color: C.accent2, margin: 0, isTextBox: true, objectName: "big2x" });
  s.addText("entre a menor e a maior previsão", { x: 8.7, y: 3.2, w: 4.0, h: 0.5, fontSize: 18, color: C.text2, margin: 0, isTextBox: true, objectName: "big2x_txt" });
  s.addText([{ text: "Só trocar o aspersor ", options: { bold: true } }, { text: "muda εG em ~30 % nos experimentos (cinza: correlações; azul: medidas)." }],
    { x: 8.7, y: 4.2, w: 4.0, h: 1.6, fontSize: 17, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "txt_asp" });
  notas(s, "Este é o problema que motiva o CFD. Para a mesma coluna e a mesma vazão, as correlações clássicas variam quase duas vezes. E os experimentos mostram que o aspersor sozinho muda a retenção em 30 %. Como a área interfacial depende de εG, o erro passa direto para o tamanho do reator.");

  // ================= SEÇÃO 3 =================
  pres.addSection({ title: "3. Onde entra o CFD" });
  s = novo({ masterName: "SECAO", sectionTitle: "3. Onde entra o CFD" });
  s.addImage({ path: A("pluma_div.png"), x: 9.3, y: 0.3, w: 3.1, h: 6.9, sizing: { type: "contain", w: 3.1, h: 6.9 }, objectName: "pluma_div", altText: "Pluma de bolhas simulada" });
  s.addText("3 · Onde entra o CFD", { placeholder: "title" });
  s.addText("Simular as bolhas para não depender só de correlações", { placeholder: "body" });
  notas(s, "Terceira parte: o nosso estudo de caso com fluidodinâmica computacional.");

  // ================= 14. O QUE É A SIMULAÇÃO =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "3. Onde entra o CFD" });
  titulo(s, "O que é a simulação, sem mistério");
  const pipe = [["Entradas", ["geometria da coluna", "vazão de gás", "propriedades do ar e da água", "tamanho das bolhas"], C.accent4],
    ["Modelo", ["água e ar como dois fluidos que se misturam", "conservação de massa e de movimento para cada um", "forças entre bolha e líquido: arrasto, sustentação, massa virtual"], C.accent1],
    ["Resultados", ["retenção de gás εG", "área interfacial a", "circulação do líquido"], C.accent1],
    ["Projeto", ["constante global K", "regime (Ha)", "altura e conversão"], C.accent2]];
  pipe.forEach(([t, itens, cor], i) => {
    const x = 0.6 + i * 3.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.65, w: 2.7, h: 0.75, rectRadius: 0.1, fill: { color: cor }, line: { color: cor }, objectName: "pipe_h" + i });
    s.addText(t, { x, y: 1.65, w: 2.7, h: 0.75, fontFace: THEME.headFontFace, fontSize: 20, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "pipe_t" + i });
    cartao(s, x, 2.55, 2.7, 3.4, "pipe_c" + i);
    s.addText(itens.map((tt, j) => ({ text: tt, options: { bullet: true, breakLine: j < itens.length - 1, paraSpaceAfter: 6 } })),
      { x: x + 0.15, y: 2.7, w: 2.45, h: 3.1, fontSize: 15, color: C.text1, valign: "top", margin: 0, isTextBox: true, objectName: "pipe_l" + i });
    if (i < 3) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.74, y: 1.85, w: 0.32, h: 0.35, fill: { color: C.accent4 }, line: { color: C.accent4 }, objectName: "pipe_s" + i });
  });
  s.addText("CFD = fluidodinâmica computacional: resolve as equações de transporte numa malha de milhares de pequenos volumes.", { x: 0.6, y: 6.2, w: 12.1, h: 0.45, fontSize: 15, italic: true, color: C.text2, margin: 0, isTextBox: true, objectName: "def_cfd" });
  notas(s, "O CFD não substitui a equação de projeto: ele fornece os parâmetros dela. Tratamos água e ar como dois fluidos que ocupam o mesmo espaço em frações diferentes (modelo euleriano de dois fluidos). As bolhas não são desenhadas uma a uma; entram por forças médias. A saída é exatamente o que as correlações tentam prever: εG, área e circulação.");

  // ================= 15. O CASO ESTUDADO (vídeo) =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "3. Onde entra o CFD" });
  titulo(s, "O caso estudado");
  const caso = [["Coluna", "0,15 m de diâmetro, 0,9 m de água"], ["Gás", "ar a 2 cm/s, distribuído no fundo"], ["Bolhas", "5 mm (medidas: 3,5–5 mm)"],
    ["Simulações", "2D (minutos) e 3D (horas)"], ["Comparação", "experimentos recentes na mesma geometria"]];
  caso.forEach(([k, v], i) => {
    const y = 1.7 + i * 0.95;
    s.addShape(pres.shapes.OVAL, { x: 0.6, y: y + 0.12, w: 0.36, h: 0.36, fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: "cb" + i });
    s.addText([{ text: k + ": ", options: { bold: true, color: HEX.dk1 } }, { text: v, options: { color: HEX.dk2 } }],
      { x: 1.15, y, w: 6.2, h: 0.6, fontSize: 19, valign: "middle", margin: 0, isTextBox: true, objectName: "ct" + i });
  });
  const capa = fs.readFileSync(A("video_capa.png")).toString("base64");
  s.addMedia({ type: "video", path: A("coluna_3D_volume.mp4"), x: 8.55, y: 1.45, w: 2.45, h: 5.6, cover: "image/png;base64," + capa, objectName: "video_pluma" });
  s.addText("Pluma de bolhas simulada em 3D (t = 6 → 29 s). Azul mais escuro = mais gás. Clique para tocar.", { x: 11.15, y: 2.4, w: 1.6, h: 3.0, fontSize: 13, italic: true, color: C.accent4, margin: 0, valign: "top", isTextBox: true, objectName: "leg_video" });
  notas(s, "Montamos uma coluna de laboratório: 15 cm de diâmetro e 90 cm de água, com ar entrando pelo fundo a 2 cm/s, no regime homogêneo. Rodamos versões 2D, que levam minutos, e uma 3D, que leva horas. Clique no vídeo: a região azul é onde há mais gás; dá para ver a coluna encher de bolhas e a superfície livre subir. Uma lição prática: a primeira tentativa injetava ar puro no fundo, formava uma camada de gás instável e o cálculo divergia. Injetar uma mistura diluída, como as bolhas reais, resolveu.");

  // ================= 16. TAMANHO DE BOLHA =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "3. Onde entra o CFD" });
  titulo(s, "1ª lição: o tamanho da bolha manda");
  s.addChart(pres.charts.LINE, [{ name: "εG previsto (UG = 2 cm/s)", labels: DADOS.ds.map((d) => String(d).replace(".", ",")), values: DADOS.eps_d }],
    { x: 0.6, y: 1.5, w: 7.4, h: 5.2, ...eixo, chartColors: [HEX.accent1], lineSize: 3, lineDataSymbolSize: 8, showLegend: false,
      showTitle: true, title: "Retenção de gás × diâmetro da bolha (mesma vazão de gás)", showCatAxisTitle: true, catAxisTitle: "diâmetro da bolha (mm)",
      showValAxisTitle: true, valAxisTitle: "εG", valAxisMinVal: 0, valAxisMaxVal: 0.4, objectName: "graf_bolha" });
  [["1 mm", "εG = 0,17", 1.6], ["5 mm", "εG = 0,086", 3.55]].forEach(([d, v, y], i) => {
    cartao(s, 8.5, y, 4.2, 1.7, "dcard" + i);
    s.addText(d, { x: 8.8, y: y + 0.15, w: 3.6, h: 0.5, fontSize: 18, bold: true, color: C.accent4, margin: 0, isTextBox: true, objectName: "dd" + i });
    s.addText(v, { x: 8.8, y: y + 0.65, w: 3.6, h: 0.85, fontFace: THEME.headFontFace, fontSize: 36, bold: true, color: i ? C.accent1 : C.accent2, margin: 0, isTextBox: true, objectName: "dv" + i });
  });
  s.addText("Bolhas pequenas sobem devagar, ficam mais tempo na coluna e acumulam mais gás. Na 1ª simulação, um diâmetro errado dobrou a retenção.",
    { x: 8.5, y: 5.45, w: 4.2, h: 1.3, fontSize: 15, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "txt_bolha" });
  notas(s, "A primeira lição veio de um erro: rodamos com bolhas de 1 mm sem querer e a retenção dobrou. A conta é simples: a retenção é a vazão de gás dividida pela velocidade de subida das bolhas. Bolhas de 1 mm sobem a 0,12 m/s; as de 5 mm, a 0,23 m/s. Moral: num modelo com um único tamanho de bolha, esse tamanho é o parâmetro mais sensível.");

  // ================= 17. VALIDAÇÃO =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "3. Onde entra o CFD" });
  titulo(s, "A simulação confere com o experimento?");
  s.addChart(pres.charts.BAR, [
    { name: "Experimento (Mudde et al., 2009)", labels: ["1,5", "2,0", "2,5", "3,2", "3,9"], values: [0.061, 0.089, 0.110, 0.160, 0.200] },
    { name: "Simulação", labels: ["1,5", "2,0", "2,5", "3,2", "3,9"], values: [0.064, 0.087, 0.108, 0.138, 0.169] }],
    { x: 0.6, y: 1.5, w: 7.6, h: 5.2, barDir: "col", barGrouping: "clustered", ...eixo, chartColors: [HEX.accent4, HEX.accent1],
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", dataLabelFontSize: 10, showLegend: true, legendPos: "b",
      showTitle: true, title: "Retenção de gás εG, coluna de 0,15 m com aspersor uniforme", showCatAxisTitle: true, catAxisTitle: "vazão de gás UG (cm/s)",
      valAxisMinVal: 0, valAxisMaxVal: 0.24, objectName: "graf_valid" });
  s.addText("±5 %", { x: 8.7, y: 1.7, w: 4.0, h: 1.2, fontFace: THEME.headFontFace, fontSize: 60, bold: true, color: C.accent1, margin: 0, isTextBox: true, objectName: "big5" });
  s.addText("de desvio até εG ≈ 0,11", { x: 8.7, y: 2.9, w: 4.0, h: 0.5, fontSize: 18, color: C.text2, margin: 0, isTextBox: true, objectName: "big5_txt" });
  s.addText([{ text: "Acima disso, o modelo subestima (−15 %): ", options: { bold: true } },
    { text: "num enxame denso, as bolhas atrapalham a subida umas das outras, e o modelo trata cada bolha como se estivesse sozinha." }],
    { x: 8.7, y: 3.7, w: 4.0, h: 2.6, fontSize: 16, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "txt_enxame" });
  notas(s, "Validação contra um experimento de 2009, com dados publicados em 2024, numa coluna do mesmo diâmetro e com aspersor uniforme de agulhas. Até 2,5 cm/s o erro fica dentro de 5 %, o mesmo nível de modelos de referência da literatura recente (Draw & Rzehak, 2024). Em vazões maiores, falta o efeito de enxame no arrasto: é uma limitação conhecida, e a correção já existe na literatura.");

  // ================= 18. CIRCULAÇÃO =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "3. Onde entra o CFD" });
  titulo(s, "2ª lição: o líquido circula");
  s.addChart(pres.charts.LINE, [{ name: "Velocidade média da água (3D)", labels: DADOS.rR.map((r) => String(r).replace(".", ",")), values: DADOS.vL3D }],
    { x: 0.6, y: 1.5, w: 7.4, h: 5.2, ...eixo, chartColors: [HEX.accent1], lineSize: 3, lineDataSymbolSize: 7, showLegend: false,
      showTitle: true, title: "Velocidade vertical média da água a meia altura", showCatAxisTitle: true, catAxisTitle: "posição radial r/R (0 = centro, 1 = parede)",
      showValAxisTitle: true, valAxisTitle: "velocidade (m/s)", valAxisMinVal: -0.1, valAxisMaxVal: 0.1, valAxisLabelFormatCode: "0.00", objectName: "graf_circ" });
  [["↑ sobe no centro", "≈ +0,06 m/s", C.accent1, 1.6], ["↓ desce na parede", "≈ −0,08 m/s", C.accent2, 3.25]].forEach(([t, v, cor, y], i) => {
    cartao(s, 8.5, y, 4.2, 1.45, "circ" + i);
    s.addText(t, { x: 8.8, y: y + 0.15, w: 3.6, h: 0.5, fontSize: 18, bold: true, color: cor, margin: 0, isTextBox: true, objectName: "ct_" + i });
    s.addText(v, { x: 8.8, y: y + 0.65, w: 3.6, h: 0.65, fontFace: THEME.headFontFace, fontSize: 28, bold: true, color: C.text1, margin: 0, isTextBox: true, objectName: "cv_" + i });
  });
  s.addText("Essa circulação é a retromistura do líquido (D_L). É ela que afasta a coluna do reator pistonado e reduz a conversão (slide 14).",
    { x: 8.5, y: 4.95, w: 4.2, h: 1.8, fontSize: 15, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "txt_circ" });
  notas(s, "A segunda lição é o que nenhuma correlação mostra diretamente: o líquido sobe pelo centro e desce junto à parede, trocando de sentido perto de 60–70 % do raio. Essa é a origem física da retromistura que entra no modelo de dispersão axial. Comparamos 2D e 3D: a retenção mudou só 4 %, e a circulação ficou parecida.");

  // ================= 19. CFD → CINÉTICA =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "3. Onde entra o CFD" });
  titulo(s, "De volta à cinética: quanto isso muda o reator?");
  s.addChart(pres.charts.BAR, [
    { name: "O₂ com consumo lento (regime lento)", labels: ["Correlação clássica", "Experimento (spider)", "Experimento (agulhas)", "Simulação"], values: [1.00, 0.58, 0.63, 0.73] },
    { name: "CO₂ em NaOH 0,1 M (regime rápido)", labels: ["Correlação clássica", "Experimento (spider)", "Experimento (agulhas)", "Simulação"], values: [1.00, 0.45, 0.43, 0.53] }],
    { x: 0.6, y: 1.5, w: 7.6, h: 5.2, barDir: "col", barGrouping: "clustered", ...eixo, chartColors: [HEX.accent5, HEX.accent2],
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", showLegend: true, legendPos: "b",
      showTitle: true, title: "Volume de reator para a mesma conversão (correlação = 1)", valAxisMinVal: 0, valAxisMaxVal: 1.2, objectName: "graf_volume" });
  s.addText("≈ 2×", { x: 8.7, y: 1.7, w: 4.0, h: 1.2, fontFace: THEME.headFontFace, fontSize: 60, bold: true, color: C.accent2, margin: 0, isTextBox: true, objectName: "big2x_b" });
  s.addText("superdimensionamento pela correlação no regime rápido", { x: 8.7, y: 2.9, w: 4.0, h: 0.8, fontSize: 17, color: C.text2, margin: 0, isTextBox: true, objectName: "big2x_b_txt" });
  s.addText([{ text: "Exemplo: ", options: { bold: true } }, { text: "remover 95 % do CO₂ exige 1,16 m de altura pela correlação, 0,61 m pela simulação e 0,52 m pelo experimento." }],
    { x: 8.7, y: 3.95, w: 4.0, h: 1.6, fontSize: 16, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "txt_co2" });
  s.addText("Com controle cinético puro, as quatro fontes dariam o mesmo reator.", { x: 8.7, y: 5.75, w: 4.0, h: 0.9, fontSize: 15, italic: true, color: C.accent4, margin: 0, valign: "top", isTextBox: true, objectName: "txt_cin" });
  notas(s, "Fechando o ciclo com a cinética. Usamos a mesma cinética com a hidrodinâmica vinda de quatro fontes. No regime lento, as diferenças ficam em 30–40 %. No regime rápido, como o CO2 em soda, o projeto depende só da área interfacial, e a correlação clássica dobraria a coluna. Se a reação fosse muito lenta, a hidrodinâmica não importaria e nenhuma simulação seria necessária. É a cinética que diz quando vale a pena simular.");

  // ================= 20. LIMITAÇÕES =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "3. Onde entra o CFD" });
  titulo(s, "Limitações e próximos passos");
  const lim = [[I.bolhas, "Um só tamanho de bolha", "Próximo passo: balanço populacional, que calcula quebra e coalescência."],
    [I.swarm, "Enxames densos (εG > 0,15)", "Próximo passo: correção de enxame no arrasto."],
    [I.filtro, "Aspersor idealizado", "Próximo passo: geometria real do distribuidor e regime heterogêneo."],
    [I.flask2, "Reação fora da simulação", "Próximo passo: resolver espécies e reação dentro do CFD (pontos quentes, seletividade)."]];
  lim.forEach(([img, t, d], i) => {
    const col = i % 2, lin = Math.floor(i / 2);
    const x = 0.6 + col * 6.15, y = 1.6 + lin * 2.55;
    cartao(s, x, y, 5.95, 2.3, "lim" + i);
    circIcone(s, img, x + 0.3, y + 0.35, 0.85, C.accent1, "lim" + i);
    s.addText(t, { x: x + 1.4, y: y + 0.3, w: 4.3, h: 0.6, fontFace: THEME.headFontFace, fontSize: 20, bold: true, color: C.text1, margin: 0, valign: "middle", isTextBox: true, objectName: "limt" + i });
    s.addText(d, { x: x + 1.4, y: y + 0.95, w: 4.3, h: 1.2, fontSize: 16, color: C.text2, margin: 0, valign: "top", isTextBox: true, objectName: "limd" + i });
  });
  notas(s, "Honestidade sobre o que o modelo não faz. Todas essas limitações têm soluções conhecidas na literatura e são o caminho natural de continuação do trabalho.");

  // ================= SEÇÃO 4: CONCLUSÕES =================
  pres.addSection({ title: "4. O que levar para casa" });
  s = novo({ masterName: "ESCURO", sectionTitle: "4. O que levar para casa" });
  bolhaDeco(s, 11.2, 0.5, 1.4); bolhaDeco(s, 12.2, 2.1, 0.7); bolhaDeco(s, 10.6, 5.6, 1.0, 80);
  s.addText("O que levar para casa", { x: 0.8, y: 0.7, w: 10, h: 0.9, fontFace: THEME.headFontFace, fontSize: 40, bold: true, color: C.background1, margin: 0, isTextBox: true, objectName: "tit_conc" });
  const conc = [["Simples por fora, complexo por dentro", "Barata e versátil, mas a hidrodinâmica decide o desempenho."],
    ["A cinética diz o que medir", "Regime lento: kLa. Regime rápido: área interfacial."],
    ["O CFD validado reduz a incerteza", "Concorda com o experimento (±5 %) e mostra a circulação que as correlações não veem."]];
  conc.forEach(([t, d], i) => {
    const y = 2.0 + i * 1.6;
    s.addShape(pres.shapes.OVAL, { x: 0.8, y, w: 1.0, h: 1.0, fill: { color: i === 2 ? C.accent2 : C.accent1 }, line: { color: i === 2 ? C.accent2 : C.accent1 }, objectName: "cn" + i });
    s.addText(String(i + 1), { x: 0.8, y, w: 1.0, h: 1.0, fontSize: 30, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "cnt" + i });
    s.addText(t, { x: 2.1, y: y - 0.05, w: 8.6, h: 0.55, fontFace: THEME.headFontFace, fontSize: 24, bold: true, color: C.background1, margin: 0, isTextBox: true, objectName: "ctit" + i });
    s.addText(d, { x: 2.1, y: y + 0.5, w: 8.6, h: 0.6, fontSize: 18, color: C.accent3, margin: 0, isTextBox: true, objectName: "cdes" + i });
  });
  notas(s, "Três mensagens. Primeiro: a coluna de bolhas é simples, mas o desempenho depende da hidrodinâmica. Segundo: o número de Hatta diz qual parâmetro importa. Terceiro: um modelo de CFD validado reduz a incerteza das correlações e mostra fenômenos que elas não capturam.");

  // ================= REFERÊNCIAS =================
  s = novo({ masterName: "CONTEUDO", sectionTitle: "4. O que levar para casa" });
  titulo(s, "Referências");
  const refs1 = ["Akita, K.; Yoshida, F. (1973). Ind. Eng. Chem. Process Des. Dev., 12, 76–80.",
    "Besagni, G.; Inzoli, F. (2016). Chem. Eng. Sci., 146, 259–290.",
    "Danckwerts, P. V. (1970). Gas–Liquid Reactions. McGraw-Hill.",
    "Deckwer, W.-D. (1992). Bubble Column Reactors. Wiley.",
    "Draw, M.; Rzehak, R. (2024). Int. J. Multiphase Flow, 181, 104969.",
    "Hikita, H. et al. (1980). Chem. Eng. J., 20, 59–67.",
    "Kantarci, N.; Borak, F.; Ulgen, K. O. (2005). Process Biochem., 40, 2263–2283."];
  const refs2 = ["Levenspiel, O. (1999). Chemical Reaction Engineering, 3ª ed., cap. 23–24. Wiley.",
    "Mudde, R. F. et al. (2009). Ind. Eng. Chem. Res., 48, 148–158.",
    "Pohorecki, R.; Moniuk, W. (1988). Chem. Eng. Sci., 43, 1677–1684.",
    "Reilly, I. G. et al. (1986). Can. J. Chem. Eng., 64, 705–717.",
    "Shah, Y. T. et al. (1982). AIChE J., 28, 353–379.",
    "Tomiyama, A. et al. (2002). Chem. Eng. Sci., 57, 1849–1858.",
    "Wehner, J. F.; Wilhelm, R. H. (1956). Chem. Eng. Sci., 6, 89–93."];
  [[refs1, 0.6], [refs2, 6.75]].forEach(([rs, x], k) => s.addText(rs.map((t, i) => ({ text: t, options: { breakLine: i < rs.length - 1, paraSpaceAfter: 9 } })),
    { x, y: 1.6, w: 5.9, h: 5.1, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true, objectName: "refs" + k }));
  notas(s, "Referências citadas. Os scripts, dados e simulações estão nos repositórios do grupo.");

  // ================= OBRIGADO =================
  s = novo({ masterName: "ESCURO", sectionTitle: "4. O que levar para casa" });
  s.addImage({ path: A("bolhas.jpg"), x: 7.9, y: 0, w: 5.433, h: 7.5, sizing: { type: "cover", w: 5.433, h: 7.5 }, objectName: "foto_fim", altText: "Bolhas" });
  s.addText("Obrigado!", { x: 0.8, y: 2.4, w: 6.8, h: 1.3, fontFace: THEME.headFontFace, fontSize: 60, bold: true, color: C.background1, margin: 0, isTextBox: true, objectName: "obrigado" });
  s.addText("Perguntas?", { x: 0.8, y: 3.8, w: 6.8, h: 0.9, fontFace: THEME.headFontFace, fontSize: 36, italic: true, color: C.accent3, margin: 0, isTextBox: true, objectName: "perguntas" });
  s.addText("Seminário de Cinética e Reatores · FEQ-UNICAMP", { x: 0.8, y: 6.4, w: 6.8, h: 0.4, fontSize: 14, color: C.accent3, margin: 0, isTextBox: true, objectName: "rodape_fim" });
  notas(s, "Encerramento e perguntas.");

  const out = path.join(__dirname, "Coluna_de_Bolhas_Seminario.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("ok", out);
})();
