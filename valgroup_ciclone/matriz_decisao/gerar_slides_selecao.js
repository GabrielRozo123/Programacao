const pptxgen=require("pptxgenjs");
const p=new pptxgen();
p.defineLayout({name:"W",width:13.333,height:7.5}); p.layout="W";
p.author="CAEXPERTS"; p.title="Valgroup - Selecao de Tecnologia de Separacao";
const NAVY="0A1A33",BLUE="1C5FA8",STEEL="3E7CA8",AMBER="D9822B",GOOD="2E8B57",BAD="C0504D",
      INK="16232E",MUTED="55677A",LINE="D7E1EC",SURF="F1F6FB",WHITE="FFFFFF",DKMUT="9FB4CC";
const F="Calibri", W=13.333,H=7.5,M=0.62;
function footer(s,n){
  s.addText([{text:"CAEXPERTS",options:{bold:true,color:BLUE}},{text:"  ·  Separacao Gas-Solido  ·  Valgroup",options:{color:MUTED}}],
    {x:M,y:7.06,w:9,h:0.3,fontFace:F,fontSize:9,align:"left",margin:0,valign:"middle"});
  s.addText(String(n),{x:W-M-0.5,y:7.06,w:0.5,h:0.3,fontFace:F,fontSize:9,color:MUTED,align:"right",margin:0,valign:"middle"});
}
function head(s,eyebrow,title){
  s.background={color:WHITE};
  s.addText(eyebrow.toUpperCase(),{x:M,y:0.42,w:9,h:0.3,fontFace:F,fontSize:11,bold:true,color:STEEL,charSpacing:2,margin:0});
  s.addText(title,{x:M,y:0.72,w:11,h:0.7,fontFace:F,fontSize:26,bold:true,color:INK,margin:0,valign:"top"});
  s.addText("CAEXPERTS",{x:W-M-2.4,y:0.42,w:2.4,h:0.3,fontFace:F,fontSize:12,bold:true,color:BLUE,align:"right",charSpacing:1,margin:0});
}
// S1 TITLE
let s=p.addSlide(); s.background={color:NAVY};
s.addImage({path:"bg_wide.png",x:0,y:0,w:W,h:H});
s.addShape(p.ShapeType.rect,{x:0,y:0,w:W,h:H,fill:{color:NAVY,transparency:34}});
s.addText("Separação Gás-Sólido",{x:M,y:1.45,w:11.5,h:1.0,fontFace:F,fontSize:44,bold:true,color:WHITE,margin:0});
s.addText("Seleção de Tecnologia — Matriz de Decisão",{x:M,y:2.5,w:11.5,h:0.6,fontFace:F,fontSize:23,color:"7FB3D5",margin:0});
s.addText([{text:"Valgroup Brasil\n",options:{bold:true,fontSize:18,color:WHITE,breakLine:true}},
  {text:"Separação do char do gás de pirólise  ·  Simcenter STAR-CCM+\n",options:{fontSize:13,color:DKMUT,breakLine:true}},
  {text:"Gabriel Hernandez Rozo",options:{fontSize:13,color:DKMUT}}],
  {x:M,y:5.5,w:8,h:1.2,fontFace:F,margin:0,valign:"top",lineSpacingMultiple:1.1});
s.addImage({path:"logo_caexperts.png",x:W-M-2.5,y:5.35,w:2.5,h:2.5*313/760});
s.addImage({path:"badge_siemens.png",x:W-M-2.5,y:6.35,w:1.7,h:1.7*200/403});
// S2 DESAFIO
s=p.addSlide(); head(s,"O contexto","O desafio — separar o char do gás quente de pirólise");
const b2=[
 "Gás de pirólise (r-PET) a 400–450 °C, 1,2 bar · ~80 kg/h de char (biomassa) a separar",
 "Restrição de perda de carga: ΔP < 40 mbar (16\" H₂O)",
 "Char abrasivo e mineral (Ti ~15%, Si, Fe — total ~21%) → separa bem, mas desgasta",
 "Cloro 2,78% → HCl a 450 °C: risco de corrosão (favorece a via SECA)",
 "Downstream = condensador casco-tubo → exige gás SECO e quente",
];
s.addText(b2.map(t=>({text:t,options:{bullet:{code:"2022"},color:INK,fontSize:15,paraSpaceAfter:11,breakLine:true}})),
  {x:M,y:1.75,w:7.4,h:4.2,fontFace:F,valign:"top",margin:0});
