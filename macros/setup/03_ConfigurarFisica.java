// Macro Star-CCM+: Configura modelos fisicos e condicoes de contorno
// Misturador Estatico 18'' - Clarificacao de Xarope
// Tres fluidos: caldo + polimero + fluido auxiliar
// Executar apos 02_ConfigurarMalha.java

import star.common.*;
import star.base.neo.*;
import star.flow.*;
import star.material.*;
import star.turbulence.*;
import star.kwturb.*;
import star.passivescalar.*;
import star.segregatedflow.*;
import star.metrics.*;
import star.vis.*;

import java.util.*;

public class ConfigurarFisica extends StarMacro {

    // =========================================================
    // PROPRIEDADES DOS FLUIDOS
    // =========================================================

    // --- CALDO (fluido principal) ---
    // ATENCAO: confirmar unidades de densidade com equipe
    // Atualmente usando 1050 kg/m3 como estimativa para caldo de cana
    // Ajustar apos confirmacao
    static final double CALDO_DENSIDADE_KGM3  = 1050.0;  // [kg/m3] - CONFIRMAR
    static final double CALDO_VISCOSIDADE_PAS  = 0.001;   // [Pa.s] = 1 cP

    // --- POLIMERO ANIONICO ---
    static final double POLIMERO_VISCOSIDADE_PAS = 0.040; // [Pa.s] = 40 cP
    static final double POLIMERO_DENSIDADE_KGM3  =
            CALDO_DENSIDADE_KGM3 * 1.35;                  // 35% maior que caldo

    // --- FLUIDO AUXILIAR ---
    static final double FLUAUX_VISCOSIDADE_PAS = 0.040;   // [Pa.s] = 40 cP
    static final double FLUAUX_DENSIDADE_KGM3  =
            CALDO_DENSIDADE_KGM3 * 1.35;                  // 35% maior que caldo

    // =========================================================
    // CONDICOES DE OPERACAO
    // =========================================================
    // IMPORTANTE: ajustar apos receber dados de vazao da equipe
    static final double VELOCIDADE_ENTRADA_MS   = 1.0;    // [m/s] - CONFIRMAR
    static final double TEMPERATURA_OPERACAO_C  = 25.0;   // [C]
    static final double PRESSAO_REFERENCIA_PA   = 101325.0; // [Pa] atmosferica

    // Fracao masssica do polimero na corrente de entrada
    // (polimero e injetado em ponto separado - co-corrente ou dupla corrente)
    static final double FRACAO_POLIMERO_INLET   = 0.05;   // 5% - CONFIRMAR

    // =========================================================
    // MODELO DE TURBULENCIA
    // =========================================================
    // k-omega SST recomendado para escoamentos com separacao e recirculacao
    // tipicos em misturadores estaticos
    static final String MODELO_TURBULENCIA = "K-Omega SST";

    // =========================================================

    @Override
    public void execute() {
        Simulation sim = getActiveSimulation();
        sim.println("=== CONFIGURANDO FISICA ===");

        // Obter regiao fluida
        Region regiao;
        try {
            regiao = sim.getRegionManager().getRegion("Fluid");
        } catch (Exception e) {
            sim.println("[ERRO] Regiao 'Fluid' nao encontrada. Verificar nome da regiao.");
            return;
        }

        PhysicsContinuum fisica = (PhysicsContinuum) sim
                .getContinuumManager().getContinuum("Physics 1");

        // --- 1. Modelos de escoamento ---
        fisica.enable(ThreeDimensionalModel.class);
        fisica.enable(SteadyModel.class);                // Regime permanente
        fisica.enable(SingleComponentLiquidModel.class);
        fisica.enable(SegregatedFlowModel.class);
        fisica.enable(ConstantDensityModel.class);

        // --- 2. Turbulencia: k-omega SST ---
        fisica.enable(TurbulentModel.class);
        fisica.enable(RansTurbulenceModel.class);
        fisica.enable(KOmegaTurbulence.class);
        fisica.enable(SstKwTurbModel.class);
        sim.println("Modelo: " + MODELO_TURBULENCIA);

        // --- 3. Escalar passivo para tracking de mistura ---
        // Usa-se escalar passivo (valor 0=caldo puro, 1=polimero puro)
        // para avaliar eficiencia de mistura sem resolver multicomponentes
        fisica.enable(PassiveScalarModel.class);
        PassiveScalarModel psm = fisica.getModelManager()
                .getModel(PassiveScalarModel.class);
        PassiveScalarMaterial ps = psm.getPassiveScalarManager()
                .createPassiveScalar();
        ps.setPresentationName("Polimero");
        ps.getLowerBound().setValue(0.0);  // caldo puro
        ps.getUpperBound().setValue(1.0);  // polimero puro
        sim.println("Escalar passivo 'Polimero' criado (0=caldo, 1=polimero).");

        // --- 4. Propriedades do fluido (mistura - usar propriedades do caldo) ---
        SingleComponentLiquidModel liquidModel = fisica.getModelManager()
                .getModel(SingleComponentLiquidModel.class);
        Liquid liquido = (Liquid) liquidModel.getMaterial();

        ConstantMaterialPropertyMethod densidade = (ConstantMaterialPropertyMethod)
                liquido.getMaterialProperties().getMaterialProperty(ConstantDensityProperty.class)
                        .getMethod();
        densidade.getQuantity().setValue(CALDO_DENSIDADE_KGM3);

        ConstantMaterialPropertyMethod viscosidade = (ConstantMaterialPropertyMethod)
                liquido.getMaterialProperties().getMaterialProperty(DynamicViscosityProperty.class)
                        .getMethod();
        viscosidade.getQuantity().setValue(CALDO_VISCOSIDADE_PAS);

        sim.println(String.format("Fluido (caldo): rho=%.1f kg/m3, mu=%.4f Pa.s",
                CALDO_DENSIDADE_KGM3, CALDO_VISCOSIDADE_PAS));

        // --- 5. Condicoes de contorno ---
        configurarCondicoes(sim, regiao, fisica);

        // --- 6. Criterios de convergencia ---
        configurarConvergencia(sim);

        sim.println("=== FISICA CONFIGURADA ===");
        sim.println("Propriedades a confirmar com a equipe:");
        sim.println("  - Densidade do caldo: " + CALDO_DENSIDADE_KGM3 + " kg/m3");
        sim.println("  - Vazao na entrada: " + VELOCIDADE_ENTRADA_MS + " m/s");
        sim.println("  - Fracao do polimero: " + (FRACAO_POLIMERO_INLET * 100) + "%");
    }

