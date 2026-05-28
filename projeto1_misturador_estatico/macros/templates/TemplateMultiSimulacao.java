// Template: Macro Multi-Simulação com 5 Classes Aninhadas
// Referência: "Intermediate Java Macros: Run Multiple Simulations" (CCM+ 2602)
//
// Estrutura:
//   CasoData      — DTO: parâmetros de entrada + resultado por caso
//   DataReader    — lê CSV de entrada, popula List<CasoData>
//   DataWriter    — escreve CSV de saída (header no construtor, append por caso)
//   SimRunner     — instanciado UMA VEZ fora do loop; localiza objetos CCM+ no construtor
//   PostProcessor — instanciado UMA VEZ fora do loop; localiza cenas no construtor
//
// REGRA CRÍTICA (tutorial "Understanding the Main Method"):
//   SimRunner e PostProcessor são criados ANTES do loop, não dentro.
//   Motivo: seus construtores localizam objetos CCM+ (regiões, cenas, reports)
//   que não mudam de posição entre casos. Instanciar N vezes seria ineficiente.
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

    // Número de iterações por caso (aumentar para valor final após testar)
    static final int N_ITERACOES = 5;   // baixo para desenvolvimento; final: 500-2000

    @Override
    public void execute() {
        // execute() inteiro em try-catch com JOptionPane (padrão do tutorial)
        try {
            Simulation sim = getActiveSimulation();
            sim.println("=== VARREDURA PARAMÉTRICA (padrão 5-classes) ===");
            new File(DIR_BASE).mkdirs();

            // ---- SEÇÃO 1: executada UMA VEZ ----
            DataReader reader = new DataReader();
            reader.readInput(PATH_CSV_ENTRADA);
            List<CasoData> casos = reader.getCasos();
            sim.println("Casos encontrados: " + casos.size());

            DataWriter    writer = new DataWriter(PATH_CSV_SAIDA);

            // SimRunner e PostProcessor: criados UMA VEZ, fora do loop.
            // Seus construtores localizam objetos CCM+ (regiões, cenas, reports).
            // Essas localizações não mudam entre casos — instanciar no loop seria errado.
            SimRunner     runner = new SimRunner(sim);
            PostProcessor postP  = new PostProcessor(sim);

            // ---- SEÇÃO 2: loop por caso ----
            int total = casos.size();
            int idx   = 0;
            for (CasoData caso : casos) {
                idx++;
                sim.println(String.format("\n=== CASO %d/%d: %s ===",
                        idx, total, caso.getNome()));

                // runCase(DTO, iterações): set params → clear → run(N) → extract
                runner.runCase(caso, N_ITERACOES);
                sim.println("  → DP=" + caso.getDP() + " Pa | CoV=" + caso.getCoV());

                // Exportar cenas (PostProcessor fecha cada cena automaticamente)
                postP.salvarCenas(DIR_BASE, caso.getNome());

                // Registrar no CSV
                writer.writeDataLine(caso);

                // Salvar .sim por caso
                sim.saveState(DIR_BASE + "/" + caso.getNome() + ".sim");
            }

            sim.println("\n=== VARREDURA CONCLUÍDA → " + PATH_CSV_SAIDA + " ===");

        } catch (Exception e) {
            // Pausa o macro e exibe janela com o erro — clique OK para continuar
            javax.swing.JOptionPane.showMessageDialog(null, e.toString());
        }
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
    //
    // INSTANCIAR UMA VEZ fora do loop (padrão do tutorial).
    // O construtor localiza objetos CCM+ que não mudam entre casos.
    // O método runCase() é chamado uma vez por caso, recebendo o DTO.
    // =========================================================

    public class SimRunner {
        private Simulation m_sim;

        // Referências a objetos CCM+ (localizados no construtor, uma vez)
        private Report m_reportDP  = null;
        private Report m_reportCoV = null;

        // Construtor: localiza objetos CCM+ que não mudam entre casos
        public SimRunner(Simulation sim) {
            m_sim = sim;
            // Localizar reports pré-configurados na simulação
            // (equivalente a navegar no object tree: Reports > "dP_Misturador")
            try { m_reportDP  = sim.getReportManager().getReport("dP_Misturador"); }
            catch (Exception e) { sim.println("[AVISO] Report dP não encontrado."); }
            try { m_reportCoV = sim.getReportManager().getReport("CoV_Outlet"); }
            catch (Exception e) { sim.println("[AVISO] Report CoV não encontrado."); }
        }

        // Chamado uma vez por caso. iterations: baixo durante dev, final para produção.
        public void runCase(CasoData caso, int iterations) {
            // Passo 1: Atualizar Design Parameters (3D-CAD) + update
            setDesignParameter("Angulo_Aleta", caso.getAngulo());
            setDesignParameter("N_Elementos",  (double) caso.getNElementos());
            atualizarCad();

            // Passo 2: Regenerar malha
            regenerarMalha();

            // Passo 3: Limpar solução anterior
            m_sim.clearSolution();

            // Passo 4: Rodar N iterações
            // run(N) → exatamente N iterações (usar durante dev com N pequeno)
            // runAutomation() → roda até condição de parada do CCM+ (para produção)
            m_sim.getSimulationIterator().run(iterations);

            // Passo 5: Extrair resultados e armazenar no DTO via setter
            caso.setDP(extrairValor(m_reportDP));
            caso.setCoV(extrairValor(m_reportCoV));
        }

        private double extrairValor(Report rep) {
            if (rep == null) return -1.0;
            try { return rep.getReportMonitorValue(); }
            catch (Exception e) { return -1.0; }
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
                    if (op instanceof AutoMeshOperation) { op.execute(); return; }
                }
            } catch (Exception e) {
                m_sim.println("[AVISO] Malha: " + e.getMessage());
            }
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
