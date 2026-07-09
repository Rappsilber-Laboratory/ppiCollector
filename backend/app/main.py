import io
from typing import List, Optional
from fastapi import FastAPI,HTTPException, Query,Depends,Header
from fastapi.responses import StreamingResponse
from app.services.convert_input_to_uniprotKB import get_job_id
from app.services.resolve_string import get_string_interactions
from app.services.resolve_intact import resolve_intact
from app.services.resolve_predictomes import resolve_predictomes
from app.services.resolve_biogrid import resolve_biogrid
from app.services.resolve_corum import resolve_corum
from app.services.resolve_huri import resolve_HuRI
from app.services.convert_input_to_ensembl import convert_to_ensemble
import pandas as pd

from app.services.select_columns_mitab import build_final_columns
from app.services.populate_mitab import DBs,populate_huri
from app.services.toParquet import flatten_results

from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,EmailStr


from fastapi.middleware.cors import CORSMiddleware


class AuthCredentials(BaseModel):
    email:EmailStr
    password:str

app=FastAPI() 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)
Tax_ids_String="../Supported_Organisms/AllSpeciesString.csv"
Tax_ids_BioGrid="../Supported_Organisms/AllSpeciesBioGrid.csv"
Tax_ids_Intact="../Supported_Organisms/AllSpeciesIntact.csv"
Tax_ids_Corum="../Supported_Organisms/AllSpeciesCorum.csv"
Tax_ids_Predictomes="../Supported_Organisms/AllSpeciesPredictomes.csv"
Tax_ids_HuRI="../Supported_Organisms/AllSpeciesHuRI.csv"

df_string=pd.read_csv(Tax_ids_String)
(rows,colums)=df_string.shape
i=0
string_ids=set()
while(i<rows):
    string_ids.add(str(df_string.loc[i,'Taxon_id']))
    i+=1

df_intact=pd.read_csv(Tax_ids_Intact)
(rows,colums)=df_intact.shape
i=0
intact_ids=set()
while(i<rows):
    intact_ids.add(str(df_intact.loc[i,'Taxon_id']))
    i+=1

df_biogrid=pd.read_csv(Tax_ids_BioGrid)
(rows,colums)=df_biogrid.shape
i=0
biogrid_ids=set()
while(i<rows):
    biogrid_ids.add(str(df_biogrid.loc[i,'Taxon_id']))
    i+=1

df_predictomes=pd.read_csv(Tax_ids_Predictomes)
(rows,colums)=df_predictomes.shape
i=0
predictomes_ids=set()
while(i<rows):
    predictomes_ids.add(str(df_predictomes.loc[i,'Taxon_id']))
    i+=1

df_corum=pd.read_csv(Tax_ids_Corum)
(rows,colums)=df_corum.shape
i=0
corum_ids=set()
while(i<rows):
    corum_ids.add(str(df_corum.loc[i,'Taxon_id']))
    i+=1

df_huri=pd.read_csv(Tax_ids_HuRI)
(rows,colums)=df_huri.shape
i=0
huri_ids=set()
while(i<rows):
    huri_ids.add(str(df_huri.loc[i,'Taxon_id']))
    i+=1           
            
@app.get("/search")
def search(id_value:str,tax_id:str,from_database:str,selected_databases:Optional[List[str]]=Query(default=None)):
    uniprotkb_id=get_job_id(id_value,from_database,tax_id)
    if(not uniprotkb_id):
        raise HTTPException(status_code=404,detail="valid entry not found")
    available_databases=set()
    if(tax_id in string_ids):
        available_databases.add("String")

    if(tax_id in intact_ids):
        available_databases.add("IntAct")

    if(tax_id in biogrid_ids):
        available_databases.add("BioGrid")

    if(tax_id in predictomes_ids):
        available_databases.add("Predictomes")

    if(tax_id in corum_ids):
        available_databases.add("Corum")
    
    if(tax_id in huri_ids):
        available_databases.add("HuRI")

    selected_databases_dict={}
    result=[]
    result.append({"Input":{"UniProtId":uniprotkb_id,"TaxonomyId":tax_id}})
    output=[]
    if(selected_databases is None):
        for db in available_databases:
            if(db=="String"):
                selected_databases_dict["String"]=get_string_interactions(uniprotkb_id,tax_id)
            if(db=="IntAct"):
                selected_databases_dict["IntAct"]=resolve_intact(uniprotkb_id,tax_id)
            if(db=="Corum"):
                selected_databases_dict["Corum"]=resolve_corum(uniprotkb_id,tax_id)
            if(db=="Predictomes"):
                selected_databases_dict["Predictomes"]=resolve_predictomes(uniprotkb_id,tax_id)
            if(db=="BioGrid"):
                selected_databases_dict["BioGrid"]=resolve_biogrid(uniprotkb_id,tax_id)
            if(db=="HuRI"):
                ensembl_id=convert_to_ensemble(uniprotkb_id)
                selected_databases_dict["HuRI"]=resolve_HuRI(ensembl_id,tax_id)
    else:
        for db in selected_databases:
            if(db in available_databases):
                if(db=="String"):
                    selected_databases_dict["String"]=get_string_interactions(uniprotkb_id,tax_id)
                if(db=="IntAct"):
                    selected_databases_dict["IntAct"]=resolve_intact(uniprotkb_id,tax_id)
                if(db=="Corum"):
                    selected_databases_dict["Corum"]=resolve_corum(uniprotkb_id,tax_id)
                if(db=="Predictomes"):
                    selected_databases_dict["Predictomes"]=resolve_predictomes(uniprotkb_id,tax_id)
                if(db=="BioGrid"):
                    selected_databases_dict["BioGrid"]=resolve_biogrid(uniprotkb_id,tax_id)
                if(db=="HuRI"):
                    ensembl_id=convert_to_ensemble(uniprotkb_id)
                    selected_databases_dict["HuRI"]=resolve_HuRI(ensembl_id,tax_id)
            else:
                output.append({db:f"{db} does not have interactions for the given Input_id"})
    
    for key in selected_databases_dict.keys():
        if(key in available_databases):
            output.append({key:selected_databases_dict[key]})

    result.append({"output":output})

    return result

from pydantic import BaseModel

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
