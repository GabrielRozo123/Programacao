# Padrões de Macro Java — Simcenter STAR-CCM+ 2602

Referência extraída dos tutoriais:
- *Understanding the Initial Macro* (Simple Java Macros)
- *Class-by-Class Breakdown* (Intermediate Java Macros: Run Multiple Simulations)
- *Understanding the SimData Nested Class*
- *Understanding the DataReader Nested Class*
- *Understanding the DataWriter Nested Class*
- *Understanding the SimRunner Nested Class*
- *Understanding the PostProcessor Nested Class*
- *Understanding the Main Method in the Macro*
- *Testing and Debugging*
- *Running the Simulation to Convergence*

---

## 1. Anatomia de um macro gravado (Initial Macro)

```java
// Classe no pacote "macro", subclasse de StarMacro
public class macroRecording extends StarMacro {
    public void execute() { execute0(); }  // CCM+ chama execute()
    private void execute0() {
        // Retrieve the current simulation
        Simulation simulation_0 = getActiveSimulation();
        ...
    }
}
```

### Navegar pelo Object Tree

Cada entidade no CCM+ é um objeto. Para interagir, siga a hierarquia do Object Tree:

```java
// Física (continuum)
PhysicsContinuum pc = (PhysicsContinuum)
    simulation_0.getContinuumManager().getContinuum("Physics 1");

// Condição inicial de velocidade
VelocityProfile vp = pc.getInitialConditions().get(VelocityProfile.class);
vp.getMethod(ConstantVectorProfileMethod.class)
  .getQuantity().setComponents(-10.0, 10.0, 0.0);

// Região → Boundary → Condição de contorno
Region region = simulation_0.getRegionManager().getRegion("trainAndTrack");
Boundary boundary = region.getBoundaryManager().getBoundary("Inflow");
VelocityProfile vpBC = boundary.getValues().get(VelocityProfile.class);
vpBC.getMethod(ConstantVectorProfileMethod.class)
    .getQuantity().setComponents(-5.0, 5.0, 0.0);
```

### API calls essenciais

| Ação | Código |
|---|---|
| Obter simulação ativa | `Simulation sim = getActiveSimulation();` |
| Limpar solução (completo) | `sim.getSolution().clearSolution(Solution.Clear.History, Solution.Clear.Fields, Solution.Clear.LagrangianDem);` |
| Rodar simulação | `sim.getSimulationIterator().runAutomation();` |
| Extrair valor de Report | `double val = report.getReportMonitorValue();` |
| Imprimir Report no log | `report.printReport();` |
| Hardcopy de Scene | `scene.printAndWait(path, 1, 1024, 768);` |
| Hardcopy de Plot (PNG) | `plot.encode(path, "png", 1024, 768);` |
| Exportar STAR-View+ (.sce) | `scene.export3DSceneFileAndWait(path, true);` |
| **Fechar cena** (ver nota!) | `scene.close(true);` |
| Salvar simulação | `sim.saveState(resolvePath("/caminho/arquivo.sim"));` |
| Caminho relativo → absoluto | `resolvePath("subdir/arquivo.png")` |

> **CRÍTICO**: sempre feche a cena com `scene.close(true)` após exportar,
> **antes** de iniciar a próxima simulação. Se não fizer isso, o tempo de
> execução aumenta dramaticamente (a cena fica renderizando em segundo plano).

---

## 2. Padrão de 5 Classes Aninhadas (Multi-Simulação)

Tutorial: *Intermediate Java Macros — Run Multiple Simulations*  
Arquivo de referência: `trainFlowAngles.java`

Este padrão é o correto para varreduras paramétricas com N casos.

```
VarreduraParametrica (extends StarMacro)
├── CasoData          — DTO: guarda parâmetros de entrada + resultado
├── DataReader        — lê CSV de entrada, cria lista de CasoData
├── DataWriter        — escreve CSV de saída (append por caso)
├── SimRunner         — executa um caso no CCM+ (set params → run → extract)
└── PostProcessor     — exporta cenas/plots como hardcopy
```

