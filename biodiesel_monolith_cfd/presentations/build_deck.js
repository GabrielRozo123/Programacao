/**
 * Preliminary Qualification — Seminário de Mestrado
 * Gabriel Hernandez Rozo | FEQ/UNICAMP
 * Structured deck: theme + layouts + placeholders + sections
 */
const pptxgen = require("pptxgenjs");
const path = require("path");
const { applyTheme } = require("/root/.claude/skills/synced/486ab0f2-4570-40a9-bfc8-e2134f0359c0_cda03110-513a-43b7-af1d-0c3964bef3c9/pptx/scripts/apply_theme.js");

const FIG = path.join(__dirname, "figs");
const OUT = path.join(__dirname, "Preliminary_Qualification_v2.pptx");

const THEME = {
  name: "Monolith CFD",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0B3C49",   // deep petrol — dominant
    lt1: "FFFFFF",
    dk2: "24505C",
    lt2: "EDF3F4",
    accent1: "2A9D8F",  // teal
    accent2: "E76F51",  // coral — corrections / alerts
    accent3: "E9C46A",  // gold — highlights
    accent4: "6B7B82",  // muted grey
    accent5: "1C7293",
    accent6: "A8C5C9",
    hlink: "2A9D8F",
    folHlink: "6B7B82",
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";            // 13.3 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "Gabriel Hernandez Rozo";
pres.title = "Preliminary Qualification — CFD of Monolithic Reactors for Biodiesel";
pres.company = "FEQ/UNICAMP";

const C = pres.SchemeColor;
const FOOT = "Gabriel H. Rozo · FEQ/UNICAMP · Seminário de Mestrado";

/* ── Layouts ──────────────────────────────────────────────────────────── */

pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: THEME.colors.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 2.25, w: 11.5, h: 1.5,
        fontSize: 40, bold: true, color: C.background1, align: "left", margin: 0 }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: 0.9, y: 3.75, w: 10.6, h: 1.0,
        fontSize: 17, color: THEME.colors.accent6, align: "left", margin: 0 }, text: " " } },
  ],
});

pres.defineSlideMaster({
  title: "SECTION",
  background: { color: THEME.colors.dk1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 3.0, w: 11.5, h: 1.1,
        fontSize: 34, bold: true, color: C.background1, align: "left", margin: 0 }, text: " " } },
    { placeholder: { options: { name: "body", type: "body", x: 0.9, y: 4.15, w: 10.0, h: 0.8,
        fontSize: 16, color: THEME.colors.accent6, align: "left", margin: 0 }, text: " " } },
  ],
});

pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.75, y: 0.45, w: 11.8, h: 0.78,
        fontSize: 30, bold: true, color: C.text1, align: "left", margin: 0 }, text: " " } },
    { text: { text: FOOT, options: { x: 0.75, y: 6.92, w: 9.0, h: 0.3, fontSize: 10,
        color: THEME.colors.accent4, align: "left", margin: 0, isTextBox: true } } },
  ],
  slideNumber: { x: 12.4, y: 6.92, w: 0.5, h: 0.3, fontSize: 10, color: THEME.colors.accent4, align: "right" },
});

pres.defineSlideMaster({
  title: "CONTENT_TINT",
  background: { color: THEME.colors.lt2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.75, y: 0.45, w: 11.8, h: 0.78,
        fontSize: 30, bold: true, color: C.text1, align: "left", margin: 0 }, text: " " } },
    { text: { text: FOOT, options: { x: 0.75, y: 6.92, w: 9.0, h: 0.3, fontSize: 10,
        color: THEME.colors.accent4, align: "left", margin: 0, isTextBox: true } } },
  ],
  slideNumber: { x: 12.4, y: 6.92, w: 0.5, h: 0.3, fontSize: 10, color: THEME.colors.accent4, align: "right" },
});

/* ── Helpers ──────────────────────────────────────────────────────────── */

// Stat callout card
function stat(s, { x, y, w, value, label, sub, accent = THEME.colors.accent1, name }) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h: 1.95, rectRadius: 0.08, fill: { color: C.background1 },
    line: { color: THEME.colors.accent6, width: 1 },
    shadow: { type: "outer", color: "0B3C49", opacity: 0.1, blur: 10, offset: 2, angle: 90 },
    objectName: name,
  });
  s.addText(value, { x: x + 0.18, y: y + 0.18, w: w - 0.36, h: 0.78, fontSize: 34, bold: true,
    color: accent, align: "left", margin: 0, isTextBox: true });
  s.addText(label, { x: x + 0.18, y: y + 0.95, w: w - 0.36, h: 0.34, fontSize: 13, bold: true,
    color: C.text1, align: "left", valign: "top", margin: 0, isTextBox: true });
  s.addText(sub, { x: x + 0.18, y: y + 1.29, w: w - 0.36, h: 0.56, fontSize: 11.5,
    color: THEME.colors.accent4, align: "left", valign: "top", margin: 0, isTextBox: true });
}

