// Template: Macro Multi-Simulação com 5 Classes Aninhadas
// Referência: "Intermediate Java Macros: Run Multiple Simulations" (CCM+ 2602)
//
// Estrutura:
//   CasoData      — DTO: parâmetros de entrada + resultado por caso
//   DataReader    — lê CSV de entrada, popula List<CasoData>
//   DataWriter    — escreve CSV de saída (header no construtor, append por caso)
//   SimRunner     — executa um caso no CCM+ (set → clear → run → extract)
//   PostProcessor — hardcopy de cenas e plots; fecha cenas antes da próxima sim
//
// Para adaptar a um projeto:
//   1. Renomear a classe principal
//   2. Ajustar campos de CasoData para os parâmetros do projeto
//   3. Implementar setDesignParameter() e extrairResultados() em SimRunner
//   4. Ajustar nomes de cenas em PostProcessor
//   5. Definir PATH_CSV_ENTRADA, PATH_CSV_SAIDA, DIR_RESULTADOS

import star.cadmodeler.*;
import star.common.*;
import star.base.neo.*;
import star.meshing.*;
import star.flow.*;
import star.report.*;
import star.vis.*;

import java.io.*;
import java.util.*;
import javax.swing.JOptionPane;

public class TemplateMultiSimulacao extends StarMacro {

    // =========================================================
    // CAMINHOS — ajustar por projeto
    // =========================================================
    static final String DIR_BASE       = System.getProperty("user.home")
            + "/Programacao/projeto1_misturador_estatico/resultados/varredura";
    static final String PATH_CSV_ENTRADA = DIR_BASE + "/casos_varredura.csv";
    static final String PATH_CSV_SAIDA   = DIR_BASE + "/resultados.csv";
    // =========================================================

    @Override
    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("=== VARREDURA PARAMÉTRICA (padrão 5-classes) ===");

        new File(DIR_BASE).mkdirs();

        // 1. Ler casos do CSV de entrada
        DataReader reader = new DataReader();
        reader.readInput(PATH_CSV_ENTRADA);
        List<CasoData> casos = reader.getCasos();
        sim.println("Casos encontrados: " + casos.size());

        // 2. Criar arquivo de saída (header)
        DataWriter writer = new DataWriter(PATH_CSV_SAIDA);

        // 3. Iterar
        int total = casos.size();
        int idx   = 0;
        for (CasoData caso : casos) {
            idx++;
            sim.println(String.format("\n=== CASO %d/%d: %s ===", idx, total, caso.getNome()));

            try {
                // 3a. Executar simulação
                SimRunner runner = new SimRunner(sim, caso);
                runner.run();

                // 3b. Exportar cenas (fecha automaticamente)
                PostProcessor pp = new PostProcessor(sim);
                pp.salvarCenas(DIR_BASE, caso.getNome());

                // 3c. Salvar .sim por caso (opcional)
                // sim.saveState(DIR_BASE + "/" + caso.getNome() + ".sim");

            } catch (Exception e) {
                caso.setStatus("ERRO: " + e.getMessage());
                sim.println("[ERRO] " + e.getMessage());
            }

            // 3d. Registrar no CSV (mesmo em caso de erro)
            writer.writeDataLine(caso);
            sim.println("  → DP=" + caso.getDP() + " Pa | CoV=" + caso.getCoV());
        }

