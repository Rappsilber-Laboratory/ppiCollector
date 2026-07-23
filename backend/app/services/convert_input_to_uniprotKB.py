import time

import requests

UNIPROT_API='https://rest.uniprot.org/idmapping'
POLL_INTERVAL_SECONDS = 1
MAX_POLL_ATTEMPTS = 30
REQUEST_TIMEOUT_SECONDS = 30


def _wait_for_job(job_id: str) -> list[dict] | None:
    for _ in range(MAX_POLL_ATTEMPTS):
        response = requests.get(f"{UNIPROT_API}/status/{job_id}", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
        status = payload.get("jobStatus")
        if "results" in payload:
            return payload.get("results", [])
        if status in {None, "FINISHED"}:
            return None
        if status in {"FAILED", "ERROR"}:
            return None
        time.sleep(POLL_INTERVAL_SECONDS)
    return None


def _get_mapping_results(job_id: str) -> list[dict]:
    params={"fields":"accession,reviewed","size":500}
    for _ in range(5):
        response = requests.get(
            f"{UNIPROT_API}/uniprotkb/results/{job_id}",
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        results = response.json().get('results',[])
        if results:
            return results
        time.sleep(POLL_INTERVAL_SECONDS)
    return []


def get_job_id(id_value:str,from_database:str,tax_id:str|None=None):
    if(from_database=='UniProtKB'):
        return id_value
    else:
        payload={'ids':id_value,'from':from_database,'to':'UniProtKB'}
        if tax_id:
            payload['taxId']=tax_id
        try:
            response=requests.post(f'{UNIPROT_API}/run',data=payload,timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            job_id=response.json().get('jobId')
            if not job_id:
                return None
            converted_id = _wait_for_job(job_id)
            if converted_id is None:
                converted_id = _get_mapping_results(job_id)
        except (requests.RequestException, ValueError):
            return None
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
