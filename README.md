# xflow-loenngennemsigtighed
[**Formål**](#formål) | [**Beskrivelse**](#beskrivelse) | [**Features**](#features) | [**Afhængigheder**](#afh%C3%A6ngigheder)

# Formål

A Flask application.

## Beskrivelse

*Kommer senere ..*

<!--
Detaljeret beskrivelse af den proces som løsningen varetager.
Procesbeskrivelsen opdeles i sektioner hvis løsningen varetager forskellige processer eller flere subprocesser.
Dette afsnit kan erstattes af `## Features`-afsnittet, hvis løsningen er et system frem for en automatiseret proces.
-->

## Features

*Kommer senere ..*

<!--
Beskrivelse af applikationens features. Dette afsnit bør kun inkluderes hvis løsningen er et system, eller varetager flere processer.
-->

## Afhængigheder

<!--
Henvisninger til applikationens afhængigheder, kategoriseret og med links til officielle websites.
-->

:cloud: | API'er, FTP-servere, CDN'er andre online services som applikationen kommunikerer med.

*TBD ..*

:heavy_dollar_sign: | Miljøvariabler som forventes at være populeret.

*TBD ..*

## Udvikling

<!--
Beskrivelse af hvordan løsningen startes lokalt.
Overblik over eventuelle API endpoints som løsningen udstiller.
Notering af eventuelle hard-codede værdier, og hvordan værdierne kan ændres.
-->

### Lokal udvikling

1) Opret et virtuelt miljø:

    *Linux/macOS*:

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

    *Windows (PowerShell)*:

    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

2) Installér dependencies:

    ```bash
    pip install -r requirements.txt -r requirements-dev.txt 
    ```

3) Opret din `.env` (hvis denne mangler)

    Kopiér eksempel-filen, og redigér værdier efter behov.

    ```bash
    cp .env.example .env
    ```

    Bemærk:

    - `.env` ignoreres af git.
    - Hvis du tilføjer nye miljøvariabler, skal du også tilføje dem i `src/utils/config.py`.

4) Kør applikationen:

    ```bash
    python src/main.py
    ```

### Docker (gunicorn)

Applikationen benytter Docker via `Dockerfile`, som kører applikationen med gunicorn.

Byg og kør applikationen:

```bash
docker build -t xflow_loenngennemsigtighed:local .
docker run --rm -p 8080:8080 -e FLASK_ENV=prod -e PORT=8080 xflow_loenngennemsigtighed:local
```

Kør applikationen med compose:

```bash
docker compose up
```

### Formatering, linting, test

Organisér imports med iSort:

```bash
isort .
```

Formatér kode, så den overholder PEP 8 med Autopep8:

```bash
autopep8 .
```

Kør linting med Flake8:

```bash
flake8
```

Kør tests med Pytest:

```bash
pytest
```