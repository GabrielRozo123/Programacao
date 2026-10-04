"""Clima de vento do local: dados de atlas/reanálise → perfil de camada limite → rosa dos ventos →
pegadas de radiação por setor e mapas de probabilidade de excedência.

Convenções
----------
* Direção meteorológica: de onde o vento VEM, em graus a partir do Norte, sentido horário
  (0 = N, 90 = E). O vento sopra para θ + 180°.
* Coordenadas do local: E (leste) e N (norte), origem no pé do flare.
* Coordenadas da LES/Chamberlain: x a jusante (para onde o vento sopra), y à esquerda de x.
  Com d = (−sen θ, −cos θ) o versor a jusante em (E, N):
      E = x·d_E − y·d_N,   N = x·d_N + y·d_E      (rotação ortonormal)
      x = E·d_E + N·d_N,   y = −E·d_N + N·d_E
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from urllib.request import Request, urlopen

import numpy as np
from scipy.ndimage import map_coordinates

from . import semiempirical as se

KAPPA = 0.41
SECTORS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
SPEED_EDGES = np.array([0.5, 2.0, 4.0, 6.0, 8.0, 10.0, 13.0, np.inf])   # m/s na altura do tip; < 0.5 = calmaria
API_LEVELS = (1.58, 4.73, 6.31, 9.46)


def sector_name(theta_deg: float) -> str:
    return SECTORS[int(((theta_deg % 360) + 11.25) // 22.5) % 16]


# ===================================================================== séries
@dataclass
class WindSeries:
    """Série horária de vento em duas alturas (velocidade em m/s, direção meteorológica em graus)."""
    source: str
    lat: float
    lon: float
    z1: float
    z2: float
    U1: np.ndarray
    U2: np.ndarray
    D1: np.ndarray
    D2: np.ndarray
    period: str = ""
    synthetic: bool = False

    def clean(self) -> "WindSeries":
        ok = (np.isfinite(self.U1) & np.isfinite(self.U2) & np.isfinite(self.D1) & np.isfinite(self.D2)
              & (self.U1 >= 0) & (self.U2 >= 0) & (self.U1 < 80) & (self.U2 < 80))
        return WindSeries(self.source, self.lat, self.lon, self.z1, self.z2, self.U1[ok], self.U2[ok],
                          self.D1[ok] % 360, self.D2[ok] % 360, self.period, self.synthetic)


def _get_text(url: str, timeout: float = 90.0, headers: dict | None = None) -> str:
    h = {"User-Agent": "flarekit/0.3 (pesquisa; Google Colab)"}
    h.update(headers or {})
    with urlopen(Request(url, headers=h), timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def _get_json(url: str, timeout: float = 90.0) -> dict:
    return json.loads(_get_text(url, timeout))


def direction_from_uv(u, v):
    """Direção meteorológica (de onde vem) a partir das componentes leste (u) e norte (v)."""
    return np.degrees(np.arctan2(-np.asarray(u), -np.asarray(v))) % 360


# ------------------------------------------------------------- Global Wind Atlas
def parse_gwa_lib(text: str) -> dict:
    """Clima de vento generalizado do Global Wind Atlas (formato WAsP .lib):
    cabeçalho; 'n_rugosidades n_alturas n_setores'; rugosidades z0 [m]; alturas [m]; e, para cada
    rugosidade, frequências por setor [%] seguidas, para cada altura, de A [m/s] e k por setor.
    O setor 0 é centrado no Norte."""
    lines = text.strip().splitlines()
    header = lines[0]
    nums = []
    for ln in lines[1:]:
        for tok in ln.replace(",", " ").split():
            try:
                nums.append(float(tok))
            except ValueError:
                pass
    nr, nh, ns = (int(round(x)) for x in nums[:3])
    i = 3
    z0s = np.array(nums[i:i + nr]); i += nr
    hs = np.array(nums[i:i + nh]); i += nh
    freq = np.zeros((nr, ns)); A = np.zeros((nr, nh, ns)); k = np.zeros((nr, nh, ns))
    for r in range(nr):
        freq[r] = nums[i:i + ns]; i += ns
        for h in range(nh):
            A[r, h] = nums[i:i + ns]; i += ns
            k[r, h] = nums[i:i + ns]; i += ns
    lat = lon = None
    if "<coordinates>" in header:
        try:
            c = header.split("<coordinates>")[1].split("</coordinates>")[0].split(",")
            lon, lat = float(c[0]), float(c[1])
        except (IndexError, ValueError):
            pass
    return {"header": header, "z0": z0s, "heights": hs, "freq": freq / 100.0, "A": A, "k": k,
            "n_sectors": ns, "lat": lat, "lon": lon}


def fetch_gwa(lat: float, lon: float) -> dict:
    """Ponto do Global Wind Atlas (endpoint não documentado usado por clientes abertos, ex. wind-stats)."""
    url = f"https://globalwindatlas.info/api/gwa/custom/Lib/?lat={lat:.4f}&long={lon:.4f}"
    return parse_gwa_lib(_get_text(url, headers={"Referer": "https://globalwindatlas.info"}))


def gwa_series(gwc: dict, lat: float, lon: float, z0_site: float = 0.3, n: int = 60000,
               z1: float = 10.0, z2: float = 50.0, seed: int = 7) -> WindSeries:
    """Amostra horas equivalentes do clima generalizado do GWA para a classe de rugosidade mais
    próxima de z0_site: setor pela frequência, direção uniforme no setor e velocidades nas duas
    alturas com o mesmo quantil da Weibull do setor (perfil coerente)."""
    rng = np.random.default_rng(seed)
    z0s = np.maximum(gwc["z0"], 1e-4)
    r = int(np.argmin(np.abs(np.log(z0s) - math.log(max(z0_site, 1e-4)))))
    f = gwc["freq"][r] / gwc["freq"][r].sum()
    ns = gwc["n_sectors"]
    width = 360.0 / ns
    hs = gwc["heights"]

    def weib_at(z, sec):
        lh = np.log(hs)
        A = np.array([np.interp(math.log(z), lh, gwc["A"][r, :, j]) for j in range(ns)])
        k = np.array([np.interp(math.log(z), lh, gwc["k"][r, :, j]) for j in range(ns)])
        return A[sec], k[sec]
    sec = rng.choice(ns, size=n, p=f)
    D = (sec * width + rng.uniform(-width / 2, width / 2, n)) % 360
    u = rng.uniform(1e-6, 1 - 1e-6, n)
    A1, k1 = weib_at(z1, sec); A2, k2 = weib_at(z2, sec)
    U1 = A1 * (-np.log(1 - u)) ** (1 / k1)
    U2 = A2 * (-np.log(1 - u)) ** (1 / k2)
    src = f"Global Wind Atlas (clima generalizado, z0 = {gwc['z0'][r]:g} m)"
    return WindSeries(src, lat, lon, z1, z2, U1, U2, D, D, f"{n} horas equivalentes", synthetic=False)


# ------------------------------------------------------------- NASA POWER
NASA_PARAMS = "WS10M,WD10M,WS50M,WD50M,U10M,V10M,U50M,V50M"


def parse_nasa_power(js: dict, lat: float, lon: float, period: str = "") -> WindSeries:
    """JSON horário da NASA POWER: properties.parameter.{PARAM} → {AAAAMMDDHH: valor}, fill_value −999.
    Se as componentes U/V vierem, a direção é recalculada delas (convenção meteorológica garantida)."""
    par = js["properties"]["parameter"]
    fill = js.get("header", {}).get("fill_value", -999.0)
    keys = sorted(par["WS10M"].keys())

    def arr(name):
        a = np.array([par[name].get(k, fill) for k in keys], dtype=float)
        a[(a == fill) | (a <= -998)] = np.nan
        return a
    D1, D2 = arr("WD10M"), arr("WD50M")
    if all(k in par for k in ("U10M", "V10M", "U50M", "V50M")):
        D1 = direction_from_uv(arr("U10M"), arr("V10M"))
        D2 = direction_from_uv(arr("U50M"), arr("V50M"))
    return WindSeries("NASA POWER (MERRA-2), horário", lat, lon, 10.0, 50.0, arr("WS10M"), arr("WS50M"),
                      D1, D2, period).clean()


def fetch_nasa_power(lat: float, lon: float, start: str = "20140101", end: str = "20231231") -> WindSeries:
    """Vento horário a 10 m e 50 m (NASA POWER, sem chave), um ano por pedido. start/end em AAAAMMDD."""
    y0, y1 = int(start[:4]), int(end[:4])
    parts = []
    for y in range(y0, y1 + 1):
        s = start if y == y0 else f"{y}0101"
        e = end if y == y1 else f"{y}1231"
        url = (f"https://power.larc.nasa.gov/api/temporal/hourly/point?parameters={NASA_PARAMS}"
               f"&community=RE&longitude={lon:.4f}&latitude={lat:.4f}&start={s}&end={e}"
               "&format=JSON&time-standard=UTC")
        parts.append(parse_nasa_power(_get_json(url, timeout=300.0), lat, lon))
    cat = lambda k: np.concatenate([getattr(p, k) for p in parts])  # noqa: E731
    return WindSeries("NASA POWER (MERRA-2), horário", lat, lon, 10.0, 50.0, cat("U1"), cat("U2"), cat("D1"),
                      cat("D2"), f"{start[:4]}–{end[:4]}").clean()


# ------------------------------------------------------------- Open-Meteo (ERA5)
def parse_open_meteo(js: dict, lat: float, lon: float, period: str = "") -> WindSeries:
    """JSON do arquivo histórico Open-Meteo: hourly.{wind_speed_10m, wind_speed_100m, wind_direction_10m,
    wind_direction_100m} (pedido com wind_speed_unit=ms); nulos viram NaN."""
    h = js["hourly"]
    g = lambda k: np.array([np.nan if v is None else v for v in h[k]], dtype=float)  # noqa: E731
    return WindSeries("Open-Meteo (ERA5), horário", lat, lon, 10.0, 100.0, g("wind_speed_10m"),
                      g("wind_speed_100m"), g("wind_direction_10m"), g("wind_direction_100m"), period).clean()


def fetch_open_meteo(lat: float, lon: float, start: str = "2014-01-01", end: str = "2023-12-31") -> WindSeries:
    """ERA5 horário a 10 m e 100 m. Uso não comercial gratuito; uso comercial exige chave."""
    url = ("https://archive-api.open-meteo.com/v1/archive?"
           f"latitude={lat:.4f}&longitude={lon:.4f}&start_date={start}&end_date={end}"
           "&hourly=wind_speed_10m,wind_speed_100m,wind_direction_10m,wind_direction_100m"
           "&wind_speed_unit=ms&timezone=GMT&models=era5")
    return parse_open_meteo(_get_json(url, timeout=300.0), lat, lon, f"{start[:4]}–{end[:4]}")


def synthetic_series(lat: float, lon: float, n: int = 8760, seed: int = 1) -> WindSeries:
    """Série SINTÉTICA de exemplo (só para rodar sem internet): rosa com predominância de SE, como a
    descrita para Campinas na literatura, Weibull k = 2, z0 = 0,3 m. Não é dado medido de nenhum local."""
    rng = np.random.default_rng(seed)
    freq = np.array([2, 2, 3, 6, 10, 14, 20, 11, 6, 4, 3, 3, 4, 4, 4, 4], float)
    freq /= freq.sum()
    sec = rng.choice(16, size=n, p=freq)
    D2 = (sec * 22.5 + rng.uniform(-11.25, 11.25, n)) % 360
    U2 = 5.0 * rng.weibull(2.0, n)
    z0 = 0.3
    U1 = U2 * math.log(10 / z0) / math.log(50 / z0)
    D1 = (D2 + rng.normal(0, 8, n)) % 360
    return WindSeries("rosa SINTÉTICA de exemplo (sem internet)", lat, lon, 10.0, 50.0, U1, U2, D1, D2,
                      "1 ano sintético", synthetic=True)


def get_wind_series(lat: float, lon: float, source: str = "auto", z0_site: float = 0.3,
                    start: str = "20140101", end: str = "20231231", verbose: bool = True,
                    H: float | None = None) -> WindSeries:
    """source: 'gwa' (Global Wind Atlas), 'nasa' (NASA POWER), 'open-meteo' (ERA5), 'sintetico' ou
    'auto' (GWA → NASA → Open-Meteo → sintético). H (altura do tip): no GWA a segunda altura amostrada
    passa a ser H (até 200 m), de modo que o vento no tip vem do próprio atlas, sem extrapolar."""
    order = {"auto": ["gwa", "nasa", "open-meteo", "sintetico"], "gwa": ["gwa"], "nasa": ["nasa"],
             "open-meteo": ["open-meteo"], "sintetico": ["sintetico"]}[source]
    errors = []
    for s in order:
        try:
            if s == "gwa":
                gwc = fetch_gwa(lat, lon)
                z2 = float(np.clip(H, 50.0, max(gwc["heights"]))) if H else 50.0
                return gwa_series(gwc, lat, lon, z0_site, z2=z2)
            if s == "nasa":
                return fetch_nasa_power(lat, lon, start, end)
            if s == "open-meteo":
                return fetch_open_meteo(lat, lon, f"{start[:4]}-{start[4:6]}-{start[6:]}",
                                        f"{end[:4]}-{end[4:6]}-{end[6:]}")
            return synthetic_series(lat, lon)
        except Exception as e:  # noqa: BLE001 — tenta a próxima fonte
            errors.append(f"{s}: {type(e).__name__}: {str(e)[:120]}")
            if verbose:
                print(f"[vento] {s} indisponível ({type(e).__name__}); tentando a próxima fonte")
    raise RuntimeError("Nenhuma fonte de vento disponível: " + " | ".join(errors))


# ===================================================================== perfil
def fit_log_profile(U1, U2, z1: float, z2: float, umin: float = 1.0) -> dict:
    """Ajusta U(z) = (u*/κ) ln(z/z0) às médias nas duas alturas (horas com U > umin em ambas).
    Também devolve o expoente da lei de potência α = ln(U2/U1)/ln(z2/z1)."""
    m = (U1 > umin) & (U2 > umin)
    a, b = float(np.mean(U1[m])), float(np.mean(U2[m]))
    alpha = math.log(b / a) / math.log(z2 / z1)
    if b > a:
        z0 = math.exp((b * math.log(z1) - a * math.log(z2)) / (b - a))
    else:
        z0 = 1e-4
    z0_clamped = float(np.clip(z0, 2e-4, 1.0))
    return {"z0": z0_clamped, "z0_raw": z0, "alpha": alpha, "U1_mean": a, "U2_mean": b,
            "u_star_mean": KAPPA * b / math.log(z2 / z0_clamped)}


def speed_at_height(U1, U2, z1, z2, z, z0):
    """Velocidade horária na altura z pela lei log, ancorada no nível de dados mais próximo."""
    if abs(math.log(z / z1)) <= abs(math.log(z / z2)):
        return U1 * math.log(z / z0) / math.log(z1 / z0)
    return U2 * math.log(z / z0) / math.log(z2 / z0)


def direction_at_height(D1, D2, z1, z2, z):
    """Interpolação circular da direção em ln z entre as duas alturas."""
    w = float(np.clip(math.log(z / z1) / math.log(z2 / z1), 0.0, 1.0))
    a1, a2 = np.radians(D1), np.radians(D2)
    s = (1 - w) * np.sin(a1) + w * np.sin(a2)
    c = (1 - w) * np.cos(a1) + w * np.cos(a2)
    return np.degrees(np.arctan2(s, c)) % 360


def weibull_fit(U):
    """Weibull por máxima verossimilhança (scipy), com localização fixa em 0."""
    from scipy.stats import weibull_min
    U = U[U > 0.1]
    k, _, c = weibull_min.fit(U, floc=0)
    return float(k), float(c)


@dataclass
class WindClimate:
    series: WindSeries
    H: float
    z0: float
    alpha: float
    U_H: np.ndarray
    D_H: np.ndarray
    freq: np.ndarray            # (16, nbins) frequências conjuntas (somam 1 − calmaria)
    calm: float
    bin_speed: np.ndarray       # velocidade representativa de cada classe [m/s]
    weibull_k: float
    weibull_c: float
    profile_fit: dict = field(default_factory=dict)

    @classmethod
    def from_series(cls, s: WindSeries, H: float, edges=SPEED_EDGES) -> "WindClimate":
        fit = fit_log_profile(s.U1, s.U2, s.z1, s.z2)
        z0 = fit["z0"]
        UH = speed_at_height(s.U1, s.U2, s.z1, s.z2, H, z0)
        DH = direction_at_height(s.D1, s.D2, s.z1, s.z2, H)
        n = len(UH)
        calm = float(np.mean(UH < edges[0]))
        sec = (((DH % 360) + 11.25) // 22.5).astype(int) % 16
        nb = len(edges) - 1
        freq = np.zeros((16, nb))
        bspeed = np.zeros(nb)
        for b in range(nb):
            m = (UH >= edges[b]) & (UH < edges[b + 1])
            bspeed[b] = float(np.mean(UH[m])) if m.any() else (edges[b] + min(edges[b + 1], edges[b] + 3)) / 2
            for k in range(16):
                freq[k, b] = np.count_nonzero(m & (sec == k)) / n
        k, c = weibull_fit(UH)
        return cls(s, H, z0, fit["alpha"], UH, DH, freq, calm, bspeed, k, c, fit)

    # ------------------------------------------------------------ resumos
    @property
    def sector_freq(self):
        return self.freq.sum(1)

    @property
    def dominant_sector(self) -> int:
        return int(np.argmax(self.sector_freq))

    def sector_speeds(self, k: int):
        sec = (((self.D_H % 360) + 11.25) // 22.5).astype(int) % 16
        return self.U_H[(sec == k) & (self.U_H >= SPEED_EDGES[0])]

    def design_wind(self, mode: str = "dominante_p90", design_speed: float = 8.9):
        """Vento para a LES: (velocidade na altura do tip, direção de onde vem)."""
        k = self.dominant_sector
        theta = 22.5 * k
        u = self.sector_speeds(k)
        if mode == "dominante_media":
            return float(np.mean(u)), theta
        if mode == "dominante_p90":
            return float(np.percentile(u, 90)), theta
        if mode == "projeto":
            return design_speed, theta
        raise ValueError(mode)

    def profile(self, z, U_H: float | None = None):
        """Perfil log com o z0 ajustado, escalado para U_H na altura do tip."""
        U_H = float(np.mean(self.U_H)) if U_H is None else U_H
        return U_H * np.log(np.asarray(z) / self.z0) / math.log(self.H / self.z0)

    def describe(self) -> str:
        s = self.series
        k = self.dominant_sector
        return (f"{s.source} · {s.period} · lat {s.lat:.3f}, lon {s.lon:.3f}\n"
                f"perfil log: z0 = {self.z0:.3f} m (α = {self.alpha:.3f}); médias {s.U1.mean():.2f} m/s a "
                f"{s.z1:.0f} m e {s.U2.mean():.2f} m/s a {s.z2:.0f} m\n"
                f"a {self.H:.0f} m: média {self.U_H.mean():.2f} m/s, P90 {np.percentile(self.U_H, 90):.2f} m/s, "
                f"Weibull k = {self.weibull_k:.2f}, c = {self.weibull_c:.2f} m/s, calmaria {100 * self.calm:.1f}%\n"
                f"setor predominante: {SECTORS[k]} ({100 * self.sector_freq[k]:.1f}% do tempo)")


# ===================================================================== pegadas
@dataclass
class SiteGrid:
    E: np.ndarray
    N: np.ndarray

    @classmethod
    def square(cls, R: float = 120.0, n: int = 121) -> "SiteGrid":
        x = np.linspace(-R, R, n)
        return cls(x, x)


def downwind_footprint(sc: se.Scenario, U: float, R: float, n: int, z_rec: float = 1.5):
    """q [kW/m²] de Chamberlain no referencial a jusante (x, y) numa grade quadrada de meia-largura R."""
    ch = se.chamberlain(sc.fuel, sc.mdot, sc.tip["u_j"], sc.tip["rho_j"], sc.rho_inf, U,
                        fs_factor=getattr(sc, "fs_factor", 1.0))
    x = np.linspace(-R, R, n)
    X, Y = np.meshgrid(x, x, indexing="ij")
    rec = np.stack([X.ravel(), Y.ravel(), np.full(X.size, z_rec)], 1)
    q = se.q_chamberlain(rec, ch, sc.tip_xyz, sc.T_inf, sc.RH).reshape(X.shape) / 1e3
    return x, q, ch


def rotate_to_site(xd: np.ndarray, yd: np.ndarray, q_down: np.ndarray, grid: SiteGrid, theta_from: float,
                   fill: float = 0.0) -> np.ndarray:
    """Amostra uma pegada do referencial a jusante (grade regular xd × yd) nos pontos (E, N) do local
    para vento vindo de theta_from."""
    th = math.radians(theta_from)
    dE, dN = -math.sin(th), -math.cos(th)
    EE, NN = np.meshgrid(grid.E, grid.N, indexing="ij")
    x = EE * dE + NN * dN
    y = -EE * dN + NN * dE
    ix = np.interp(x, xd, np.arange(len(xd)), left=-1, right=len(xd))
    iy = np.interp(y, yd, np.arange(len(yd)), left=-1, right=len(yd))
    out = map_coordinates(q_down, [ix, iy], order=1, mode="constant", cval=fill)
    return out


def exceedance_maps(sc: se.Scenario, cl: WindClimate, grid: SiteGrid, levels=API_LEVELS, sub: int = 3,
                    q_solar: float = 0.0):
    """Probabilidade (dado que o flare queima) de cada ponto exceder cada nível, ponderada pela rosa
    dos ventos, e envoltória (máximo sobre as condições com frequência > 0).

    Cada setor é dividido em `sub` subdireções (evita mapas em raios). Calmaria → chama vertical.
    P usa a velocidade média de cada classe; a envoltória inclui também a maior velocidade observada
    (o fluxo máximo cresce com o vento, e a média da classe mais alta subestimaria o pior caso).
    q_solar [kW/m²] é somado ao fluxo do flare quando o critério é de radiação total (0 = só o flare)."""
    R = max(abs(grid.E).max(), abs(grid.N).max()) * 1.45
    nd = 2 * int(R / 3.0) + 1
    P = {L: np.zeros((len(grid.E), len(grid.N))) for L in levels}
    Psec = {L: np.zeros((16, len(grid.E), len(grid.N))) for L in levels}
    env = np.zeros((len(grid.E), len(grid.N)))
    q_mean = np.zeros((len(grid.E), len(grid.N)))   # fluxo esperado (média ponderada pela rosa)
    foot = {}

    def subdirs(k):
        return [22.5 * k + (j - (sub - 1) / 2) * 22.5 / sub for j in range(sub)]

    for b, U in enumerate(cl.bin_speed):
        if cl.freq[:, b].sum() <= 0:
            continue
        xd, qd, _ = downwind_footprint(sc, U, R, nd)
        qd = qd + q_solar
        foot[b] = (xd, qd)
        for k in range(16):
            f = cl.freq[k, b]
            if f <= 0:
                continue
            for th in subdirs(k):
                q = rotate_to_site(xd, xd, qd, grid, th)
                for L in levels:
                    hit = (f / sub) * (q >= L)
                    P[L] += hit
                    Psec[L][k] += hit
                env = np.maximum(env, q)
                q_mean += (f / sub) * q
    # pior caso: maior velocidade observada, nas direções em que a classe mais alta ocorre
    top = [b for b in range(cl.freq.shape[1]) if cl.freq[:, b].sum() > 0]
    U_max = float(np.max(cl.U_H)) if len(cl.U_H) else 0.0
    if top and U_max > cl.bin_speed[top[-1]] + 0.1:
        xd, qd, _ = downwind_footprint(sc, U_max, R, nd)
        qd = qd + q_solar
        foot["U_max"] = (xd, qd)
        for k in range(16):
            if cl.freq[k, top[-1]] > 0:
                for th in subdirs(k):
                    env = np.maximum(env, rotate_to_site(xd, xd, qd, grid, th))
    if cl.calm > 0:
        xd, qd, _ = downwind_footprint(sc, 0.0, R, nd)
        qd = qd + q_solar
        q = rotate_to_site(xd, xd, qd, grid, 0.0)
        for L in levels:
            P[L] += cl.calm * (q >= L)
        env = np.maximum(env, q)
        q_mean += cl.calm * q
        foot["calm"] = (xd, qd)
    return {"P": P, "P_sector": Psec, "envelope": env, "q_mean": q_mean, "footprints": foot, "grid": grid,
            "q_solar": q_solar, "U_max": U_max}


def receiver_box(sc: se.Scenario, U: float, level: float = 1.58, margin: float = 15.0) -> tuple:
    """(x0, x1, y_meia) que cobre a zona q ≥ level no referencial a jusante, com folga: união da zona
    de Chamberlain com a da fonte pontual do API 521 (mais conservadora a barlavento, onde a chama curta
    da LES irradia mais que o frustum). Use em LESConfig(receiver_box=...) para não cortar a zona."""
    r_pt = math.sqrt(sc.cham.F_s * sc.Q / (4 * math.pi * level * 1e3))   # alcance da fonte pontual (τ = 1)
    R = max(60.0, 3.5 * sc.H + sc.cham.L_b, sc.cham.L_b + 1.2 * r_pt)
    for _ in range(4):
        x, q, ch = downwind_footprint(sc, U, R, 2 * int(R / 3.0) + 1)
        X, Y = np.meshgrid(x, x, indexing="ij")
        c = se.flame_center_chamberlain(ch, sc.tip_xyz)
        rec = np.stack([X.ravel(), Y.ravel(), np.full(X.size, 1.5)], 1)
        qp = se.q_point_source(rec, c, ch.F_s, sc.Q, sc.T_inf, sc.RH).reshape(X.shape) / 1e3
        m = (q >= level) | (qp >= level)
        if not (m[0].any() or m[-1].any() or m[:, 0].any() or m[:, -1].any()):
            break
        R *= 1.5                                     # a zona encostou na borda: amplia e refaz
    if not m.any():
        return (-margin, margin, margin)
    return (float(X[m].min() - margin), float(X[m].max() + margin), float(np.abs(Y[m]).max() + margin))


def les_footprint_downwind(rec_x, rec_y, q_les, sc: se.Scenario, U: float, R: float, n: int,
                           blend: float = 10.0):
    """Pegada média da LES num quadrado regular a jusante; fora do domínio de receptores da LES usa
    Chamberlain para a mesma velocidade (a LES cobre a região de maior fluxo). Uma faixa de `blend` metros
    junto à borda dos receptores mistura linearmente as duas, para não criar degrau nas isolinhas."""
    xd, qd, _ = downwind_footprint(sc, U, R, n)
    X, Y = np.meshgrid(xd, xd, indexing="ij")
    d = np.minimum.reduce([X - rec_x[0], rec_x[-1] - X, Y - rec_y[0], rec_y[-1] - Y])
    b = max(1e-6, min(blend, 0.25 * min(rec_x[-1] - rec_x[0], rec_y[-1] - rec_y[0])))
    w = np.clip(d / b, 0.0, 1.0)
    ix = np.interp(X, rec_x, np.arange(len(rec_x)))
    iy = np.interp(Y, rec_y, np.arange(len(rec_y)))
    ql = map_coordinates(np.asarray(q_les, float), [ix, iy], order=1, mode="nearest")
    return xd, w * ql + (1.0 - w) * qd
