import io
from typing import List, Optional
from fastapi import FastAPI,HTTPException, Query
from fastapi.responses import StreamingResponse
from app.services.convert_input_to_uniprotKB import get_job_id
from app.services.resolve_string import get_string_interactions
from app.services.resolve_intact import resolve_intact
from app.services.resolve_predictomes import resolve_predictomes
from app.services.resolve_biogrid import resolve_biogrid
from app.services.resolve_corum import resolve_corum
from app.services.resolve_huri import resolve_HuRI
from app.services.convert_input_to_ensembl import convert_to_ensemble
from app.services.species_index import get_species_by_tax_id, get_supported_databases, resolve_species_name, search_species
from app.services.species_ppi_export import build_species_mitab, build_species_parquet
from app.services.species_ppi_jobs import create_species_ppi_job, get_species_display_name, get_species_ppi_job, get_species_ppi_job_rows
from app.services.uniprot_gene_search import search_gene_name_candidates
from app.services.uniprot_lookup import get_uniprot_taxonomy_id
import pandas as pd

from app.services.select_columns_mitab import build_final_columns
from app.services.populate_mitab import DBs,populate_huri
from app.services.toParquet import flatten_results

from pydantic import BaseModel,EmailStr


from fastapi.middleware.cors import CORSMiddleware


class AuthCredentials(BaseModel):
    email:EmailStr
    password:str


class SpeciesPPIJobRequest(BaseModel):
    tax_id: Optional[str] = None
    species_name: Optional[str] = None
    selected_databases: list[str]


class SpeciesPPIDownloadRequest(BaseModel):
    selected_databases: list[str]
    selected_columns: list[str]

app=FastAPI() 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174","http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def resolve_species_context(tax_id: Optional[str], species_name: Optional[str]):
    resolved_species=None
    resolved_tax_id=(tax_id or "").strip() or None
    requested_species_name=(species_name or "").strip()

    if resolved_tax_id:
        resolved_species=get_species_by_tax_id(resolved_tax_id)
        if resolved_species is None:
            raise HTTPException(status_code=404,detail="Taxonomy ID is not supported by the configured organism list")
    elif requested_species_name:
        resolved_species=resolve_species_name(requested_species_name)
        if resolved_species is None:
            species_matches=search_species(requested_species_name,limit=5)
            if species_matches:
                raise HTTPException(status_code=400,detail="Species name is ambiguous. Please choose one of the suggestions or enter a taxonomy ID")
            raise HTTPException(status_code=404,detail="Species name not found in the supported organism list")
        resolved_tax_id=resolved_species["tax_id"]

    return resolved_tax_id, requested_species_name, resolved_species

@app.get("/species/search")
def species_search(q:str="",limit:int=8):
    safe_limit=max(1,min(limit,10))
    return {"results":search_species(q,safe_limit)}


@app.get("/gene-name/search")
def gene_name_search(
    query:str,
    tax_id:Optional[str]=None,
    species_name:Optional[str]=None,
    limit:int=8,
):
    resolved_tax_id, requested_species_name, resolved_species = resolve_species_context(tax_id, species_name)
    if resolved_tax_id is None:
        raise HTTPException(
            status_code=400,
            detail="Gene name lookup requires a species name or taxonomy ID",
        )

    safe_limit=max(1,min(limit,10))
    candidates=search_gene_name_candidates(query.strip(), resolved_tax_id, safe_limit)
    return {
        "query": query,
        "tax_id": resolved_tax_id,
        "species_name": resolved_species["display_name"] if resolved_species else requested_species_name,
        "candidates": candidates,
    }


@app.post("/species-ppi/jobs")
def start_species_ppi_job(request: SpeciesPPIJobRequest):
    resolved_tax_id, requested_species_name, resolved_species = resolve_species_context(
        request.tax_id, request.species_name
    )
    if resolved_tax_id is None:
        raise HTTPException(
            status_code=400,
            detail="Complete species PPI search requires a species name or taxonomy ID",
        )

    if not request.selected_databases:
        raise HTTPException(status_code=400, detail="Select at least one database")

    species_label = (
        resolved_species["display_name"]
        if resolved_species
        else get_species_display_name(resolved_tax_id, requested_species_name)
    )
    return create_species_ppi_job(resolved_tax_id, species_label, request.selected_databases)


