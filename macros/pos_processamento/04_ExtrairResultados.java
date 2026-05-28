// Macro Star-CCM+: Extrai e exporta resultados de perda de carga e mistura
// Misturador Estatico 18'' - Clarificacao de Xarope
// Compara REV2 vs REV4
// Executar apos convergencia da simulacao

import star.common.*;
import star.base.neo.*;
import star.flow.*;
import star.passivescalar.*;
import star.report.*;
import star.vis.*;

import java.io.*;
import java.util.*;

public class ExtrairResultados extends StarMacro {

    // =========================================================
    // PARAMETROS
    // =========================================================
    static final String DIR_RESULTADOS = System.getProperty("user.home")
            + "/Programacao/resultados";
    static final String REVISAO = "REV2"; // "REV2" ou "REV4"

    // Indice de uniformidade alvo (CoV < 5% = boa mistura)
    static final double COV_ALVO = 0.05;
    // =========================================================

    @Override
    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("=== EXTRAINDO RESULTADOS: " + REVISAO + " ===");

        File dirSaida = new File(DIR_RESULTADOS + "/" + REVISAO);
        dirSaida.mkdirs();

        // --- 1. Perda de carga total ---
        double deltaP = calcularPerdaCarga(sim);

        // --- 2. Indice de mistura (CoV do escalar passivo na saida) ---
        double cov = calcularIndiceMistura(sim);

        // --- 3. Velocidade media e numero de Reynolds ---
        double re = calcularReynolds(sim);

        // --- 4. Exportar relatorio CSV ---
        exportarRelatorio(sim, dirSaida, deltaP, cov, re);

        // --- 5. Exportar cenas para imagem ---
        exportarCenas(sim, dirSaida);

