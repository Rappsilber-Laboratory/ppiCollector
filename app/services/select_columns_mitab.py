def default():
    final_columns=["#ID(s) interactor A",
    "ID(s) interactor B",
    "Taxid interactor A",
    "Taxid interactor B",
    "Source database(s)"]
    return final_columns

def select_columns_from_string(selected_columns:list,final_columns):
    string_scores=['combined_score','gene_neighbourhood_score','gene_fusion_score',
    'phylogenetic_profile_score','experimental_score','coexpression_score','textmining_score',
    'database_score']

    if any(s in selected_columns for s in string_scores):
        if("Confidence value(s)" not in final_columns):
            final_columns.append("Confidence value(s)")
            

def select_columns_from_intact(selected_columns:list,final_columns):
    intact_scores = ['Interaction_Score_Intact', 'Num_Interaction_IntAct',
                     'Minimum_feature_count', 'Maximum_feature_count']
    if any(s in selected_columns for s in intact_scores):
        if "Confidence value(s)" not in final_columns:
            final_columns.append("Confidence value(s)")
            
    if 'Unique_Identification_Methods' in selected_columns:
        final_columns.append("Participant identification method(s)")
    if 'PubMed_Ids' in selected_columns:
        final_columns.append("Publication Identifier(s)")

def select_columns_from_biogrid(selected_columns:list,final_columns):

    if 'Interaction_Detection_Method' in selected_columns:
        final_columns.append("BioGrid interaction detection method(s)")
    if 'Interaction_Type' in selected_columns:
        final_columns.append("Interaction type(s)")
    if 'Confidence_Score' in selected_columns:
        if("Confidence value(s)" not in final_columns):
            final_columns.append("Confidence value(s)")
            
    
def select_columns_from_predictomes(selected_columns:list,final_columns):
    predictomes_scores=['spoc_score','kirc_score','num_unique_contacts']
    if any(s in selected_columns for s in predictomes_scores):
        if("Confidence value(s)" not in final_columns):
            final_columns.append("Confidence value(s)")
            

    
def select_columns_from_corum(selected_columns:list,final_columns):
    if 'complex_name' in selected_columns:
        final_columns.append("Corum complex name(s)")
    if 'cell_line' in selected_columns:
        final_columns.append("Corum cell line(s)")
    if 'Purification_Method' in selected_columns:
        final_columns.append("Corum purification method(s)")
        
def select_columns_from_huri(selected_columns:list,final_columns):
    pass


COLUMN_BUILDERS = {
    "String": select_columns_from_string,
    "IntAct": select_columns_from_intact,
    "BioGrid": select_columns_from_biogrid,
    "Predictomes": select_columns_from_predictomes,
    "Corum": select_columns_from_corum,
    "HuRI": select_columns_from_huri
}

def build_final_columns(selected_databases,selected_columns):
    final_columns=default()
    for db in selected_databases:
        if db in COLUMN_BUILDERS:
            COLUMN_BUILDERS[db](selected_columns,final_columns)
    return final_columns
    
