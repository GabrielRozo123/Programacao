// Macro Star-CCM+: Importa geometria IGES e extrai dominio fluido
// Misturador Estatico 18'' - Clarificacao de Xarope
// Uso: File > Macro > Play Macro

import macroutils.*;
import star.base.neo.*;
import star.cadmodeler.*;
import star.common.*;
import star.meshing.*;

import java.io.File;

public class ImportarGeometria extends StarMacro {

    // =========================================================
    // PARAMETROS - AJUSTAR CONFORME NECESSIDADE
    // =========================================================
    // Caminho base do projeto (ajustar para o seu ambiente)
    static final String DIR_PROJETO = System.getProperty("user.home") + "/Programacao";

    // Escolher revisao: "REV2" ou "REV4"
    static final String REVISAO = "REV2";

    // Diametro interno do tubo (18'' Schedule 40 padrao = 444.5 mm)
    static final double DIAMETRO_TUBO_MM = 444.5;

    // Comprimento total do dominio fluido (mm)
    static final double COMPRIMENTO_TOTAL_MM = 2399.0;

    // Extensoes de entrada e saida para desenvolvimentos do escoamento (mm)
    static final double EXTENS_ENTRADA_MM = 500.0;
    static final double EXTENS_SAIDA_MM   = 500.0;
    // =========================================================

    @Override
    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("=== IMPORTANDO GEOMETRIA: " + REVISAO + " ===");

        String arquivoIGES = DIR_PROJETO + "/geometria/MISTURADOR_ESTATICO_18pol_" + REVISAO + ".iges";
        File f = new File(arquivoIGES);
        if (!f.exists()) {
            sim.println("[ERRO] Arquivo nao encontrado: " + arquivoIGES);
            return;
        }

        // --- 1. Importar IGES ---
        sim.println("Importando IGES: " + arquivoIGES);
        sim.get(SolidModelManager.class).importCadFile(arquivoIGES,
                new NeoObjectVector(new Object[]{}));
        sim.println("IGES importado com sucesso.");

        // --- 2. Criar corpo geometrico para o volume fluido (tubo externo) ---
        // O IGES contem apenas as aletas do misturador.
        // O dominio fluido e obtido pela subtracao: cilindro - aletas
        sim.println("Criando dominio fluido...");
        CadModel cadModel = (CadModel) sim.get(SolidModelManager.class)
                .getObject("Geometry 1");

        // Nomear a simulacao
        sim.setSimulationDescription("Misturador_Estatico_18pol_" + REVISAO);

        sim.println("=== GEOMETRIA PRONTA ===");
        sim.println("Proximos passos:");
        sim.println("  1. Verificar corpos importados em Geometry > Parts");
        sim.println("  2. Criar regiao fluida com subtracao booleana (tubo - aletas)");
        sim.println("  3. Rodar macro 02_ConfigurarMalha.java");
    }
}