### Fluxo no método execute()

```java
public void execute() {
    Simulation sim = getActiveSimulation();

    DataReader  reader    = new DataReader();
    reader.readInput(PATH_CSV_ENTRADA);            // lê todos os casos

    DataWriter  writer    = new DataWriter(PATH_CSV_SAIDA); // cria header

    for (CasoData caso : reader.getCasos()) {
        SimRunner   runner = new SimRunner(sim, caso);
        runner.run();                              // set → clear → run → extract

        PostProcessor pp   = new PostProcessor(sim);
        pp.salvarCenas(DIR_RESULTADOS, caso.getNome()); // hardcopy + fechar!

        writer.writeDataLine(caso);                // append ao CSV
    }
}
```

---

## 3. Classe CasoData (DTO)

```java
public class CasoData {
    // Parâmetros de entrada
    private double m_angulo;
    private int    m_nElementos;

    // Resultado (preenchido pelo SimRunner)
    private double m_dP    = -1.0;
    private double m_cov   = -1.0;

    // Construtor (chamado pelo DataReader)
    public CasoData(double angulo, int n) {
        m_angulo     = angulo;
        m_nElementos = n;
    }

    // Getters
    public double getAngulo()     { return m_angulo; }
    public int    getNElementos() { return m_nElementos; }
    public double getDP()         { return m_dP; }
    public double getCoV()        { return m_cov; }
    public String getNome() {
        return String.format("ang%03.0f_n%02d", m_angulo, m_nElementos);
    }

    // Setters (usados pelo SimRunner após rodar)
    public void setDP(double dP)   { m_dP  = dP; }
    public void setCoV(double cov) { m_cov = cov; }
}
```

---

## 4. Classe DataReader

Lê arquivo CSV de entrada e cria um objeto `CasoData` por linha.  
Usa `Scanner` (Java) — não é API do CCM+.

```java
public class DataReader {
    private List<CasoData> m_casos = new ArrayList<CasoData>();

    public void readInput(String fileToRead) {
        try {
            FileReader     fr = new FileReader(fileToRead);
            BufferedReader br = new BufferedReader(fr);
            Scanner        sc = new Scanner(br);

            while (sc.hasNextLine()) {
                sc.nextLine();                        // avança a linha
                if (sc.hasNextDouble()) {             // só lê se tem número
                    double angulo     = sc.nextDouble();
                    double nElementos = sc.nextDouble();
                    CasoData cd = new CasoData(angulo, (int) nElementos);
                    m_casos.add(cd);
                }
            }
        } catch (Exception e) {
            // JOptionPane apenas para depuração interativa
            JOptionPane.showMessageDialog(null, e.toString());
        }
    }

    public List<CasoData> getCasos() { return m_casos; }
}
```

**Formato do CSV de entrada** (`casos_varredura.csv`):
```
Angulo,N_Elementos
30,2
30,3
45,2
...
```

---

## 5. Classe DataWriter

Cria arquivo de saída no construtor (header), depois adiciona uma linha por caso.  
Abre em modo **append** (`true`) em cada chamada — nunca sobrescreve.

```java
public class DataWriter {
    private String m_outputFile;

    public DataWriter(String fileToWrite) {
        m_outputFile = fileToWrite;
        try {
            FileWriter     fw = new FileWriter(m_outputFile);   // cria/sobrescreve
            BufferedWriter bw = new BufferedWriter(fw);
            bw.write("Caso,Angulo_graus,N_Elementos,dP_Pa,CoV,Status");
            bw.newLine();
            bw.close();
        } catch (Exception e) { }
    }

    public void writeDataLine(CasoData d) {
        try {
            FileWriter     fw = new FileWriter(m_outputFile, true);  // APPEND
            BufferedWriter bw = new BufferedWriter(fw);
            bw.write(d.getNome() + "," + d.getAngulo() + ","
                   + d.getNElementos() + "," + d.getDP() + ","
                   + d.getCoV());
            bw.newLine();
            bw.close();
        } catch (Exception e) { }
    }
}
```

