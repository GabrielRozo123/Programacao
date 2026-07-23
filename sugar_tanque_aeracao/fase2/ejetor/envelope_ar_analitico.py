import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Bico nativo 7xO9
mu=6.5; rho=1300.0; N=7; D=0.009; L=0.045; A_hole=np.pi*D**2/4
def dP(Q_lance):  # Q em m3/s por lanca
    Qh=Q_lance/N; v=Qh/A_hole
    dP_visc=128*mu*L*Qh/(np.pi*D**4)     # Hagen-Poiseuille
    dP_acc =0.5*rho*v**2                  # aceleracao ao jato
    dP_ent =0.5*(0.5*rho*v**2)           # entrada abrupta K~0.5
    return dP_visc+dP_acc+dP_ent, dP_visc, dP_acc+dP_ent, v

# ponto de operacao
Qop=32.5/3600
dt,dv,dm,vop=dP(Qop)
print(f"OP 32,5 m3/h/lanca: v_furo={vop:.1f} m/s  dP_analitico={dt/1e6:.2f} MPa (visc {dv/1e6:.2f} + resto {dm/1e6:.2f})  | CFD=3,04 MPa")

# curva
Q=np.linspace(0.5,40,300)/3600
DP=np.array([dP(q)[0] for q in Q])/1e6
Qh=Q*3600
# pressoes de ar
airs={'1 kgf':0.098,'2 kgf':0.196,'3 kgf':0.294}
# crossover: onde dP == p_ar
def crossover(pair):
    f=np.array([dP(q)[0]/1e6-pair for q in Q])
    idx=np.where(np.diff(np.sign(f)))[0]
    return Qh[idx[0]] if len(idx) else np.nan
print("\nEnvelope (vazao maxima p/ o ar ENTRAR):")
for k,p in airs.items():
    qc=crossover(p); print(f"  ar {k} ({p*1000:.0f} kPa) -> ar entra so se vazao <= {qc:.1f} m3/h/lanca  (op e 32,5)")

plt.figure(figsize=(9,6))
plt.plot(Qh,DP,'k-',lw=2.5,label='Contrapressao do bico 7xØ9 (analitico)')
plt.scatter([32.5],[3.04],c='red',s=90,zorder=5,label='CFD VOF (3,04 MPa) — bate na curva')
for k,p in airs.items():
    plt.axhline(p,ls='--',lw=1.3,label=f'suprimento ar {k} ({p*1000:.0f} kPa)')
    qc=crossover(p)
    if not np.isnan(qc): plt.scatter([qc],[p],s=45,zorder=5)
plt.axvline(32.5,color='gray',ls=':',lw=1); plt.text(33,7,'operacao\n32,5 m³/h/lança',fontsize=8)
plt.yscale('log'); plt.xlabel('Vazao de xarope por lanca (m³/h)'); plt.ylabel('Pressao a montante do bico (MPa)')
plt.title('Envelope: o ar so entra ONDE a curva do xarope fica ABAIXO da linha do ar')
plt.grid(True,which='both',alpha=0.3); plt.legend(fontsize=8,loc='lower right')
out="/tmp/claude-0/-home-user-Programacao/d7e95d58-0a9a-5744-b0e9-262c592f6690/scratchpad/envelope_ar.png"
plt.tight_layout(); plt.savefig(out,dpi=130); print("\n",out)
