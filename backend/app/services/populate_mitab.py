def populate_string(data:list,final_columns:list,selected_columns:list,uniprot_id,tax_id):
    direct_interactions=data[1]["Direct_Interactions"]
    indirect_interactions=data[2]["Indirect_Interactions"]

    rows=[]

    for interaction in direct_interactions:
        row={}
        for column in final_columns:
            row[column]="-"
        row["#ID(s) interactor A"]=f"hgnc.symbol:{interaction.get("Interactor_A",'-')}"
        row["ID(s) interactor B"]=f"hgnc.symbol:{interaction.get("Interactor_B",'-')}"
        row["Source database(s)"]='psi-mi:"MI:1201"(string)'

        if "Confidence value(s)" in final_columns:
            scores=[]
            if 'combined_score' in selected_columns:
                scores.append(f"string-score:{interaction.get('combined_score', '-')}")
            if 'experimental_score' in selected_columns:
                scores.append(f"string-experimental-score:{interaction.get('experimental_score', '-')}")
            if 'coexpression_score' in selected_columns:
                scores.append(f"string-coexpression-score:{interaction.get('coexpression_score', '-')}")
            if 'textmining_score' in selected_columns:
                scores.append(f"string-textmining-score:{interaction.get('textmining_score', '-')}")
            if 'database_score' in selected_columns:
                scores.append(f"string-database-score:{interaction.get('database_score', '-')}")
            if 'gene_neighbourhood_score' in selected_columns:
                scores.append(f"string-database-score:{interaction.get('gene_neighbourhood_score', '-')}")
            if 'gene_fusion_score' in selected_columns:
                scores.append(f"string-database-score:{interaction.get('gene_fusion_score', '-')}")
            if 'phylogenetic_profile_score' in selected_columns:
                scores.append(f"string-database-score:{interaction.get('phylogenetic_profile_score', '-')}")
            if scores:
                row["Confidence value(s)"] = "|".join(scores)
        rows.append(row)
    
    for interaction in indirect_interactions:
        row={}
        for column in final_columns:
            row[column]="-"
        row["#ID(s) interactor A"]=f"hgnc.symbol:{interaction.get("Interactor_A",'-')}"
        row["ID(s) interactor B"]=f"hgnc.symbol:{interaction.get("Interactor_B",'-')}"
        row["Source database(s)"]='psi-mi:"MI:1201"(string)'

        if "Confidence value(s)" in final_columns:
            scores=[]
            if 'combined_score' in selected_columns:
                scores.append(f"string-score:{interaction.get('combined_score', '-')}")
        rows.append(row)

    return rows

def populate_predictomes(data:list,final_columns:list,selected_columns:list,uniprot_id,tax_id):
    rows=[]
    interactions=data[1]['Interactors']
    for interaction in interactions:
        row={}
        for column in final_columns:
            row[column]="-"
        row["#ID(s) interactor A"]=f"uniprotkb:{interaction.get("Interactor_A",'-')}"
        row["ID(s) interactor B"]=f"uniprotkb:{interaction.get("Interactor_B",'-')}"
        row["Source database(s)"]='predictomes'

        if "Confidence value(s)" in final_columns:
            scores=[]
            if 'spoc_score' in selected_columns:
                scores.append(f"spoc-score:{interaction.get('spoc_score', '-')}")
            if 'kirc_score' in selected_columns:
                scores.append(f"kirc-score:{interaction.get('kirc_score', '-')}")
            if 'num_unique_contacts' in selected_columns:
                scores.append(f"unique-contacts:{interaction.get('num_unique_contacts', '-')}")
            if scores:
                row["Confidence value(s)"]='|'.join(scores) 
        rows.append(row)
    return rows
    


