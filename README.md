# KlinkPPI

KlinkPPI is a web application for exploring protein-protein interaction (PPI) data across multiple sources from one interface. It combines results from `STRING`, `CORUM`, `IntAct`, `BioGRID`, `HuRI`, and `Predictomes`, then lets users inspect and download the results in a `PSI-MI TAB 2.8`-compatible tab-delimited format or `Parquet`.

## Features

- Search by `UniProtKB`, `GeneID`, `Ensembl`, or `Gene Name`
- Filter queries by taxonomy ID
- Query one database or several at once
- Review results in separate sections by database
- Download selected results as `MI TAB`-compatible tab-delimited files or `Parquet`

## Examples

### Intro

![Search Bar](imgs/intro.png)

### Search

![Search Bar](imgs/search.png)

### Results

![Search Summary](imgs/search_summary.png)
![Sample Result 1](imgs/sample_result.png)

## Project Structure

- `backend/`: FastAPI backend
- `frontend/`: React + Vite frontend
- `Data/`: local database files used by several backend resolvers
- `../Supported_Organisms/`: taxonomy support tables for each source

## Prerequisites

- `Python 3.11+` recommended
- `Node.js 20.19+` or `22.12+`
- `npm`

`Node.js 18` is not sufficient for the current Vite version in this repository. For installing the new one: 

```bash
# 1. Download and run the install script
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.5/install.sh | bash

# 2. Load NVM into your current terminal session
# (Try bashrc first; if you use zsh, replace with ~/.zshrc)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 3. Verify installation
nvm --version
nvm install 20
nvm use 20
   
```

## Installation

Clone the repository and work from the project root:

```bash
git clone <your-repo-url>
cd KlinkPPI
```

Install the backend and frontend dependencies from the project root:

```bash
npm install
```

This creates `.venv/`, installs `requirements.txt`, and installs the frontend npm packages.

## Running the Application

Start both the FastAPI backend and Vite frontend from one terminal:

```bash
npm run dev
```

Then open:

```text
http://localhost:5174
```

## Notes

- The frontend is configured to connect with to the backend at `http://127.0.0.1:8000`.
- The backend CORS configuration currently allows `http://localhost:5174`.
- Several backend resolvers call external services such as UniProt, Ensembl, STRING, and IntAct, so an internet connection is required for full functionality.
- If `npm run dev` or `npm run build` fails after switching Node versions, remove stale dependencies and reinstall with `npm install`.
- MITAB exports use shared core columns for all selected databases. The `Source database(s)` field uses verified PSI-MI source terms where available: `psi-mi:"MI:1014"(string)`, `psi-mi:"MI:0463"(biogrid)`, and `psi-mi:"MI:0469"(intact)`. Sources without verified PSI-MI database terms are exported as `corum`, `huri`, and `predictomes`.

## API Endpoints

- `GET /search`
- `POST /mitab`
- `POST /parquet`
