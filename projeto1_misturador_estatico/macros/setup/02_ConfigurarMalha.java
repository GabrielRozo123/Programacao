// Macro Star-CCM+: Configura malha para misturador estatico
// Misturador Estatico 18'' - Clarificacao de Xarope
//
// CORRECAO v2: usa AutomatedMeshOperation (CCM+ 2602)
// A API antiga MeshPipelineController foi substituida por
// Operations > Automated Mesh na versao 2602.
//
// Tutorial de referencia:
//   - Selecting the Meshers (CCM+ 2602)
//   - Setting the Mesh Default Controls (CCM+ 2602)
//
// Meshers selecionados para escoamento interno (misturador):
//   Surface:  Surface Remesher
//   Volume:   Polyhedral Mesher  (melhor que Trimmed para geometrias
//             complexas com aletas curvadas — Trimmed e melhor para
//             geometrias externas/box)
//   Boundary: Prism Layer Mesher

import star.common.*;
import star.base.neo.*;
import star.meshing.*;
import star.prismmesher.*;
import star.resurfacer.*;
import star.dualmesher.*;
import star.trimmer.*;

import java.util.*;

public class ConfigurarMalha extends StarMacro {

    // =========================================================
    // PARAMETROS DE MALHA — Misturador Estatico 18''
    // =========================================================
    // Diametro interno do tubo [m]
    static final double D_TUBO_M = 0.4445;

    // Tamanho base: 5% do diametro = ~22 mm
    // (bom equilibrio resolucao/custo para Re > 100.000)
    static final double BASE_SIZE_M = D_TUBO_M * 0.05;

    // Tamanho minimo de superficie: 1.25% do diametro = ~5.5 mm
    // (necessario para capturar detalhes das bordas das aletas)
    static final double MIN_SURF_SIZE_PCT = 25.0;  // % do BASE_SIZE

    // Tamanho alvo de superficie: 100% do BASE_SIZE
    static final double TGT_SURF_SIZE_PCT = 100.0; // % do BASE_SIZE

    // Camadas prismaticas (boundary layer nas paredes)
    static final int    N_PRISMA     = 8;
    static final double PRISMA_PCT   = 30.0;  // 30% do BASE_SIZE = espessura total
    static final String PRISMA_GROW  = "Medium"; // razao de crescimento

    // Growth rates do volume
    static final String VOL_GROWTH   = "Medium";
    static final String SURF_GROWTH  = "Medium";

    // Nome da Part e da Regiao (deve coincidir com 01b_AssociarPartesRegioes)
    static final String NOME_PART   = "Fluid_Volume";
    static final String NOME_REGIAO = "Fluid";
    // =========================================================

    @Override
    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("=== CONFIGURANDO MALHA (AutomatedMesh) ===");
        sim.println(String.format("Base size: %.1f mm (%.0f%% de %.0f mm)",
                BASE_SIZE_M * 1000, 5.0, D_TUBO_M * 1000));

        // --- 1. Criar operacao AutomatedMesh ---
        AutoMeshOperation meshOp = criarAutomatedMesh(sim);
        if (meshOp == null) {
            sim.println("[ERRO] Nao foi possivel criar AutomatedMesh.");
            return;
        }

        // --- 2. Configurar tamanho base ---
        configurarTamanhoBase(sim, meshOp);

        // --- 3. Configurar Surface Remesher ---
        configurarSurfaceRemesher(sim, meshOp);

        // --- 4. Configurar Polyhedral Mesher ---
        configurarPolyhedralMesher(sim, meshOp);

        // --- 5. Configurar Prism Layer Mesher ---
        configurarPrismLayer(sim, meshOp);

        // --- 6. Criar refinamento volumetrico nas aletas ---
        criarRefinamentoAletas(sim, meshOp);

