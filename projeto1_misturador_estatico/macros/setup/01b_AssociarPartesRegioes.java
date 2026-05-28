// Macro Star-CCM+: Associa partes geometricas a regioes de simulacao
// Misturador Estatico 18'' - Clarificacao de Xarope
//
// EXECUTAR APOS: 01_ImportarGeometria.java
// EXECUTAR ANTES: 02_ConfigurarMalha.java
//
// Por que este passo e necessario:
//   Sem associar Parts a Regions, o CCM+ nao tem regioes para aplicar
//   fisica, condicoes de contorno, ou gerar malha.
//   Equivale a: botao direito em Geometry > Parts > [part] >
//               Assign Parts to Regions...
//
// Tutorial de referencia: Assigning Parts to Regions (CCM+ 2602)
//   Region mode:   Create a Region for Each Part
//   Boundary mode: Create a Boundary for Each Part Surface

import star.common.*;
import star.base.neo.*;
import star.meshing.*;

import java.util.*;

public class AssociarPartesRegioes extends StarMacro {

    // =========================================================
    // PARAMETROS
    // =========================================================
    // Nome da Part que representa o volume fluido
    // (criado pela subtracao booleana: tubo - aletas)
    // Ajustar para o nome real apos importar no 3D-CAD
    static final String NOME_PART_FLUIDO   = "Fluid_Volume";

    // Nomes esperados dos boundaries apos a associacao
    // (CCM+ cria um boundary por superficie da Part)
    // Renomear manualmente ou via macro apos a associacao
    static final String NOME_INLET        = "Inlet";
    static final String NOME_OUTLET       = "Outlet";
    static final String NOME_PAREDES      = "Walls";
    static final String NOME_ALETAS       = "Mixer_Blades";
    // =========================================================

    @Override
    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("=== ASSOCIANDO PARTES A REGIOES ===");

        // --- 1. Localizar a Part do volume fluido ---
        GeometryPart partFluido = localizarPart(sim, NOME_PART_FLUIDO);
        if (partFluido == null) {
            sim.println("[ERRO] Part '" + NOME_PART_FLUIDO + "' nao encontrada.");
            sim.println("       Verificar nome da Part em Geometry > Parts.");
            sim.println("       Parts disponiveis:");
            for (GeometryPart p : sim.getGeometryPartManager().getParts()) {
                sim.println("         - " + p.getPresentationName());
            }
            return;
        }

        // --- 2. Associar Part a Regiao ---
        // Equivalente a: botao direito > Assign Parts to Regions
        // Region mode:   Create a Region for Each Part
        // Boundary mode: Create a Boundary for Each Part Surface
        sim.println("Associando Part '" + NOME_PART_FLUIDO + "' a uma regiao...");

        MeshActionManager meshAction = sim.get(MeshActionManager.class);
        meshAction.assignPartsToRegions(
                new NeoObjectVector(new Object[]{partFluido}),
                MeshActionManager.AssignPartToRegionMode.MULTIPLE,    // uma regiao por Part
                MeshActionManager.CreateBoundaryMode.PARTSURF_AS_BOUNDARY, // uma boundary por superficie
                MeshActionManager.FeatureCurveCreationMode.NONE,
                true  // criar regiao se nao existir
        );

        sim.println("Regiao criada com sucesso.");

        // --- 3. Verificar e listar boundaries criadas ---
        sim.println("\nBoundaries criadas:");
        Region regiao = sim.getRegionManager().getRegion(NOME_PART_FLUIDO);
        if (regiao == null) {
            // CCM+ pode usar nome diferente — tentar pegar a primeira regiao
            Collection<Region> regioes = sim.getRegionManager().getRegions();
            if (!regioes.isEmpty()) {
                regiao = regioes.iterator().next();
                sim.println("  (Usando regiao: " + regiao.getPresentationName() + ")");
            }
        }

        if (regiao != null) {
            regiao.setPresentationName("Fluid");  // padronizar nome
            for (Boundary b : regiao.getBoundaryManager().getBoundaries()) {
                sim.println("  - " + b.getPresentationName());
            }

            sim.println("\nINSTRUCAO: Renomear as boundaries acima para:");
            sim.println("  Face de entrada principal  → '" + NOME_INLET + "'");
            sim.println("  Face de saida              → '" + NOME_OUTLET + "'");
            sim.println("  Paredes do tubo            → '" + NOME_PAREDES + "'");
            sim.println("  Superficies das aletas     → '" + NOME_ALETAS + "'");
            sim.println("\nOU usar o macro 01c_RenomearBoundaries.java");
        } else {
            sim.println("[AVISO] Nao foi possivel localizar a regiao criada.");
            sim.println("        Verificar em Regions no arvore da simulacao.");
        }

        sim.println("\n=== ASSOCIACAO CONCLUIDA ===");
        sim.println("Proximo passo: 02_ConfigurarMalha.java");
    }

    // =========================================================
    // HELPERS
    // =========================================================

    private GeometryPart localizarPart(Simulation sim, String nome) {
        // Tenta pelo nome exato
        try {
            return sim.getGeometryPartManager().getPart(nome);
        } catch (Exception e) { /* nao encontrou */ }

        // Tenta nome parcial (case insensitive)
        for (GeometryPart p : sim.getGeometryPartManager().getParts()) {
            if (p.getPresentationName().toLowerCase()
                    .contains(nome.toLowerCase())) {
                return p;
            }
        }
        return null;
    }
}
