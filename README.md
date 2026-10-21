# API – XFlow Løngennemsigtighed
[**Formål**](#formål) | [**Beskrivelse**](#beskrivelse) | [**Afhængigheder**](#afhængigheder)

## Formål

Applikationen modtager en medarbejders CPR-nummer, en rapportdato og en e-mailadresse fra XFlow via et HTTP-endpoint. Den henter en Excel-rapport om løngennemsigtighed for den valgte måned. Månedslønnede modtager Excel-rapporten som vedhæftet fil og timelønnede modtager i stedet en besked uden bilag.

### Dataflow

XFlow (CPR, dato og e-mail) → løngennemsigtigheds-KRL-API (Excel-rapport) → filtrering af ark → SMTP (e-mail til adressen fra XFlow).

## Beskrivelse

Det primære flow ligger i `POST /api/xflow` i [src/api_endpoints.py](src/api_endpoints.py).

### Blanket og arbejdsgang i XFlow

- **Blanketskabelon:** `Løngennemsigtighed` skal aflevere CPR, dato for søgningen og e-mailadresse. CPR-feltet udfyldes automatisk, når brugeren tilgår blanketten med MitID, som er den eneste adgangsmulighed til blanketten. Brugeren angiver datoen og sin private mail adresse.
- **Arbejdsskabelon:** `Løngennemsigtighed` er knyttet til blanketskabelonen. Her styres blandt andet, om eksterne MitID-brugere må starte arbejdsgangen.
- **Flowdesign:** Dataafleveringen `Løngennemsigtighed` skal sende de udfyldte værdier til API'et som `cpr` (CPR uden bindestreg fra CPR-opslaget), `dato` (dato fra datofeltet) og `email` (modtagerens e-mailadresse). Datoen skal afleveres i formatet `DD-MM-YYYY`.


### Overordnet flow

1. Dataafleveringen fra XFlow sender JSON med `cpr`, `dato` (dato i formatet `DD-MM-YYYY`) og `email` til `POST /api/xflow`.
2. API'et kontrollerer felterne og datoformatet; ugyldigt input giver `400`.
3. KRL API'et hentes via `APIClient` fra `KRL_API_URL` med år, måned, CPR, API-nøgle og `excel=true` som forespørgselsparametre.
4. API'et kontrollerer `Medarbejdernummer` i Q2 og læser nummeret i Q3 på hvert ark. Ark Sheets med numre, der begynder med 7, 8 eller 9, fjernes fra vedhæftningen. Hvis alle ark er timelønnede, sendes en mail uden bilag om, at løsningen kun er beregnet til månedslønnede. Ellers sendes de resterende ark som Excel-fil med navnet `Loenngennemsigtighed_YYYY-MM.xlsx`. Begge mails har emnet `Løngennemsigtighed YYYY-MM`.
5. Hvis Excel-downloadet ikke er en gyldig projektmappe, mangler `xl/workbook.xml`, har ugyldig XML eller mangler medarbejdernumre, svarer API'et med `400` uden at sende en mail. Fejlloggen indeholder ikke rapportens indhold.

## Afhængigheder

### :heavy_dollar_sign: Miljøvariabler

Applikationen læser variablerne i [src/utils/config.py](src/utils/config.py). En lokal `.env` indlæses, men overskriver ikke allerede angivne miljøvariabler.

#### **Generelle variabler**

| Navn | Default | Beskrivelse |
|---|---|---|
| `PORT` | `8080` | Port for Flask/Gunicorn |
| `DEBUG` | `False` | Aktiverer Flask debug og mere detaljeret logning ved `True` eller `true` |
| `POD_NAME` | `pod_name_not_set` | Label i readiness-metric |
| `XFLOW_MOCK_PAYLOAD` | Ikke sat | Ved `1` og aktiv Flask debug erstattes `cpr` med `TEST_CPR` og `dato` med `01-09-2026` og `email` med `TEST_EMAIL`  |
| `TEST_CPR` | Tom streng | CPR-nummer til den lokale mock-payload. Kun relevant sammen med `XFLOW_MOCK_PAYLOAD=1` |
| `TEST_EMAIL` | Tom streng | Email til den lokale mock-payload. Kun relevant sammen med `XFLOW_MOCK_PAYLOAD=1` |

#### **Løngennemsigtighed KRL API**

**Bitwarden-navn:** `KRL - Løngennemsigtighed Robot Bruger`

| Navn | Beskrivelse |
|---|---|
| `KRL_API_URL` | URL til API'et |
| `KRL_API_KEY` | API-nøgle til API'et |

#### **SMTP**

**Bitwarden-navn:** `Postkasse - Løngennemsigtighed`

| Navn | Beskrivelse |
|---|---|
| `SMTP_SERVER` | SMTP-server til afsendelse |
| `SMTP_SENDER` | Afsenderadresse |
| `SMTP_PASSWORD` | Adgangskode til SMTP |
| `REPLY_TO_EMAIL` | Svaradresse for udsendte e-mails |

### API endpoints

- `POST /api/xflow` – hent og send løngennemsigtighedsrapport

#### Eksempel: kald til `POST /api/xflow`

**Payload**:

```json
{
  "cpr": "0000000000",
  "dato": "01-10-2026",
  "email": "modtager@hotmail.com"
}
```
