from typing import List, Optional
from fastapi import FastAPI,HTTPException, Query,Depends,Header
from app.services.convert_input_to_uniprotKB import get_job_id
from app.services.resolve_string import get_string_interactions
from app.services.resolve_intact import resolve_intact
from app.services.resolve_predictomes import resolve_predictomes
from app.services.resolve_biogrid import resolve_biogrid
from app.services.resolve_corum import resolve_corum
from app.services.resolve_huri import resolve_HuRI
from app.services.convert_input_to_ensembl import convert_to_ensemble
from app.supabase_client import supabase
import pandas as pd

from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,EmailStr
from app.supabase_client import supabase,supabase_admin

from app.dependencies import get_optional_user

class AuthCredentials(BaseModel):
    email:EmailStr
    password:str

app=FastAPI() 
Tax_ids_String="/Users/sukrit/Desktop/AggPPIplatform/Supported_Organisms/AllSpeciesString.csv"
Tax_ids_BioGrid="/Users/sukrit/Desktop/AggPPIplatform/Supported_Organisms/AllSpeciesBioGrid.csv"
Tax_ids_Intact="/Users/sukrit/Desktop/AggPPIplatform/Supported_Organisms/AllSpeciesIntact.csv"
Tax_ids_Corum="/Users/sukrit/Desktop/AggPPIplatform/Supported_Organisms/AllSpeciesCorum.csv"
Tax_ids_Predictomes="/Users/sukrit/Desktop/AggPPIplatform/Supported_Organisms/AllSpeciesPredictomes.csv"
Tax_ids_HuRI="/Users/sukrit/Desktop/AggPPIplatform/Supported_Organisms/AllSpeciesHuRI.csv"

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

@app.get("/")
def home(current_user=Depends(get_optional_user)):
    response=supabase_admin.table("history").select("available_databases,choosen_databases,input_uniprot_id,taxonomy_id").execute()

    df=pd.DataFrame(response.data)
    stats={}
    (rows,colums)=df.shape
    if(rows==0):
        return stats
    stats["Total Number of Queries"]=rows

    available_database_count={"IntAct":0,"BioGrid":0,"Corum":0,"String":0,"HuRI":0,"Predictomes":0}
    i=0
    while i<rows:
        for db in df.loc[i,"available_databases"]:
            available_database_count[db]+=1
        i+=1

    queried_databases_count={"IntAct":0,"BioGrid":0,"Corum":0,"String":0,"HuRI":0,"Predictomes":0}
    i=0
    while i<rows:
        for db in df.loc[i,"choosen_databases"]:
            queried_databases_count[db]+=1
        i+=1

    databases_usage={}
    for db in queried_databases_count:
        if(available_database_count[db]==0):
            databases_usage[db]=0
        else:
            databases_usage[db]=round(queried_databases_count[db]/available_database_count[db]*100)

    sorted_usage=dict(sorted(databases_usage.items(),key=lambda x: x[1],reverse=True))
    
    stats["Most_Queried_Databases"]=sorted_usage

   
    trending_proteins={}
    
    i=0
    while i<rows:
        if df.loc[i,"input_uniprot_id"] not in trending_proteins :
            trending_proteins[df.loc[i,"input_uniprot_id"]]=1
        else:
            trending_proteins[df.loc[i,"input_uniprot_id"]]+=1
        i+=1
    trending_proteins = dict(sorted(trending_proteins.items(),key=lambda x: x[1],reverse=True))
    top5=dict(list(trending_proteins.items())[:5])
    stats["Trending Proteins"]=top5
    return stats            
            
@app.get("/search")
def search(id_value:str,tax_id:str,from_database:str,selected_databases:Optional[List[str]]=Query(default=None),current_user=Depends(get_optional_user)):
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

    if current_user:
        supabase_admin.table('history').insert({
            "user_id":current_user.id,
            "input_id":id_value,
            "input_uniprot_id":uniprotkb_id,
            "taxonomy_id":tax_id,
            "available_databases":list(available_databases),
            "choosen_databases":list(selected_databases)
        }).execute()

    return result


@app.post("/signup")
def sign_up(credentials:AuthCredentials):
    try:
        response=supabase.auth.sign_up({'email':credentials.email,'password':credentials.password})
        return {"message":"SignUp successful, please verify your email"}
    except:
        raise HTTPException(status_code=400,detail="signup failed")

@app.post("/login")
def login(credentials:AuthCredentials):
    try:
        response=supabase.auth.sign_in_with_password({'email':credentials.email,'password':credentials.password})

        return{
            "access_token":response.session.access_token,
            "token_type":"bearer",
        }
    except:
        raise HTTPException(status_code=401,detail="Invalid Credentials")

@app.get('/logout')
def logout(authorization:str=Header(None)):
    try:
        token=authorization.split(" ")
        supabase.auth.admin.sign_out(token[1])
        return {"message":"Log Out successfully"}
    except:
        raise HTTPException(status_code=401,detail="Invalid Credentials")
    
@app.get('/deleteprofile')
def delete_profile(current_user=Depends(get_optional_user)):
    try:
        supabase_admin.auth.admin.delete_user(current_user.id)
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400,detail=str(e))

@app.get("/history")
def get_history(current_user=Depends(get_optional_user)):
    try:
        response = (
            supabase_admin
            .table("history")
            .select("searched_at,input_id,input_uniprot_id,taxonomy_id,choosen_databases,available_databases")
            .eq("user_id",current_user.id)
            .execute()
        )
    except:
        raise HTTPException(status_code=401,detail="Login Required")
    return response

@app.delete("/history/delete/{history_id}")
def delete_history(history_id:int,current_user=Depends(get_optional_user)):
    if not current_user:
        return {"message":"user not logged in"}
    try:
        response=supabase_admin.table("history").delete().eq("id",history_id).eq("user_id",current_user.id).execute()
        if not response.data:
            raise HTTPException(status_code=401,detail="Invalid Credentials")
        return {"message":"History deleted successfully"}
    except:
        raise HTTPException(status_code=401,detail="Invalid Credentials")

@app.post("/history/favourites/{history_id}")
def set_favourite(history_id:int,current_user=Depends(get_optional_user)):
    if not current_user:
        return {"message":"user not logged in"}
    try:
        response=supabase_admin.table("history").select("is_favourite").eq("id",history_id).eq("user_id",current_user.id).execute()
        if not response.data:
            raise HTTPException(status_code=401,detail="Invalid Credentials")

        if response.data[0]["is_favourite"]==True:
            supabase_admin.table("history").update({"is_favourite":False}).eq("id", history_id).eq("user_id", current_user.id).execute()
            return {"message":"Query removed as favourite"}
        else:
            supabase_admin.table("history").update({"is_favourite":True}).eq("id", history_id).eq("user_id", current_user.id).execute()
            return {"message":"Query set as favourite"}
    except:
        raise HTTPException(status_code=401,detail="Invalid Credentials")