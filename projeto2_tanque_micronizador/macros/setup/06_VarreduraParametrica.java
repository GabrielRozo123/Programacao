// Macro Star-CCM+: Varredura Paramétrica do Tanque com Micronizador
//
// Objetivo: varrer automaticamente (N_micronizadores × Raio × Altura)
// e extrair Eficiência de Incorporação de Microbolhas para cada
// configuração → posição e quantidade ótima de micronizadores.
//
// PRÉ-REQUISITO: geometria 3D-CAD com Design Parameters:
//   - "N_Micronizadores"  (Circular Pattern Count)
//   - "Raio_Micronizador" (Distance Dimension, em mm)
//   - "Altura_Injecao"    (Distance Dimension do fundo, em mm)
//
// Como criar no 3D-CAD:
//   1. Criar o corpo do micronizador no fundo do tanque
//   2. Criar Circular Pattern no eixo central do tanque
//      Count → Expose Parameter → "N_Micronizadores"
//   3. Criar Distance Dimension do eixo até o orifício
//      → Expose Parameter → "Raio_Micronizador"
//   4. Criar Distance Dimension do fundo até o orifício
//      → Expose Parameter → "Altura_Injecao"

import star.cadmodeler.*;
import star.common.*;
import star.base.neo.*;
import star.meshing.*;
import star.report.*;

import java.io.*;
import java.util.*;

public class VarreduraParametrica extends StarMacro {

    // =========================================================
    // ESPAÇO DE PARÂMETROS A VARRER
    // =========================================================
    // Número de micronizadores
    static final int[] N_MICRONIZADORES = {2, 3, 4, 6, 8};

    // Raio de instalação (fração do raio do tanque)
    // Ex: 0.4 = 40% do raio → para tanque de D=2m: r = 0.4m
    static final double[] FRACAO_RAIO    = {0.3, 0.5, 0.6, 0.7, 0.8};

    // Altura de injeção (fração da altura do tanque)
    static final double[] FRACAO_ALTURA  = {0.05, 0.10, 0.20};

    // Geometria do tanque (atualizar quando receber dados)
    static final double R_TANQUE_MM      = 1000.0;  // mm (D=2m → R=1m)
    static final double H_TANQUE_MM      = 3000.0;  // mm

    // =========================================================
    // CONTROLE
    // =========================================================
    static final boolean RODAR_CFD       = false;   // false = modelo analítico
    static final String DIR_RESULTADOS   = System.getProperty("user.home")
            + "/Programacao/projeto2_tanque_micronizador/resultados/varredura";

    // =========================================================

    @Override
    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("=== VARREDURA PARAMÉTRICA — TANQUE COM MICRONIZADOR ===");
        sim.println("N_mic: " + Arrays.toString(N_MICRONIZADORES));
        sim.println("Frações de raio: " + Arrays.toString(FRACAO_RAIO));
        sim.println("Frações de altura: " + Arrays.toString(FRACAO_ALTURA));

        new File(DIR_RESULTADOS).mkdirs();
        String csvPath = DIR_RESULTADOS + "/varredura_micronizador.csv";

        try (PrintWriter csv = new PrintWriter(new FileWriter(csvPath))) {
            csv.println("N_mic,Raio_mm,Altura_mm,Fracao_raio,Fracao_altura,"
                      + "d_bolha_um,v_ascensao_mms,t_res_s,efic_inc_pct,"
                      + "We,Status");

            int total = N_MICRONIZADORES.length * FRACAO_RAIO.length * FRACAO_ALTURA.length;
            int atual = 0;

            double melhorEfic = 0.0;
            String melhorCaso = "";

            for (int n : N_MICRONIZADORES) {
                for (double fr : FRACAO_RAIO) {
                    for (double fh : FRACAO_ALTURA) {
                        atual++;
                        double raio_mm   = R_TANQUE_MM * fr;
                        double altura_mm = H_TANQUE_MM * fh;

                        sim.println(String.format("\n--- Caso %d/%d: N=%d, r=%.0fmm (%.0f%%), h=%.0fmm ---",
                                atual, total, n, raio_mm, fr * 100, altura_mm));

                        String status = "OK";
                        try {
                            // Atualizar geometria paramétrica
                            atualizarParametros(sim, n, raio_mm, altura_mm);

                            // Calcular métricas (analítico ou CFD)
                            double[] metricas = RODAR_CFD
                                    ? extrairMetricasCFD(sim)
                                    : calcularMetricasAnaliticas(n, raio_mm, altura_mm);

                            double dBolha  = metricas[0];  // µm
                            double vAscMs  = metricas[1];  // mm/s
                            double tRes    = metricas[2];  // s
                            double efic    = metricas[3];  // 0-1
                            double we      = metricas[4];

                            sim.println(String.format(
                                    "  d_bol=%.1fµm, v=%.3fmm/s, t=%.0fs, efic=%.1f%%, We=%.5f",
                                    dBolha, vAscMs, tRes, efic * 100, we));

                            csv.printf("%d,%.1f,%.1f,%.2f,%.2f,%.2f,%.4f,%.1f,%.2f,%.6f,%s%n",
                                    n, raio_mm, altura_mm, fr, fh,
                                    dBolha, vAscMs, tRes, efic * 100, we, status);
                            csv.flush();

                            if (efic > melhorEfic) {
                                melhorEfic = efic;
                                melhorCaso = String.format("N=%d, r=%.0fmm, h=%.0fmm",
                                        n, raio_mm, altura_mm);
                            }

                        } catch (Exception e) {
                            status = "ERRO: " + e.getMessage();
                            sim.println("  [ERRO] " + e.getMessage());
                            csv.printf("%d,%.1f,%.1f,%.2f,%.2f,,,,,,,%s%n",
                                    n, raio_mm, altura_mm, fr, fh, status);
                            csv.flush();
                        }
                    }
                }
            }

            sim.println("\n=== RESULTADO DA OTIMIZAÇÃO ===");
            sim.println("→ MELHOR CONFIGURAÇÃO (maior eficiência de incorporação):");
            sim.println("  " + melhorCaso);
            sim.println(String.format("  Eficiência: %.1f%%", melhorEfic * 100));

        } catch (IOException e) {
            sim.println("[ERRO] " + e.getMessage());
        }