def populate_intact(data:list,final_columns:list,selected_columns:list,uniprot_id,tax_id):
    method_to_mi ={
    "spr": "MI:0107",
    "surface plasmon resonance": "MI:0107",
    "3d-em-single": "MI:2339",
    "electron microscopy 3d single particle reconstruction": "MI:2339",
    "x-ray diffraction": "MI:0114",
    "protease assay": "MI:0428",
    "molecular sieving": "MI:0071",
    "anti tag coip": "MI:0007",
    "anti tag coimmunoprecipitation": "MI:0007",
    "validated two hybrid": "MI:1356",
    "two hybrid prey pooling approach": "MI:1112",
    "two hybrid array": "MI:0397"}

    rows=[]
    interactions=data[1]['Interactions']
    for interaction in interactions:
        row={}
        for column in final_columns:
            row[column]="-"
        row["#ID(s) interactor A"]=f"uniprotkb:{interaction.get('Interactor_A','-')}"
        row["ID(s) interactor B"]=f"uniprotkb:{interaction.get('Interactor_B','-')}"
        row["Source database(s)"]='psi-mi:"MI:0469"(intact)'

        if "Publication Identifier(s)" in final_columns:
            pub_list=[]
            for ids in interaction.get('PubMed_Ids','-'):
                pub_list.append(ids)
            row["Publication Identifier(s)"] = "|".join(pub_list)

        if "Confidence value(s)" in final_columns:
            scores = []
            if 'Interaction_Score_Intact' in selected_columns:
                scores.append(f"intact-miscore:{interaction.get('Interaction_Score_Intact', '-')}")
            if 'Num_Interaction_IntAct' in selected_columns:
                scores.append(f"intact-interaction-count:{interaction.get('Num_Interaction_IntAct', '-')}")
            if 'Minimum_feature_count' in selected_columns:
                scores.append(f"minimum-feature-count:{interaction.get('Minimum_feature_count', '-')}")
            if 'Maximum_feature_count' in selected_columns:
                scores.append(f"maximum-feature-count:{interaction.get('Maximum_feature_count', '-')}")   
            if scores:
                row["Confidence value(s)"] = "|".join(scores)

        if "Participant identification method(s)" in final_columns:
            method_list=[]
            for method in interaction.get("Unique_Identification_Methods",'-'):
                method_lower=method.lower()
                if(method_lower in method_to_mi.keys()):
                    method_list.append(f'psi-mi:"{method_to_mi[method_lower]}"({method})')
                else:
                    method_list.append(method)
            row['Participant identification method(s)']='|'.join(method_list) if method_list else "-"
        rows.append(row)
    return rows

def populate_huri(data:list,final_columns:list,selected_columns:list,uniprot_id,tax_id):
    rows=[]
    interactions=data[1]['Interactions']
    for interaction in interactions:
        row={}
        for column in final_columns:
            row[column]="-"
        row["#ID(s) interactor A"]=f"ensembl:{interaction.get("Interactor_A",'-')}"
        row["ID(s) interactor B"]=f"ensembl:{interaction.get("Interactor_B",'-')}"
        row["Source database(s)"]='psi-mi:"MI:1237"(huri)'
        rows.append(row)
    return rows

def populate_biogrid(data:list,final_columns:list,selected_columns:list,uniprot_id,tax_id):
    BIOGRID_TYPE_CODES = {
        "physical association": 'psi-mi:"MI:0915"(physical association)',
        "direct interaction": 'psi-mi:"MI:0407"(direct interaction)',
        "association": 'psi-mi:"MI:0914"(association)',
        "colocalization": 'psi-mi:"MI:0403"(colocalization)',
        "genetic interference": 'psi-mi:"MI:0254"(genetic interference)',
        "synthetic lethality": 'psi-mi:"MI:0797"(synthetic lethality)',
    }

    interaction_detection_methods = {
    # Affinity-based methods
    "pull down": 'psi-mi:"MI:0096"(pull down)',
    "coimmunoprecipitation": 'psi-mi:"MI:0019"(coimmunoprecipitation)',
    "anti bait coip": 'psi-mi:"MI:0006"(anti bait coimmunoprecipitation)',
    "anti tag coip": 'psi-mi:"MI:0007"(anti tag coimmunoprecipitation)',
    "affinity chromatography technology": 'psi-mi:"MI:0004"(affinity chromatography technology)',
    "tandem affinity purification": 'psi-mi:"MI:0676"(tandem affinity purification)',
    "far western blotting": 'psi-mi:"MI:0047"(far western blotting)',

    # Two-hybrid methods
    "two hybrid": 'psi-mi:"MI:0018"(two hybrid)',
    "validated two hybrid": 'psi-mi:"MI:1356"(validated two hybrid)',
    "two hybrid array": 'psi-mi:"MI:0397"(two hybrid array)',
    "two hybrid pooling approach": 'psi-mi:"MI:0398"(two hybrid pooling approach)',
    "two hybrid prey pooling approach": 'psi-mi:"MI:1112"(two hybrid prey pooling approach)',

    # Biophysical methods
    "spr": 'psi-mi:"MI:0107"(surface plasmon resonance)',
    "surface plasmon resonance": 'psi-mi:"MI:0107"(surface plasmon resonance)',
    "fluorescence resonance energy transfer": 'psi-mi:"MI:0055"(fluorescence resonance energy transfer)',
    "fret": 'psi-mi:"MI:0055"(fluorescence resonance energy transfer)',
    "bioluminescence resonance energy transfer": 'psi-mi:"MI:0017"(bioluminescence resonance energy transfer)',
    "bret": 'psi-mi:"MI:0017"(bioluminescence resonance energy transfer)',

    # Structural methods
    "x-ray diffraction": 'psi-mi:"MI:0114"(x-ray crystallography)',
    "x-ray crystallography": 'psi-mi:"MI:0114"(x-ray crystallography)',
    "3d-em-single": 'psi-mi:"MI:2339"(electron microscopy 3d single particle reconstruction)',
    "electron microscopy": 'psi-mi:"MI:0040"(electron microscopy)',

    # Other experimental methods
    "protein complementation assay": 'psi-mi:"MI:0090"(protein complementation assay)',
    "protease assay": 'psi-mi:"MI:0428"(protease assay)',
    "molecular sieving": 'psi-mi:"MI:0071"(molecular sieving)',
    "cross-linking study": 'psi-mi:"MI:0030"(cross-linking study)',
    "protein array": 'psi-mi:"MI:0089"(protein array)',
    "mass spectrometry":'psi-mi:"MI:0427"(mass spectrometry)',

    # Generic
    "unspecified method": 'psi-mi:"MI:0686"(unspecified method)'
    }   
    rows=[]
    interactions=data[1]['Interactors']
    for interaction in interactions:
        row={}
        for column in final_columns:
            row[column]="-"
        row["#ID(s) interactor A"]=f"uniprotkb:{interaction.get("Interactor_A",'-')}"
        row["ID(s) interactor B"]=f"uniprotkb:{interaction.get("Interactor_B",'-')}"
        row["Source database(s)"]='psi-mi:"MI:0463"(biogrid)'

        if "Interaction type(s)" in final_columns:
            for type in interaction.get("Interaction_Type",'-'):
                if type in BIOGRID_TYPE_CODES.keys():
                    row['BioGrid interaction type(s)']=BIOGRID_TYPE_CODES[type]
                else:
                    row['BioGrid interaction type(s)']=type

        if "BioGrid interaction detection method(s)" in final_columns:
            method=interaction.get("Interaction_Detection_Method",'-')
            if method in interaction_detection_methods.keys():
                row['BioGrid interaction detection method(s)']=interaction_detection_methods[method]
            else:
                row['BioGrid interaction detection method(s)']=method
        rows.append(row)
    return rows