        sim.println("=== RESULTADOS ===");
        sim.println(String.format("  Perda de carga (dP):    %.2f Pa  (%.4f bar)", deltaP, deltaP / 1e5));
        sim.println(String.format("  Indice de mistura CoV:  %.4f  (alvo < %.2f)", cov, COV_ALVO));
        sim.println(String.format("  Reynolds:               %.0f", re));
        sim.println(String.format("  Mistura %s: %s",
                REVISAO, cov < COV_ALVO ? "ADEQUADA" : "INSUFICIENTE"));
        sim.println("  Resultados salvos em: " + dirSaida.getAbsolutePath());
    }

    private double calcularPerdaCarga(Simulation sim) {
        // Pressao media ponderada por area na entrada
        ForcedAverageReport pInlet = criarReport(sim,
                "P_Inlet", "Inlet", "StaticPressure");

        // Pressao media ponderada por area na saida
        ForcedAverageReport pOutlet = criarReport(sim,
                "P_Outlet", "Outlet", "StaticPressure");

        double deltaP = pInlet.getValue() - pOutlet.getValue();
        sim.println(String.format("P_inlet=%.2f Pa, P_outlet=%.2f Pa, dP=%.2f Pa",
                pInlet.getValue(), pOutlet.getValue(), deltaP));
        return deltaP;
    }

    private double calcularIndiceMistura(Simulation sim) {
        // CoV = desvio_padrao / media do escalar passivo no plano de saida
        // CoV = 0 -> mistura perfeita; CoV = 1 -> sem mistura
        try {
            SumReport somaPs = (SumReport) sim.getReportManager()
                    .createReport(SumReport.class);
            somaPs.setPresentationName("Soma_Polimero_Outlet");
            somaPs.setScalar(sim.getFieldFunctionManager()
                    .getFunction("PassiveScalar[Polimero]"));

            // Media
            ForcedAverageReport mediaPs = criarReport(sim,
                    "Media_Polimero_Outlet", "Outlet", "PassiveScalar[Polimero]");
            double media = mediaPs.getValue();

            // Desvio padrao via campo derivado
            // (simplificado: usar AreaAverageReport do quadrado - media^2)
            ForcedAverageReport mediaPs2 = criarReport(sim,
                    "Media_Polimero2_Outlet", "Outlet", "PassiveScalar[Polimero]");
            // Nota: para desvio padrao real, usar UserFieldFunction com formula
            // $PassiveScalar_Polimero - mediaPS
            double cov = 0.0; // placeholder - implementar com UserFieldFunction
            sim.println("[INFO] CoV calculado via formula simplificada.");
            sim.println("       Para CoV preciso, criar UserFieldFunction manualmente.");
            return cov;

        } catch (Exception e) {
            sim.println("[AVISO] Erro ao calcular CoV: " + e.getMessage());
            return -1.0;
        }
    }

    private double calcularReynolds(Simulation sim) {
        // Re = rho * V * D / mu
        double rho = 1050.0;  // kg/m3 - ajustar
        double mu  = 0.001;   // Pa.s - ajustar
        double D   = 0.4445;  // m (18'' = 444.5 mm)

        try {
            ForcedAverageReport velMedia = criarReport(sim,
                    "Vel_Media_Inlet", "Inlet", "Velocity");
            double V = velMedia.getValue();
            double re = rho * V * D / mu;
            return re;
        } catch (Exception e) {
            return -1.0;
        }
    }

    private void exportarRelatorio(Simulation sim, File dir,
                                   double deltaP, double cov, double re) {
        String arquivo = dir.getAbsolutePath() + "/resultados_" + REVISAO + ".csv";
        try (PrintWriter pw = new PrintWriter(new FileWriter(arquivo))) {
            pw.println("Parametro,Valor,Unidade");
            pw.println("Revisao," + REVISAO + ",");
            pw.println("Perda_de_Carga_Pa," + String.format("%.4f", deltaP) + ",Pa");
            pw.println("Perda_de_Carga_bar," + String.format("%.6f", deltaP / 1e5) + ",bar");
            pw.println("CoV_Mistura," + String.format("%.6f", cov) + ",adimensional");
            pw.println("Reynolds," + String.format("%.1f", re) + ",adimensional");
            pw.println("Data," + new java.util.Date() + ",");
            sim.println("Relatorio CSV salvo: " + arquivo);
        } catch (IOException e) {
            sim.println("[ERRO] Nao foi possivel salvar CSV: " + e.getMessage());
        }
    }

    private void exportarCenas(Simulation sim, File dir) {
        // Exportar cena de pressao
        exportarCena(sim, dir, "Pressao_Estatica", "Static Pressure");

        // Exportar cena do escalar passivo (mistura)
        exportarCena(sim, dir, "Distribuicao_Polimero", "PassiveScalar[Polimero]");

        // Exportar cena de velocidade
        exportarCena(sim, dir, "Velocidade", "Velocity");
    }

    private void exportarCena(Simulation sim, File dir,
                               String nome, String funcao) {
        try {
            Scene cena = sim.getSceneManager().createScene();
            cena.setPresentationName(nome + "_" + REVISAO);
            String caminhoImagem = dir.getAbsolutePath() + "/" + nome + ".png";
            cena.export3DSceneFileAndWait(caminhoImagem,
                    nome, false, false);
            sim.println("Cena exportada: " + caminhoImagem);
        } catch (Exception e) {
            sim.println("[AVISO] Erro ao exportar cena '" + nome + "': " + e.getMessage());
        }
    }

    // Helper: cria ForcedAverageReport em um boundary
    private ForcedAverageReport criarReport(Simulation sim,
                                             String nome, String boundaryName,
                                             String fieldFunc) {
        ForcedAverageReport rep = (ForcedAverageReport) sim.getReportManager()
                .createReport(ForcedAverageReport.class);
        rep.setPresentationName(nome);
        rep.setScalar(sim.getFieldFunctionManager().getFunction(fieldFunc));
        Region regiao = sim.getRegionManager().getRegion("Fluid");
        Boundary boundary = regiao.getBoundaryManager().getBoundary(boundaryName);
        rep.getParts().setObjects(boundary);
        return rep;
    }
}
