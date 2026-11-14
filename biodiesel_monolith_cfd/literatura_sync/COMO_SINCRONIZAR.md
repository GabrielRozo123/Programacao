# Como levar estes arquivos para o repositório Literatura

As ferramentas de GitHub desta sessão só alcançam o repositório `Programacao`.
Os arquivos desta pasta ficam versionados aqui e são copiados manualmente.

## Destino de cada arquivo

```
FASE3_resultados_CFD.md         →  raiz do repositório Literatura
fig4_camada_limite_x49mm.pdf    →  06_Modelagem_e_Simulacao/figuras/
fig4_camada_limite_x49mm.png    →  06_Modelagem_e_Simulacao/figuras/
perfil_camada_limite_x49mm.csv  →  06_Modelagem_e_Simulacao/dados/
```

## PowerShell, a partir de C:\Users\User\Literatura

Ajuste `$origem` para onde estiver o clone do repositório `Programacao`.

```powershell
cd C:\Users\User\Literatura
$origem = "C:\Users\User\Programacao\biodiesel_monolith_cfd\literatura_sync"

New-Item -ItemType Directory -Force -Path 06_Modelagem_e_Simulacao\figuras, 06_Modelagem_e_Simulacao\dados

Copy-Item "$origem\FASE3_resultados_CFD.md" .
Copy-Item "$origem\fig4_camada_limite_x49mm.pdf" 06_Modelagem_e_Simulacao\figuras\
Copy-Item "$origem\fig4_camada_limite_x49mm.png" 06_Modelagem_e_Simulacao\figuras\
Copy-Item "$origem\perfil_camada_limite_x49mm.csv" 06_Modelagem_e_Simulacao\dados\

git add -A
git commit -m "Fase 3 concluida: Da = 0,74, regime misto, X_TG = 1,42 porcento"
git push origin main
```

## Depois de copiar

Atualizar à mão, no `README.md` da raiz do Literatura, a linha de status da
Fase 3 e o link para `FASE3_resultados_CFD.md`, no mesmo padrão das Fases 1 e 2.