s.addShape(p.ShapeType.roundRect,{x:8.35,y:1.85,w:4.35,h:3.6,rectRadius:0.08,fill:{color:SURF},line:{color:STEEL,width:1.25}});
s.addText("A PERGUNTA",{x:8.6,y:2.05,w:3.9,h:0.3,fontFace:F,fontSize:11,bold:true,color:STEEL,charSpacing:1,margin:0});
s.addText([{text:"Qual tecnologia separa o char\n",options:{fontSize:16,bold:true,color:INK,breakLine:true}},
  {text:"— com alta eficiência, ΔP baixo, resistindo ao HCl e entregando gás seco quente ao condensador?",options:{fontSize:13.5,color:MUTED}}],
  {x:8.6,y:2.45,w:3.85,h:2.7,fontFace:F,margin:0,valign:"top"});
footer(s,2);
// S3 TECNOLOGIAS
s=p.addSlide(); head(s,"As opções","6 tecnologias avaliadas");
const techs=[["Ciclone","Via seca · centrífuga · sem partes móveis"],
 ["Quench Tower","Via úmida · resfria e dissolve o char"],
 ["Filtro Cerâmico","Velas porosas · retém finos"],
 ["ESP","Eletrostático · precipita partículas"],
 ["Scrubber Úmido","Lavagem · captura com líquido"],
 ["Settler Gravit.","Câmara de decantação · gravidade"]];
let gx=[M,4.83,9.04], gy=[1.75,3.9];
techs.forEach((t,i)=>{ const x=gx[i%3], y=gy[Math.floor(i/3)];
  s.addShape(p.ShapeType.roundRect,{x,y,w:3.9,h:1.9,rectRadius:0.07,fill:{color:SURF},line:{color:LINE,width:1}});
  s.addText(t[0],{x:x+0.25,y:y+0.22,w:3.4,h:0.5,fontFace:F,fontSize:18,bold:true,color:BLUE,margin:0});
  s.addText(t[1],{x:x+0.25,y:y+0.82,w:3.45,h:0.9,fontFace:F,fontSize:13,color:MUTED,margin:0,valign:"top"}); });
footer(s,3);
// S4 CRITERIOS (novo -- pedido do Marcus, antes da matriz)
s=p.addSlide(); head(s,"Os critérios","Os critérios de avaliação e seus pesos");
s.addText([{text:"Peso 2",options:{bold:true,color:BLUE}},{text:" = crítico técnico / de processo (define se funciona)      ",options:{color:MUTED}},{text:"Peso 1",options:{bold:true,color:STEEL}},{text:" = econômico / risco (secundário)",options:{color:MUTED}}],
  {x:M,y:1.5,w:12,h:0.32,fontFace:F,fontSize:13,margin:0,valign:"middle"});
const crit=[
 ["Temperatura de operação","2","Gás entra a 400–450 °C — a tecnologia não pode degradar a quente"],
 ["Faixa de partículas","2","O char tem finos < 75 µm que precisam ser capturados"],
 ["Eficiência de coleta","2","É o objetivo do projeto: quanto do char realmente separa"],
 ["Queda de pressão (ΔP)","2","Restrição dura do processo: ΔP < 40 mbar"],
 ["Char pegajoso a 450 °C","2","Risco de aglomerar e entupir o separador"],
 ["Adequação ao downstream","2","O condensador casco-tubo exige gás SECO e quente"],
 ["Filtração de líquido","2","Critério do e-mail do cliente: evitar ter de filtrar líquido"],
 ["Custo de investimento","1","Importa, mas é secundário ao desempenho técnico"],
 ["Manutenção","1","Custo operacional e paradas de limpeza"],
 ["Maturidade tecnológica","1","Risco de adotar tecnologia não comprovada"],
];
let cy=1.95, rh=0.44;
s.addShape(p.ShapeType.rect,{x:M,y:cy,w:12.1,h:0.4,fill:{color:BLUE}});
s.addText("Critério",{x:M+0.15,y:cy,w:4,h:0.4,fontFace:F,fontSize:11,bold:true,color:WHITE,valign:"middle",margin:0});
s.addText("Peso",{x:M+4.35,y:cy,w:0.8,h:0.4,fontFace:F,fontSize:11,bold:true,color:WHITE,align:"center",valign:"middle",margin:0});
s.addText("Por que importa",{x:M+5.4,y:cy,w:6.6,h:0.4,fontFace:F,fontSize:11,bold:true,color:WHITE,valign:"middle",margin:0});
cy+=0.4;
crit.forEach((c,i)=>{
  s.addShape(p.ShapeType.rect,{x:M,y:cy,w:12.1,h:rh,fill:{color:i%2?WHITE:SURF},line:{color:LINE,width:0.5}});
  s.addText(c[0],{x:M+0.15,y:cy,w:4.05,h:rh,fontFace:F,fontSize:11.5,bold:true,color:INK,valign:"middle",margin:0});
  s.addShape(p.ShapeType.roundRect,{x:M+4.42,y:cy+0.08,w:0.62,h:rh-0.16,rectRadius:0.04,fill:{color:c[1]==="2"?BLUE:STEEL}});
  s.addText(c[1],{x:M+4.42,y:cy+0.05,w:0.62,h:rh-0.1,fontFace:F,fontSize:12,bold:true,color:WHITE,align:"center",valign:"middle",margin:0});
  s.addText(c[2],{x:M+5.4,y:cy,w:6.65,h:rh,fontFace:F,fontSize:11.5,color:MUTED,valign:"middle",margin:0});
  cy+=rh;
});
footer(s,4);
// S5 MATRIZ
s=p.addSlide(); head(s,"O método","A matriz de decisão");
s.addImage({path:"matriz.png",x:M,y:1.6,w:5.6*2088/1701,h:5.6});
s.addText("Como funciona",{x:8.1,y:1.9,w:4.6,h:0.35,fontFace:F,fontSize:15,bold:true,color:STEEL,margin:0});
const b4=[
 "10 critérios técnicos, com PESO 1 ou 2 (os mais críticos pesam 2)",
 "Cada tecnologia recebe +1 (positivo) · 0 (neutro) · −1 (negativo) por critério",
 "Critério do email do cliente incluído: 'evitar filtração de líquido' (peso 2)",
 "Soma ponderada → ranking objetivo (máx. +17)",
];
s.addText(b4.map(t=>({text:t,options:{bullet:{code:"2022"},color:INK,fontSize:13.5,paraSpaceAfter:10,breakLine:true}})),
  {x:8.1,y:2.35,w:4.65,h:4,fontFace:F,valign:"top",margin:0});
