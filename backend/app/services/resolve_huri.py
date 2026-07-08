import pandas as pd
from fastapi import FastAPI
import requests
import pandas as pd
import time
from app.services.convert_input_to_uniprotKB import get_job_id

URL1="https://rest.uniprot.org/taxonomy"

df=pd.read_csv("/Users/sukrit/Desktop/AggPPIplatform/Data/HuRI/HuRI.tsv",sep='\t',header=None)
df.columns=['interactorA','interactorB']

def taxon_id_to_name(tax_id:str):
    tax_id_to_name_json=(requests.get(f"{URL1}/{tax_id}")).json()
    return (tax_id_to_name_json['scientificName'])

def resolve_HuRI(input_id:str,tax_id:str):
    (rows,columns)=df.shape
    interactions=[]
    interactions.append({"info":{"database":"HuRI","Input_UniProt":input_id,"organism":taxon_id_to_name(tax_id)}})
    i=0
    interactors=[]
    while(i<rows):
        if(df.loc[i,'interactorA']==input_id):
            if(df.loc[i,'interactorB']!=input_id):
                interactors.append({'Interactor_A':df.loc[i,'interactorB'],'Interactor_B':df.loc[i,'interactorA'],'Interactor_Link':f"https://interactome-atlas.org/search/{df.loc[i,'interactorB']}"})
        i+=1
    interactions.append({"Interactions":interactors})
    return interactions
    



