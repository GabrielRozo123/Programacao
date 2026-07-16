import cadquery as cq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mp
import math

# ================= COTAS (tudo em mm; datum z=0 = inicio da parede cilindrica) =================
D_CIL      = 1659.0          # diametro do cilindro (confirmado no desenho)
R          = D_CIL/2.0       # 829.5
H_LIQ      = 1530.0          # altura de liquido no cilindro (1,53 m, confirmado)
H_CONE     = 268.0           # altura do cone de fundo  <-- ASSUMIDO p/ fechar ~3500 L (confirmar c/ Pedro)
R_APEX     = 40.0            # raio do apice/saida do cone <-- ASSUMIDO (confirmar DN)
# alturas dos bocais (relativas ao datum z=0):
Z_SUC_CHILLER = 1350.0       # succao ao chiller: NOVA posicao 1,35 m (confirmado no e-mail)
Z_SUC_BASE    = 850.0        # succao ao chiller: posicao original 0,85 m (baseline)
Z_RET_CHILLER = 50.0         # retorno do chiller: FUNDO (CONFIRMADO no diagrama EGISA 16/07)
# recirc (Sim 2): captacao no FUNDO, retorno no TOPO (CONFIRMADO 16/07). Alturas exatas [SUPOSTO]; DN pendente.
Z_RECIRC_CAPT = 100.0        # captacao da recirc: fundo <-- altura exata a confirmar
Z_RECIRC_RET  = 1500.0       # retorno da recirc: topo (~nivel de liquido) <-- altura exata a confirmar

# ================= SOLIDO (dominio de liquido: cone + cilindro ate 1,53 m) =================
cyl  = cq.Solid.makeCylinder(R, H_LIQ, pnt=cq.Vector(0,0,0),      dir=cq.Vector(0,0,1))
cone = cq.Solid.makeCone(R_APEX, R, H_CONE, pnt=cq.Vector(0,0,-H_CONE), dir=cq.Vector(0,0,1))
body = cyl.fuse(cone)
w = cq.Workplane(obj=body)
cq.exporters.export(w, "tank_chiller_base_DRAFT.step")

vol_mm3 = body.Volume()
vol_L   = vol_mm3/1e6   # mm3 -> mL... nao: 1 L = 1e6 mm3
print(f"Volume do dominio de liquido (cone+cilindro ate 1,53m): {vol_L:,.0f} L")
A = math.pi*(R/1000.0)**2
print(f"  - so cilindro (0->1,53m): {A*1.53*1000:,.0f} L")
print(f"  - so cone (h={H_CONE/1000:.3f}m): {vol_L - A*1.53*1000:,.0f} L")

# ================= ESQUEMATICO LIMPO (corte r-z) =================
fig,ax=plt.subplots(figsize=(6.2,7.6),dpi=150)
r=R/1000.0; hl=H_LIQ/1000.0; hc=H_CONE/1000.0; ra=R_APEX/1000.0
NAVY='#0E2A45'; CYAN='#23B5D3'; AMBER='#F2B84B'; RED='#E4572E'; GREEN='#2ECC71'; GREY='#9FB3C8'
# parede
ax.plot([-r,-r],[0,hl],color=NAVY,lw=2); ax.plot([r,r],[0,hl],color=NAVY,lw=2)
ax.plot([-r,-ra],[0,-hc],color=NAVY,lw=2); ax.plot([r,ra],[0,-hc],color=NAVY,lw=2)
ax.plot([-ra,ra],[-hc,-hc],color=NAVY,lw=2)
# liquido
ax.fill_between([-r,r],[0,0],[hl,hl],color=CYAN,alpha=0.12)
ax.fill([-r,r,ra,-ra],[0,0,-hc,-hc],color=CYAN,alpha=0.12)
ax.plot([-r,r],[hl,hl],color=CYAN,lw=1.6,ls='--')
ax.text(0,hl+0.04,f'nivel de liquido  1,53 m',ha='center',color=CYAN,fontsize=9,fontweight='bold')
ax.plot([r+0.02,r+0.02],[0,hl],color=GREY,lw=0.8)
# datum
ax.plot([-r-0.15,-r],[0,0],color='k',lw=0.8); ax.text(-r-0.17,0,'0 (inicio cilindro)',ha='right',va='center',fontsize=8,color='k')
def bocal(z,txt,col,side=-1):
    x0=side*r
    ax.annotate('',xy=(x0+side*0.16,z),xytext=(x0,z),arrowprops=dict(arrowstyle='-',color=col,lw=3))
    ax.plot([x0],[z],'o',color=col,ms=7)
    ha='right' if side<0 else 'left'
    ax.text(x0+side*0.20,z,txt,ha=ha,va='center',fontsize=8.5,color=col,fontweight='bold')
bocal(Z_SUC_CHILLER/1000.0,'succao chiller\n1,35 m (NOVO)',RED,side=-1)
bocal(Z_SUC_BASE/1000.0,   'succao chiller\n0,85 m (baseline)',AMBER,side=-1)
bocal(Z_RET_CHILLER/1000.0,'retorno chiller\nfundo (confirmado)',GREEN,side=1)
bocal(Z_RECIRC_CAPT/1000.0,'recirc: captacao\nfundo (Sim 2)','#8E44AD',side=1)
bocal(Z_RECIRC_RET/1000.0, 'recirc: retorno\ntopo (Sim 2)','#8E44AD',side=-1)
ax.text(0,-hc-0.12,'saida cone (apice)',ha='center',fontsize=8,color=GREY)
ax.text(0.0,hl*0.5,'RECIRC:\nbocais + DN\nPENDENTES\n(Pedro)',ha='center',va='center',
        fontsize=9,color=RED,style='italic',bbox=dict(boxstyle='round',fc='white',ec=RED,alpha=0.9))
ax.set_aspect('equal'); ax.axis('off')
ax.set_title('TAG 3500 L — corte / mapa de bocais (DRAFT)',fontsize=11,fontweight='bold',color=NAVY)
plt.tight_layout()
plt.savefig('tank_chiller_esquematico.png',bbox_inches='tight',facecolor='white')
print("STEP + PNG gerados.")
