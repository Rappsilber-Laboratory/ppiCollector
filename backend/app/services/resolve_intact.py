import requests
import math
URL="https://www.ebi.ac.uk/intact/ws"
METHOD1="interactor/findInteractor/body"
METHOD3="interaction/findInteractions"
METHOD2="interaction/countInteractionResult"
URL1="https://rest.uniprot.org/taxonomy"
def taxon_id_to_name(tax_id:str):
    tax_id_to_name_json=(requests.get(f"{URL1}/{tax_id}")).json()
    return (tax_id_to_name_json['scientificName'])

def resolve_intact(input_id:str,tax_id:str):
    result_conversion=requests.post(f"{URL}/{METHOD1}",json={"page":0,"pageSize":10,"query":input_id})
    result_conversion_json=result_conversion.json()
    intact_id=""
    for data in result_conversion_json['content']:
        if data['interactorPreferredIdentifier']==input_id:
            intact_id=data['interactorAc']
    if(intact_id==''):
        return {"error":"Protein not found in IntAct","interactions":[],"network_link":None}
    
    result_num_interactions=requests.post(f"{URL}/{METHOD2}/{intact_id}",json={"query":"*","batchSearch": False,"advancedSearch": False,"intraSpeciesFilter": False,"interactorSpeciesFilter": [],"interactorTypesFilter": [],"interactionDetectionMethodsFilter": [],"participantDetectionMethodsFilter": [],"interactionTypesFilter": [],"interactionHostOrganismsFilter": [],"negativeFilter": "POSITIVE_ONLY","mutationFilter": False,"expansionFilter": False,"minMIScore": 0,"maxMIScore": 1,"binaryInteractionIds": None,"interactorAcs":None})
    result_num_interactions_json=result_num_interactions.json()
    all_interactions=[]
    page=0
    iterations=math.ceil(result_num_interactions_json/20)
    i=0
    while i<iterations:
        result_interactions=requests.get(f"{URL}/{METHOD3}/{intact_id}",params={"page":page,"size":20,"sort":[]})
        content=(result_interactions.json()['content'])
        all_interactions.extend(content)
        page+=1
        i+=1
    all_interactions_refined=[]
    for data in all_interactions:
        if data['uniqueIdA']==data['uniqueIdB']:
            continue
        else:
            all_interactions_refined.append(data)
    all_interactions_more_refined=[]
    for data in all_interactions_refined:
        if(data['uniqueIdB']<data['uniqueIdA']):
            temp=data['uniqueIdA']
            data['uniqueIdA']=data['uniqueIdB']
            data['uniqueIdB']=temp
        all_interactions_more_refined.append(data)
    
    raw_response_data={}
    for data in all_interactions_more_refined:
        key=(data['uniqueIdA'],data['uniqueIdB'])
        if (key) in raw_response_data:
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['identification_method'].add(data['detectionMethod'])
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['publication_id'].add(data['publicationPubmedIdentifier'])
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['feature_count'].append(data['featureCount'])
            temp=data['confidenceValues']
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['num_interactions']+=1
        else:
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]={}

            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['num_interactions']=1
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['identification_method']=set()
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['publication_id']=set()
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['feature_count']=[]


            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['identification_method'].add(data['detectionMethod'])
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['publication_id'].add(data['publicationPubmedIdentifier'])
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['feature_count'].append(data['featureCount'])
            temp=data['confidenceValues']
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['confidence_value']=(temp[0])
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['moleculeA']=(data['moleculeA'])
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['TaxIdA']=(data['taxIdA'])
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['moleculeB']=(data['moleculeB'])
            raw_response_data[(data['uniqueIdA'],data['uniqueIdB'])]['TaxIdB']=(data['taxIdB'])

    interactions=[]
    interactions.append({"info":{"database":"IntAct","Input_Uniprot":input_id,"organism":taxon_id_to_name(tax_id)}})
    interactors=[]

    for key in raw_response_data.keys():
        temp=len(raw_response_data[key]['confidence_value'])
        if key[0]==input_id:
           interactors.append({
            "Interactor_A":key[1],
            "Interactor_B":key[0],
            "organism":taxon_id_to_name(raw_response_data[key]['TaxIdB']),
            "Num_Interaction_IntAct":raw_response_data[key]['num_interactions'],
            "Minimum_feature_count":min(raw_response_data[key]['feature_count']),
            "Maximum_feature_count":max(raw_response_data[key]['feature_count']),
            "Interaction_Score_Intact":raw_response_data[key]['confidence_value'][15:temp],
            "Unique_Identification_Methods":[s for s in raw_response_data[key]['identification_method']],
            "PubMed_Ids":[s for s in raw_response_data[key]['publication_id']],
            "Interactor_Link":f"https://www.ebi.ac.uk/intact/search?query={key[1]}"
        })
        if key[1]==input_id:
           interactors.append({
            "Interactor_A":key[0],
            "Interactor_B":key[1],
            "organism":taxon_id_to_name(raw_response_data[key]['TaxIdA']),
            "Num_Interaction_IntAct":raw_response_data[key]['num_interactions'],
            "Minimum_feature_count":min(raw_response_data[key]['feature_count']),
            "Maximum_feature_count":max(raw_response_data[key]['feature_count']),
            "Interaction_Score_Intact":raw_response_data[key]['confidence_value'][15:temp],
            "Unique_Identification_Methods":[s for s in raw_response_data[key]['identification_method']],
            "PubMed_Ids":[s for s in raw_response_data[key]['publication_id']],
            "Interactor_Link":f"https://www.ebi.ac.uk/intact/search?query={key[0]}"
        })
    interactions.append({"Interactions":interactors})
    return interactions