footer(s,5);
// S6 RESULTADO
s=p.addSlide(); head(s,"O resultado","O Ciclone é a tecnologia recomendada");
s.addImage({path:"ranking.png",x:M,y:1.75,w:7.2,h:7.2*546/1105});
s.addShape(p.ShapeType.roundRect,{x:8.15,y:2.2,w:4.55,h:2.6,rectRadius:0.08,fill:{color:SURF},line:{color:GOOD,width:1.5}});
s.addText("VENCEDOR",{x:8.4,y:2.4,w:4,h:0.3,fontFace:F,fontSize:11,bold:true,color:GOOD,charSpacing:1,margin:0});
s.addText([{text:"CICLONE  ",options:{fontSize:30,bold:true,color:GOOD}},{text:"+11/17",options:{fontSize:22,bold:true,color:INK}}],
  {x:8.4,y:2.75,w:4,h:0.7,fontFace:F,margin:0,valign:"middle"});
s.addText("Vantagem clara sobre o 2º (Filtro Cerâmico, +8) e o 3º (Settler, +7). As vias úmidas (Quench/Scrubber) ficaram em último (+3).",
  {x:8.4,y:3.5,w:4.05,h:1.2,fontFace:F,fontSize:13.5,color:MUTED,margin:0,valign:"top"});
footer(s,6);
// S7 POR QUE CICLONE
s=p.addSlide(); head(s,"Por quê","6 razões pelas quais o ciclone venceu");
const adv=[["Alta temperatura","Opera a 450 °C direto (via seca) — sem resfriar o gás"],
 ["ΔP baixo","5–25 mbar < 40 mbar do projeto"],
 ["Sem partes móveis","Baixo custo e baixa manutenção"],
 ["Gás seco e quente","Perfeito para o condensador casco-tubo a jusante"],
 ["Evita filtração","Não gera líquido a filtrar (critério do cliente)"],
 ["Resiste ao HCl","Via seca vence a corrosão que afunda as úmidas"]];
let vx=[M,4.83,9.04], vy=[1.75,3.9];
adv.forEach((t,i)=>{ const x=vx[i%3], y=vy[Math.floor(i/3)];
  s.addShape(p.ShapeType.roundRect,{x,y,w:3.9,h:1.9,rectRadius:0.07,fill:{color:SURF},line:{color:LINE,width:1}});
  s.addShape(p.ShapeType.roundRect,{x:x+0.22,y:y+0.22,w:0.42,h:0.42,rectRadius:0.05,fill:{color:GOOD}});
  s.addText("✓",{x:x+0.22,y:y+0.2,w:0.42,h:0.42,fontFace:F,fontSize:15,bold:true,color:WHITE,align:"center",valign:"middle",margin:0});
  s.addText(t[0],{x:x+0.78,y:y+0.2,w:3,h:0.45,fontFace:F,fontSize:15,bold:true,color:INK,margin:0,valign:"middle"});
  s.addText(t[1],{x:x+0.25,y:y+0.78,w:3.5,h:0.95,fontFace:F,fontSize:12.5,color:MUTED,margin:0,valign:"top"}); });
