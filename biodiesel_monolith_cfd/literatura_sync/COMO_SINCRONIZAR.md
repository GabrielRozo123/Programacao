# Como levar estes arquivos para o repositório Literatura

As ferramentas de GitHub desta sessão só alcançam o repositório `Programacao`.
Os arquivos desta pasta ficam versionados aqui e são copiados manualmente.

## Destino de cada arquivo

```
README.md                        →  raiz (SUBSTITUI o atual)
FASE3_resultados_CFD.md          →  06_Modelagem_e_Simulacao/
fig4_camada_limite_x49mm.pdf     →  06_Modelagem_e_Simulacao/figuras/
fig4_camada_limite_x49mm.png     →  06_Modelagem_e_Simulacao/figuras/
fig5_thiele_washcoat.pdf         →  06_Modelagem_e_Simulacao/figuras/
fig6_poiseuille_fase3.pdf        →  06_Modelagem_e_Simulacao/figuras/
perfil_camada_limite_x49mm.csv   →  06_Modelagem_e_Simulacao/dados/
perfil_velocidade_x49mm_raw.csv  →  06_Modelagem_e_Simulacao/dados/
```

> **Atenção ao README.** O da raiz do Literatura ainda traz, no Mapa Conceitual,
> três conclusões da Fase 2 que a Fase 3 derrubou: `δ_c ≈ 22 µm`, `regime MTL` e
> o auto-enriquecimento de metanol na parede. A versão nova corrige as três,
> estende o mapa até a Fase 3 e registra as correções numa seção própria, para
> que não voltem a circular. **Substitua o arquivo, não faça merge.**

## PowerShell, a partir de C:\Users\User\Literatura

Ajuste `$origem` para onde estiver o clone do repositório `Programacao`.

```powershell
cd C:\Users\User\Literatura
$origem = "C:\Users\User\Programacao\biodiesel_monolith_cfd\literatura_sync"

New-Item -ItemType Directory -Force -Path 06_Modelagem_e_Simulacao\figuras, 06_Modelagem_e_Simulacao\dados

Copy-Item "$origem\README.md" .
Copy-Item "$origem\FASE3_resultados_CFD.md" 06_Modelagem_e_Simulacao\
Copy-Item "$origem\*.pdf" 06_Modelagem_e_Simulacao\figuras\
Copy-Item "$origem\*.png" 06_Modelagem_e_Simulacao\figuras\
Copy-Item "$origem\*.csv" 06_Modelagem_e_Simulacao\dados\

git add -A
git commit -m "Fase 3 concluida: Da = 0,76, regime misto, X_TG = 1,40 porcento"
git push origin main
```

## Depois de copiar

Nada. O `README.md` novo já está atualizado com a Fase 3, com a tabela de
referências estendida e com a seção de correções.