// Numbered step row
function stepRow(s, { x, y, w, n, head, body, accent = THEME.colors.accent1 }) {
  s.addShape(pres.ShapeType.ellipse, { x, y, w: 0.46, h: 0.46, fill: { color: accent },
    objectName: `step-${n}` });
  s.addText(String(n), { x, y, w: 0.46, h: 0.46, fontSize: 15, bold: true,
    color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
  s.addText(head, { x: x + 0.66, y: y - 0.05, w: w - 0.66, h: 0.32, fontSize: 15, bold: true,
    color: C.text1, align: "left", valign: "top", margin: 0, isTextBox: true });
  s.addText(body, { x: x + 0.66, y: y + 0.28, w: w - 0.66, h: 0.5, fontSize: 12.5,
    color: THEME.colors.accent4, align: "left", valign: "top", margin: 0, isTextBox: true });
}

// Caption under a figure
function caption(s, txt, { x, y, w }) {
  s.addText(txt, { x, y, w, h: 0.3, fontSize: 11, italic: true,
    color: THEME.colors.accent4, align: "left", margin: 0, isTextBox: true });
}

/* ══ 1. TITLE ═════════════════════════════════════════════════════════ */
pres.addSection({ title: "Opening" });
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Opening" });
  s.addText("PRELIMINARY QUALIFICATION", { x: 0.9, y: 1.62, w: 9, h: 0.4, fontSize: 14,
    bold: true, charSpacing: 3, color: THEME.colors.accent3, align: "left", margin: 0, isTextBox: true });
  s.addText("CFD Modelling of a Structured Monolithic Reactor for Biodiesel Production",
    { placeholder: "title" });
  s.addText("Heterogeneous transesterification in a catalytic washcoat channel — model development, verification and regime analysis",
    { placeholder: "body" });

  s.addShape(pres.ShapeType.line, { x: 0.9, y: 5.35, w: 3.2, h: 0,
    line: { color: THEME.colors.accent1, width: 2.5 }, objectName: "rule" });
  s.addText("CANDIDATE", { x: 0.9, y: 5.6, w: 4.5, h: 0.28, fontSize: 11, bold: true,
    charSpacing: 2, color: THEME.colors.accent3, margin: 0, isTextBox: true });
  s.addText("Gabriel Hernandez Rozo", { x: 0.9, y: 5.9, w: 5.0, h: 0.35, fontSize: 17,
    color: C.background1, margin: 0, isTextBox: true });
  s.addText("ADVISORS", { x: 6.6, y: 5.6, w: 5.5, h: 0.28, fontSize: 11, bold: true,
    charSpacing: 2, color: THEME.colors.accent3, margin: 0, isTextBox: true });
  s.addText("Prof. Dr. Raphael Soeiro Suppino\nProf. Dr. Dirceu Noriler",
    { x: 6.6, y: 5.9, w: 5.8, h: 0.7, fontSize: 15, color: C.background1, margin: 0,
      lineSpacing: 20, isTextBox: true });
  s.addText("School of Chemical Engineering · UNICAMP · November 2026",
    { x: 0.9, y: 6.85, w: 8, h: 0.3, fontSize: 11, color: THEME.colors.accent4,
      margin: 0, isTextBox: true });
  s.addNotes("Apresentação de andamento. A pesquisa está em curso: o modelo CFD está construído e verificado; os dados experimentais ainda não chegaram.");
}

/* ══ 2. MOTIVATION ════════════════════════════════════════════════════ */
pres.addSection({ title: "Context" });
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Context" });
  s.addText("Why a monolithic reactor for biodiesel", { placeholder: "title" });

  const items = [
    ["Heterogeneous catalysis", "Solid catalyst removes the soap formation and washing steps that burden homogeneous alkaline routes."],
    ["Structured channels", "Straight parallel channels give an ordered flow field and a negligible pressure drop."],
    ["Thin catalytic washcoat", "Catalyst is coated on the channel wall — reaction becomes a surface process."],
    ["Open question", "Monoliths are designed to defeat mass-transfer limits. Does this system actually have one?"],
  ];
  items.forEach(([h, b], i) => stepRow(s, {
    x: 0.75, y: 1.55 + i * 1.24, w: 6.5, n: i + 1, head: h, body: b,
    accent: i === 3 ? THEME.colors.accent2 : THEME.colors.accent1,
  }));

  s.addShape(pres.ShapeType.roundRect, { x: 7.75, y: 1.75, w: 4.8, h: 4.0, rectRadius: 0.08,
    fill: { color: THEME.colors.lt2 }, line: { color: THEME.colors.accent6, width: 1 },
    objectName: "spec-card" });
  s.addText("MODELLED CONFIGURATION", { x: 8.05, y: 2.0, w: 4.2, h: 0.3, fontSize: 11,
    bold: true, charSpacing: 1.5, color: THEME.colors.accent1, margin: 0, isTextBox: true });
  const spec = [
    ["Channel", "400 CPSI · Dh = 1.1 mm"],
    ["Length", "50 mm"],
    ["Temperature", "120 °C · 8 bar"],
    ["Feed", "triolein + methanol, 6:1 molar"],
    ["Catalyst", "ZnAl₂O₄ washcoat, 20 µm"],
    ["Flow", "laminar, Re = 0.16"],
  ];
  spec.forEach(([k, v], i) => {
    s.addText(k, { x: 8.05, y: 2.45 + i * 0.52, w: 1.6, h: 0.32, fontSize: 12,
      color: THEME.colors.accent4, margin: 0, isTextBox: true });
    s.addText(v, { x: 9.6, y: 2.45 + i * 0.52, w: 2.75, h: 0.32, fontSize: 12.5,
      bold: true, color: C.text1, margin: 0, isTextBox: true });
  });
  s.addNotes("O monólito é escolhido para vencer limitação de transferência de massa. A pergunta no item 4 é a que este trabalho responde.");
}

/* ══ 3. OBJECTIVES ════════════════════════════════════════════════════ */
{
  const s = pres.addSlide({ masterName: "CONTENT_TINT", sectionTitle: "Context" });
  s.addText("Objectives", { placeholder: "title" });

  s.addShape(pres.ShapeType.roundRect, { x: 0.75, y: 1.5, w: 11.8, h: 1.4, rectRadius: 0.08,
    fill: { color: THEME.colors.dk1 }, objectName: "main-obj" });
  s.addText("PRIMARY OBJECTIVE", { x: 1.1, y: 1.72, w: 5, h: 0.28, fontSize: 11, bold: true,
    charSpacing: 1.5, color: THEME.colors.accent3, margin: 0, isTextBox: true });
  s.addText("Build and verify a CFD model of heterogeneous transesterification in a monolith channel, and use it to identify the controlling regime",
    { x: 1.1, y: 2.05, w: 11.1, h: 0.7, fontSize: 17, color: "FFFFFF", margin: 0, isTextBox: true });

  const objs = [
    ["Hydrodynamics", "Validate the laminar velocity field against the analytical Poiseuille solution."],
    ["Surface reaction", "Implement the Allain (2015) kinetics as a wall species-flux boundary condition."],
    ["Verification", "Check every link of the numerical chain against independent hand calculation."],
    ["Regime analysis", "Determine whether kinetics or transport limits conversion."],
    ["Design insight", "Quantify what would be needed to reach a useful conversion."],
    ["Calibration", "Prepare the model to receive laboratory data."],
  ];
  objs.forEach(([h, b], i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = 0.75 + col * 4.03, y = 3.25 + row * 1.75;
    s.addShape(pres.ShapeType.roundRect, { x, y, w: 3.75, h: 1.5, rectRadius: 0.06,
      fill: { color: C.background1 }, line: { color: THEME.colors.accent6, width: 1 },
      objectName: `obj-${i}` });
    s.addText(h, { x: x + 0.22, y: y + 0.18, w: 3.3, h: 0.32, fontSize: 14, bold: true,
      color: THEME.colors.accent1, margin: 0, isTextBox: true });
    s.addText(b, { x: x + 0.22, y: y + 0.52, w: 3.35, h: 0.86, fontSize: 11.5,
      color: C.text1, margin: 0, valign: "top", isTextBox: true });
  });
  s.addNotes("Os quatro primeiros objetivos estão cumpridos. Os dois últimos dependem dos dados de laboratório.");
}

