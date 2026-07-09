from fastapi import FastAPI
import pandas as pd
# python3 resolve_predictomes.py
df=pd.read_csv('../Data/Predictomes/Predictomes.csv')
def resolve_predictomes(input_id:str,tax_id:str):
    (rows,columns)=df.shape
    num_rows=rows
    i=0
    interactions=[]
    interactors_list=[]
    interactions.append({"info":{"database":"Predictomes","Input_UniProt":input_id,"organism":"Human"}})

    while i<num_rows:
        interaction=df.loc[i,'uniprot_ids']
        interaction_list=interaction.split(":")
        UniprotId_A=interaction_list[0].strip()
        UniprotId_B=interaction_list[1].strip()

        if(UniprotId_A==input_id):
            interactor=UniprotId_B
            filt=(df['uniprot_ids']==f"{input_id}:{interactor}")
            extraction_row=(df.loc[filt])
            spoc_score:float=extraction_row['spoc_score'].values[0]
            kirc_score:float=extraction_row['kirc_score'].values[0]
            num_unique_contacts:int=extraction_row['num_unique_contacts'].values[0]

            interactors_list.append({"Interactor_A":UniprotId_B,"Interactor_B":UniprotId_A,"spoc_score":float(spoc_score),"kirc_score":float(kirc_score),"num_unique_contacts":int(num_unique_contacts),"Interactor_Link":f"https://predictomes.org/hp/?pid={UniprotId_B}"})

        if(UniprotId_B==input_id):
            interactor=UniprotId_A
            filt=(df['uniprot_ids']==f"{interactor}:{input_id}")
            extraction_row=(df.loc[filt])
            spoc_score:float=extraction_row['spoc_score'].values[0]
            kirc_score:float=extraction_row['kirc_score'].values[0]
            num_unique_contacts:int=extraction_row['num_unique_contacts'].values[0]
            interactors_list.append({"Interactor_A":UniprotId_A,"Interactor_B":UniprotId_B,"spoc_score":float(spoc_score),"kirc_score":float(kirc_score),"num_unique_contacts":int(num_unique_contacts),"Interactor_Link":f"https://predictomes.org/hp/?pid={UniprotId_A}"})

        i+=1
    

    sorted_interactions=sorted(interactors_list, key=lambda x: x['spoc_score'], reverse=True)
    final_interactions=[]
    for data in sorted_interactions:
        if(data['spoc_score']>0.0):
            final_interactions.append(data)
    if(len(final_interactions)==0):
        return "The input doesn't exist on Predictomes"
    interactions.append({"Interactors":final_interactions})

    return interactions

