# KlinkPPI

KlinkPPI is a web application for exploring protein-protein interaction (PPI) data across multiple sources from one interface. It combines results from `STRING`, `CORUM`, `IntAct`, `BioGRID`, `HuRI`, and `Predictomes`, then lets users inspect and download the results in `PSI-MI TAB 2.8` or `Parquet` format.

## Features

- Search by `UniProtKB`, `GeneID`, `Ensembl`, or `Gene Name`
- Filter queries by taxonomy ID
- Query one database or several at once
- Review results in separate sections by database
- Download selected results as `MI TAB` or `Parquet`

## Screenshots

### Search

![Search Bar](screenshots_for_readme/search.png)

### Results

![Search Summary](screenshots_for_readme/search_summary.png)
![Sample Result 1](screenshots_for_readme/sample_result.png)
![Sample Result 2](screenshots_for_readme/sample_result_2.png)
![Data dne](screenshots_for_readme/dne.png)

### Downloads

![MI TAB](screenshots_for_readme/download_results.png)
![Parquet](screenshots_for_readme/download_results_2.png)
![Downloaded MI TAB](screenshots_for_readme/mitab.png)
![Downloaded Parquet](screenshots_for_readme/parquet.png)

## Project Structure

- `backend/`: FastAPI backend
- `frontend/`: React + Vite frontend
- `Data/`: local database files used by several backend resolvers
- `Supported_Organisms/`: taxonomy support tables for each source

## Prerequisites

- `Python 3.11+` recommended
- `Node.js 20.19+` or `22.12+`
- `npm`

`Node.js 18` is not sufficient for the current Vite version in this repository.

## Installation

Clone the repository and work from the project root:

```bash
git clone <your-repo-url>
cd KlinkPPI
```

Create a fresh Python virtual environment and install backend dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

## Running the Application

Start the backend from the `backend/` directory:

```bash
source .venv/bin/activate
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```bash
cd frontend
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

## API Endpoints

- `GET /search`
- `POST /mitab`
- `POST /parquet`
