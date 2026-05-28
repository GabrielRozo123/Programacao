// Macro Star-CCM+: Varredura Paramétrica do Misturador Estático
//
// Objetivo: varrer automaticamente (ângulo × N_elementos) e extrair
// ΔP e CoV para cada configuração → tabela de otimização completa.
//
// PRÉ-REQUISITO: a geometria 3D-CAD deve ter os seguintes Design Parameters:
//   - "Angulo_Aleta"    (Planar Angle Dimension, em graus)
//   - "N_Elementos"     (Linear Pattern Count)
//   - "Espaco_Elementos" (Linear Pattern Spacing, em mm)
//
// Como criar esses parâmetros no 3D-CAD:
//   1. Criar sketch de referência na face da aleta
//   2. Features > Create Assembly Constraint Feature
//   3. Planar Angle Dimension → selecionar arestas → Expose Parameter → nome "Angulo_Aleta"
//   4. Botão direito na aleta → Create Pattern > Linear Pattern
//      Count → Expose Parameter → "N_Elementos"
//      Spacing → Expose Parameter → "Espaco_Elementos"

import star.cadmodeler.*;
import star.common.*;
import star.base.neo.*;
import star.meshing.*;
import star.flow.*;
import star.report.*;

import java.io.*;
import java.util.*;

public class VarreduraParametrica extends StarMacro {

    // =========================================================
    // ESPAÇO DE PARÂMETROS A VARRER
    // =========================================================
    static final double[] ANGULOS_GRAUS   = {30.0, 45.0, 60.0, 75.0, 90.0};
    static final int[]    N_ELEMENTOS     = {2, 3, 4, 5, 6};
    static final double   ESPACO_MM       = 400.0;   // fixo por ora

    // =========================================================
    // CONTROLE DE EXECUÇÃO
    // =========================================================
    // true  → remesh + run completo (lento, resultado preciso)
    // false → só atualiza geometria e extrai ΔP analítico (rápido, triagem)
    static final boolean RODAR_CFD        = false;

    static final String DIR_RESULTADOS    = System.getProperty("user.home")
            + "/Programacao/projeto1_misturador_estatico/resultados/varredura";

    // =========================================================

    @Override
    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("=== VARREDURA PARAMÉTRICA — MISTURADOR ESTÁTICO ===");
        sim.println("Ângulos: " + Arrays.toString(ANGULOS_GRAUS));
        sim.println("N elementos: " + Arrays.toString(N_ELEMENTOS));
        sim.println("Rodar CFD: " + RODAR_CFD);

        new File(DIR_RESULTADOS).mkdirs();
        String csvPath = DIR_RESULTADOS + "/varredura_completa.csv";

        try (PrintWriter csv = new PrintWriter(new FileWriter(csvPath))) {
            csv.println("Angulo_graus,N_Elementos,dP_Pa,CoV,L_total_mm,Status");

            int total = ANGULOS_GRAUS.length * N_ELEMENTOS.length;
            int atual = 0;

            for (double angulo : ANGULOS_GRAUS) {
                for (int n : N_ELEMENTOS) {
                    atual++;
                    sim.println(String.format("\n--- Caso %d/%d: θ=%.0f°, N=%d ---",
                            atual, total, angulo, n));

                    String status = "OK";
                    double dP = 0.0, cov = 0.0;

                    try {
                        // 1. Atualizar parâmetros geométricos
                        atualizarParametros(sim, angulo, n, ESPACO_MM);

                        if (RODAR_CFD) {
                            // 2a. Regenerar malha
                            sim.println("  Gerando malha...");
                            sim.getMeshPipelineController().generateVolumeMesh();

                            // 2b. Rodar simulação
                            sim.println("  Rodando simulação...");
                            sim.getSimulationIterator().runAutomation();

                            // 2c. Extrair resultados
                            dP  = extrairDeltaP(sim);
                            cov = extrairCoV(sim);
                        } else {
                            // Modo rápido: modelo analítico embutido
                            dP  = calcularDPAnalitico(angulo, n, ESPACO_MM);
                            cov = calcularCoVAnalitico(angulo, n);
                            sim.println(String.format("  ΔP=%.2f Pa, CoV=%.4f", dP, cov));
                        }

                        double lTotal = 500.0 + n * ESPACO_MM + 400.0;  // entrada + aletas + saída
                        csv.printf("%.0f,%d,%.4f,%.6f,%.1f,%s%n",
                                angulo, n, dP, cov, lTotal, status);
                        csv.flush();

                    } catch (Exception e) {
                        status = "ERRO: " + e.getMessage();
                        sim.println("  [ERRO] " + e.getMessage());
                        csv.printf("%.0f,%d,,,,%s%n", angulo, n, status);
                        csv.flush();
                    }
                }
            }

            // Gerar relatório de otimização
            gerarRelatorio(sim, csvPath);

        } catch (IOException e) {
            sim.println("[ERRO] Não foi possível criar arquivo CSV: " + e.getMessage());
        }

