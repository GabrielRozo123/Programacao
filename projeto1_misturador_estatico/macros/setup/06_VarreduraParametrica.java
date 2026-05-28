// Macro Star-CCM+: Varredura Paramétrica do Misturador Estático
//
// Objetivo (metodologia CCM+ 2602 - Designing the Macro):
//   "Para cada combinação (ângulo × N_elementos): limpar solução anterior,
//    atualizar geometria paramétrica, regenerar malha, rodar simulação,
//    extrair ΔP e CoV, exportar cenas, salvar .sim e registrar no CSV."
//
// Plano de ação (Creating a Simple Plan):
//   1. Limpar solução anterior       → sim.clearSolution()
//   2. Atualizar Design Parameters   → cadModel.getDesignParameterManager()
//   3. Atualizar geometria           → cadModel.update()
//   4. Regenerar malha               → meshOp.execute()
//   5. Rodar simulação               → sim.getSimulationIterator().run()
//   6. Extrair ΔP e CoV             → Reports
//   7. Exportar cenas (hardcopy)     → scene.printAndWait()
//   8. Salvar .sim                   → sim.saveState()
//   9. Gravar resultado no CSV
//  10. Repetir para próximo caso
//
// PRÉ-REQUISITO: Design Parameters no 3D-CAD:
//   - "Angulo_Aleta"     (Planar Angle Dimension, graus)
//   - "N_Elementos"      (Linear Pattern Count)
//   - "Espaco_Elementos" (Linear Pattern Spacing, mm)

import star.cadmodeler.*;
import star.common.*;
import star.base.neo.*;
import star.meshing.*;
import star.flow.*;
import star.report.*;
import star.vis.*;

import java.io.*;
import java.util.*;

public class VarreduraParametrica extends StarMacro {

    // =========================================================
    // ESPAÇO DE PARÂMETROS
    // =========================================================
    static final double[] ANGULOS_GRAUS = {30.0, 45.0, 60.0, 75.0, 90.0};
    static final int[]    N_ELEMENTOS   = {2, 3, 4, 5, 6};
    static final double   ESPACO_MM     = 400.0;

    // =========================================================
    // CONTROLE
    // =========================================================
    static final boolean RODAR_CFD      = false;  // false = analítico (triagem)
    static final int     N_ITERACOES    = 500;     // iterações por caso CFD
    static final boolean SALVAR_SIM     = true;    // salvar .sim por caso
    static final boolean EXPORTAR_CENAS = true;    // hardcopy de cenas

    static final String DIR_RESULTADOS  = System.getProperty("user.home")
            + "/Programacao/projeto1_misturador_estatico/resultados/varredura";
    // =========================================================

    @Override
    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("=== VARREDURA PARAMÉTRICA — MISTURADOR ESTÁTICO ===");
        sim.println("Ângulos: " + Arrays.toString(ANGULOS_GRAUS));
        sim.println("N elementos: " + Arrays.toString(N_ELEMENTOS));
        sim.println("Modo: " + (RODAR_CFD ? "CFD completo" : "Analítico (triagem)"));

        new File(DIR_RESULTADOS).mkdirs();
        String csvPath = DIR_RESULTADOS + "/varredura_completa.csv";

