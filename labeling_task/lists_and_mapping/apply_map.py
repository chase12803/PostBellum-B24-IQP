import pandas as pd
import json


def filter_witness(label_dict, map_dict, type):
    past = list(set(label_dict['past']))
    present = list(set(label_dict['present']))
    regions = list(set(label_dict['czech_regions']))
    past_final = [x for x in past]
    present_final = [x for x in present]
    regions_final = [x for x in regions]
    
    for dict in map_dict:
        if type == 'past':
            for country in past:
                if country in dict['labeled']:
                    try:
                        past_final.remove(country)
                    except ValueError:
                        print(f"trying to remove {country} from {past_final}")
                    past_final.extend(dict['correct_past'])
                    present_final.extend(dict['correct_present'])
        elif type == 'present':
            for country in present:
                if country in dict['labeled']:
                    try:
                        present_final.remove(country)
                    except ValueError:
                        print(f"trying to remove {country} from {present_final}")
                    past_final.extend(dict['correct_past'])
                    present_final.extend(dict['correct_present'])
        else:
            for region in regions:
                if region in dict['labeled']:
                    try:
                        regions_final.remove(region)
                    except ValueError:
                        print(f"trying to remove {country} from {regions_final}")
                    regions_final.extend(dict['correct'])
    
    final_dict = {"past": list(set(past_final)), "present": list(set(present_final)), "czech_regions": list(set(regions_final))}
    return final_dict


def apply_to_all(df, map_dict, type):
    if isinstance(df['past'].tolist()[0], str):
        past = [eval(x) for x in df['past'].tolist()]
        present = [eval(x) for x in df['present'].tolist()]
        region = [eval(x) for x in df['czech_regions'].tolist()]
    else:
        past = df['past'].tolist()
        present = df['present'].tolist()
        region = df['czech_regions'].tolist()
    lists = list(zip(past, present, region))
    dicts = []
    for x, y, z in lists:
        dicts.append({"past": x, "present": y, "czech_regions": z})
    
    dicts = [filter_witness(x, map_dict, type) for x in dicts]
    pasts = [x['past'] for x in dicts]
    presents = [x['present'] for x in dicts]
    regions = [x['czech_regions'] for x in dicts]
    
    df['past'] = pasts
    df['present'] = presents
    df['czech_regions'] = regions
    return df


df_file = 'Witness_biography_published_All_en_labeled_fixed'
past_file = 'lists llm/past_map.json'
present_file = 'lists llm/present_map.json'
region_file = 'lists llm/regions_map.json'

with open(past_file, 'r') as file:
    map_past = json.load(file)
with open(present_file, 'r') as file:
    map_present = json.load(file)
with open(region_file, 'r') as file:
    map_regions = json.load(file)
    
with open(f'{df_file}.csv', encoding='utf-8-sig', errors='replace') as file:
    final_df = pd.read_csv(file)

final_df = apply_to_all(final_df, map_past, 'past')
final_df = apply_to_all(final_df, map_present, 'present')
final_df = apply_to_all(final_df, map_regions, 'regions')

final_df.to_csv(f'{df_file}_filtered.csv', index=False, encoding='utf-8-sig')