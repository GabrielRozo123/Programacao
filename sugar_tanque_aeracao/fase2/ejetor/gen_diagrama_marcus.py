import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
NAVY='#0A1A33'; BLUE='#1C5FA8'; AMBER='#D9822B'; GOOD='#2E8B57'; BAD='#C0504D'; GREY='#5a6570'
fig,ax=plt.subplots(figsize=(15.5,8.6)); ax.set_xlim(0,100); ax.set_ylim(0,100); ax.axis('off')
def box(x,y,w,h,titulo,linhas,cor,fs=9.5,tfs=10.5,fill='white',lw=2.2):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.6,rounding_size=1.2",
                 facecolor=fill,edgecolor=cor,linewidth=lw,zorder=2))
    ax.text(x+w/2,y+h-2.6,titulo,ha='center',va='top',fontsize=tfs,fontweight='bold',color=cor,zorder=3)
    ax.text(x+w/2,y+h-7.2,linhas,ha='center',va='top',fontsize=fs,color='#1a1a1a',zorder=3,linespacing=1.55)
def seta(x1,y1,x2,y2,cor=NAVY,lw=2.6):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=22,
                 color=cor,linewidth=lw,zorder=1))
ax.text(50,97.5,'POR QUE O AR NÃO ENTRA NO EJETOR',ha='center',fontsize=17,fontweight='bold',color=NAVY)
ax.text(50,93.6,'Projeto Ito · bico 7×Ø9 · vazão informada 130 m³/h · ar 1 kgf/cm²',ha='center',fontsize=10.5,color=GREY)
# ---- cadeia principal (esquerda) ----
X,W=4,50
box(X,76,W,14,'1 · GEOMETRIA  (do STEP nativo do Brendo)',
    'Xarope desce pelo tubo de 4"  →  passa a válvula de ar 1½"\n→  redução  →  BICO 7×Ø9  →  lança de 3 m\n'
    'A entrada de ar fica ANTES do bico (confirmado no CAD)',BLUE)
seta(X+W/2,75.5,X+W/2,70.5)
box(X,55,W,14,'2 · COMO O AR FOI SETADO   ← a sua dúvida',
    'Ar_in = STAGNATION INLET · 1 kgf/cm² (98.066 Pa) · VF_ar = 1\n'
    'É a BC correta para ar sob pressão: o solver calcula a vazão\n'
    'de ar que essa pressão consegue empurrar.',AMBER)
seta(X+W/2,54.5,X+W/2,49.5)
box(X,34,W,14,'3 · O QUE O XAROPE EXIGE',
    'Empurrar 130 m³/h de xarope 6,5 Pa·s pelos 7 furos Ø9\n'
    'exige  23,5 bar  de pressão antes do bico.\n'
    '(CFD + cálculo analítico + modelo calibrado concordam)',BAD)
seta(X+W/2,33.5,X+W/2,28.0)
box(X,2,W,25,'4 · O DUELO DE PRESSÕES  (é só isso)',
    'XAROPE empurrando .......  23,5 bar\nAR disponível ...............   1,0 bar\n'
    '______________________________________\n\nO ar é  24×  mais fraco  →  NÃO ENTRA\n'
    'e o xarope ainda REFLUI pela linha de ar',NAVY,fs=10.5,tfs=11.5,fill='#F2F5F9',lw=3)
# ---- coluna direita: objeções ----
X2,W2=58,38
box(X2,72,W2,18,'"E se a BC do ar estivesse errada?"',
    'Não mudaria a resposta.\nPara o ar entrar, a BC teria de estar\n'
    '24× errada — não é ajuste fino,\né uma ordem de grandeza.',GOOD,fs=9.5)
seta(X2+W2/2,71.5,X2+W2/2,66.5,GOOD)
box(X2,48,W2,17,'"E o vácuo que o Ito descreve?"',
    'Vácuo tem TETO FÍSICO de 1 bar.\nContra 23,5 bar, mudaria só 4%.\n'
    'Mesmo vácuo PERFEITO não muda\na conclusão.',GOOD,fs=9.5)
seta(X2+W2/2,47.5,X2+W2/2,42.5)
box(X2,20,W2,20,'O QUE ISSO SIGNIFICA',
    'A vazão real NÃO deve ser 130 m³/h.\n\nSe houvesse vácuo de fato, a vazão\n'
    'teria de ser ~60× menor.\nA observação do Ito CONFIRMA isso.',BLUE,fs=9.5,fill='#EAF1F8')
seta(X2+W2/2,19.5,X2+W2/2,15.0)
box(X2,0.5,W2,15,'OS 2 DADOS QUE FALTAM',
    '1 · Pressão de descarga da BOMBA\n2 · Pressão do ar que alimenta o EJETOR\n'
    '(os 1–3 kgf são da Fase 1 / aerador)',AMBER,fs=9.5,fill='#FDF6EE')
plt.tight_layout()
out="/home/user/Programacao/sugar_tanque_aeracao/fase2/ejetor/diagrama_explicativo_marcus.png"
plt.savefig(out,dpi=145,bbox_inches='tight',facecolor='white'); print(out)