        sim.println("\n=== CONFIGURACAO DE MALHA COMPLETA ===");
        sim.println("Para gerar: botao direito em Automated Mesh > Execute");
        sim.println("            ou: Mesh > Generate Volume Mesh");
        sim.println("Celulas esperadas: ~2-5 milhoes");
        sim.println("Proximo passo: 03_ConfigurarFisica.java");
    }

    // =========================================================
    // 1. CRIAR AUTOMATED MESH OPERATION
    // =========================================================

    private AutoMeshOperation criarAutomatedMesh(Simulation sim) {
        try {
            // Verificar se ja existe
            for (MeshOperation op : sim.get(MeshOperationManager.class)
                    .getObjects()) {
                if (op instanceof AutoMeshOperation) {
                    sim.println("AutomatedMesh ja existe — reusando.");
                    return (AutoMeshOperation) op;
                }
            }

            // Localizar Part
            GeometryPart part = null;
            try {
                part = sim.getGeometryPartManager().getPart(NOME_PART);
            } catch (Exception e) {
                // Usar primeira Part disponivel
                Collection<GeometryPart> parts = sim.getGeometryPartManager().getParts();
                if (!parts.isEmpty()) {
                    part = parts.iterator().next();
                    sim.println("[AVISO] Part '" + NOME_PART
                            + "' nao encontrada. Usando: "
                            + part.getPresentationName());
                }
            }
            if (part == null) {
                sim.println("[ERRO] Nenhuma Part encontrada na simulacao.");
                return null;
            }

            // Criar operacao com os tres meshers
            // Caminho equivalente no GUI:
            //   Geometry > Operations > New > Mesh > Automated Mesh
            //   Parts: [NOME_PART]
            //   Meshers: Surface Remesher + Polyhedral Mesher + Prism Layer Mesher
            AutoMeshOperation meshOp = (AutoMeshOperation)
                    sim.get(MeshOperationManager.class).createAutoMeshOperation(
                            new StringVector(new String[]{
                                    "star.resurfacer.ResurfacerAutoMesher",    // Surface Remesher
                                    "star.dualmesher.DualAutoMesher",          // Polyhedral Mesher
                                    "star.prismmesher.PrismAutoMesher"         // Prism Layer Mesher
                            }),
                            new NeoObjectVector(new Object[]{part})
                    );
            meshOp.setPresentationName("Automated Mesh - Misturador");
            sim.println("AutomatedMesh criado com 3 meshers.");
            return meshOp;

        } catch (Exception e) {
            sim.println("[ERRO] Criando AutomatedMesh: " + e.getMessage());
            sim.println("       Criar manualmente: Geometry > Operations > "
                      + "New > Mesh > Automated Mesh");
            return null;
        }
    }

    // =========================================================
    // 2. TAMANHO BASE (Default Controls)
    // =========================================================

    private void configurarTamanhoBase(Simulation sim, AutoMeshOperation meshOp) {
        try {
            // Operations > Automated Mesh > Default Controls > Base Size
            meshOp.getDefaultControls().getBaseSize()
                    .getValue().setValue(BASE_SIZE_M);
            sim.println(String.format("Base Size: %.2f m (%.1f mm)",
                    BASE_SIZE_M, BASE_SIZE_M * 1000));
        } catch (Exception e) {
            sim.println("[AVISO] Base Size: " + e.getMessage());
        }

        try {
            // Volume Growth Rate: Medium
            meshOp.getDefaultControls().getVolumeGrowthRate()
                    .setSelectedElement(VOL_GROWTH);
            // Surface Growth Rate: Medium
            meshOp.getDefaultControls().getSurfaceGrowthRate()
                    .setSelectedElement(SURF_GROWTH);
            sim.println("Growth rates: Volume=" + VOL_GROWTH
                    + ", Surface=" + SURF_GROWTH);
        } catch (Exception e) {
            sim.println("[AVISO] Growth rates: " + e.getMessage());
        }
    }

    // =========================================================
    // 3. SURFACE REMESHER
    // =========================================================

    private void configurarSurfaceRemesher(Simulation sim,
                                            AutoMeshOperation meshOp) {
        try {
            ResurfacerAutoMesher remesher = meshOp.getMeshers()
                    .query(ResurfacerAutoMesher.class);

            // Tamanho minimo: 25% do base (~5.5 mm)
            remesher.getDefaultMinimumSize()
                    .getRelativeOrAbsoluteSize()
                    .setRelativeSize(MIN_SURF_SIZE_PCT);

            // Tamanho alvo: 100% do base (~22 mm)
            remesher.getDefaultTargetSize()
                    .getRelativeOrAbsoluteSize()
                    .setRelativeSize(TGT_SURF_SIZE_PCT);

            sim.println(String.format(
                    "Surface Remesher: min=%.0f%% (%.1fmm), target=%.0f%% (%.1fmm)",
                    MIN_SURF_SIZE_PCT, BASE_SIZE_M * MIN_SURF_SIZE_PCT / 100 * 1000,
                    TGT_SURF_SIZE_PCT, BASE_SIZE_M * TGT_SURF_SIZE_PCT / 100 * 1000));
        } catch (Exception e) {
            sim.println("[AVISO] Surface Remesher: " + e.getMessage());
        }
    }

    // =========================================================
    // 4. POLYHEDRAL MESHER
    // =========================================================

    private void configurarPolyhedralMesher(Simulation sim,
                                             AutoMeshOperation meshOp) {
        try {
            DualAutoMesher polyMesher = meshOp.getMeshers()
                    .query(DualAutoMesher.class);
            // O tamanho de celula do volume e controlado pelo Base Size
            // Configuracoes adicionais ficam nos Default Controls
            sim.println("Polyhedral Mesher: ativo (tamanho via Base Size)");
        } catch (Exception e) {
            sim.println("[AVISO] Polyhedral Mesher: " + e.getMessage());
        }
    }

    // =========================================================
    // 5. PRISM LAYER MESHER
    // =========================================================

    private void configurarPrismLayer(Simulation sim,
                                       AutoMeshOperation meshOp) {
        try {
            PrismAutoMesher prismMesher = meshOp.getMeshers()
                    .query(PrismAutoMesher.class);

            // Numero de camadas
            prismMesher.setNumLayers(N_PRISMA);

            // Espessura total: 30% do BASE_SIZE
            // Operations > Default Controls > Prism Layer Controls >
            //              Prism Layer Total Thickness > Percentage of Base
            meshOp.getDefaultControls()
                    .get(PrismLayerParameters.class)
                    .getPrismThickness()
                    .getRelativeOrAbsoluteSize()
                    .setRelativeSize(PRISMA_PCT);

            // Growth rate do prism
            meshOp.getDefaultControls()
                    .get(PrismLayerParameters.class)
                    .getStretching()
                    .getGrowthRate()
                    .setSelectedElement(PRISMA_GROW);

            sim.println(String.format(
                    "Prism Layer: %d camadas, espessura=%.0f%% de base (%.2fmm)",
                    N_PRISMA, PRISMA_PCT, BASE_SIZE_M * PRISMA_PCT / 100 * 1000));

        } catch (Exception e) {
            sim.println("[AVISO] Prism Layer: " + e.getMessage());
            sim.println("        Configurar manualmente: Default Controls > "
                      + "Prism Layer Controls");
        }
    }

    // =========================================================
    // 6. REFINAMENTO NAS ALETAS (Volumetric Control)
    // =========================================================

    private void criarRefinamentoAletas(Simulation sim,
                                         AutoMeshOperation meshOp) {
        // Cria um controle volumetrico com tamanho menor na regiao das aletas
        // (cilindro central de L=1600mm onde as aletas estao)
        try {
            VolumetricMeshControl volControl = meshOp.getVolumetricControls()
                    .createVolumetricControl();
            volControl.setPresentationName("Refinamento_Aletas");

            // Tamanho: 25% do BASE_SIZE (~5.5 mm) — captura geometria das aletas
            volControl.getCustomConditions()
                    .get(VolumetricMeshSizeCondition.class)
                    .getSizeOption()
                    .setSelected(VolumetricMeshSizeOption.Type.RELATIVE_TO_BASE);
            volControl.getCustomValues()
                    .get(VolumetricMeshSizeValue.class)
                    .getRelativeOrAbsoluteSize()
                    .setRelativeSize(REFINO_ALETAS_PCT);

            sim.println(String.format(
                    "Refinamento aletas: %.0f%% do base (%.1fmm)",
                    REFINO_ALETAS_PCT, BASE_SIZE_M * REFINO_ALETAS_PCT / 100 * 1000));
            sim.println("[INFO] Associar este controle a uma Shape (cilindro) "
                      + "centrado na secao das aletas (L=1600mm).");

        } catch (Exception e) {
            sim.println("[AVISO] Refinamento volumetrico: " + e.getMessage());
            sim.println("        Criar manualmente em Default Controls > "
                      + "Add > Volumetric Control");
        }
    }

    // Constante adicional para refinamento
    static final double REFINO_ALETAS_PCT = 25.0; // 25% do BASE_SIZE
}
