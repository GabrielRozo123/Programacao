import csv, math

UP = "/root/.claude/uploads/d7e95d58-0a9a-5744-b0e9-262c592f6690/"

def load(fn):
    t, v = [], []
    with open(UP + fn) as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            t.append(float(row[0])); v.append(float(row[1]))
    return t, v

def stats(vals):
    n = len(vals); m = sum(vals)/n
    sd = math.sqrt(sum((x-m)**2 for x in vals)/n)
    return m, sd

def window(t, v, t0, t1):
    return [x for x in zip(t, v) if t0 <= x[0] <= t1]

# ============ 1. TORQUE ============
t, tq = load("3b2f3f28-TORQUE.csv")
print("="*60)
print("1. TORQUE (Reator)")
# janelas: 10-15s vs 16-21.2s -> checa deriva
for (a,b) in [(5,10),(10,15),(16,21.3)]:
    w = window(t,tq,a,b)
    m,sd = stats([x[1] for x in w])
    print(f"  janela {a}-{b}s: media={m:.2f} N.m  desvio={sd:.3f}  n={len(w)}")
w = window(t,tq,16,21.3)
T_mean, T_sd = stats([x[1] for x in w])
omega = 109.3*2*math.pi/60
P = abs(T_mean)*omega
rho, N, D = 1350.0, 109.3/60, 0.8
Np = P/(rho*N**3*D**5)
print(f"  >>> Torque final={T_mean:.2f}±{T_sd:.2f} N.m | omega={omega:.4f} rad/s")
print(f"  >>> Potencia={P:.1f} W = {P/1000:.3f} kW | Np(2 estagios)={Np:.3f} | Np/estagio={Np/2:.3f}")

# ============ 2. VAZAO Q ============
t, q = load("3894e4ce-Vazao_q.csv")
print("="*60)
print("2. VAZAO Q (Surface Integral, disco r=0.4m)")
per = 60/109.3  # periodo de rotacao
print(f"  periodo de rotacao = {per:.4f} s")
print(f"  faixa de dados: t={t[0]:.2f} a {t[-1]:.2f}s")
# medias por janela de 2s pra ver deriva
a = math.floor(t[0]); 
while a < t[-1]-1.5:
    w = window(t,q,a,a+2)
    if len(w)>5:
        m,sd = stats([x[1] for x in w])
        print(f"  janela {a:5.1f}-{a+2:5.1f}s: Q_medio={m:.4f} m3/s (desvio {sd:.4f})")
    a += 2
# taxa de deriva no fim (ultimos 4s), por regressao linear
w = window(t,q,t[-1]-4,t[-1])
tw = [x[0] for x in w]; qw=[x[1] for x in w]
n=len(tw); mt=sum(tw)/n; mq=sum(qw)/n
slope = sum((a-mt)*(b-mq) for a,b in zip(tw,qw))/sum((a-mt)**2 for a in tw)
print(f"  deriva nos ultimos 4s: {slope:.5f} m3/s por segundo ({slope/mq*100:.2f}%/s do valor)")
# media sobre numero inteiro de rotacoes no fim: ultimas 6 rotacoes
nrot=6; t1=t[-1]; t0=t1-nrot*per
w = window(t,q,t0,t1)
Qm, Qsd = stats([x[1] for x in w])
Nq = abs(Qm)/(N*D**3)
print(f"  >>> Q medio (ultimas {nrot} rotacoes, {t0:.2f}-{t1:.2f}s) = {Qm:.4f}±{Qsd:.4f} m3/s")
print(f"  >>> Nq(2 estagios)={Nq:.3f} | Nq/estagio={Nq/2:.3f}")

# ============ 3. SMD PERTO INJETOR ============
t, s = load("f274d372-SMD_PERTO_INJETOR.csv")
print("="*60)
print("3. SMD PERTO INJETOR (platô?)")
for (a,b) in [(8,10),(12,14),(16,18),(19,21.3)]:
    w = window(t,s,a,b)
    if w:
        m,sd = stats([x[1] for x in w])
        print(f"  janela {a}-{b}s: SMD={m:.1f}±{sd:.1f} um")