/* ══ 4. METHOD ════════════════════════════════════════════════════════ */
pres.addSection({ title: "Method" });
{
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Method" });
  s.addText("Model construction", { placeholder: "title" });
  s.addText("Geometry · mesh · physics · kinetics", { placeholder: "body" });
}

{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Method" });
  s.addText("Numerical model", { placeholder: "title" });

  const cards = [
    ["GEOMETRY", ["Representative channel, pseudo-2D", "50 × 1.1 mm, symmetry on side faces", "Built parametrically in build123d"]],
    ["MESH", ["286 440 cells, trimmed + prism layers", "10 prism layers on the catalytic wall", "First cell 1.43 µm"]],
    ["PHYSICS", ["Single-phase multicomponent liquid", "Six species: TG, DG, MG, FAME, GL, MeOH", "Laminar, segregated solver"]],
  ];
  cards.forEach(([head, lines], i) => {
    const x = 0.75 + i * 4.03;
    s.addShape(pres.ShapeType.roundRect, { x, y: 1.5, w: 3.75, h: 2.35, rectRadius: 0.08,
      fill: { color: THEME.colors.lt2 }, line: { color: THEME.colors.accent6, width: 1 },
      objectName: `meth-${i}` });
    s.addText(head, { x: x + 0.25, y: 1.72, w: 3.3, h: 0.3, fontSize: 11.5, bold: true,
      charSpacing: 1.5, color: THEME.colors.accent1, margin: 0, isTextBox: true });
    s.addText(lines.map((t, j) => ({ text: t, options: { bullet: true, breakLine: j < lines.length - 1 } })),
      { x: x + 0.25, y: 2.08, w: 3.3, h: 1.6, fontSize: 12, color: C.text1,
        margin: 0, paraSpaceAfter: 6, valign: "top", isTextBox: true });
  });

  s.addShape(pres.ShapeType.roundRect, { x: 0.75, y: 4.1, w: 11.8, h: 2.45, rectRadius: 0.08,
    fill: { color: THEME.colors.dk1 }, objectName: "kinetics-card" });
  s.addText("KINETIC MODEL — Allain et al. (2015), Chem. Eng. J. 283:833", { x: 1.05, y: 4.32,
    w: 8, h: 0.3, fontSize: 11.5, bold: true, charSpacing: 1.2,
    color: THEME.colors.accent3, margin: 0, isTextBox: true });
  s.addText("Three reversible second-order steps on a solid ZnAl₂O₄ catalyst", { x: 1.05,
    y: 4.64, w: 7.5, h: 0.3, fontSize: 13, color: THEME.colors.accent6, margin: 0, isTextBox: true });
  s.addText("TG + MeOH  ⇌  DG + FAME\nDG + MeOH  ⇌  MG + FAME\nMG + MeOH  ⇌  GL + FAME",
    { x: 1.05, y: 5.08, w: 5.0, h: 1.2, fontSize: 15, color: "FFFFFF",
      fontFace: "Courier New", lineSpacing: 24, margin: 0, isTextBox: true });
  s.addText([
    { text: "rᵢ = kᵢ(T)·[ C_A·C_MeOH − (1/Kᵢ)·C_B·C_FAME ]", options: { breakLine: true } },
    { text: "kᵢ(T) = kᵢ⁰ · exp(−Eaᵢ/RT)", options: { breakLine: true } },
    { text: "Wall basis:  r_wall = r_vol × ρ_washcoat × δ_washcoat", options: {} },
  ], { x: 6.5, y: 5.08, w: 5.8, h: 1.2, fontSize: 12.5, color: THEME.colors.accent6,
       margin: 0, lineSpacing: 22, isTextBox: true });
  s.addNotes("Escolhemos o modelo clássico de 2ª ordem de Allain em vez do Eley-Rideal: ele ajusta melhor (LS 0,022 vs 0,044) com menos parâmetros.");
}

