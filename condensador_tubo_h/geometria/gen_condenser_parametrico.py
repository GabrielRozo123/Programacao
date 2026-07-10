import cadquery as cq
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyArrow

# ===== COTAS (mm) — ancoradas na pesquisa =====
D_TUBO = 25.4          # OD do tubo (1")  [industrial + escala do experimento]
R = D_TUBO/2.0
W = 10*D_TUBO          # largura do dominio (254 mm)
H = 10*D_TUBO          # altura do dominio (254 mm)
CY = 0.12*H            # centro do tubo acima do meio (espaco p/ drenagem embaixo)
T = 1.0                # espessura do slab (2D)

# ===== GEOMETRIA: dominio de fluido = caixa - tubo, extrudado fino =====
box  = cq.Workplane("XY").rect(W, H).extrude(T)
tube = cq.Workplane("XY").center(0, CY).circle(R).extrude(T)
fluid = box.cut(tube)
cq.exporters.export(fluid, "condenser_tube_2D.step")
bb = fluid.val().BoundingBox()
print(f"STEP salvo. BBox mm: X[{bb.xmin:.0f},{bb.xmax:.0f}] Y[{bb.ymin:.0f},{bb.ymax:.0f}] Z[{bb.zmin:.1f},{bb.zmax:.1f}]")
print(f"Tubo OD={D_TUBO} mm, centro y={CY:.1f} mm, dominio {W:.0f}x{H:.0f} mm")

# ===== ESQUEMATICO =====
INK='#1a2733'; BLUE='#1F6BB0'; CYAN='#23B5D3'; AMBER='#E39A2E'; MUTED='#6b7a89'; NAVY='#0E2A45'
plt.rcParams['font.family']='DejaVu Sans'
fig,ax=plt.subplots(figsize=(6.6,6.8),dpi=160)
w=W/1000; h=H/1000; r=R/1000; cy=CY/1000
# dominio (vapor)
ax.add_patch(Rectangle((-w/2,-h/2),w,h,fc='#eaf3fa',ec=NAVY,lw=2))
ax.text(-w/2+0.006,h/2-0.012,'VAPOR  (T_sat = 100 °C, 1 atm)',color=BLUE,fontsize=10,fontweight='bold',va='top')
# tubo frio
ax.add_patch(Circle((0,cy),r,fc='#d7e6f2',ec=BLUE,lw=2.5))
ax.text(0,cy,'TUBO\nfrio\nØ25,4',ha='center',va='center',fontsize=9,color=INK,fontweight='bold',linespacing=1.0)
# filme de condensado (indicacao)
ax.add_patch(Circle((0,cy),r*1.06,fc='none',ec=CYAN,lw=1.4,ls=(0,(3,2))))
ax.annotate('filme de\ncondensado\n(dezenas-centenas µm)',xy=(r*0.75,cy-r*0.75),xytext=(w/2-0.075,cy-0.02),
            color=CYAN,fontsize=8.5,fontweight='bold',ha='left',linespacing=1.05,
            arrowprops=dict(arrowstyle='->',color=CYAN,lw=1.2))
# gota drenando
ax.annotate('',xy=(0,cy-r-0.03),xytext=(0,cy-r),arrowprops=dict(arrowstyle='->',color=CYAN,lw=2))
ax.text(0.006,cy-r-0.02,'dreno',color=CYAN,fontsize=8,va='center')
# gravidade
ax.add_patch(FancyArrow(-w/2+0.02,0.0,0,-0.04,width=0.002,color=INK,length_includes_head=True,head_width=0.008))
ax.text(-w/2+0.03,-0.02,'g',color=INK,fontsize=12,fontweight='bold',style='italic')
# h extraction
ax.text(0,-h/2+0.01,'h(θ) = q″/(T_sat − T_parede)  →  validar vs Nusselt',
        ha='center',va='bottom',fontsize=9,color=AMBER,fontweight='bold')
ax.set_xlim(-w/2-0.01,w/2+0.01); ax.set_ylim(-h/2-0.01,h/2+0.01)
ax.set_aspect('equal'); ax.axis('off')
ax.set_title('Condensador — domínio 2D (condensação filmwise em tubo horizontal)',
             fontsize=11,fontweight='bold',color=NAVY)
plt.tight_layout()
plt.savefig('condenser_esquema.png',facecolor='white',bbox_inches='tight')
print('esquema salvo.')