        try (PrintWriter csv = new PrintWriter(new FileWriter(csvPath))) {
            csv.println("Caso,Angulo_graus,N_Elementos,dP_Pa,dP_bar,CoV,"
                      + "L_total_mm,Re,Regime,Status");

            int total = ANGULOS_GRAUS.length * N_ELEMENTOS.length;
            int caso  = 0;

            for (double angulo : ANGULOS_GRAUS) {
                for (int n : N_ELEMENTOS) {
                    caso++;
                    String nomeCaso = String.format("ang%03.0f_n%02d",
                            angulo, n);
                    sim.println(String.format(
                            "\n======= CASO %d/%d: θ=%.0f°, N=%d =======",
                            caso, total, angulo, n));

                    String status = "OK";
                    double dP = 0, cov = 0, re = 0;
                    String regime = "Turbulento";

                    try {
                        if (RODAR_CFD) {
                            // ---- MODO CFD COMPLETO ----
                            // Passo 1: Limpar solução anterior
                            sim.println("  [1/8] Limpando solução anterior...");
                            sim.clearSolution();

                            // Passo 2-3: Atualizar geometria paramétrica
                            sim.println("  [2/8] Atualizando geometria...");
                            atualizarParametros(sim, angulo, n, ESPACO_MM);

                            // Passo 4: Regenerar malha
                            sim.println("  [3/8] Regenerando malha...");
                            regenerarMalha(sim);

                            // Passo 5: Rodar simulação
                            sim.println("  [4/8] Rodando " + N_ITERACOES + " iterações...");
                            sim.getSimulationIterator()
                               .runAutomation();

                            // Passo 6: Extrair resultados
                            sim.println("  [5/8] Extraindo resultados...");
                            dP  = extrairDeltaP(sim);
                            cov = extrairCoV(sim);

                        } else {
                            // ---- MODO ANALÍTICO (triagem rápida) ----
                            atualizarParametros(sim, angulo, n, ESPACO_MM);
                            dP  = calcularDPAnalitico(angulo, n, ESPACO_MM);
                            cov = calcularCoVAnalitico(angulo, n);
                        }

                        re = calcularRe(angulo);
                        regime = re > 4000 ? "Turbulento"
                               : re > 2300 ? "Transicao" : "Laminar";

                        sim.println(String.format(
                                "  → ΔP=%.2f Pa | CoV=%.4f | Re=%.0f | %s",
                                dP, cov, re, regime));

                        // Passo 7: Exportar cenas
                        if (EXPORTAR_CENAS && RODAR_CFD) {
                            sim.println("  [6/8] Exportando cenas...");
                            exportarCenas(sim, DIR_RESULTADOS, nomeCaso);
                        }

                        // Passo 8: Salvar .sim
                        if (SALVAR_SIM && RODAR_CFD) {
                            sim.println("  [7/8] Salvando simulação...");
                            String simPath = DIR_RESULTADOS + "/"
                                    + nomeCaso + ".sim";
                            sim.saveState(simPath);
                            sim.println("  Salvo em: " + simPath);
                        }

                    } catch (Exception e) {
                        status = "ERRO: " + e.getMessage();
                        sim.println("  [ERRO] " + e.getMessage());
                    }

                    // Passo 9: Gravar no CSV
                    double lTotal = 500.0 + n * ESPACO_MM + 400.0;
                    csv.printf("%s,%.0f,%d,%.4f,%.8f,%.6f,%.1f,%.0f,%s,%s%n",
                            nomeCaso, angulo, n,
                            dP, dP / 1e5, cov, lTotal, re, regime, status);
                    csv.flush();
                }
            }

            // Relatório final
            gerarRelatorio(sim, csvPath);

        } catch (IOException e) {
            sim.println("[ERRO] CSV: " + e.getMessage());
        }