---

## 6. Classe SimRunner

Conecta o DTO ao CCM+: lê parâmetros do `CasoData`, configura a simulação,
roda, extrai resultado e armazena de volta no objeto.

```java
public class SimRunner {
    private Simulation m_sim;
    private CasoData   m_caso;

    public SimRunner(Simulation sim, CasoData caso) {
        m_sim  = sim;
        m_caso = caso;
    }

    public void run() {
        // 1. Atualizar Design Parameters
        // (ver PARAMETRIZACAO_3DCAD_STARCCM.md)
        setDesignParameter("Angulo_Aleta",    m_caso.getAngulo());
        setDesignParameter("N_Elementos",     m_caso.getNElementos());

        // 2. Limpar solução (forma completa do tutorial)
        m_sim.getSolution().clearSolution(
            Solution.Clear.History,
            Solution.Clear.Fields,
            Solution.Clear.LagrangianDem
        );

        // 3. Rodar
        m_sim.getSimulationIterator().runAutomation();

        // 4. Extrair resultados e armazenar no DTO
        m_caso.setDP(extrairDeltaP());
        m_caso.setCoV(extrairCoV());
    }

    private void setDesignParameter(String nome, double val) {
        try {
            CadModel cad = (CadModel) m_sim.get(SolidModelManager.class)
                    .getObject("3D-CAD Model 1");
            cad.getDesignParameterManager()
               .getParameter(nome).getQuantity().setValue(val);
            cad.update();
        } catch (Exception e) {
            m_sim.println("[AVISO] Param '" + nome + "': " + e.getMessage());
        }
    }

    private double extrairDeltaP() {
        try {
            Report rep = m_sim.getReportManager().getReport("dP_Misturador");
            return rep.getReportMonitorValue();
        } catch (Exception e) { return -1.0; }
    }

    private double extrairCoV() {
        try {
            Report rep = m_sim.getReportManager().getReport("CoV_Outlet");
            return rep.getReportMonitorValue();
        } catch (Exception e) { return -1.0; }
    }
}
```

---

## 7. Classe PostProcessor

Encontra cenas/plots no construtor, exporta por método.  
**Sempre fechar cenas após exportar** (antes da próxima simulação).

```java
public class PostProcessor {
    private Simulation m_sim;
    private Scene      m_pressao    = null;
    private Scene      m_velocidade = null;
    private Scene      m_polimero   = null;
    private ResidualPlot m_residuos = null;

    public PostProcessor(Simulation sim) {
        m_sim = sim;
        try { m_pressao    = (Scene) sim.getSceneManager().getScene("Pressao_Estatica"); } catch (Exception e) {}
        try { m_velocidade = (Scene) sim.getSceneManager().getScene("Velocidade");       } catch (Exception e) {}
        try { m_polimero   = (Scene) sim.getSceneManager().getScene("Polimero");          } catch (Exception e) {}
        try { m_residuos   = (ResidualPlot) sim.getPlotManager().getObject("Residuals"); } catch (Exception e) {}
    }

    public void salvarCenas(String dir, String nomeCaso) {
        salvarScene(m_pressao,    dir + "/pressao_"    + nomeCaso + ".png");
        salvarScene(m_velocidade, dir + "/velocidade_" + nomeCaso + ".png");
        salvarScene(m_polimero,   dir + "/polimero_"   + nomeCaso + ".png");
        salvarPlot(m_residuos,    dir + "/residuos_"   + nomeCaso + ".png");
    }

    private void salvarScene(Scene scene, String path) {
        if (scene == null) return;
        try {
            scene.printAndWait(path, 1, 1920, 1080);
            scene.close(true);   // CRÍTICO: fechar antes da próxima simulação
        } catch (Exception e) {}
    }

    private void salvarPlot(ResidualPlot plot, String path) {
        if (plot == null) return;
        try {
            plot.encode(path, "png", 1920, 1080);
        } catch (Exception e) {}
    }

    // Para exportar STAR-View+ (.sce) ao invés de PNG:
    // scene.export3DSceneFileAndWait(path, true);
    // scene.close(true);
}
```

