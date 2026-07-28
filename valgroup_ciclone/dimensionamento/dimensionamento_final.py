"""
DIMENSIONAMENTO FINAL do ciclone — Valgroup
Condição de projeto confirmada (Gabriel/Marcus): suspensão 1900 kg/h − 80 kg/h de particulado
→ GÁS = 1820 kg/h · sólido = 80 kg/h. Rodadas a 100% e 50% da vazão nominal.

Base: planilha "Dimensionamento de Ciclone Lapple" (colegas) + Peçanha cap.3 / Cremasco cap.6,8.
Compara família LAPPLE (convencional) × STAIRMAND (alta eficiência).
"""
import numpy as np

# ── CONDIÇÃO DE PROJETO ───────────────────────────────────────────────────
M_TOT, M_SOL = 1900.0, 80.0          # kg/h (suspensão total, particulado)
M_GAS = M_TOT - M_SOL                # kg/h → 1820
RHO_400 = 3.946                      # kg/m³ @400°C 1,2 bar (cliente/planilha)
T_PROJ = 400.0                       # °C (planilha; SCADA TT-209 dá ~343 → mais denso, mais margem)
MU = 9.5e-5                          # Pa·s (planilha) ⚠️ alto p/ vapor HC; ver sensibilidade
RHO_S = 776.75                       # kg/m³ (planilha = BULK) ⚠️ o correto é a densidade da PARTÍCULA
V_I = 15.239                         # m/s velocidade recomendada de entrada (planilha)
DP_MAX = 40e2                        # Pa (16" H2O)

# famílias: (nome, a/Dc, b/Dc, De/Dc, S/Dc, h/Dc, H/Dc, B/Dc, Ne, xi)
FAM = {
 "LAPPLE   (convencional)": (0.50,0.25,0.50,0.625,2.0,4.0,0.25,5,8.0),
 "STAIRMAND (alta efic.)" : (0.50,0.20,0.50,0.50 ,1.5,4.0,0.375,6,6.4),
}

def rho_at(T): return RHO_400*(T_PROJ+273.15)/(T+273.15)

def sizing(fam, Q, mu=MU, rho=RHO_400, rho_s=RHO_S, vi=V_I):
    a,b,De,S,h,H,B,Ne,xi = FAM[fam]
    Dc = np.sqrt(Q/(a*b*vi))                       # área entrada = a·b·Dc²
    vi_r = Q/(a*Dc*b*Dc)
    dstar = np.sqrt(9*mu*(b*Dc)/(2*np.pi*Ne*vi_r*(rho_s-rho)))   # Lapple
    dP = xi*0.5*rho*vi_r**2
    return dict(Dc=Dc,a=a*Dc,b=b*Dc,De=De*Dc,S=S*Dc,h=h*Dc,H=H*Dc,B=B*Dc,
                Ne=Ne,vi=vi_r,dstar=dstar,dP=dP)

def perf(g, Q, mu=MU, rho=RHO_400, rho_s=RHO_S):
    """recalcula d* e ΔP para OUTRA vazão no MESMO ciclone (turndown)"""
    a,b = g['a'],g['b']; vi = Q/(a*b)
    dstar = np.sqrt(9*mu*b/(2*np.pi*g['Ne']*vi*(rho_s-rho)))
    xi = 8.0 if g['Ne']==5 else 6.4
    return vi, dstar, xi*0.5*rho*vi**2

# PSD da amostra EXTRAÍDA (⚠️ o char CARREADO é mais fino)
BINS=[(12500,20000,2.78),(4750,12500,3.77),(1000,4750,9.51),(425,1000,12.10),
      (150,425,25.79),(75,150,36.91),(20,75,9.41)]
def eta_global(dstar):
    tot=sum(m for *_,m in BINS); acc=0.0
    for lo,hi,m in BINS:
        d=np.sqrt(lo*hi)*1e-6
        acc += m/(1+(dstar/d)**2)
    return acc/tot

rho=RHO_400; Q100=(M_GAS/3600)/rho; Q50=Q100/2
print("="*74)
print(f" CONDIÇÃO: {M_TOT:.0f} − {M_SOL:.0f} = {M_GAS:.0f} kg/h de gás · ρ={rho:.3f} · T={T_PROJ:.0f}°C")
print(f"   100% → Q = {Q100*3600:.1f} m³/h ({Q100:.4f} m³/s)")
print(f"    50% → Q = {Q50*3600:.1f} m³/h ({Q50:.4f} m³/s)")
print("="*74)
for fam in FAM:
    g = sizing(fam, Q100)
    print(f"\n### {fam}  — dimensionado a 100% (v_i={g['vi']:.1f} m/s)")
    print(f"  Dc={g['Dc']*1000:6.1f} mm | entrada a×b = {g['a']*1000:.0f}×{g['b']*1000:.0f} mm | "
          f"De={g['De']*1000:.0f} | S={g['S']*1000:.0f}")
    print(f"  h(cil)={g['h']*1000:.0f} | H(total)={g['H']*1000:.0f} mm | saída pó B={g['B']*1000:.0f} mm | Ne={g['Ne']}")
    print(f"  {'carga':<8}{'v_i (m/s)':>11}{'d* (µm)':>10}{'ΔP (mbar)':>12}{'η global':>11}{'ΔP<40?':>9}")
    for tag,Qx in [("100%",Q100),("50%",Q50)]:
        vi,ds,dP = perf(g,Qx)
        print(f"  {tag:<8}{vi:11.2f}{ds*1e6:10.2f}{dP/100:12.2f}{eta_global(ds)*100:10.2f}%{'  OK' if dP<=DP_MAX else ' EXCEDE':>9}")

print("\n" + "="*74)
print(" SENSIBILIDADE aos 2 inputs duvidosos (ciclone LAPPLE @100%)")
print("="*74)
g = sizing("LAPPLE   (convencional)", Q100)
print(f"  {'ρ_s':>8} {'µ':>10}   d* (µm)   η global")
for rs,tag in [(776.75,"bulk(planilha)"),(1500,"partícula est."),(2000,"partícula alta")]:
    for mu,mtag in [(9.5e-5,"planilha"),(2.5e-5,"HC típico")]:
        _,ds,_ = perf(g,Q100,mu=mu,rho_s=rs)
        print(f"  {rs:8.1f} {mu:10.1e}   {ds*1e6:7.2f}   {eta_global(ds)*100:6.2f}%   ({tag}/{mtag})")
print("\n  ⚠️ ρ_s da planilha é BULK (com vazios) → subestima a inércia → d* pessimista.")
print("     µ=9,5e-5 é alto p/ vapor de HC a 400°C (típico 1,5–3e-5) → também pessimista.")
print("     Ou seja: o dimensionamento da planilha é CONSERVADOR. Bom para projeto.")