        sim.println("\n=== VARREDURA CONCLUÍDA ===");
        sim.println("Resultados em: " + csvPath);
    }

    // =========================================================
    // ATUALIZAÇÃO DOS DESIGN PARAMETERS
    // =========================================================

    private void atualizarParametros(Simulation sim, double angulo,
                                      int nElem, double espacoMm) {
        CadModel cadModel = obterCadModel(sim);
        if (cadModel == null) {
            sim.println("  [AVISO] 3D-CAD Model não encontrado. Usando modo analítico.");
            return;
        }

        // Atualizar ângulo da aleta
        setDesignParameter(sim, cadModel, "Angulo_Aleta", angulo);

        // Atualizar número de elementos
        setDesignParameter(sim, cadModel, "N_Elementos", (double) nElem);

        // Atualizar espaçamento
        setDesignParameter(sim, cadModel, "Espaco_Elementos", espacoMm);

        // Recalcular geometria
        cadModel.update();
        sim.println(String.format("  Geometria atualizada: θ=%.0f°, N=%d, espaço=%.0fmm",
                angulo, nElem, espacoMm));
    }

    private void setDesignParameter(Simulation sim, CadModel model,
                                     String nome, double valor) {
        try {
            DesignParameter param = model.getDesignParameterManager()
                    .getParameter(nome);
            param.getQuantity().setValue(valor);
            sim.println(String.format("  %s = %.2f", nome, valor));
        } catch (Exception e) {
            sim.println("  [AVISO] Parâmetro '" + nome + "' não encontrado: "
                    + e.getMessage());
        }
    }

    private CadModel obterCadModel(Simulation sim) {
        try {
            return (CadModel) sim.get(SolidModelManager.class)
                    .getObject("3D-CAD Model 1");
        } catch (Exception e) {
            return null;
        }
    }

    // =========================================================
    // EXTRAÇÃO DE RESULTADOS CFD
    // =========================================================

    private double extrairDeltaP(Simulation sim) {
        try {
            Region regiao = sim.getRegionManager().getRegion("Fluid");
            ForcedAverageReport pIn = (ForcedAverageReport) sim.getReportManager()
                    .createReport(ForcedAverageReport.class);
            pIn.setPresentationName("_tmp_pIn");
            pIn.setScalar(sim.getFieldFunctionManager()
                    .getFunction("StaticPressure"));
            pIn.getParts().setObjects(
                    regiao.getBoundaryManager().getBoundary("Inlet"));

            ForcedAverageReport pOut = (ForcedAverageReport) sim.getReportManager()
                    .createReport(ForcedAverageReport.class);
            pOut.setPresentationName("_tmp_pOut");
            pOut.setScalar(sim.getFieldFunctionManager()
                    .getFunction("StaticPressure"));
            pOut.getParts().setObjects(
                    regiao.getBoundaryManager().getBoundary("Outlet"));

            double dP = pIn.getValue() - pOut.getValue();
            sim.getReportManager().remove(pIn);
            sim.getReportManager().remove(pOut);
            return dP;
        } catch (Exception e) {
            return -1.0;
        }
    }

    private double extrairCoV(Simulation sim) {
        // CoV = desvio_padrão / média do escalar passivo no outlet
        // Implementar via UserFieldFunction:
        //   ff = (PassiveScalar[Polimero] - media)^2
        //   CoV = sqrt(avg(ff)) / media
        // Simplificado aqui — implementar completamente após setup da física
        return -1.0;
    }

    // =========================================================
    // MODELO ANALÍTICO EMBUTIDO (modo rápido, sem CFD)
    // Correlações idênticas ao modelo_misturador_estatico.py
    // =========================================================

    private double calcularDPAnalitico(double angulo, int n, double espacoMm) {
        double rho = 1050.0, mu = 0.001, D = 0.4445, Q = 0.10;
        double V   = Q / (Math.PI * D * D / 4.0);
        double Re  = rho * V * D / mu;
        double f   = 0.316 / Math.pow(Re, 0.25);
        double Z   = 5.0 * Math.pow(angulo / 90.0, 1.5);
        double L_elem = espacoMm / 1000.0;
        double dP_mist = Z * f * (n * L_elem / D) * (rho * V * V / 2.0);
        double dP_reto = f * ((0.50 + 0.40) / D) * (rho * V * V / 2.0);
        return dP_mist + dP_reto;
    }

    private double calcularCoVAnalitico(double angulo, int n) {
        double rho = 1050.0, mu = 0.001, D = 0.4445, Q = 0.10;
        double V  = Q / (Math.PI * D * D / 4.0);
        double Re = rho * V * D / mu;
        double r_ref = 0.30;
        double fAng = Math.pow(90.0 / angulo, 0.4);
        double fRe  = Math.pow(10000.0 / Math.max(Re, 10000.0), 0.1);
        double r    = Math.min(r_ref * fAng * fRe, 0.95);
        return Math.pow(r, n);
    }

    // =========================================================
    // RELATÓRIO FINAL
    // =========================================================

    private void gerarRelatorio(Simulation sim, String csvPath) {
        sim.println("\n--- TABELA DE OTIMIZAÇÃO ---");
        sim.println(String.format("%-10s %-12s %-12s %-10s %-8s",
                "Ângulo", "N_elementos", "ΔP [Pa]", "CoV", "Status"));
        sim.println("-".repeat(55));

        try (BufferedReader br = new BufferedReader(new FileReader(csvPath))) {
            br.readLine(); // header
            String linha;
            double melhorDP = Double.MAX_VALUE;
            String melhorCaso = "";

            while ((linha = br.readLine()) != null) {
                String[] p = linha.split(",");
                if (p.length >= 5) {
                    sim.println(String.format("%-10s %-12s %-12s %-10s %-8s",
                            p[0] + "°", p[1], p[2], p[3], p[4]));
                    try {
                        double dp = Double.parseDouble(p[2]);
                        double cov = Double.parseDouble(p[3]);
                        if (dp < melhorDP && cov < 0.05) {
                            melhorDP = dp;
                            melhorCaso = "θ=" + p[0] + "°, N=" + p[1];
                        }
                    } catch (NumberFormatException ex) { /* ignora */ }
                }
            }

            if (!melhorCaso.isEmpty()) {
                sim.println("\n→ MELHOR CONFIGURAÇÃO (menor ΔP com CoV < 5%):");
                sim.println("  " + melhorCaso + " → ΔP = " + melhorDP + " Pa");
            }
        } catch (IOException e) {
            sim.println("[AVISO] Não foi possível gerar relatório: " + e.getMessage());
        }
    }
}