        sim.println("\nResultados em: " + csvPath);
    }

    // =========================================================
    // ATUALIZAÇÃO DOS DESIGN PARAMETERS
    // =========================================================

    private void atualizarParametros(Simulation sim, int n,
                                      double raio_mm, double altura_mm) {
        CadModel cadModel = obterCadModel(sim);
        if (cadModel == null) {
            sim.println("  [AVISO] Modo analítico (3D-CAD não encontrado).");
            return;
        }

        setDesignParameter(sim, cadModel, "N_Micronizadores", (double) n);
        setDesignParameter(sim, cadModel, "Raio_Micronizador", raio_mm);
        setDesignParameter(sim, cadModel, "Altura_Injecao",    altura_mm);
        cadModel.update();

        sim.println(String.format("  Geometria: N=%d, r=%.1fmm, h=%.1fmm",
                n, raio_mm, altura_mm));
    }

    private void setDesignParameter(Simulation sim, CadModel model,
                                     String nome, double valor) {
        try {
            DesignParameter param = model.getDesignParameterManager()
                    .getParameter(nome);
            param.getQuantity().setValue(valor);
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
    // MODELO ANALÍTICO EMBUTIDO
    // Correlações idênticas ao modelo_tanque_micronizador.py
    // =========================================================

    private double[] calcularMetricasAnaliticas(int n, double raio_mm, double altura_mm) {
        // Propriedades
        double rho_L  = 1050.0;    // kg/m³ caldo
        double rho_G  = 1.2;       // kg/m³ ar
        double mu_L   = 0.001;     // Pa·s
        double sigma   = 0.07;     // N/m
        double g       = 9.81;     // m/s²
        double Q_ar   = 0.005;     // m³/s total
        double d_or   = 0.001;     // m orifício

        // Vazão por micronizador
        double Q_mic = Q_ar / n;
        double A_or  = Math.PI * d_or * d_or / 4.0;
        double v_or  = Q_mic / A_or;

        // Diâmetro de bolha no orifício
        double We_or = rho_L * v_or * v_or * d_or / sigma;
        double d_bol = (We_or < 1.0)
                ? d_or * 1.5
                : 0.76 * d_or * Math.pow(We_or, -0.5);
        d_bol = Math.max(d_bol, 10e-6);

        // Velocidade de ascensão (Stokes)
        double v_asc = (d_bol * d_bol * (rho_L - rho_G) * g) / (18.0 * mu_L);

        // Tempo de residência
        double H_inj  = altura_mm / 1000.0;
        double H_tank = H_TANQUE_MM / 1000.0;
        double t_res  = (H_tank - H_inj) / v_asc;

        // Weber bolha
        double v_rel = 0.1 * v_asc;
        double We_b  = rho_L * v_rel * v_rel * d_bol / sigma;

        // Eficiência de incorporação
        double alpha   = 0.05;  // fração de vazio estimada
        double taxa_coal = (We_b < 1.0) ? alpha * 0.3 : alpha * 0.7;
        taxa_coal = Math.min(taxa_coal, 0.95);
        double d_ref = 80e-6;
        double cob   = Math.min(1.0, Math.sqrt(d_ref / d_bol));
        double efic  = (1.0 - taxa_coal) * cob;

        return new double[]{
            d_bol * 1e6,    // µm
            v_asc * 1000.0, // mm/s
            t_res,          // s
            efic,           // 0-1
            We_b            // adimensional
        };
    }

    // =========================================================
    // EXTRAÇÃO DE RESULTADOS CFD (S-Gamma)
    // =========================================================

    private double[] extrairMetricasCFD(Simulation sim) {
        try {
            // Diâmetro médio de bolha (campo do S-Gamma: "Mean Particle Diameter")
            Region regiao = sim.getRegionManager().getRegion("Fluid");
            VolumeAverageReport dMedio = (VolumeAverageReport) sim.getReportManager()
                    .createReport(VolumeAverageReport.class);
            dMedio.setPresentationName("_tmp_dMedio");
            dMedio.setScalar(sim.getFieldFunctionManager()
                    .getFunction("MeanParticleDiameter"));
            dMedio.getParts().setObjects(regiao);
            double dBolha = dMedio.getValue() * 1e6;  // m → µm
            sim.getReportManager().remove(dMedio);

            // Eficiência: fração volumétrica de ar média no tanque
            VolumeAverageReport alphaReport = (VolumeAverageReport) sim.getReportManager()
                    .createReport(VolumeAverageReport.class);
            alphaReport.setPresentationName("_tmp_alpha");
            alphaReport.setScalar(sim.getFieldFunctionManager()
                    .getFunction("VolumeFraction[Air]"));
            alphaReport.getParts().setObjects(regiao);
            double alpha = alphaReport.getValue();
            sim.getReportManager().remove(alphaReport);

            // Eficiência = razão entre alpha real e alpha injetado
            double alpha_injetado = 0.05;
            double efic = Math.min(alpha / alpha_injetado, 1.0);

            return new double[]{dBolha, -1.0, -1.0, efic, -1.0};

        } catch (Exception e) {
            sim.println("  [AVISO] Erro ao extrair resultados CFD: " + e.getMessage());
            return new double[]{-1, -1, -1, -1, -1};
        }
    }
}
