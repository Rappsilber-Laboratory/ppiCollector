from fastapi import FastAPI
import requests
import time
from app.services.convert_input_to_uniprotKB import get_job_id
import pandas as pd

URL="https://version-12-0.string-db.org/api"
OUTPUT_FORMAT="json"
METHOD1="get_string_ids"
METHOD2="network"
METHOD3="get_link"
URL1="https://rest.uniprot.org/taxonomy"
def taxon_id_to_name(tax_id:str):
    tax_id_to_name_json=(requests.get(f"{URL1}/{tax_id}")).json()
    return (tax_id_to_name_json['scientificName'])

def get_string_interactions(input_id:str,tax_id:str):
    payload_conversion={'species':(tax_id),'identifiers':input_id}
    result_conversion=requests.post(f"{URL}/{OUTPUT_FORMAT}/{METHOD1}",data=payload_conversion)
    result_conversion_json=(result_conversion.json())
    if not result_conversion_json:
        return {"error":"Protein not found in STRING","interactions":[],"network_link":None}
    string_id=result_conversion_json[0]['stringId']

    payload_interactions={'identifiers':string_id}
    result_interactions=requests.post(f"{URL}/{OUTPUT_FORMAT}/{METHOD2}",data=payload_interactions)
    result_interactions_json=result_interactions.json()

    interactions=[]

    interactions.append({"info":{"database":"STRING","Input_UniProt":input_id,"organism":taxon_id_to_name(tax_id)}})

    direct_interactors=[]
    indirect_interactors=[]

    for data in result_interactions_json:
        if(data['stringId_A']==string_id):
            payload_get_link={'species':data['ncbiTaxonId'],'identifiers':data['preferredName_B']}
            result_get_link=requests.post(f"{URL}/{OUTPUT_FORMAT}/{METHOD3}",data=payload_get_link)
            result_get_link_json=result_get_link.json()
            Interactor_A=(data['preferredName_B'])
            Interactor_B=(data['preferredName_A'])
            direct_interactors.append({"Interactor_A":Interactor_A,"Interactor_B":Interactor_B,"Organism":taxon_id_to_name(data['ncbiTaxonId']),"combined_score":data["score"],"gene_neighbourhood_score":data["nscore"],"gene_fusion_score":data["fscore"],"phylogenetic_profile_score":data["pscore"],"experimental_score":data["escore"],"coexpression_score":data["ascore"],"textmining_score": data["tscore"],"database_score":data["dscore"],"Interactor_Link":result_get_link_json})
        if(data['stringId_B']==string_id):
            payload_get_link={'species':data['ncbiTaxonId'],'identifiers':data['preferredName_A']}
            result_get_link=requests.post(f"{URL}/{OUTPUT_FORMAT}/{METHOD3}",data=payload_get_link)
            result_get_link_json=result_get_link.json()
            Interactor_A=(data['preferredName_A'])
            Interactor_B=(data['preferredName_B'])
            direct_interactors.append({"Interactor_A":Interactor_A,"Interactor_B":Interactor_B,"Organism":taxon_id_to_name(data['ncbiTaxonId']),"combined_score":data["score"],"gene_neighbourhood_score":data["nscore"],"gene_fusion_score":data["fscore"],"phylogenetic_profile_score":data["pscore"],"experimental_score":data["escore"],"coexpression_score":data["ascore"],"textmining_score": data["tscore"],"database_score":data["dscore"],"Interactor_Link":result_get_link_json})
        else:
            payload_get_link_A={'species':data['ncbiTaxonId'],'identifiers':data['preferredName_A']}
            result_get_link_A=requests.post(f"{URL}/{OUTPUT_FORMAT}/{METHOD3}",data=payload_get_link_A)
            result_get_link_json_A=result_get_link_A.json() 

            payload_get_link_B={'species':tax_id,'identifiers':data['preferredName_B']}
            result_get_link_B=requests.post(f"{URL}/{OUTPUT_FORMAT}/{METHOD3}",data=payload_get_link_B)
            result_get_link_json_B=result_get_link_B.json()

            Interactor_A=(data['preferredName_A'])
            Interactor_B=(data['preferredName_B'])

            indirect_interactors.append({"Interactor_A":Interactor_A,"Interactor_B":Interactor_B,"Organism":taxon_id_to_name(data['ncbiTaxonId']),"combined_score":data["score"],"gene_neighbourhood_score":data["nscore"],"gene_fusion_score":data["fscore"],"phylogenetic_profile_score":data["pscore"],"experimental_score":data["escore"],"coexpression_score":data["ascore"],"textmining_score": data["tscore"],"database_score":data["dscore"],"Interactor_Link_A":result_get_link_json_A,"Interactor_Link_B":result_get_link_json_B})

    interactions.append({"Direct_Interactions":direct_interactors})

    interactions.append({"Indirect_Interactions":indirect_interactors})

    return interactions


