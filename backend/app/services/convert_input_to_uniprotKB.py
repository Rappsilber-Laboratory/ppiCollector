import requests

UNIPROT_API='https://rest.uniprot.org/idmapping'

def get_job_id(id_value:str,from_database:str,tax_id:str|None=None):
    if(from_database=='UniProtKB'):
        return id_value
    else:
        payload={'ids':id_value,'from':from_database,'to':'UniProtKB'}
        if tax_id:
            payload['taxId']=tax_id
        response=requests.post(f'{UNIPROT_API}/run',data=payload)
        job_id=response.json().get('jobId')
        if not job_id:
            return None

        converted_id=requests.get(f"{UNIPROT_API}/uniprotkb/results/{job_id}").json().get('results',[])
        if(not converted_id):
            return None
        else:
            k=len(converted_id)
            i=0
            while(i<k):
                target=converted_id[i].get('to',{})
                if(target.get('entryType')=="UniProtKB reviewed (Swiss-Prot)"):
                    return target.get('primaryAccession')
                i+=1
            first_target=converted_id[0].get('to',{})
            return first_target.get('primaryAccession')