        sim.println("\n=== VARREDURA CONCLUÍDA ===");
        sim.println("Resultados: " + csvPath);
    }

    // =========================================================
    // ATUALIZAÇÃO DE PARÂMETROS (Design Parameters 3D-CAD)
    // =========================================================

    private void atualizarParametros(Simulation sim, double angulo,
                                      int n, double espacoMm) {
        CadModel cad = obterCadModel(sim);
        if (cad == null) return;
        setParam(sim, cad, "Angulo_Aleta",    angulo);
        setParam(sim, cad, "N_Elementos",     (double) n);
        setParam(sim, cad, "Espaco_Elementos", espacoMm);
        cad.update();
        sim.println(String.format("  Geometria: θ=%.0f°, N=%d, espaço=%.0fmm",
                angulo, n, espacoMm));
    }

    private void setParam(Simulation sim, CadModel cad, String nome, double val) {
        try {
            cad.getDesignParameterManager().getParameter(nome)
               .getQuantity().setValue(val);
        } catch (Exception e) {
            sim.println("  [AVISO] Parâmetro '" + nome + "' não encontrado.");
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
    // REGENERAR MALHA
    // =========================================================

    private void regenerarMalha(Simulation sim) {
        try {
            // Localiza a operação Automated Mesh e re-executa
            for (MeshOperation op : sim.get(MeshOperationManager.class)
                    .getObjects()) {
                if (op instanceof AutoMeshOperation) {
                    op.execute();
                    sim.println("  Malha regenerada.");
                    return;
                }
            }
            sim.println("  [AVISO] AutomatedMesh não encontrado.");
        } catch (Exception e) {
            sim.println("  [AVISO] Erro ao regenerar malha: " + e.getMessage());
        }
    }

    // =========================================================
    // EXTRAIR RESULTADOS CFD
    // =========================================================

    private double extrairDeltaP(Simulation sim) {
        try {
            Region reg = sim.getRegionManager().getRegion("Fluid");
            double pIn  = criarReportBoundary(sim, reg, "Inlet",
                    "StaticPressure", "_tmp_pIn");
            double pOut = criarReportBoundary(sim, reg, "Outlet",
                    "StaticPressure", "_tmp_pOut");
            return pIn - pOut;
        } catch (Exception e) {
            sim.println("  [AVISO] ΔP: " + e.getMessage());
            return -1.0;
        }
    }

    private double criarReportBoundary(Simulation sim, Region reg,
            String boundaryName, String fieldFunc, String reportName) {
        ForcedAverageReport rep = (ForcedAverageReport)
                sim.getReportManager().createReport(ForcedAverageReport.class);
        rep.setPresentationName(reportName);
        rep.setScalar(sim.getFieldFunctionManager().getFunction(fieldFunc));
        rep.getParts().setObjects(reg.getBoundaryManager()
                .getBoundary(boundaryName));
        double val = rep.getValue();
        sim.getReportManager().remove(rep);
        return val;
    }

    private double extrairCoV(Simulation sim) {
        // CoV = sqrt(média((φ - φ_média)²)) / φ_média  no plano Outlet
        // Implementar via UserFieldFunction quando física estiver configurada:
        //   ff_desvio = ($PassiveScalar_Polimero - MEDIA)^2
        //   CoV = sqrt(areaAvg(ff_desvio)) / MEDIA
        // Por ora retorna -1 (implementar após 03_ConfigurarFisica rodar)
        return -1.0;
    }

    // =========================================================
    // EXPORTAR CENAS (hardcopy) — Planning Actions to Record
    // =========================================================

    private void exportarCenas(Simulation sim, String dir, String nomeCaso) {
        // Cena de pressão
        exportarCena(sim, dir + "/pressao_" + nomeCaso + ".png",
                "Pressao_Estatica");
        // Cena de velocidade
        exportarCena(sim, dir + "/velocidade_" + nomeCaso + ".png",
                "Velocidade");
        // Cena do escalar passivo (mistura do polímero)
        exportarCena(sim, dir + "/polimero_" + nomeCaso + ".png",
                "Polimero");
    }

    private void exportarCena(Simulation sim, String caminho, String nomeCena) {
        try {
            Scene cena = sim.getSceneManager().getScene(nomeCena);
            // printAndWait: exporta hardcopy sem precisar abrir a cena
            // (equivalente a: botão direito na cena > Save Hardcopy)
            cena.printAndWait(caminho, 1, 1920, 1080);
            sim.println("  Imagem: " + new File(caminho).getName());
        } catch (Exception e) {
            sim.println("  [AVISO] Cena '" + nomeCena + "': " + e.getMessage());
        }
    }

    // =========================================================
    // MODELOS ANALÍTICOS (modo rápido — triagem sem CFD)
    // =========================================================

    private double calcularDPAnalitico(double angulo, int n, double espacoMm) {
        double rho = 1050.0, mu = 0.001, D = 0.4445, Q = 0.10;
        double V   = Q / (Math.PI * D * D / 4.0);
        double Re  = rho * V * D / mu;
        double f   = 0.316 / Math.pow(Re, 0.25);
        double Z   = 5.0 * Math.pow(angulo / 90.0, 1.5);
        double Lem = espacoMm / 1000.0;
        return Z * f * (n * Lem / D) * (rho * V * V / 2.0)
             + f * (0.90 / D) * (rho * V * V / 2.0);
    }

    private double calcularCoVAnalitico(double angulo, int n) {
        double rho = 1050.0, mu = 0.001, D = 0.4445, Q = 0.10;
        double V  = Q / (Math.PI * D * D / 4.0);
        double Re = rho * V * D / mu;
        double r  = Math.min(0.30 * Math.pow(90.0/angulo, 0.4)
                           * Math.pow(10000.0/Math.max(Re,10000.0), 0.1), 0.95);
        return Math.pow(r, n);
    }

    private double calcularRe(double angulo) {
        double rho = 1050.0, mu = 0.001, D = 0.4445, Q = 0.10;
        double V = Q / (Math.PI * D * D / 4.0);
        return rho * V * D / mu;
    }

    // =========================================================
    // RELATÓRIO FINAL
    // =========================================================

    private void gerarRelatorio(Simulation sim, String csvPath) {
        sim.println("\n--- TABELA DE OTIMIZAÇÃO ---");
        sim.println(String.format("%-14s %-8s %-6s %-12s %-10s %-8s",
                "Caso", "Ângulo", "N", "ΔP [Pa]", "CoV", "Status"));
        sim.println("-".repeat(60));

        double melhorDP  = Double.MAX_VALUE;
        String melhorCaso = "";

        try (BufferedReader br = new BufferedReader(new FileReader(csvPath))) {
            br.readLine(); // header
            String linha;
            while ((linha = br.readLine()) != null) {
                String[] p = linha.split(",");
                if (p.length >= 9) {
                    sim.println(String.format("%-14s %-8s %-6s %-12s %-10s %-8s",
                            p[0], p[1]+"°", p[2], p[3], p[5], p[9]));
                    try {
                        double dp  = Double.parseDouble(p[3]);
                        double cov = Double.parseDouble(p[5]);
                        if (dp > 0 && cov < 0.05 && dp < melhorDP) {
                            melhorDP   = dp;
                            melhorCaso = p[0];
                        }
                    } catch (NumberFormatException ex) { /* ignora */ }
                }
            }
        } catch (IOException e) {
            sim.println("[AVISO] Lendo CSV: " + e.getMessage());
        }

        if (!melhorCaso.isEmpty()) {
            sim.println("\n→ CONFIGURAÇÃO ÓTIMA (menor ΔP com CoV < 5%):");
            sim.println("  Caso: " + melhorCaso
                    + " → ΔP = " + String.format("%.2f", melhorDP) + " Pa");
        }
    }
}
