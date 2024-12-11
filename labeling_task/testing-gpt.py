# import google.generativeai as genai
# from google.api_core.exceptions import ResourceExhausted
from openai import OpenAI
from pydantic import BaseModel
import pandas as pd
import os
import time
import json
import typing_extensions as typing


class CountryList(BaseModel):
    present: list[str]
    past: list[str]


class TerritoryList(BaseModel):
    territories: list[str]


class TownList(BaseModel):
    czech_towns: list[str]


class RegionList(BaseModel):
    czech_regions: list[str]



MODEL = "gpt-4o"
def chat_4o(prompt, output_format):
    context.append({"role": "user", "content": prompt})
    # print(context)
    response = client.beta.chat.completions.parse(
        model=MODEL,
        messages=context,
        response_format=output_format,
    )
    output = response.choices[0].message
    context.append({"role": "assistant", "content": output.content})
    print(output.content)
    return output.content


if __name__ == '__main__':
    print("=================================\nPost Bellum B24 IQP LLM Labelling\n=================================\n")
    print("When being prompted for any filenames, input 'last'/'lastall' to reuse the most recently used file(s).")
    key_file = input('API Key Filename (txt): ')
    if key_file == 'lastall':
        key_file = 'last'
        instruction_file = 'last'
        bio_file = 'last'
        out_file = 'last'
    else:
        instruction_file = input(
            'Instruction Filename (json with system, country, town(optional) and region fields for each stage of prompting): ')
        bio_file = input(
            "Biographies Filename (csv with 'nid' and 'field_biography_value' columns): ")
        out_file = input("Output Filename: ")

    # find previous filenames if using last
    if 'last' in [key_file, instruction_file, bio_file]:
        try:
            with open('last-gpt.txt', 'r') as file:
                lasts = file.readlines()

            lasts = [elt.strip('\n') for elt in lasts]

            if key_file == 'last':
                key_file = lasts[0]

            if instruction_file == 'last':
                instruction_file = lasts[1]

            if bio_file == 'last':
                bio_file = lasts[2]

            if out_file == 'last':
                out_file = lasts[3]
        except FileNotFoundError:
            print("Could not locate previous filenames.")
            input("Press enter to exit.")
            exit()

    # read all content in the files
    try:
        with open(key_file, 'r') as file:
            api_key = file.read()
    except FileNotFoundError:
        print("API key file not found.")
        input("Press enter to exit.")
        exit()

    try:
        with open(instruction_file, 'r') as file:
            inst_dict = json.load(file)
    except FileNotFoundError:
        print("Instructions file not found.")
        input("Press enter to exit.")
        exit()

    try:
        bios = pd.read_csv(bio_file)
    except FileNotFoundError:
        print("Biography file not found.")
        input("Press enter to exit.")
        exit()

    # save new filenames to last.txt
    with open('last-gpt.txt', 'w') as file:
        for filename in [key_file, instruction_file, bio_file, out_file]:
            print(filename, file=file)

    # also grab list of locations
    try:
        with open('prompt_components/tomas_locs.json', 'r', encoding='utf-8') as file:
            locs_dict = json.load(file)
    except FileNotFoundError:
        print("prompt_components/tomas_locs.json not found.")
        input("Press enter to exit.")
        exit()

    instructions = list(zip(inst_dict['system'],
                            inst_dict['country'],
                            inst_dict['retry'] if 'retry' in inst_dict.keys(
    ) else [None for _ in inst_dict['country']],
        inst_dict['occupation'] if 'occupation' in inst_dict.keys() else [
        None for _ in inst_dict['country']],
        inst_dict['towns'] if 'towns' in inst_dict.keys(
    ) else [None for _ in inst_dict['country']],
        inst_dict['region']))

    # Find number of total prompts and confirm with user
    num_instruct = len(instructions)
    num_bios = len(bios.index)

    print(f'Running this script will process {num_instruct * num_bios} prompts.')
    confirm = input('Are you sure you want to continue? [y]/n: ').lower()

    if confirm == 'n':
        exit()
    sleep = input(
        'How many seconds should the script sleep between requests? (int): ')

    # set api key
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", api_key))

    # format location string
    locs = f"\nPresent: {locs_dict['present']}\nPast: {
        locs_dict['past']}\nCzech Regions: {locs_dict['czech_regions']}"

    # makes output file, adds instruction file line
    if not os.path.exists('output'):
        os.mkdir('output')

    with open(f'output/{out_file}.txt', 'w') as file:
        print(instruction_file, file=file)
    with open(f'output/{out_file}_nofilter.txt', 'w') as file:
        print(instruction_file, file=file)

    # prompting loop
    print('\nBeginning Prompting.\n')
    for i, insts in enumerate(instructions):

        # fill in keys in all parts of the prompt
        final_insts = [x.replace('[PRESENT LIST]', f'Present: {locs_dict['present']}').replace('[PAST LIST]', f'Past: {locs_dict['past']}').replace(
            '[CZREGION LIST]', f'Czech Regions: {locs_dict['czech_regions']}').replace('[REGION LIST]', locs) + "\n" if x is not None else None for x in insts]

        print(f'Instruction: {i+1}/{len(instructions)}')

        # start processing biographies
        for j, bio in enumerate(bios['field_biography_value'].tolist()):
            context = [{"role": "system", "content": final_insts[0]}]

            re1_dict = {"present": [], "past": []}
            re11_dict = {"present": [], "past": []}
            re125_dict = {"territories": []}
            re15_dict = {"czech_towns": []}
            re2_dict = {"czech_regions": []}
            print(f'Bio: {j+1}/{len(bios)}')
        
            # prompt the model for a list of countries
            response1 = chat_4o(f'{final_insts[1]}\n\nBiography: {bio}', CountryList)
            
            if final_insts[2] is not None:
                response1_1 = chat_4o(final_insts[2], CountryList)
                re1_dict = json.loads(response1_1)
            if final_insts[3] is not None:
                response1_25 = chat_4o(final_insts[3], TerritoryList)
                re125_dict = json.loads(response1_25)

            # save pre-filtered output
            final_country_list = response1 if final_insts[2] is None else response1_1
            with open(f'output/{out_file}_nofilter.txt', 'a', encoding='utf-8') as file:
                print(final_country_list, file=file)
                
            # add territories to countries
            # re1_dict = json.loads(filter_response1.text)
            re1_dict['past'] = re1_dict['past'] + re125_dict['territories']

            # check for czech and prompt for towns/regions
            if 'Czechia' in re1_dict['present'] or 'Czechoslovakia' in re1_dict['past']:
                if final_insts[2] is not None:
                    response1_5 = chat_4o(final_insts[4], TownList)
                    re15_dict = json.loads(response1_5)
                
                response2 = chat_4o(final_insts[5], RegionList)
                re2_dict = json.loads(response2)

            # merge dictionaries for output
            merged_dict = {**re1_dict, **re15_dict, **re2_dict}

            # sleep a given amount of time
            print('Sleeping')
            for i in range(int(sleep)):
                print(f"\r{' ' * len(sleep)}", end='', flush=True)
                print(f"\r{int(sleep)-i}", end='', flush=True)
                time.sleep(1)
            print()

            # write to file
            with open(f'output/{out_file}.txt', 'a', encoding='utf-8') as file:
                print(merged_dict, file=file)
