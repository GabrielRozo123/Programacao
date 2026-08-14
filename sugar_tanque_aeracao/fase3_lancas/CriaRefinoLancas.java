// CriaRefinoLancas.java — cria os 16 cilindros de refino dos injetores das lancas
// Fase 3 · Ito · aerador com 16 lancas
//
// Uso:  File -> Macro -> Play Macro...  e escolha este arquivo.
// APAGUE ANTES os Refino_Injetor_1/2/3 antigos: eles estao nas posicoes das
// 3 lancas originais (r = 305 mm, ponta em z = -5.2465), que nao existem mais.
//
// Cada cilindro cobre 350 mm abaixo e 150 mm acima do disco do injetor,
// com raio 100 mm (~3,2x o raio da lanca). Total 0,2513 m3 = 1,26% do dominio.

package macro;

import java.util.*;
import star.common.*;
import star.base.neo.*;
import star.meshing.*;

public class CriaRefinoLancas extends StarMacro {

    public void execute() {
        Simulation sim = getActiveSimulation();
        Units m = sim.getUnitsManager().getPreferredUnits(
            new IntVector(new int[] {0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0}));

        cria(sim, m, "refino_lanca_01", 0.575000, -0.440000, -5.8000, -5.3000, 0.1);
        cria(sim, m, "refino_lanca_02", 0.315881, -0.083354, -5.8000, -5.3000, 0.1);
        cria(sim, m, "refino_lanca_03", -0.103381, -0.219581, -5.8000, -5.3000, 0.1);
        cria(sim, m, "refino_lanca_04", -0.103381, -0.660419, -5.8000, -5.3000, 0.1);
        cria(sim, m, "refino_lanca_05", 0.315881, -0.796646, -5.8000, -5.3000, 0.1);
        cria(sim, m, "refino_lanca_06", 0.938810, -0.223066, -5.0100, -4.5100, 0.1);
        cria(sim, m, "refino_lanca_07", 0.704243, 0.141927, -5.0100, -4.5100, 0.1);
        cria(sim, m, "refino_lanca_08", 0.309582, 0.322163, -5.0100, -4.5100, 0.1);
        cria(sim, m, "refino_lanca_09", -0.119870, 0.260417, -5.0100, -4.5100, 0.1);
        cria(sim, m, "refino_lanca_10", -0.447765, -0.023707, -5.0100, -4.5100, 0.1);
        cria(sim, m, "refino_lanca_11", -0.570000, -0.440000, -5.0100, -4.5100, 0.1);
        cria(sim, m, "refino_lanca_12", -0.447765, -0.856293, -5.0100, -4.5100, 0.1);
        cria(sim, m, "refino_lanca_13", -0.119870, -1.140417, -5.0100, -4.5100, 0.1);
        cria(sim, m, "refino_lanca_14", 0.309582, -1.202163, -5.0100, -4.5100, 0.1);
        cria(sim, m, "refino_lanca_15", 0.704243, -1.021927, -5.0100, -4.5100, 0.1);
        cria(sim, m, "refino_lanca_16", 0.938810, -0.656934, -5.0100, -4.5100, 0.1);

        sim.println("refino_lanca_01..16 criados.");
    }

    private void cria(Simulation sim, Units m, String nome,
                      double x, double y, double z0, double z1, double raio) {

        MeshPartFactory f = sim.get(MeshPartFactory.class);
        SimpleCylinderPart c = f.createNewCylinderPart(sim.get(SimulationPartManager.class));
        c.setDoNotRetessellate(true);

        LabCoordinateSystem lab =
            sim.getCoordinateSystemManager().getLabCoordinateSystem();

        c.getStartCoordinate().setCoordinateSystem(lab);
        c.getStartCoordinate().setCoordinate(m, m, m,
            new DoubleVector(new double[] {x, y, z0}));

        c.getEndCoordinate().setCoordinateSystem(lab);
        c.getEndCoordinate().setCoordinate(m, m, m,
            new DoubleVector(new double[] {x, y, z1}));

        c.getRadius().setUnits(m);
        c.getRadius().setValue(raio);

        c.getTessellationDensityOption().setSelected(TessellationDensityOption.Type.MEDIUM);
        c.rebuildSimpleShapePart();
        c.setDoNotRetessellate(false);
        c.setPresentationName(nome);
    }
}
