from fastapi import FastAPI
import requests
import pandas as pd
import time

UNIPROT_API='https://rest.uniprot.org/idmapping'

def get_job_id(id_value:str,from_database:str,tax_id:str):
    if(from_database=='UniProtKB'):
        return id_value
    else:
        payload={'ids':id_value,'from':from_database,'to':'UniProtKB','taxId':tax_id}
        response=requests.post(f'{UNIPROT_API}/run',data=payload)
        job_id=response.json()['jobId']


        converted_id=requests.get(f"{UNIPROT_API}/uniprotkb/results/{job_id}").json().get('results',[])
        if(not converted_id):
            return ("Incorrect ID or TaxonomyId, kindly recheck")
        else:
            k=len(converted_id)
            i=0
            while(i<k):
                if(converted_id[i]['to']['entryType']=="UniProtKB reviewed (Swiss-Prot)"):
                    return converted_id[i]['to']['primaryAccession']
                i+=1
            print("there does not exist a UniProtKB reviewed id, please input another protein")