        sim.println("\n=== VARREDURA CONCLUÍDA → " + PATH_CSV_SAIDA + " ===");
    }

    // =========================================================
    // CLASSE 1: CasoData — DTO (Data Transfer Object)
    // =========================================================

    public class CasoData {
        // --- Parâmetros de entrada ---
        private double m_angulo;
        private int    m_nElementos;

        // --- Resultados (preenchidos pelo SimRunner) ---
        private double m_dP     = -1.0;
        private double m_cov    = -1.0;
        private String m_status = "OK";

        public CasoData(double angulo, int n) {
            m_angulo     = angulo;
            m_nElementos = n;
        }

        // Getters
        public double getAngulo()     { return m_angulo; }
        public int    getNElementos() { return m_nElementos; }
        public double getDP()         { return m_dP; }
        public double getCoV()        { return m_cov; }
        public String getStatus()     { return m_status; }
        public String getNome() {
            return String.format("ang%03.0f_n%02d", m_angulo, m_nElementos);
        }

        // Setters (usados pelo SimRunner)
        public void setDP(double v)       { m_dP     = v; }
        public void setCoV(double v)      { m_cov    = v; }
        public void setStatus(String s)   { m_status = s; }
    }

    // =========================================================
    // CLASSE 2: DataReader — lê CSV de entrada
    // =========================================================

    public class DataReader {
        private List<CasoData> m_casos = new ArrayList<CasoData>();

        // Formato esperado do CSV:
        //   Angulo,N_Elementos
        //   30,2
        //   30,3
        //   45,2
        public void readInput(String fileToRead) {
            try {
                FileReader     fr = new FileReader(fileToRead);
                BufferedReader br = new BufferedReader(fr);
                Scanner        sc = new Scanner(br);
                sc.useDelimiter("[,\n\r]+");  // vírgula ou quebra de linha

                sc.nextLine();  // pular header
                while (sc.hasNextLine()) {
                    sc.nextLine();
                    if (sc.hasNextDouble()) {
                        double angulo     = sc.nextDouble();
                        double nElementos = sc.nextDouble();
                        m_casos.add(new CasoData(angulo, (int) nElementos));
                    }
                }
            } catch (Exception e) {
                JOptionPane.showMessageDialog(null,
                        "DataReader: " + e.toString());
            }
        }

        public List<CasoData> getCasos() { return m_casos; }
    }

    // =========================================================
    // CLASSE 3: DataWriter — escreve CSV de saída
    // =========================================================

    public class DataWriter {
        private String m_outputFile;

        // Construtor: cria arquivo e escreve header
        public DataWriter(String fileToWrite) {
            m_outputFile = fileToWrite;
            try {
                FileWriter     fw = new FileWriter(m_outputFile);    // cria/sobrescreve
                BufferedWriter bw = new BufferedWriter(fw);
                bw.write("Caso,Angulo_graus,N_Elementos,dP_Pa,CoV,Status");
                bw.newLine();
                bw.close();
            } catch (Exception e) { }
        }

        // Adiciona uma linha ao final do arquivo (append)
        public void writeDataLine(CasoData d) {
            try {
                FileWriter     fw = new FileWriter(m_outputFile, true);  // true = APPEND
                BufferedWriter bw = new BufferedWriter(fw);
                bw.write(String.format("%s,%.0f,%d,%.4f,%.6f,%s",
                        d.getNome(), d.getAngulo(), d.getNElementos(),
                        d.getDP(), d.getCoV(), d.getStatus()));
                bw.newLine();
                bw.close();
            } catch (Exception e) { }
        }
    }

    // =========================================================
    // CLASSE 4: SimRunner — executa um caso no CCM+
    // =========================================================

    public class SimRunner {
        private Simulation m_sim;
        private CasoData   m_caso;

        public SimRunner(Simulation sim, CasoData caso) {
            m_sim  = sim;
            m_caso = caso;
        }

        public void run() {
            // Passo 1: Atualizar Design Parameters (3D-CAD)
            setDesignParameter("Angulo_Aleta",    m_caso.getAngulo());
            setDesignParameter("N_Elementos",     (double) m_caso.getNElementos());
            atualizarCad();

            // Passo 2: Regenerar malha
            regenerarMalha();

            // Passo 3: Limpar solução (forma COMPLETA do tutorial CCM+ 2602)
            m_sim.getSolution().clearSolution(
                    Solution.Clear.History,
                    Solution.Clear.Fields,
                    Solution.Clear.LagrangianDem
            );

            // Passo 4: Rodar
            m_sim.getSimulationIterator().runAutomation();

            // Passo 5: Extrair e armazenar no DTO
            m_caso.setDP(extrairDeltaP());
            m_caso.setCoV(extrairCoV());
        }

        private void setDesignParameter(String nome, double val) {
            try {
                CadModel cad = (CadModel) m_sim.get(SolidModelManager.class)
                        .getObject("3D-CAD Model 1");
                cad.getDesignParameterManager()
                   .getParameter(nome).getQuantity().setValue(val);
            } catch (Exception e) {
                m_sim.println("[AVISO] Param '" + nome + "': " + e.getMessage());
            }
        }

        private void atualizarCad() {
            try {
                CadModel cad = (CadModel) m_sim.get(SolidModelManager.class)
                        .getObject("3D-CAD Model 1");
                cad.update();
            } catch (Exception e) {
                m_sim.println("[AVISO] CAD update: " + e.getMessage());
            }
        }

        private void regenerarMalha() {
            try {
                for (MeshOperation op : m_sim.get(MeshOperationManager.class).getObjects()) {
                    if (op instanceof AutoMeshOperation) {
                        op.execute();
                        return;
                    }
                }
            } catch (Exception e) {
                m_sim.println("[AVISO] Malha: " + e.getMessage());
            }
        }

        private double extrairDeltaP() {
            try {
                // Report "dP_Misturador" deve estar pré-configurado na simulação
                // Usar getReportMonitorValue() — retorna double direto
                return m_sim.getReportManager()
                        .getReport("dP_Misturador")
                        .getReportMonitorValue();
            } catch (Exception e) { return -1.0; }
        }

        private double extrairCoV() {
            try {
                return m_sim.getReportManager()
                        .getReport("CoV_Outlet")
                        .getReportMonitorValue();
            } catch (Exception e) { return -1.0; }
        }
    }

    // =========================================================
    // CLASSE 5: PostProcessor — exporta cenas e plots
    // =========================================================

    public class PostProcessor {
        private Simulation   m_sim;
        private Scene        m_pressao    = null;
        private Scene        m_velocidade = null;
        private Scene        m_polimero   = null;
        private ResidualPlot m_residuos   = null;

        // Construtor: encontra objetos no CCM+ (não exporta ainda)
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
            salvarPlot( m_residuos,   dir + "/residuos_"   + nomeCaso + ".png");
        }

        private void salvarScene(Scene scene, String path) {
            if (scene == null) return;
            try {
                scene.printAndWait(path, 1, 1920, 1080);
                // CRÍTICO: fechar a cena antes da próxima simulação.
                // Cena aberta → renderiza em background → tempo de run explode.
                scene.close(true);
            } catch (Exception e) {
                m_sim.println("[AVISO] Cena '" + path + "': " + e.getMessage());
            }
        }

        private void salvarPlot(ResidualPlot plot, String path) {
            if (plot == null) return;
            try {
                // encode() para plots (não printAndWait)
                plot.encode(path, "png", 1920, 1080);
            } catch (Exception e) {}
        }

        // Alternativa: exportar como STAR-View+ (.sce) em vez de PNG
        private void exportarStarView(Scene scene, String path) {
            if (scene == null) return;
            try {
                scene.export3DSceneFileAndWait(path, true);
                scene.close(true);
            } catch (Exception e) {}
        }
    }
}
