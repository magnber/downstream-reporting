# Saving the provided markdown content to a .md file
markdown_content = """
# Nedstrømsrapportering for NG Metall

Denne koden er utviklet for å beregne nedstrømsrapportering basert på NG Metalls data. NG Metall driver med resirkulering av metaller og materialer, og kjøper inn materialer fra leverandører (oppstrøms), behandler dem, og selger dem videre (nedstrøms). Formålet med programmet er å gi leverandørene innsikt i hva som skjer med materialene de leverer.

## Steg 1: Laste inn data

**Datainnhenting**: Programmet laster inn nødvendig data fra flere CSV-filer. Dette inkluderer informasjon om:
- Materialer
- Fasiliteter
- Materialtransformasjoner
- Utslippsfaktorer
- Transportavstander
- Andre relevante data

**Dataindeksering**: Etter innlasting organiseres dataene i oppslagsstrukturer (indekser) for raskere og enklere tilgang under beregningene.

## Steg 2: Behandle fakturaer

- **Fakturaliste**: Programmet tar inn en liste over fakturaer som representerer leveranser fra kunder til NG Metalls fasiliteter.
- **Iterasjon over fakturaer**: For hver faktura i listen utføres en serie beregninger for å produsere en resirkuleringsrapport.

## Steg 3: Beregne utgangsvolumer

- **Hente materialtransformasjoner**: For hvert mottatt materiale på en fasilitet hentes relevante transformasjoner som viser hvordan inngangsmaterialet blir til ulike utgangsmaterialer.
- **Beregne utgangsvolum**: Mengden av hvert utgangsmateriale beregnes ved å multiplisere det leverte volumet med prosentandelen for hver transformasjon.

## Steg 4: Beregne prosesseringsutslipp

- **Hente utslippsfaktor**: For hvert inngangsmateriale og fasilitet hentes en utslippsfaktor som representerer kg CO₂e per tonn behandlet.
- **Beregne totale prosesseringsutslipp**: Det totale utslippet fra prosesseringen beregnes ved å multiplisere det leverte volumet med utslippsfaktoren.
- **Fordele utslipp på utgangsmaterialer**: De totale prosesseringsutslippene fordeles proporsjonalt på hvert utgangsmateriale basert på deres respektive volumer.

## Steg 5: Beregne transportutslipp (oppstrøms)

- **Hente oppstrøms transportdata**: For hver kunde og fasilitet hentes gjennomsnittlig transportavstand og transportmodus.
- **Hente transportutslippsfaktor**: Basert på transportmodusen hentes en utslippsfaktor (kg CO₂e per tonn-km).
- **Beregne totale oppstrøms transportutslipp**: Utslippene beregnes ved å multiplisere det leverte volumet med avstanden og utslippsfaktoren.
- **Fordele utslipp på utgangsmaterialer**: De totale oppstrøms transportutslippene fordeles proporsjonalt på hvert utgangsmateriale.

## Steg 6: Beregne transportutslipp (nedstrøms) for materialgjenvinning

- **Identifisere materialer for gjenvinning**: Kun utgangsmaterialer kategorisert som "Material Recycling" behandles i dette steget.
- **Hente nedstrøms distribusjonsdata**: For hvert utgangsmateriale hentes estimert geografisk fordeling av hvor materialet selges (destinasjonsland) og prosentandel.
- **Hente nedstrøms transportdata**: For hver fasilitet og destinasjonsland hentes gjennomsnittlig transportavstand og transportmodus.
- **Beregne nedstrøms transportutslipp**: For hvert destinasjonsland beregnes utslippene ved å multiplisere volumet som sendes dit med avstanden og utslippsfaktoren for transportmodusen.
- **Samlede transportutslipp**: De oppstrøms og nedstrøms transportutslippene summeres for å få totale transportutslipp.

## Steg 7: Beregne produksjonsbenchmark

- **Hente benchmark-data**: For hvert utgangsmateriale hentes en benchmark for produksjonsutslipp (kg CO₂e per tonn) for jomfruelig materialproduksjon.
- **Beregne produksjonsutslipp**: Benchmark-utslippene beregnes ved å multiplisere volumet som sendes til hvert destinasjonsland med benchmark-utslippet.

## Steg 8: Generere resirkuleringsrapport

**Sammenstille data**: For hvert utgangsmateriale og destinasjonsland opprettes en rapport som inkluderer alle beregnede verdier:
- **Fakturadetaljer**: Faktura-ID, kunde-ID, leveringsdato, fasilitet, inngangsmateriale.
- **Materialdetaljer**: Utgangsmateriale, kategori, volum levert, utgangsvolum.
- **Utslippsdata**:
    - Prosesseringsutslipp
    - Transportutslipp (oppstrøms og nedstrøms)
    - Totale transportutslipp
    - Produksjonsbenchmark-utslipp
- **Destinasjonsdata**: Destinasjonsland og volum sendt dit.

**Lagre rapporten**: Rapportene konverteres til et passende format (for eksempel JSON) og lagres til en fil for videre bruk eller deling med kunder.

## Steg 9: Håndtere materialer uten nedstrøms utslipp

- **Energi gjenvinning og tap**: For utgangsmaterialer kategorisert som "Energy Recycling" eller "Losses" beregnes ikke nedstrøms transportutslipp eller produksjonsbenchmark.
- **Opprette rapporter**: For disse materialene opprettes rapporter som inkluderer relevante data, men med nedstrøms felter satt til null eller "N/A".
"""

