import requests

URL='http://rest.ensembl.org/xrefs/symbol/homo_sapiens'

def convert_to_ensemble(input_id:str):
    response=requests.get(f"{URL}/{input_id}?content-type=application/json")
    response_json=(response.json())
    convert_id=""
    for data in response_json:
        if data['type']=='gene':
            converted_id=data['id']
    if converted_id=="":
        return "error"
    return converted_id
