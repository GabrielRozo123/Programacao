// Macro Star-CCM+: Compara resultados REV2 vs REV4
// Le os CSVs gerados por 04_ExtrairResultados.java e gera relatorio comparativo
// Pode ser executado fora do Star-CCM+ como Java standalone ou dentro do CCM+

import star.common.*;

import java.io.*;
import java.util.*;

public class CompararRevisoes extends StarMacro {

    static final String DIR_RESULTADOS = System.getProperty("user.home")
            + "/Programacao/resultados";

    @Override
    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("=== COMPARATIVO REV2 vs REV4 ===");

        Map<String, Map<String, Double>> dados = new HashMap<>();

        for (String rev : new String[]{"REV2", "REV4"}) {
            String csv = DIR_RESULTADOS + "/" + rev + "/resultados_" + rev + ".csv";
            dados.put(rev, lerCSV(sim, csv));
        }

        if (dados.get("REV2").isEmpty() || dados.get("REV4").isEmpty()) {
            sim.println("[ERRO] Um ou mais arquivos de resultado nao encontrados.");
            sim.println("       Execute a simulacao de ambas as revisoes primeiro.");
            return;
        }

        double dpRev2 = dados.get("REV2").getOrDefault("Perda_de_Carga_Pa", Double.NaN);
        double dpRev4 = dados.get("REV4").getOrDefault("Perda_de_Carga_Pa", Double.NaN);
        double covRev2 = dados.get("REV2").getOrDefault("CoV_Mistura", Double.NaN);
        double covRev4 = dados.get("REV4").getOrDefault("CoV_Mistura", Double.NaN);

        double redDp  = (dpRev4 - dpRev2) / dpRev2 * 100.0;
        double redCov = (covRev4 - covRev2) / covRev2 * 100.0;

        sim.println("+-----------------------------------------+----------+----------+----------+");
        sim.println("| Parametro                               |   REV2   |   REV4   |  Delta % |");
        sim.println("+-----------------------------------------+----------+----------+----------+");
        sim.println(String.format("| Perda de Carga [Pa]                     | %8.2f | %8.2f | %+8.2f |",
                dpRev2, dpRev4, redDp));
        sim.println(String.format("| Perda de Carga [bar]                    | %8.5f | %8.5f | %+8.2f |",
                dpRev2 / 1e5, dpRev4 / 1e5, redDp));
        sim.println(String.format("| CoV Mistura [-]                         | %8.4f | %8.4f | %+8.2f |",
                covRev2, covRev4, redCov));
        sim.println("+-----------------------------------------+----------+----------+----------+");

        sim.println("");
        if (redDp < 0) {
            sim.println("  REV4 reduz a perda de carga em " + String.format("%.1f%%", Math.abs(redDp)));
        } else {
            sim.println("  REV4 aumenta a perda de carga em " + String.format("%.1f%%", redDp));
        }
        if (redCov < 0) {
            sim.println("  REV4 MELHORA a mistura em " + String.format("%.1f%%", Math.abs(redCov)));
        } else {
            sim.println("  REV4 PIORA a mistura em " + String.format("%.1f%%", redCov));
        }

        // Salvar comparativo
        String csvComp = DIR_RESULTADOS + "/comparativo_REV2_vs_REV4.csv";
        try (PrintWriter pw = new PrintWriter(new FileWriter(csvComp))) {
            pw.println("Parametro,REV2,REV4,Delta_porcento");
            pw.printf("Perda_Carga_Pa,%.4f,%.4f,%+.2f%n", dpRev2, dpRev4, redDp);
            pw.printf("Perda_Carga_bar,%.6f,%.6f,%+.2f%n", dpRev2/1e5, dpRev4/1e5, redDp);
            pw.printf("CoV_Mistura,%.6f,%.6f,%+.2f%n", covRev2, covRev4, redCov);
            sim.println("Comparativo salvo: " + csvComp);
        } catch (IOException e) {
            sim.println("[ERRO] Nao foi possivel salvar comparativo: " + e.getMessage());
        }
    }

    private Map<String, Double> lerCSV(Simulation sim, String caminho) {
        Map<String, Double> valores = new HashMap<>();
        File f = new File(caminho);
        if (!f.exists()) {
            sim.println("[AVISO] Arquivo nao encontrado: " + caminho);
            return valores;
        }
        try (BufferedReader br = new BufferedReader(new FileReader(f))) {
            String linha;
            br.readLine(); // cabecalho
            while ((linha = br.readLine()) != null) {
                String[] partes = linha.split(",");
                if (partes.length >= 2) {
                    try {
                        valores.put(partes[0].trim(), Double.parseDouble(partes[1].trim()));
                    } catch (NumberFormatException ex) { /* ignora campos nao numericos */ }
                }
            }
        } catch (IOException e) {
            sim.println("[ERRO] Lendo CSV " + caminho + ": " + e.getMessage());
        }
        return valores;
    }
}