@app.get("/species-ppi/jobs/{job_id}")
def get_species_ppi_job_status(job_id: str):
    try:
        return get_species_ppi_job(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Species PPI job not found")


@app.post("/species-ppi/jobs/{job_id}/mitab")
def download_species_mitab(job_id: str, request: SpeciesPPIDownloadRequest):
    try:
        summary, rows_by_db = get_species_ppi_job_rows(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Species PPI job not found")

    if summary["status"] != "completed":
        raise HTTPException(status_code=400, detail="Species PPI job is not finished yet")

    available_databases = [
        db_name
        for db_name, status in summary["database_statuses"].items()
        if status["status"] == "completed"
    ]
    selected_databases = [db_name for db_name in request.selected_databases if db_name in available_databases]
    if not selected_databases:
        raise HTTPException(status_code=400, detail="No completed databases were selected for export")

    buffer = build_species_mitab(rows_by_db, summary["tax_id"], selected_databases, request.selected_columns)
    filename = f"{summary['species_name'].replace(' ', '_')}_{summary['tax_id']}_ppi.mitab.txt"
    return StreamingResponse(
        buffer,
        media_type="text/tab-separated-values",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/species-ppi/jobs/{job_id}/parquet")
def download_species_parquet(job_id: str, request: SpeciesPPIDownloadRequest):
    try:
        summary, rows_by_db = get_species_ppi_job_rows(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Species PPI job not found")

    if summary["status"] != "completed":
        raise HTTPException(status_code=400, detail="Species PPI job is not finished yet")

    available_databases = [
        db_name
        for db_name, status in summary["database_statuses"].items()
        if status["status"] == "completed"
    ]
    selected_databases = [db_name for db_name in request.selected_databases if db_name in available_databases]
    if not selected_databases:
        raise HTTPException(status_code=400, detail="No completed databases were selected for export")

    buffer = build_species_parquet(rows_by_db, selected_databases)
    filename = f"{summary['species_name'].replace(' ', '_')}_{summary['tax_id']}_ppi.parquet"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.apache.parquet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/search")
def search(
    id_value:str,
    from_database:str,
    tax_id:Optional[str]=None,
    species_name:Optional[str]=None,
    selected_databases:Optional[List[str]]=Query(default=None)
):
    resolved_tax_id, requested_species_name, resolved_species = resolve_species_context(tax_id, species_name)

    uniprotkb_id=get_job_id(id_value,from_database,resolved_tax_id)
    if(not uniprotkb_id):
        context_details = []
        if requested_species_name:
            context_details.append(f"species '{requested_species_name}'")
        if resolved_tax_id:
            context_details.append(f"taxonomy ID '{resolved_tax_id}'")

        if from_database == "Gene_Name":
            if context_details:
                raise HTTPException(
                    status_code=404,
                    detail=f"Gene name '{id_value}' could not be resolved to a UniProtKB entry for {' and '.join(context_details)}",
                )
            raise HTTPException(
                status_code=404,
                detail=f"Gene name '{id_value}' could not be resolved to a UniProtKB entry. Try adding a species name or taxonomy ID",
            )

        if context_details:
            raise HTTPException(
                status_code=404,
                detail=f"Input '{id_value}' could not be resolved from {from_database} for {' and '.join(context_details)}",
            )

        raise HTTPException(
            status_code=404,
            detail=f"Input '{id_value}' could not be resolved from {from_database}",
        )

    if resolved_tax_id is None:
        resolved_tax_id=get_uniprot_taxonomy_id(uniprotkb_id)
        if resolved_tax_id is None:
            raise HTTPException(status_code=400,detail="Could not infer a taxonomy ID from the input. Please provide a species name or taxonomy ID")
        resolved_species=get_species_by_tax_id(resolved_tax_id)

    available_databases=get_supported_databases(resolved_tax_id)

    selected_databases_dict={}
    result=[]
    result.append({
        "Input":{
            "UniProtId":uniprotkb_id,
            "TaxonomyId":resolved_tax_id,
            "SpeciesName":resolved_species["display_name"] if resolved_species else requested_species_name
        }
    })
    output=[]
    if(selected_databases is None):
        for db in available_databases:
            if(db=="String"):
                selected_databases_dict["String"]=get_string_interactions(uniprotkb_id,resolved_tax_id)
            if(db=="IntAct"):
                selected_databases_dict["IntAct"]=resolve_intact(uniprotkb_id,resolved_tax_id)
            if(db=="Corum"):
                selected_databases_dict["Corum"]=resolve_corum(uniprotkb_id,resolved_tax_id)
            if(db=="Predictomes"):
                selected_databases_dict["Predictomes"]=resolve_predictomes(uniprotkb_id,resolved_tax_id)
            if(db=="BioGrid"):
                selected_databases_dict["BioGrid"]=resolve_biogrid(uniprotkb_id,resolved_tax_id)
            if(db=="HuRI"):
                ensembl_id=convert_to_ensemble(uniprotkb_id)
                selected_databases_dict["HuRI"]=resolve_HuRI(ensembl_id,resolved_tax_id)
    else:
        for db in selected_databases:
            if(db in available_databases):
                if(db=="String"):
                    selected_databases_dict["String"]=get_string_interactions(uniprotkb_id,resolved_tax_id)
                if(db=="IntAct"):
                    selected_databases_dict["IntAct"]=resolve_intact(uniprotkb_id,resolved_tax_id)
                if(db=="Corum"):
                    selected_databases_dict["Corum"]=resolve_corum(uniprotkb_id,resolved_tax_id)
                if(db=="Predictomes"):
                    selected_databases_dict["Predictomes"]=resolve_predictomes(uniprotkb_id,resolved_tax_id)
                if(db=="BioGrid"):
                    selected_databases_dict["BioGrid"]=resolve_biogrid(uniprotkb_id,resolved_tax_id)
                if(db=="HuRI"):
                    ensembl_id=convert_to_ensemble(uniprotkb_id)
                    selected_databases_dict["HuRI"]=resolve_HuRI(ensembl_id,resolved_tax_id)
            else:
                output.append({db:f"{db} does not have interactions for the given Input_id"})
    
    for key in selected_databases_dict.keys():
        if(key in available_databases):
            output.append({key:selected_databases_dict[key]})

    result.append({"output":output})

    return result

class DownloadRequest(BaseModel):
    results: list
    selected_databases: list[str]
    selected_columns: list[str]
    uniprot_id: str
    tax_id: str
    
@app.post("/mitab")
def download_mitab(request: DownloadRequest):
    final_columns = build_final_columns(request.selected_databases, request.selected_columns)
    all_rows = []
    
    output = request.results[1]["output"]

    for db_result in output:
        db_name = list(db_result.keys())[0]
        if db_name not in request.selected_databases:
            continue
        db_data = db_result[db_name]
        if isinstance(db_data, str):
            continue

        if db_name == "HuRI":
            rows = populate_huri(db_data, final_columns, request.uniprot_id,request.selected_columns, request.tax_id)
        elif db_name in DBs:
            rows = DBs[db_name](db_data,final_columns,request.selected_columns,request.uniprot_id, request.tax_id)
        else:
            continue

        all_rows.extend(rows)

    tsv_lines = ["\t".join(final_columns)]
    for row in all_rows:
        line = "\t".join(str(row.get(col, "-")) for col in final_columns)
        tsv_lines.append(line)
    tsv_content = "\n".join(tsv_lines)
    # return output
    # return final_columns
    return StreamingResponse(
        io.StringIO(tsv_content),
        media_type="text/tab-separated-values",
        headers={"Content-Disposition": f"attachment; filename={request.uniprot_id}_interactions.mitab.txt"}
    )

@app.post("/parquet")
def download_parquet(request: DownloadRequest):
    rows = flatten_results(
        request.results,
        request.selected_databases
    )
    if not rows:
        raise HTTPException(status_code=404,detail="No Data")
    
    df=pd.DataFrame(rows)
    buffer=io.BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.apache.parquet",
        headers={
            "Content-Disposition":
            f"attachment; filename={request.uniprot_id}.parquet"
        }
    )
