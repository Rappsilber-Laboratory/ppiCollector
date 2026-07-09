import pandas as pd
import operator as op
import requests
URL1="https://rest.uniprot.org/taxonomy"
df=pd.read_csv("../Data/BioGrid/BIOGRID-ALL-5.0.258.mitab.txt",sep="\t")

def taxon_id_to_name(tax_id:str):
    tax_id_to_name_json=(requests.get(f"{URL1}/{tax_id}")).json()
    return (tax_id_to_name_json['scientificName'])

def resolve_biogrid(input_id:str,tax_id:str):
    (rows,columns)=df.shape
    num_rows=rows
    i=0
    interactions=[] 
    interaction_method=[]
    interactions.append({"info":{"database":"BioGrid","Input_UniProt":input_id,"organism":taxon_id_to_name(tax_id)}})
    interactors=[]
    while(i<num_rows):
        alt_ids_a=df.loc[i,'Alt IDs Interactor A']
        alt_ids_b=df.loc[i,'Alt IDs Interactor B']

        idsA=alt_ids_a.split('|')
        idsB=alt_ids_b.split('|')

        uniprotA=""
        for alt_ids in idsA:
            if 'uniprot/swiss-prot' in alt_ids:
                uniprotA=(alt_ids.split(":")[1])
                break

        uniprotB=""
        for alt_ids in idsB:
            if 'uniprot/swiss-prot' in alt_ids:
                uniprotB=(alt_ids.split(":")[1])
                break
          
        if(uniprotA==input_id):
            interactor_id_biogrid=""
            for alt_ids in idsB:
                if 'biogrid' in alt_ids:
                    interactor_id_biogrid=(alt_ids.split(":")[1])
                break
            if(df.loc[i,'Confidence Values']!='-'):
                interactors.append({"Interactor_A":uniprotB,"Interactor_B":uniprotA,"organism":taxon_id_to_name(df.loc[i,'Taxid Interactor B'].split(":")[1]),"Interaction_Detection_Method":df.loc[i,'Interaction Detection Method'].split("(")[1][0:len(df.loc[i,'Interaction Detection Method'].split("(")[1])-1],"Interaction_Type":df.loc[i,'Interaction Types'].split('"')[2][1:len(df.loc[i,'Interaction Types'].split('"')[2])-1],"Confidence_Score":df.loc[i,'Confidence Values'].split(':')[1],"Interactor_Link":f"https://thebiogrid.org/{interactor_id_biogrid}/table.html"})
            else:
                interactors.append({"Interactor_A":uniprotB,"Interactor_B":uniprotA,"organism":taxon_id_to_name(df.loc[i,'Taxid Interactor B'].split(":")[1]),"Interaction_Detection_Method":df.loc[i,'Interaction Detection Method'].split("(")[1][0:len(df.loc[i,'Interaction Detection Method'].split("(")[1])-1],"Interaction_Type":df.loc[i,'Interaction Types'].split('"')[2][1:len(df.loc[i,'Interaction Types'].split('"')[2])-1],"Confidence_Score":df.loc[i,'Confidence Values'],"Interactor_Link":f"https://thebiogrid.org/{interactor_id_biogrid}/table.html"})
        if(uniprotB==input_id):
            interactor_id_biogrid=""
            for alt_ids in idsA:
                if 'biogrid' in alt_ids:
                    interactor_id_biogrid=(alt_ids.split(":")[1])
                break
            if(df.loc[i,'Confidence Values']!='-'):
                interactors.append({"Interactor_A":uniprotA,"Interactor_B":uniprotB,"organism":taxon_id_to_name(df.loc[i,'Taxid Interactor A'].split(":")[1]),"Interaction_Detection_Method":df.loc[i,'Interaction Detection Method'].split("(")[1][0:len(df.loc[i,'Interaction Detection Method'].split("(")[1])-1],"Interaction_Type":df.loc[i,'Interaction Types'].split('"')[2][1:len(df.loc[i,'Interaction Types'].split('"')[2])-1],"Confidence_Score":df.loc[i,'Confidence Values'].split(':')[1],"Interactor_Link":f"https://thebiogrid.org/{interactor_id_biogrid}/table.html"})
            else:
                interactors.append({"Interactor_A":uniprotA,"Interactor_B":uniprotB,"organism":taxon_id_to_name(df.loc[i,'Taxid Interactor A'].split(":")[1]),"Interaction_Detection_Method":df.loc[i,'Interaction Detection Method'].split("(")[1][0:len(df.loc[i,'Interaction Detection Method'].split("(")[1])-1],"Interaction_Type":df.loc[i,'Interaction Types'].split('"')[2][1:len(df.loc[i,'Interaction Types'].split('"')[2])-1],"Confidence_Score":df.loc[i,'Confidence Values'],"Interactor_Link":f"https://thebiogrid.org/{interactor_id_biogrid}/table.html"})
        i+=1
    interactions.append({"Interactors":interactors})
    return interactions