/* ══ 5. IMPLEMENTATION ════════════════════════════════════════════════ */
{
  const s = pres.addSlide({ masterName: "CONTENT_TINT", sectionTitle: "Method" });
  s.addText("Implementation as a wall boundary condition", { placeholder: "title" });

  s.addText("The published kinetics are expressed per mass of catalyst; Star-CCM+ requires a flux per unit wall area. Sixteen chained field functions perform the conversion.",
    { x: 0.75, y: 1.3, w: 11.8, h: 0.5, fontSize: 14, color: C.text1, margin: 0, isTextBox: true });

  const chain = [
    ["Cᵢ", "concentrations\nfrom ρ and Yᵢ"],
    ["kᵢ(T)", "Arrhenius\nrate constants"],
    ["rᵢ,vol", "volumetric rate\nmol/kg_cat·s"],
    ["rᵢ,wall", "× ρ·δ washcoat\nmol/m²·s"],
    ["Jᵢ", "species flux\nkg/m²·s"],
  ];
  chain.forEach(([sym, desc], i) => {
    const x = 0.75 + i * 2.44;
    s.addShape(pres.ShapeType.roundRect, { x, y: 2.05, w: 2.08, h: 1.45, rectRadius: 0.08,
      fill: { color: C.background1 }, line: { color: THEME.colors.accent1, width: 1.5 },
      objectName: `chain-${i}` });
    s.addText(sym, { x, y: 2.2, w: 2.08, h: 0.45, fontSize: 19, bold: true,
      color: THEME.colors.accent1, align: "center", margin: 0, isTextBox: true });
    s.addText(desc, { x: x + 0.1, y: 2.68, w: 1.88, h: 0.7, fontSize: 10.5,
      color: THEME.colors.accent4, align: "center", margin: 0, isTextBox: true });
    if (i < 4) s.addText("→", { x: x + 2.08, y: 2.5, w: 0.36, h: 0.4, fontSize: 18,
      color: THEME.colors.accent4, align: "center", margin: 0, isTextBox: true });
  });

  s.addShape(pres.ShapeType.roundRect, { x: 0.75, y: 3.85, w: 5.75, h: 2.6, rectRadius: 0.08,
    fill: { color: C.background1 }, line: { color: THEME.colors.accent6, width: 1 },
    objectName: "stoich-card" });
  s.addText("STOICHIOMETRIC WALL FLUXES", { x: 1.0, y: 4.05, w: 5, h: 0.3, fontSize: 11,
    bold: true, charSpacing: 1.2, color: THEME.colors.accent1, margin: 0, isTextBox: true });
  s.addText([
    "TG    = −0.8854 · r₁",
    "DG    = +0.6210 · (r₁ − r₂)",
    "MG    = +0.3570 · (r₂ − r₃)",
    "MeOH  = −0.0320 · (r₁ + r₂ + r₃)",
    "FAME  = +0.2970 · (r₁ + r₂ + r₃)",
    "GL    = +0.0920 · r₃",
  ].map((t, j) => ({ text: t, options: { breakLine: j < 5 } })),
    { x: 1.0, y: 4.4, w: 5.2, h: 1.9, fontSize: 12, fontFace: "Courier New",
      color: C.text1, margin: 0, lineSpacing: 19, valign: "top", isTextBox: true });

  s.addShape(pres.ShapeType.roundRect, { x: 6.8, y: 3.85, w: 5.75, h: 2.6, rectRadius: 0.08,
    fill: { color: C.background1 }, line: { color: THEME.colors.accent6, width: 1 },
    objectName: "note-card" });
  s.addText("WASHCOAT CONVERSION FACTOR", { x: 7.05, y: 4.05, w: 5, h: 0.3, fontSize: 11,
    bold: true, charSpacing: 1.2, color: THEME.colors.accent1, margin: 0, isTextBox: true });
  s.addText("ρ_washcoat × δ_washcoat\n= 1180 kg/m³ × 20 µm\n= 0.0236 kg_cat / m²_wall",
    { x: 7.05, y: 4.42, w: 5.2, h: 0.95, fontSize: 14, color: C.text1,
      margin: 0, lineSpacing: 22, isTextBox: true });
  s.addText("The result is strictly linear in this factor — it is also the least certain input in the model.",
    { x: 7.05, y: 5.5, w: 5.2, h: 0.75, fontSize: 12, italic: true,
      color: THEME.colors.accent2, margin: 0, isTextBox: true });
  s.addNotes("A conversão de base — massa de catalisador para área de parede — é o elo que mais depende de dado experimental.");
}

/* ══ 6. RESULTS: PHASE 1 ══════════════════════════════════════════════ */
pres.addSection({ title: "Results" });
{
  const s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Results" });
  s.addText("Verification and results", { placeholder: "title" });
  s.addText("Hydrodynamics · reaction chain · mesh independence · regime", { placeholder: "body" });
}

{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("Phase 1 — hydrodynamics verified", { placeholder: "title" });

  s.addImage({ path: path.join(FIG, "A_fase1_poiseuille.png"), x: 0.75, y: 1.45, w: 6.6, h: 4.75 });
  caption(s, "Outlet velocity profile at x = L, against the analytical plane-channel solution",
    { x: 0.75, y: 6.25, w: 6.6 });

  s.addText("The laminar field is reproduced exactly", { x: 7.8, y: 1.55, w: 4.8, h: 0.5,
    fontSize: 17, bold: true, color: C.text1, margin: 0, isTextBox: true });
  s.addText("Before enabling any chemistry, the cold-flow solution was checked against the closed-form Poiseuille result. Agreement is within 0.1 %.",
    { x: 7.8, y: 2.1, w: 4.75, h: 0.95, fontSize: 13, color: THEME.colors.accent4,
      margin: 0, isTextBox: true });

  const rows = [
    ["Reynolds number", "0.160", "Stokes regime"],
    ["u_max / u_mean", "1.500", "exact"],
    ["Pressure drop", "2.975 Pa", "vs 8 bar operating"],
    ["Entry length", "8.8 µm", "0.02 % of channel"],
  ];
  rows.forEach(([k, v, note], i) => {
    const y = 3.25 + i * 0.78;
    s.addText(k, { x: 7.8, y, w: 2.5, h: 0.3, fontSize: 12.5, color: THEME.colors.accent4,
      margin: 0, isTextBox: true });
    s.addText(v, { x: 10.3, y: y - 0.05, w: 1.3, h: 0.36, fontSize: 15, bold: true,
      color: THEME.colors.accent1, align: "right", margin: 0, isTextBox: true });
    s.addText(note, { x: 7.8, y: y + 0.3, w: 4.6, h: 0.28, fontSize: 10.5,
      color: THEME.colors.accent4, italic: true, margin: 0, isTextBox: true });
  });
  s.addNotes("Fase 1 valida a malha e o solver antes de introduzir qualquer química.");
}