---

## 8. Diferenças: Simple vs. Intermediate Macros

| Aspecto | Simple (batch 2) | Intermediate (este batch) |
|---|---|---|
| Estrutura | Uma classe, métodos private | 5 classes aninhadas |
| Entrada | Constantes no código | CSV lido pelo DataReader |
| Saída CSV | `PrintWriter` + `flush()` | `DataWriter` com append |
| Escenas | Métodos ad-hoc | `PostProcessor` dedicado |
| Reuso | Difícil | Fácil — cada classe tem responsabilidade única |

O padrão de 5 classes é o **correto para produção** — cada classe tem uma
única responsabilidade (princípio SRP). Para protótipos rápidos, o padrão
simples (como está no `06_VarreduraParametrica.java` atual) é aceitável.

---

## 9. Gotchas e Armadilhas

1. **Não fechar cenas** → tempo de simulação explode (cena renderiza em background)
2. **`clearSolution()` sem args** → pode não limpar campos (usar forma completa com enum)
3. **`FileWriter(path, true)`** → append; sem `true` → sobrescreve tudo a cada caso
4. **`resolvePath()`** → converte caminho relativo ao diretório do .sim em absoluto
5. **`getReportMonitorValue()`** → retorna `double` diretamente; `printReport()` só loga
6. **Scanner reconhece espaço/tab/CR como separadores** → CSV com vírgulas precisa de `sc.useDelimiter(",")`
7. **`SimRunner` e `PostProcessor` fora do loop** → instanciar UMA vez antes do loop (ver seção 10)
8. **`run(N)` vs `runAutomation()`** → `run(N)` roda exatamente N iterações; `runAutomation()` roda até a condição de parada do CCM+

---

## 10. Correções ao Template (batch 3 de tutoriais)

### SimRunner e PostProcessor: instanciar FORA do loop

O tutorial *Understanding the SimRunner Nested Class* e *Understanding the Main Method*
mostram claramente: **`SimRunner` e `PostProcessor` são criados UMA VEZ**, antes do loop.
O motivo é que seus **construtores localizam objetos no CCM+** (regiões, boundaries, cenas,
reports) — e esses objetos não mudam de posição entre os casos. Criar dentro do loop seria
ineficiente e potencialmente problemático.

```java
// ERRADO — instanciar dentro do loop:
for (CasoData caso : casos) {
    SimRunner   runner = new SimRunner(sim, caso);  // localiza objetos N vezes
    PostProcessor pp   = new PostProcessor(sim);    // localiza cenas N vezes
    runner.run();
}

// CORRETO — instanciar fora do loop (padrão do tutorial):
Simulation    theSim = getActiveSimulation();
DataReader    reader = new DataReader();
reader.readInput(inputFile);
List<CasoData> listCases = reader.getCasos();

SimRunner     runner = new SimRunner(theSim);         // uma vez
PostProcessor postP  = new PostProcessor(theSim);     // uma vez

for (CasoData sD : listCases) {
    runner.runCase(sD, N_ITERACOES);
    writer.writeDataLine(sD);
    postP.salvarCenas(DIR_BASE, sD.getNome());
    theSim.saveState(DIR_BASE + "/caso_" + sD.getNome() + ".sim");
}
```

### run(N) — controle de iterações por caso