def populate_corum(data:list,final_columns:list,selected_columns:list,uniprot_id,tax_id):
    purification_methods = {
    # Immunoprecipitation-based
    "coimmunoprecipitation": 'psi-mi:"MI:0019"(coimmunoprecipitation)',
    "anti bait coip": 'psi-mi:"MI:0006"(anti bait coimmunoprecipitation)',
    "anti tag coip": 'psi-mi:"MI:0007"(anti tag coimmunoprecipitation)',
    "immunoprecipitation": 'psi-mi:"MI:0098"(immunoprecipitation)',

    # Affinity purification
    "affinity chromatography technology": 'psi-mi:"MI:0004"(affinity chromatography technology)',
    "affinity purification": 'psi-mi:"MI:0004"(affinity chromatography technology)',
    "pull down": 'psi-mi:"MI:0096"(pull down)',
    "gst pull down": 'psi-mi:"MI:0079"(gst pull down)',
    "his pull down": 'psi-mi:"MI:0061"(his pull down)',
    "tandem affinity purification": 'psi-mi:"MI:0676"(tandem affinity purification)',
    "tap": 'psi-mi:"MI:0676"(tandem affinity purification)',

    # Chromatography / separation
    "molecular sieving": 'psi-mi:"MI:0071"(molecular sieving)',
    "gel filtration": 'psi-mi:"MI:0071"(molecular sieving)',
    "size exclusion chromatography": 'psi-mi:"MI:0071"(molecular sieving)',

    # Other commonly seen isolation methods
    "cell fractionation": 'psi-mi:"MI:0025"(cell fractionation)',
    "centrifugation": 'psi-mi:"MI:0027"(centrifugation)',
    "density gradient centrifugation": 'psi-mi:"MI:0031"(density gradient centrifugation)',

    # Generic
    "unspecified method": 'psi-mi:"MI:0686"(unspecified method)',
    }
    rows=[]
    info=data[0]['info']
    interactions=data[1]['Interactors']
    for interaction in interactions:
        row={}
        for column in final_columns:
            row[column]="-"
        row["#ID(s) interactor A"]=f"uniprotkb:{interaction.get("Interactor_A",'-')}"
        row["ID(s) interactor B"]=f"uniprotkb:{interaction.get("Interactor_B",'-')}"
        row["Source database(s)"]='psi-mi:"MI:0464"(corum)'
        if "Corum complex name(s)" in final_columns:
            row['CORUM complex name(s)']=info.get("complex_name",'-')

        if 'Corum cell line(s)' in final_columns:
            row['CORUM cell line(s)']=info.get("cell_line",'-')

        if "Corum purification method(s)" in final_columns:
            for methods in info.get("Purification_Method",'-'):
                if methods in purification_methods.keys():
                    row['Corum purification method(s)']=purification_methods[methods]
                else:
                    row['Corum purification method(s)']=methods
        rows.append(row)
    return rows

DBs={
    "String":populate_string,
    "Predictomes":populate_predictomes,
    "BioGrid":populate_biogrid,
    "IntAct":populate_intact,
    "HuRI":populate_huri,
    "Corum":populate_corum,
}



