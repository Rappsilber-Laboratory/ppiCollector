import pandas as pd

def resolve_corum(input_id:str,tax_id:str):
    df1=pd.read_csv("/Users/sukrit/Desktop/AggPPIplatform/Data/Corum/corum_uniprotCorumMapping.txt",sep="\t")
    (rows,columns)=df1.shape
    i=0
    corum_id=""
    while(i<rows):
        if (df1.loc[i,'UniProtKB_accession_number']==input_id):
            corum_id=df1.loc[i,'corum_id']
        i+=1
    if(corum_id==""):
        return "this input does not exist in the Corum Database"

    df=pd.read_json("/Users/sukrit/Desktop/AggPPIplatform/Data/Corum/corum_allComplexes.json")
    (rows,columns)=df.shape
    i=3
    interactions=[]
    while(i<rows):
        if(df.loc[i,'complex_id']==corum_id):
            purification_methods=df.loc[i,'purification_methods']
            purification_methods_name=[]
            for methods in purification_methods:
                purification_methods_name.append(methods['name'])
            
            interactions.append({"info":{"database":'CORUM',"Input_UniProt":input_id,"organism":df.loc[i,'organism'],"complex_name":df.loc[i,'complex_name'],"cell_line":df.loc[i,'cell_line'],"Purification_Method":purification_methods_name}})


            interactors_list=[]
            for subunit in df.loc[i,'subunits']:
                if(subunit['swissprot']['uniprot_id']==input_id):
                    continue
                interactors_list.append({"Interactor":subunit['swissprot']['uniprot_id'],"Organism":subunit['swissprot']['organism'],"Interactor_Link":f"https://mips.helmholtz-muenchen.de/corum/?query={subunit['swissprot']['uniprot_id']}"})
            interactions.append({"Interactors":interactors_list})
            break
        i+=1
    return interactions
