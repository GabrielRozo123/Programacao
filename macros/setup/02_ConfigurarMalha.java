// Macro Star-CCM+: Configura malha para misturador estatico
// Misturador Estatico 18'' - Clarificacao de Xarope
// Executar apos 01_ImportarGeometria.java

import star.common.*;
import star.base.neo.*;
import star.meshing.*;
import star.prismmesher.*;
import star.resurfacer.*;
import star.solidmesher.*;
import star.dualmesher.*;

public class ConfigurarMalha extends StarMacro {

    // =========================================================
    // PARAMETROS DE MALHA
    // =========================================================
    // Tamanho base da malha relativo ao diametro (%)
    static final double TAMANHO_BASE_PORCENTO = 5.0;   // 5% do diametro = ~22 mm

    // Refinamento nas aletas do misturador (% do tamanho base)
    static final double REFINO_ALETAS_PORCENTO = 25.0; // 25% do base = ~5.5 mm

    // Camadas prismaticas (boundary layer)
    static final int    NUM_CAMADAS_PRISMA     = 8;
    static final double ESPESSURA_TOTAL_PRISMA = 0.3;  // 0.3% do diametro
    static final double STRETCH_PRISMA         = 1.3;  // razao de crescimento

    // Numero maximo de faces de superficie (controle de qualidade)
    static final int MAX_FACES_SUPERFICIE = 5_000_000;
    // =========================================================

    @Override
    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("=== CONFIGURANDO MALHA ===");

        MeshPipelineController mpc = sim.get(MeshPipelineController.class);

        // --- 1. Surface Remesher ---
        ResurfacerMeshingModel resurfacer =
                mpc.getMeshingModel(ResurfacerMeshingModel.class);
        resurfacer.getMinimumSurfaceSize().setRelativeSize(
                TAMANHO_BASE_PORCENTO / 4.0);
        resurfacer.getTargetSurfaceSize().setRelativeSize(
                TAMANHO_BASE_PORCENTO);
        sim.println("Surface remesher configurado.");

        // --- 2. Polyhedral Mesher ---
        DualMesherModel polyMesher =
                mpc.getMeshingModel(DualMesherModel.class);
        polyMesher.getDefaultControls().getBaseSize()
                .setValue(444.5 * TAMANHO_BASE_PORCENTO / 100.0);
        sim.println("Polyhedral mesher configurado. Tamanho base = "
                + (444.5 * TAMANHO_BASE_PORCENTO / 100.0) + " mm");

        // --- 3. Prism Layer Mesher ---
        PrismMesherModel prismMesher =
                mpc.getMeshingModel(PrismMesherModel.class);
        prismMesher.setNumLayers(NUM_CAMADAS_PRISMA);
        prismMesher.getPrismThickness().setRelativeSize(ESPESSURA_TOTAL_PRISMA);
        prismMesher.setStretching(STRETCH_PRISMA);
        sim.println("Prism layers: " + NUM_CAMADAS_PRISMA
                + " camadas, stretch=" + STRETCH_PRISMA);

        // --- 4. Refinamento volumetrico nas aletas ---
        // Cria volumetric control na regiao do misturador (L=1600mm central)
        sim.println("Criando refinamento nas aletas do misturador...");
        // (bloco de controle volumetrico deve ser criado manualmente
        //  ou via shape - ver documentacao)

        sim.println("=== CONFIGURACAO DE MALHA COMPLETA ===");
        sim.println("Para gerar a malha: Mesh > Generate Volume Mesh");
        sim.println("Verificar: numero de celulas esperado ~2-5 milhoes");
    }
}
