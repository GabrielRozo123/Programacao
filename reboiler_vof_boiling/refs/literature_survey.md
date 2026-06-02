# Literatura — Reboiler VOF+Boiling CFD

## 1. Correlações Fundamentais de Ebulição

### Rohsenow, W.M. (1952)
**A Method of Correlating Heat Transfer Data for Surface Boiling of Liquids**  
*Trans. ASME, 74, 969–976*  
Correlação original de ebulição nucleada em pool. Base de validação para o modelo RPI.

### Chen, J.C. (1966)
**Correlation for Boiling Heat Transfer to Saturated Fluids in Convective Flow**  
*I&EC Process Des. Dev., 5(3), 322–329*  
DOI: 10.1021/i260019a023  
Combinação de ebulição nucleada + convecção forçada (flow boiling).

### Fritz, W. (1935)
**Berechnung des Maximalvolumens von Dampfblasen** (cálculo do volume máximo de bolhas)  
*Physikalische Zeitschrift, 36, 379–384*  
Correlação para diâmetro de departura de bolha (R_db). Ainda usada no modelo RPI.

### Kutateladze, S.S. (1951)
**A hydrodynamic theory of changes in boiling process under free convection**  
*Izvestia Akademii Nauk SSSR, Otdelenie Tekhnicheskikh Nauk, 4, 529*  
Correlação para flux crítico (CHF) em pool boiling — ponto DNB.

---

## 2. Modelos CFD de Ebulição em Pool

### Raj, R., Kim, J., McQuillen, J. (2012)
**Subcooled and Saturated Nucleate Pool Boiling in Variable Gravity Environments**  
*J. Heat Transfer, 134(1), 011502*  
DOI: 10.1115/1.4004840  
Validação experimental de VOF + modelo RPI.

### Stephan, P., Busse, C.A. (1992)
**Analysis of the heat transfer coefficient of grooved heat pipe evaporator walls**  
*Int. J. Heat Mass Transfer, 35(2), 383–391*  
DOI: 10.1016/0017-9310(92)90276-X  
Modelagem de microregião de ebulição na base da bolha.

### Colombo, M., Fairweather, M. (2015)
**Accuracy of Eulerian-Eulerian, two-fluid CFD boiling models of subcooled boiling flows**  
*Int. J. Heat Mass Transfer, 85, 881–895*  
DOI: 10.1016/j.ijheatmasstransfer.2015.02.030  
Avaliação sistemática do modelo RPI (Wall Heat Flux Partitioning).

### Krepper, E., Končar, B., Egorov, Y. (2007)
**CFD modelling of subcooled boiling — Concept, validation and application to fuel assembly design**  
*Nucl. Eng. Des., 237(7), 716–731*  
DOI: 10.1016/j.nucengdes.2006.10.023  
Implementação RPI no ANSYS CFX — parâmetros e calibração.

---

## 3. VOF para Ebulição em Pool

### Welch, S.W.J., Wilson, J. (2000)
**A Volume of Fluid Based Method for Fluid Flows with Phase Change**  
*J. Comput. Phys., 160(2), 662–682*  
DOI: 10.1006/jcph.2000.6481  
Método VOF com transferência de massa por mudança de fase (condensação/ebulição).

### Kunkelmann, C., Stephan, P. (2009)
**CFD Simulation of Boiling Flows Using the Volume-of-Fluid Method**  
*Numerical Heat Transfer Part A, 56(8), 631–646*  
DOI: 10.1080/10407780903423908  
VOF + transferência de calor para ebulição nucleada individual de bolha.

---

## 4. Propriedades de n-Pentano e Hidrocarbonetos

### NIST WebBook — n-Pentane (C₅H₁₂)
URL: https://webbook.nist.gov/cgi/cbook.cgi?ID=C109660&Type=SATPROPS&Digits=5  
Propriedades saturadas de 1 a 5 bar.

### Pioro, I.L. (2004)
**Experimental data on nucleate pool-boiling heat transfer and burnout**  
*Can. J. Chem. Eng., 82(3), 454–461*  
DOI: 10.1002/cjce.5450820305  
Parâmetros C_sf e θ_contact para hidrocarbonetos em diferentes superfícies.

### Mostinski, I.L. (1963)
**Application of the rule of corresponding states for calculation of heat transfer and CCT**  
*Teploenergetika, 4, 66*  
Correlação reduzida universal para pool boiling de hidrocarbonetos.

---

## 5. Projeto de Reboilers (Referências de Engenharia)

### Perry's Chemical Engineers' Handbook (8th ed., 2008)
**Section 11: Heat-Transfer Equipment**  
*McGraw-Hill, New York*  
Projeto de kettle reboilers: formulação de Mostinski, parâmetros típicos.

### Hewitt, G.F., Shires, G.L., Bott, T.R. (1994)
**Process Heat Transfer**  
*CRC Press, Boca Raton*  
ISBN: 978-0849399589  
Referência padrão de projeto de trocadores industriais.

### Kern, D.Q. (1950)
**Process Heat Transfer**  
*McGraw-Hill*  
ISBN clássico — projeto de reboilers e evaporadores, correlações práticas.

### TEMA (2007)
**Standards of the Tubular Exchanger Manufacturers Association (9th ed.)**  
*TEMA, New York*  
Padrões de projeto, materiais e nomenclatura TEMA K (kettle reboilers).

---

## 6. Aplicações Industriais e Segurança

### Bhatt, B.I., Vora, S.M. (2004)
**Stoichiometry (4th ed.)**  
*Tata McGraw-Hill*  
Contexto de destilação de nafta e reboilers em refinarias.

### API Standard 521 (2014)
**Pressure-relieving and Depressuring Systems (6th ed.)**  
*American Petroleum Institute*  
Calor absorvido por reboilers em cenário de fire case — input para HAZOP.