```java
// runAutomation() → roda até a condição de parada configurada no CCM+
m_sim.getSimulationIterator().runAutomation();

// run(N) → roda exatamente N iterações (útil durante desenvolvimento)
m_sim.getSimulationIterator().run(iterations);
// onde 'iterations' é passado como argumento para runCase(SimData sD, int iterations)
```

Usar `run(5)` durante o desenvolvimento (rápido), depois aumentar para o valor final.

### execute() com try-catch externo

O tutorial mostra que o `execute()` inteiro fica dentro de um `try-catch` com `JOptionPane`:

```java
public void execute() {
    try {
        // Seção 1: uma vez (getActiveSimulation, DataReader, SimRunner, PostProcessor)
        Simulation theSim = getActiveSimulation();
        DataReader reader  = new DataReader();
        reader.readInput(folder + "/trainInput.txt");
        List<SimData> listCases = reader.getFlowDetails();
        PostProcessor postP     = new PostProcessor(theSim);
        SimRunner     runner    = new SimRunner(theSim);

        // Seção 2: loop por caso
        for (SimData sD : listCases) {
            runner.runCase(sD, 5);
            writer.writeDataLine(sD);
            postP.saveVelMagScene(folder + "/velMag" + sD.getAngle() + ".png");
            theSim.saveState(folder + "/train" + sD.getAngle() + ".sim");
        }

    } catch (Exception e) {
        jOptionPane.showMessageDialog(null, e.toString());  // pausa e mostra erro
    }
}
```

### SimData: variáveis private + getters/setters

```java
public class SimData {
    private double m_angDeg  = 0.0;  // sempre private
    private double m_velX    = 0.0;
    private double m_dragC   = 0.0;

    // Construtor pode calcular valores derivados
    public SimData(double angDeg, double velWnd) {
        m_angDeg = angDeg;
        double angRad = Math.toRadians(angDeg);
        m_velX = -1 * velWnd * Math.sin(angRad);  // componente X calculada aqui
    }

    public double getAngle() { return m_angDeg; }    // getter: público
    public void setDrag(double d) { m_dragC = d; }   // setter: só para valores modificáveis
}
```

### Debugging com sim.println()

```java
// Imprimir no Output window do CCM+ — use em cada passo chave
sim.println("Setting " + myStr + ": " + myInt + " " + myDbl);
// resultado no Output: "Setting initial conditions: 910 19.84"

// No catch: JOptionPane pausa o macro e mostra o erro
} catch (Exception e) {
    JOptionPane.showMessageDialog(null, e.toString());
}
// Depois de clicar OK, o macro tenta continuar; se não conseguir, para.
```

**Estratégia de debug**: coloque `sim.println("Passo X concluído")` antes de cada bloco
crítico. Se o macro parar, o último println diz exatamente onde está o problema.

---

## 11. Workflow Final: Desenvolvimento → Produção

Tutorial: *Running the Simulation to Convergence*

O único passo para passar de desenvolvimento para produção é mudar o número
de iterações em `runner.runCase(sD, N)`:

```
DEV:     runner.runCase(sD,   5);   // testa em segundos; verifica que não quebra
PROD:    runner.runCase(sD, 400);   // ou 500, 2000 — dependendo do caso
```

O tutorial do trem usa **400 iterações** para escoamento externo k-ω SST. O residual
plot mostra convergência atingida por volta de 200-250 iterações (resíduos abaixo de
1e-4 para continuidade, momentum X, Y, Z, TKE, TDR).

**Para o misturador estático** (escoamento interno, regime turbulento, Re > 300.000):
- Usar **500 iterações** como ponto de partida (valor conservador)
- Critério de convergência: resíduos < 1e-5 (já configurado em `03_ConfigurarFisica.java`)
- Se não convergir em 500: aumentar para 1000 ou checar CFL / relaxation factors

**Durante a varredura** (25 casos): o CCM+ exibe na barra de status
`"Iterating: Running 500"` — para interromper, clicar no botão **Abort** (●)
ao lado da barra de status.