footer(s,7);
// S8 POR QUE AS OUTRAS
s=p.addSlide(); head(s,"O trade-off","Por que as outras não passaram");
const rows=[["Filtro Cerâmico","+8","Melhor eficiência, MAS regeneração de 6–9 h → inviável em contínuo + custo alto",AMBER],
 ["Settler Gravit.","+7","Barato e simples, MAS não captura os finos (<200 µm escapam)",AMBER],
 ["ESP","+5","Degrada acima de 400 °C — eficiência cai e consumo sobe",BAD],
 ["Quench / Scrubber","+3","Via úmida: exige filtrar/tratar o líquido, resfria o gás (incompatível com o downstream) e o HCl vira ácido",BAD]];
let ry=1.85;
rows.forEach(r=>{
  s.addShape(p.ShapeType.roundRect,{x:M,y:ry,w:12.1,h:1.12,rectRadius:0.06,fill:{color:SURF},line:{color:LINE,width:1}});
  s.addText(r[0],{x:M+0.25,y:ry,w:3,h:1.12,fontFace:F,fontSize:15,bold:true,color:INK,margin:0,valign:"middle"});
  s.addShape(p.ShapeType.roundRect,{x:M+3.3,y:ry+0.34,w:0.9,h:0.44,rectRadius:0.05,fill:{color:r[3]}});
  s.addText(r[1],{x:M+3.3,y:ry+0.32,w:0.9,h:0.46,fontFace:F,fontSize:14,bold:true,color:WHITE,align:"center",valign:"middle",margin:0});
  s.addText(r[2],{x:M+4.45,y:ry,w:7.5,h:1.12,fontFace:F,fontSize:13,color:MUTED,margin:0,valign:"middle"});
  ry+=1.24; });
footer(s,8);
// S9 CONCLUSAO
s=p.addSlide(); s.background={color:NAVY};
s.addImage({path:"bg_wide.png",x:0,y:0,w:W,h:H});
s.addShape(p.ShapeType.rect,{x:0,y:0,w:W,h:H,fill:{color:NAVY,transparency:20}});
s.addText("RECOMENDAÇÃO",{x:M,y:0.7,w:9,h:0.35,fontFace:F,fontSize:13,bold:true,color:"7FB3D5",charSpacing:3,margin:0});
s.addText("Ciclone — e os 2 desafios do próximo estágio",{x:M,y:1.05,w:11.5,h:0.7,fontFace:F,fontSize:29,bold:true,color:WHITE,margin:0});
function col(x,tag,body){
  s.addShape(p.ShapeType.roundRect,{x,y:2.35,w:5.7,h:2.9,rectRadius:0.08,fill:{color:"14294A",transparency:12},line:{color:"7FB3D5",width:1.25}});
  s.addText(tag,{x:x+0.35,y:2.6,w:5,h:0.5,fontFace:F,fontSize:19,bold:true,color:WHITE,margin:0,valign:"top"});
  s.addText(body,{x:x+0.35,y:3.35,w:5,h:1.7,fontFace:F,fontSize:14,color:DKMUT,margin:0,valign:"top"}); }
col(M,"① Capturar os finos","O ponto fraco do ciclone é a fração < 75 µm do char carreado. O CFD (fase discreta) quantifica a eficiência por tamanho — o Lapple só dá o limite superior.");
col(7.0,"② Evitar a condensação","O gás deve ficar ACIMA do ponto de orvalho dos hidrocarbonetos. O CFD verifica o gradiente parede-gás (o ciclone compacto ajuda: residência curta, pouca perda térmica).");
s.addText("Próximo: dimensionamento + CFD (STAR-CCM+) para cravar a eficiência real e a operação acima do orvalho.",
  {x:M,y:5.55,w:11.7,h:0.5,fontFace:F,fontSize:14.5,italic:true,bold:true,color:WHITE,align:"center",margin:0});
s.addImage({path:"logo_caexperts.png",x:W/2-1.05,y:6.1,w:2.1,h:2.1*313/760});
p.writeFile({fileName:"Valgroup_Selecao_Tecnologia.pptx"}).then(f=>console.log("OK:",f));