# taxa de crescimento: regressao nos ultimos 3s
w = window(t,s,t[-1]-3,t[-1])
tw=[x[0] for x in w]; sw=[x[1] for x in w]
n=len(tw); mt=sum(tw)/n; ms=sum(sw)/n
slope = sum((a-mt)*(b-ms) for a,b in zip(tw,sw))/sum((a-mt)**2 for a in tw)
print(f"  taxa de crescimento ultimos 3s: {slope:.2f} um/s (era ~63.6 um/s entre t=4 e 9.5s)")
print(f"  ultimo valor: {s[-1]:.1f} um em t={t[-1]:.2f}s")
# fit exponencial S(t)=Sinf-(Sinf-S0)exp(-t/tau) via 3 pontos espaçados (t=10,15.5,21)
def interp(tq_):
    for i in range(1,len(t)):
        if t[i]>=tq_:
            f=(tq_-t[i-1])/(t[i]-t[i-1]); return s[i-1]+f*(s[i]-s[i-1])
t1_,t2_,t3_ = 10.0, 15.6, 21.2
s1,s2,s3 = interp(t1_),interp(t2_),interp(t3_)
print(f"  pontos p/ fit: S({t1_})={s1:.1f}, S({t2_})={s2:.1f}, S({t3_})={s3:.1f}")
# com espacamento igual dt: razao r=(s3-s2)/(s2-s1)=exp(-dt/tau)
r = (s3-s2)/(s2-s1)
if 0<r<1:
    dt_ = t2_-t1_
    tau = -dt_/math.log(r)
    Sinf = (s2 - s1*r*r/r)  # formula: Sinf = (s2^2? ) -- usar formula correta abaixo
    # Para pontos igualmente espacados: Sinf = (s1*s3 - s2^2)/(s1+s3-2*s2)
    Sinf = (s1*s3 - s2*s2)/(s1+s3-2*s2)
    t95 = t1_ + tau*math.log((Sinf-s1)/(0.05*(Sinf-s1)))
    print(f"  fit exp: tau={tau:.1f}s | S_inf={Sinf:.0f} um | 95% do platô em t≈{t95:.1f}s")
else:
    print(f"  razao r={r:.3f} fora de (0,1) — sem fit exponencial valido")

# ============ 4. BOLHA FLOTAVEL ============
t, b = load("93f7690c-BOLHA_FLOTAVEL.csv")
print("="*60)
print("4. PERCENTUAL BOLHA FLOTAVEL")
w = window(t,b,15,21.3)
m,sd = stats([x[1] for x in w])
print(f"  janela 15-21.2s: {m:.3e} ± {sd:.1e} %")
print(f"  ultimo valor: {b[-1]:.3e} % em t={t[-1]:.2f}s")

# ============ 5. ANALITICO (Bird et al.) ============
print("="*60)
print("5. CALCULOS ANALITICOS (Bird, Armstrong & Hassager Ex 1.4-2)")
mu, g = 6.5, 9.81
SMD_final = s3  # ultimo smd interp
for d_um in [200, 1000, SMD_final, 2000, 3000]:
    R = d_um*1e-6/2
    V = (1/3)*rho*g*R*R/mu
    t_rise = 6.47/V if V>0 else float('inf')
    print(f"  d={d_um:7.1f} um: V_subida={V*1000:8.4f} mm/s | t p/ 6.47m = {t_rise/3600:9.2f} h")
# volume de ar total informado (report pontual)
Var = 9.383882e-04
V_aer = 20.17
print(f"  Volume de Ar total no Aerador (t=21s): {Var*1000:.3f} L (report pontual)")
print(f"  Holdup de gas = {Var/V_aer*100:.5f}% do volume do tanque (20.17 m3)")