    private void configurarCondicoes(Simulation sim, Region regiao,
                                     PhysicsContinuum fisica) {
        sim.println("Configurando condicoes de contorno...");

        try {
            // Entrada principal (caldo)
            Boundary inlet = regiao.getBoundaryManager().getBoundary("Inlet");
            inlet.setBoundaryType(VelocityInletProfile.class);
            VelocityMagnitudeProfile velProfile = inlet.getValues()
                    .get(VelocityMagnitudeProfile.class);
            velProfile.getMethod(ConstantScalarProfileMethod.class)
                    .getQuantity().setValue(VELOCIDADE_ENTRADA_MS);

            // Configurar escalar passivo na entrada: caldo puro = 0
            PassiveScalarProfile psInlet = inlet.getValues()
                    .get(PassiveScalarProfile.class);
            psInlet.getMethod(ConstantScalarProfileMethod.class)
                    .getQuantity().setValue(0.0);
            sim.println("Inlet configurado: V=" + VELOCIDADE_ENTRADA_MS + " m/s, escalar=0 (caldo)");

            // Saida (pressao)
            Boundary outlet = regiao.getBoundaryManager().getBoundary("Outlet");
            outlet.setBoundaryType(PressureOutletProfile.class);
            sim.println("Outlet configurado: pressao estatica = 0 Pa (referencia)");

            // Entrada do polimero (co-corrente / dupla corrente)
            // NOTA: o ponto de injecao do polimero precisa ser identificado
            // na geometria importada e nomeado "Inlet_Polimero"
            try {
                Boundary inletPoli = regiao.getBoundaryManager()
                        .getBoundary("Inlet_Polimero");
                inletPoli.setBoundaryType(VelocityInletProfile.class);
                PassiveScalarProfile psInletPoli = inletPoli.getValues()
                        .get(PassiveScalarProfile.class);
                psInletPoli.getMethod(ConstantScalarProfileMethod.class)
                        .getQuantity().setValue(1.0); // polimero puro = 1
                sim.println("Inlet_Polimero configurado: escalar=1 (polimero puro)");
            } catch (Exception ex) {
                sim.println("[AVISO] Boundary 'Inlet_Polimero' nao encontrado.");
                sim.println("        Criar manualmente o inlet de injecao do polimero.");
            }

        } catch (Exception e) {
            sim.println("[AVISO] Boundaries 'Inlet'/'Outlet' nao encontrados automaticamente.");
            sim.println("        Configurar manualmente apos identificar as faces na geometria.");
        }
    }

    private void configurarConvergencia(Simulation sim) {
        // Reduzir residuos para 1e-5 (adequado para misturadores)
        ResidualMonitor[] monitores = new ResidualMonitor[]{
                (ResidualMonitor) sim.getMonitorManager().getMonitor("Continuity"),
                (ResidualMonitor) sim.getMonitorManager().getMonitor("X-momentum"),
                (ResidualMonitor) sim.getMonitorManager().getMonitor("Y-momentum"),
                (ResidualMonitor) sim.getMonitorManager().getMonitor("Z-momentum"),
        };
        for (ResidualMonitor m : monitores) {
            try { m.getNormalizedResidual().setValue(1.0e-5); } catch (Exception ex) {}
        }

        // Numero de iteracoes
        sim.getSolverManager().getSolver(SegregatedFlowSolver.class)
                .getStoppingCriteria().setMaximumSteps(2000);

        sim.println("Convergencia: residuos < 1e-5, max 2000 iteracoes.");
    }
}