/* ══ 7. VERIFICATION — the methodological contribution ════════════════ */
{
  const s = pres.addSlide({ masterName: "CONTENT_TINT", sectionTitle: "Results" });
  s.addText("Phase 2 — every link verified against hand calculation", { placeholder: "title" });

  s.addText("The wall flux computed by the solver was compared with the same quantity derived by hand from the published rate constants. This became the standard test of the project.",
    { x: 0.75, y: 1.3, w: 11.8, h: 0.55, fontSize: 14, color: C.text1, margin: 0, isTextBox: true });

  stat(s, { x: 0.75, y: 2.05, w: 3.75, value: "0.2 %", label: "Flux agreement",
    sub: "solver vs independent\nanalytical calculation", name: "v-flux" });
  stat(s, { x: 4.78, y: 2.05, w: 3.75, value: "0.1 %", label: "Mesh independence",
    sub: "1.43 M → 286 k cells,\nsame wall flux", name: "v-mesh" });
  stat(s, { x: 8.80, y: 2.05, w: 3.75, value: "1.0000000", label: "Mass closure",
    sub: "sum of the six outlet\nmass fractions", name: "v-mass" });

  s.addImage({ path: path.join(FIG, "B_mesh_independence.png"), x: 0.9, y: 4.25, w: 5.6, h: 2.35 });

  s.addShape(pres.ShapeType.roundRect, { x: 6.95, y: 4.25, w: 5.6, h: 2.35, rectRadius: 0.08,
    fill: { color: C.background1 }, line: { color: THEME.colors.accent2, width: 1.5 },
    objectName: "why-card" });
  s.addText("WHY THIS MATTERED", { x: 7.2, y: 4.45, w: 5.1, h: 0.3, fontSize: 11, bold: true,
    charSpacing: 1.2, color: THEME.colors.accent2, margin: 0, isTextBox: true });
  s.addText("The first converged-looking solution disagreed with hand calculation by a factor of 2338. That discrepancy exposed a diverging species solution whose results looked physically plausible — large radial gradients, a sharp boundary layer — but were numerical artefacts.",
    { x: 7.2, y: 4.78, w: 5.1, h: 1.6, fontSize: 12, color: C.text1, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("Esta é a contribuição metodológica central: um teste independente que separa resultado de artefato.");
}

/* ══ 8. ERROR AUDIT ═══════════════════════════════════════════════════ */
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("What the verification caught", { placeholder: "title" });

  s.addTable([
    [{ text: "Issue", options: { bold: true, color: "FFFFFF", fill: { color: THEME.colors.dk1 } } },
     { text: "Detected by", options: { bold: true, color: "FFFFFF", fill: { color: THEME.colors.dk1 } } },
     { text: "Resolution", options: { bold: true, color: "FFFFFF", fill: { color: THEME.colors.dk1 } } }],
    ["Inlet composition gave a 3.77:1 molar ratio, not the specified 6:1",
     "Stoichiometric check of the mass fractions", "Corrected to Y_TG = 0.8218 / Y_MeOH = 0.1782"],
    ["Species equations diverging — residuals reaching 10⁸",
     "TG consumed did not match products formed (45× gap)",
     "Non-negative concentration clamps; flow frozen after convergence; transient marching"],
    ["Boundary-layer thickness reported as 22 µm",
     "Comparison with the Lévêque solution", "220 µm — an order of magnitude larger"],
    ["Regime reported as mass-transfer limited",
     "Damköhler number evaluation", "Kinetically controlled, Da ≈ 0.003"],
  ], {
    x: 0.75, y: 1.5, w: 11.8, colW: [3.7, 3.6, 4.5], border: { pt: 1, color: THEME.colors.accent6 },
    fontSize: 11.5, color: THEME.colors.dk1, valign: "middle", rowH: 0.74, margin: 0.14,
    fill: { color: C.background1 },
  });

  s.addShape(pres.ShapeType.roundRect, { x: 0.75, y: 5.55, w: 11.8, h: 1.15, rectRadius: 0.08,
    fill: { color: THEME.colors.lt2 }, line: { color: THEME.colors.accent1, width: 1.5 },
    objectName: "lesson" });
  s.addText([
    { text: "A plausible-looking CFD result is not evidence.  ", options: { bold: true, color: THEME.colors.accent1 } },
    { text: "Four of the six findings originally reported were artefacts of a solution that had converged in appearance only. All were caught by one independent calculation.", options: { color: THEME.colors.dk1 } },
  ], { x: 1.05, y: 5.74, w: 11.2, h: 0.78, fontSize: 13.5, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("Reportar os erros encontrados é parte do resultado — mostra que o trabalho tem controle de qualidade, não sorte.");
}

/* ══ 9. REGIME ════════════════════════════════════════════════════════ */
{
  const s = pres.addSlide({ masterName: "CONTENT_TINT", sectionTitle: "Results" });
  s.addText("The controlling regime is kinetic, not transport", { placeholder: "title" });

  s.addImage({ path: path.join(FIG, "C_damkohler.png"), x: 0.9, y: 1.5, w: 11.5, h: 2.88 });

  s.addShape(pres.ShapeType.roundRect, { x: 0.75, y: 4.72, w: 5.75, h: 1.9, rectRadius: 0.08,
    fill: { color: C.background1 }, line: { color: THEME.colors.accent6, width: 1 },
    objectName: "da-calc" });
  s.addText("Da = r_wall / J_max = 3.04×10⁻⁶ / 9.85×10⁻⁴ = 0.003",
    { x: 1.0, y: 4.95, w: 5.25, h: 0.4, fontSize: 13, bold: true, color: C.text1,
      margin: 0, valign: "top", isTextBox: true });
  s.addText("The catalytic wall receives roughly 300 times more triglyceride than it can consume. Surface concentration is essentially the bulk value.",
    { x: 1.0, y: 5.38, w: 5.25, h: 1.0, fontSize: 12, color: THEME.colors.accent4,
      margin: 0, valign: "top", isTextBox: true });

  s.addShape(pres.ShapeType.roundRect, { x: 6.8, y: 4.72, w: 5.75, h: 1.9, rectRadius: 0.08,
    fill: { color: THEME.colors.dk1 }, objectName: "da-note" });
  s.addText("A HIGH SCHMIDT NUMBER IS NOT A LIMITATION", { x: 7.05, y: 4.95, w: 5.25, h: 0.3,
    fontSize: 11, bold: true, charSpacing: 1, color: THEME.colors.accent3, margin: 0, valign: "top", isTextBox: true });
  s.addText("Sc ≈ 59 000 means the concentration boundary layer is thin — not that transport is the bottleneck. The Damköhler number decides that. Conflating the two produced the error in the earlier analysis.",
    { x: 7.05, y: 5.32, w: 5.25, h: 1.2, fontSize: 11.5, color: THEME.colors.accent6,
      margin: 0, valign: "top", isTextBox: true });
  s.addNotes("Distinção conceitual central do trabalho: Schmidt alto diz que a camada é fina; Damköhler diz quem limita.");
}

/* ══ 10. CONVERSION RESULT ════════════════════════════════════════════ */
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("Predicted conversion and why it is so low", { placeholder: "title" });

  s.addShape(pres.ShapeType.roundRect, { x: 0.75, y: 1.45, w: 3.6, h: 2.1, rectRadius: 0.08,
    fill: { color: THEME.colors.dk1 }, objectName: "conv-hero" });
  s.addText("0.017 %", { x: 0.95, y: 1.7, w: 3.2, h: 0.85, fontSize: 40, bold: true,
    color: THEME.colors.accent3, margin: 0, isTextBox: true });
  s.addText("TG conversion per pass", { x: 0.95, y: 2.55, w: 3.2, h: 0.3, fontSize: 13,
    bold: true, color: "FFFFFF", margin: 0, isTextBox: true });
  s.addText("120 °C · 50 mm · 6:1 · 1 mm/s", { x: 0.95, y: 2.87, w: 3.2, h: 0.4, fontSize: 11,
    color: THEME.colors.accent6, margin: 0, isTextBox: true });

  s.addText("X = r₁ · W / F_TG   —   three multiplying factors", { x: 4.65, y: 1.5, w: 7.9,
    h: 0.36, fontSize: 15, bold: true, color: C.text1, margin: 0, isTextBox: true });
  const factors = [
    ["Slow kinetics at 120 °C", "k₁ is 16.5× smaller than at 185 °C; 120 °C is below the source's range."],
    ["Low catalyst inventory", "A 20 µm washcoat gives 21 kg/m³ — 33× less than a packed bed."],
    ["Short contact time", "τ = L/u = 50 s in a single pass."],
  ];
  factors.forEach(([h, b], i) => stepRow(s, {
    x: 4.65, y: 1.95 + i * 0.68, w: 7.9, n: i + 1, head: h, body: b,
    accent: THEME.colors.accent2,
  }));

  s.addImage({ path: path.join(FIG, "D_catalyst_inventory.png"), x: 0.75, y: 3.9, w: 3.4, h: 2.65 });

  s.addShape(pres.ShapeType.roundRect, { x: 4.65, y: 3.9, w: 7.9, h: 2.65, rectRadius: 0.08,
    fill: { color: THEME.colors.lt2 }, line: { color: THEME.colors.accent1, width: 1.5 },
    objectName: "design-insight" });
  s.addText("DESIGN IMPLICATION", { x: 4.95, y: 4.12, w: 7.3, h: 0.3, fontSize: 11, bold: true,
    charSpacing: 1.2, color: THEME.colors.accent1, margin: 0, isTextBox: true });
  s.addText("A monolith exists to overcome mass-transfer limitation — straight channels, negligible pressure drop, a thin boundary layer. With Da ≈ 0.003 transport is not the bottleneck, so none of that is being used, while the geometry's one real cost is paid in full.",
    { x: 4.95, y: 4.44, w: 7.3, h: 1.15, fontSize: 13, color: C.text1, margin: 0, valign: "top", isTextBox: true });
  s.addText("The geometry is optimised for a regime this system is not in.",
    { x: 4.95, y: 5.68, w: 7.3, h: 0.5, fontSize: 14, bold: true, italic: true,
      color: THEME.colors.accent2, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("Não é um resultado negativo: é uma conclusão de engenharia quantificada, que só a simulação entrega antes do experimento.");
}

/* ══ 11. TRANSIENT ════════════════════════════════════════════════════ */
{
  const s = pres.addSlide({ masterName: "CONTENT_TINT", sectionTitle: "Results" });
  s.addText("A practical finding for the experimental campaign", { placeholder: "title" });

  s.addImage({ path: path.join(FIG, "F_transient.png"), x: 0.75, y: 1.5, w: 7.6, h: 2.95 });
  caption(s, "Outlet depletion of TG during start-up, and its extrapolation to steady state",
    { x: 0.75, y: 4.5, w: 7.6 });

  s.addShape(pres.ShapeType.roundRect, { x: 8.65, y: 1.5, w: 3.9, h: 2.95, rectRadius: 0.08,
    fill: { color: THEME.colors.dk1 }, objectName: "settle-card" });
  s.addText("≈ 30 min", { x: 8.95, y: 1.78, w: 3.3, h: 0.85, fontSize: 36, bold: true,
    color: THEME.colors.accent3, margin: 0, isTextBox: true });
  s.addText("to reach steady state", { x: 8.95, y: 2.62, w: 3.3, h: 0.3, fontSize: 13.5,
    bold: true, color: "FFFFFF", margin: 0, isTextBox: true });
  s.addText("Despite a residence time of only 50 s — about 32 residence times.",
    { x: 8.95, y: 3.0, w: 3.3, h: 0.62, fontSize: 12, color: THEME.colors.accent6,
      margin: 0, valign: "top", isTextBox: true });
  s.addText("Samples drawn earlier will understate the conversion.",
    { x: 8.95, y: 3.68, w: 3.3, h: 0.6, fontSize: 12, bold: true,
      color: THEME.colors.accent3, margin: 0, isTextBox: true });

  s.addShape(pres.ShapeType.roundRect, { x: 0.75, y: 4.95, w: 11.8, h: 1.6, rectRadius: 0.08,
    fill: { color: C.background1 }, line: { color: THEME.colors.accent6, width: 1 },
    objectName: "why-slow" });
  s.addText("WHY SO SLOW", { x: 1.05, y: 5.15, w: 4, h: 0.3, fontSize: 11, bold: true,
    charSpacing: 1.2, color: THEME.colors.accent1, margin: 0, isTextBox: true });
  s.addText("Triglyceride is depleted exactly where the velocity vanishes, and its diffusivity (1.3×10⁻¹⁰ m²/s) is far too low to carry it into the fast-moving core. Fluid 10 µm from the wall needs 926 s to traverse the channel; at 5 µm, 1840 s. The controlling time scale is near-wall transit, not the mean residence time.",
    { x: 1.05, y: 5.46, w: 11.2, h: 0.95, fontSize: 12.5, color: C.text1, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("Recomendação concreta para os alunos de IC: curva de partida com amostras em 5, 10, 20, 30 e 45 min. Valida o transiente e evita dados fora de regime.");
}

/* ══ 12. OPEN QUESTION ════════════════════════════════════════════════ */
pres.addSection({ title: "Next" });
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Next" });
  s.addText("The open question", { placeholder: "title" });

  s.addShape(pres.ShapeType.roundRect, { x: 0.75, y: 1.45, w: 5.6, h: 2.0, rectRadius: 0.08,
    fill: { color: THEME.colors.lt2 }, line: { color: THEME.colors.accent6, width: 1 },
    objectName: "firth" });
  s.addText("Firth (2014), University of Bath", { x: 1.0, y: 1.68, w: 5.1, h: 0.3,
    fontSize: 12, bold: true, color: THEME.colors.accent4, margin: 0, isTextBox: true });
  s.addText("> 90 %", { x: 1.0, y: 2.0, w: 5.1, h: 0.75, fontSize: 36, bold: true,
    color: THEME.colors.accent1, margin: 0, isTextBox: true });
  s.addText("conversion in a monolith at 120 °C with an SrO washcoat",
    { x: 1.0, y: 2.78, w: 5.1, h: 0.5, fontSize: 12.5, color: C.text1, margin: 0, isTextBox: true });

  s.addShape(pres.ShapeType.roundRect, { x: 6.95, y: 1.45, w: 5.6, h: 2.0, rectRadius: 0.08,
    fill: { color: THEME.colors.lt2 }, line: { color: THEME.colors.accent6, width: 1 },
    objectName: "thiswork" });
  s.addText("This model, ZnAl₂O₄ kinetics", { x: 7.2, y: 1.68, w: 5.1, h: 0.3,
    fontSize: 12, bold: true, color: THEME.colors.accent4, margin: 0, isTextBox: true });
  s.addText("0.017 %", { x: 7.2, y: 2.0, w: 5.1, h: 0.75, fontSize: 36, bold: true,
    color: THEME.colors.accent2, margin: 0, isTextBox: true });
  s.addText("conversion per pass at the same nominal temperature",
    { x: 7.2, y: 2.78, w: 5.1, h: 0.5, fontSize: 12.5, color: C.text1, margin: 0, isTextBox: true });

  s.addText("Nearly four orders of magnitude apart — three candidate explanations",
    { x: 0.75, y: 3.65, w: 11.8, h: 0.4, fontSize: 16, bold: true, color: C.text1,
      margin: 0, isTextBox: true });

  const expl = [
    ["Catalyst activity", "SrO is a strong base; the ZnAl₂O₄ study required 140–220 °C, while Firth operated at 120 °C."],
    ["Recirculation", "If the charge passes the monolith repeatedly over hours, a minute per-pass conversion is consistent with 90 % accumulated."],
    ["Catalyst loading", "The real washcoat may hold considerably more catalyst than the 20 µm assumed here."],
  ];
  expl.forEach(([h, b], i) => {
    const x = 0.75 + i * 4.03;
    s.addShape(pres.ShapeType.roundRect, { x, y: 4.2, w: 3.75, h: 1.75, rectRadius: 0.06,
      fill: { color: C.background1 }, line: { color: THEME.colors.accent6, width: 1 },
      objectName: `expl-${i}` });
    s.addText(h, { x: x + 0.22, y: 4.4, w: 3.3, h: 0.32, fontSize: 14, bold: true,
      color: THEME.colors.accent1, margin: 0, isTextBox: true });
    s.addText(b, { x: x + 0.22, y: 4.73, w: 3.35, h: 1.1, fontSize: 11.5, color: C.text1,
      margin: 0, valign: "top", isTextBox: true });
  });

  s.addText("If recirculation is the answer, the structure becomes elegant: CFD supplies the per-pass conversion, a batch balance supplies the hours-long curve.",
    { x: 0.75, y: 6.1, w: 11.8, h: 0.5, fontSize: 13, italic: true,
      color: THEME.colors.accent1, margin: 0, isTextBox: true });
  s.addNotes("Esta pergunta só apareceu porque a simulação funciona e dá um número. É a pergunta certa para levar aos orientadores.");
}

/* ══ 13. TEMPERATURE SWEEP ════════════════════════════════════════════ */
{
  const s = pres.addSlide({ masterName: "CONTENT_TINT", sectionTitle: "Next" });
  s.addText("Ready for calibration", { placeholder: "title" });

  s.addImage({ path: path.join(FIG, "E_temperature_sweep.png"), x: 0.75, y: 1.5, w: 6.0, h: 4.1 });
  caption(s, "Predicted conversion against temperature, from the validated reference point",
    { x: 0.75, y: 5.65, w: 6.0 });

  s.addText("Because Da ≪ 1, the reactor is differential and conversion scales linearly",
    { x: 7.1, y: 1.55, w: 5.45, h: 0.6, fontSize: 15, bold: true, color: C.text1,
      margin: 0, isTextBox: true });

  s.addShape(pres.ShapeType.roundRect, { x: 7.1, y: 2.25, w: 5.45, h: 0.8, rectRadius: 0.06,
    fill: { color: THEME.colors.dk1 }, objectName: "scaling" });
  s.addText("X_TG  ∝  k(T) · ρ · δ · L / u", { x: 7.1, y: 2.25, w: 5.45, h: 0.8,
    fontSize: 17, bold: true, color: THEME.colors.accent3, align: "center",
    valign: "middle", margin: 0, isTextBox: true });

  s.addText("Any new parameter set can therefore be evaluated before running CFD — the simulation then confirms a few points rather than sweeping the whole space.",
    { x: 7.1, y: 3.18, w: 5.45, h: 0.8, fontSize: 12.5, color: THEME.colors.accent4,
      margin: 0, valign: "top", isTextBox: true });

  s.addText("DATA STILL REQUIRED, BY IMPACT", { x: 7.1, y: 4.02, w: 5.45, h: 0.3,
    fontSize: 11, bold: true, charSpacing: 1.2, color: THEME.colors.accent1,
    margin: 0, isTextBox: true });
  const needs = [
    ["Catalyst and kinetic source", "10–1000×", THEME.colors.accent2],
    ["Single pass or recirculation", "10–100×", THEME.colors.accent2],
    ["Washcoat loading", "linear", THEME.colors.accent1],
    ["Flow rate and bed length", "linear", THEME.colors.accent1],
    ["Fluid properties ρ, µ, D", "negligible", THEME.colors.accent4],
  ];
  needs.forEach(([k, v, col], i) => {
    const y = 4.40 + i * 0.40;
    s.addText(k, { x: 7.1, y, w: 3.6, h: 0.32, fontSize: 12, color: C.text1,
      margin: 0, isTextBox: true });
    s.addText(v, { x: 10.7, y, w: 1.85, h: 0.32, fontSize: 12, bold: true, color: col,
      align: "right", margin: 0, isTextBox: true });
  });
  s.addText("Because the regime is kinetic, fluid properties barely move the answer — the characterisation effort belongs on the first three rows.",
    { x: 7.1, y: 6.34, w: 5.45, h: 0.5, fontSize: 10.5, italic: true,
      color: THEME.colors.accent4, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("A lei de escala é o que torna a calibração barata: prevê-se antes, confirma-se depois.");
}

/* ══ 14. SCHEDULE ═════════════════════════════════════════════════════ */
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Next" });
  s.addText("Work plan", { placeholder: "title" });

  const phases = [
    ["Model construction", "Geometry, mesh, kinetics implementation", "Complete", THEME.colors.accent1],
    ["Verification", "Independent checks, mesh independence, regime analysis", "Complete", THEME.colors.accent1],
    ["Laboratory data", "Kinetics and conversion from the undergraduate team", "In progress", THEME.colors.accent3],
    ["Calibration", "Fit the model to measured conditions and compare", "Next", THEME.colors.accent4],
    ["Parametric study", "Temperature, residence time, molar ratio, washcoat", "Planned", THEME.colors.accent4],
    ["Dissertation", "Writing and defence", "Planned", THEME.colors.accent4],
  ];

  phases.forEach(([h, b, status, col], i) => {
    const y = 1.5 + i * 0.86;
    s.addShape(pres.ShapeType.ellipse, { x: 0.85, y: y + 0.12, w: 0.3, h: 0.3,
      fill: { color: col }, objectName: `ph-dot-${i}` });
    if (i < phases.length - 1) {
      s.addShape(pres.ShapeType.line, { x: 1.0, y: y + 0.42, w: 0, h: 0.56,
        line: { color: THEME.colors.accent6, width: 2 }, objectName: `ph-line-${i}` });
    }
    s.addText(h, { x: 1.45, y: y + 0.02, w: 5.0, h: 0.34, fontSize: 16, bold: true,
      color: C.text1, margin: 0, isTextBox: true });
    s.addText(b, { x: 1.45, y: y + 0.36, w: 7.4, h: 0.32, fontSize: 12,
      color: THEME.colors.accent4, margin: 0, isTextBox: true });
    s.addShape(pres.ShapeType.roundRect, { x: 10.6, y: y + 0.04, w: 1.95, h: 0.42,
      rectRadius: 0.1, fill: { color: col }, objectName: `ph-tag-${i}` });
    s.addText(status, { x: 10.6, y: y + 0.04, w: 1.95, h: 0.42, fontSize: 11.5, bold: true,
      color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
  });
  s.addNotes("O modelo está pronto e verificado. O caminho crítico agora é o dado experimental.");
}

/* ══ 15. SUMMARY ══════════════════════════════════════════════════════ */
{
  const s = pres.addSlide({ masterName: "CONTENT_TINT", sectionTitle: "Next" });
  s.addText("Summary", { placeholder: "title" });

  const pts = [
    ["A verified CFD model", "Hydrodynamics within 0.1 % of the analytical solution; reaction chain within 0.2 % of independent calculation; mesh independence demonstrated."],
    ["The regime is kinetic", "Da ≈ 0.003. The catalytic wall receives about 300× more reactant than it consumes — transport is not the bottleneck."],
    ["Conversion is set by catalyst inventory", "A 20 µm washcoat holds 33× less catalyst per reactor volume than a packed bed; the monolith's advantage is not being used."],
    ["An operational prediction", "Steady state takes roughly 30 minutes, not the 50 s residence time — relevant to how the experiment is sampled."],
    ["A question for the advisors", "Four orders of magnitude separate this model from Firth (2014). Catalyst identity and recirculation would resolve it."],
  ];
  pts.forEach(([h, b], i) => {
    const y = 1.45 + i * 1.07;
    s.addShape(pres.ShapeType.ellipse, { x: 0.8, y, w: 0.42, h: 0.42,
      fill: { color: i === 4 ? THEME.colors.accent2 : THEME.colors.accent1 },
      objectName: `sum-${i}` });
    s.addText(String(i + 1), { x: 0.8, y, w: 0.42, h: 0.42, fontSize: 14, bold: true,
      color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(h, { x: 1.45, y: y - 0.04, w: 10.9, h: 0.34, fontSize: 16, bold: true,
      color: C.text1, margin: 0, isTextBox: true });
    s.addText(b, { x: 1.45, y: y + 0.30, w: 10.9, h: 0.62, fontSize: 12.5,
      color: THEME.colors.accent4, margin: 0, valign: "top", isTextBox: true });
  });
}

/* ══ 16. CLOSING ══════════════════════════════════════════════════════ */
{
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Next" });
  s.addText("Thank you", { placeholder: "title" });
  s.addText("Questions and suggestions are welcome", { placeholder: "body" });
  s.addShape(pres.ShapeType.line, { x: 0.9, y: 5.0, w: 3.2, h: 0,
    line: { color: THEME.colors.accent1, width: 2.5 }, objectName: "rule-end" });
  s.addText("Gabriel Hernandez Rozo · ghrozo97@gmail.com", { x: 0.9, y: 5.3, w: 7, h: 0.35,
    fontSize: 14, color: THEME.colors.accent6, margin: 0, isTextBox: true });
  s.addText("Advisors: Prof. Dr. Raphael Soeiro Suppino · Prof. Dr. Dirceu Noriler",
    { x: 0.9, y: 5.68, w: 8.5, h: 0.35, fontSize: 13, color: THEME.colors.accent4,
      margin: 0, isTextBox: true });
}

/* ══ 17. REFERENCES ═══════════════════════════════════════════════════ */
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Next" });
  s.addText("References", { placeholder: "title" });
  const refs = [
    ["Allain, F. et al. (2015)", "Estimation of kinetic parameters and diffusion coefficients for the transesterification of triolein with methanol on a solid ZnAl₂O₄ catalyst. Chem. Eng. J. 283:833–845.", "Kinetic model and diffusion coefficients used throughout"],
    ["Firth, B. (2014)", "Biodiesel Production in Fixed-Bed Monolithic Reactors. PhD thesis, University of Bath.", "Geometry, operating conditions and the > 90 % benchmark"],
    ["Noureddini, H.; Zhu, D. (1997)", "Kinetics of transesterification of soybean oil. JAOCS 74:1457–1463.", "Mechanistic foundation of the stepwise scheme"],
    ["Ezzati, R. et al. (2021)", "Kinetics models of transesterification reaction for biodiesel production. Renew. Energy 168:280–296.", "Comparative framework for rate models"],
    ["Omranpour, S.; Larimi, A. (2024)", "Modeling and simulation of biodiesel synthesis in fixed bed and packed bed membrane reactors. Sci. Rep. 14:10153.", "CFD benchmark for heterogeneous biodiesel reactors"],
  ];
  refs.forEach(([a, t, note], i) => {
    const y = 1.45 + i * 1.05;
    s.addText(a, { x: 0.8, y, w: 3.3, h: 0.32, fontSize: 13, bold: true,
      color: THEME.colors.accent1, margin: 0, isTextBox: true });
    s.addText(t, { x: 4.2, y, w: 8.35, h: 0.52, fontSize: 11.5, color: C.text1,
      margin: 0, valign: "top", isTextBox: true });
    s.addText(note, { x: 4.2, y: y + 0.52, w: 8.35, h: 0.3, fontSize: 10.5, italic: true,
      color: THEME.colors.accent4, margin: 0, isTextBox: true });
  });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("deck:", OUT);
})();
