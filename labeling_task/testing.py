import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import pandas as pd
import os
import time
import json
import typing_extensions as typing


class CountryList(typing.TypedDict):
    present: list[str]
    past: list[str]
    

class TerritoryList(typing.TypedDict):
    territories: list[str]


class TownList(typing.TypedDict):
    czech_towns: list[str]


class RegionList(typing.TypedDict):
    czech_regions: list[str]


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
            with open('last.txt', 'r') as file:
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
        bios = pd.read_csv(f'{bio_file}.csv')
    except FileNotFoundError:
        print("Biography file not found.")
        input("Press enter to exit.")
        exit()

    # save new filenames to last.txt
    with open('last.txt', 'w') as file:
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
                                inst_dict['retry'] if 'retry' in inst_dict.keys() else [None for _ in inst_dict['country']],
                                inst_dict['occupation'] if 'occupation' in inst_dict.keys() else [None for _ in inst_dict['country']],
                                inst_dict['towns'] if 'towns' in inst_dict.keys() else [None for _ in inst_dict['country']],
                                inst_dict['region']))

    # Find number of total prompts and confirm with user
    num_instruct = len(instructions)
    num_bios = len(bios.index)

    print(f'Running this script will process {
          num_instruct * num_bios} prompts. The Gemini 1.5 Pro API permits only 50 free requests per day.')
    confirm = input('Are you sure you want to continue? [y]/n: ').lower()

    if confirm == 'n':
        exit()
    sleep = input(
        'How many seconds should the script sleep between requests? (int): ')

    # set api key
    genai.configure(api_key=api_key)

    # format location string
    locs = f"\nPresent: {locs_dict['present']}\nPast: {
        locs_dict['past']}\nCzech Regions: {locs_dict['czech_regions']}"

    # makes output file, adds instruction file line
    if not os.path.exists('output'):
        os.mkdir('output')

    # with open(f'output/{out_file}.txt', 'w') as file:
    #     print(instruction_file, file=file)
    # with open(f'output/{out_file}_nofilter.txt', 'w') as file:
    #     print(instruction_file, file=file)

    # prompting loop
    print('\nBeginning Prompting.\n')
    for i, insts in enumerate(instructions):

        # fill in keys in all parts of the prompt
        final_insts = [x.replace('[PRESENT LIST]', f'Present: {locs_dict['present']}').replace('[PAST LIST]', f'Past: {locs_dict['past']}').replace(
            '[CZREGION LIST]', f'Czech Regions: {locs_dict['czech_regions']}').replace('[REGION LIST]', locs) + "\n" for x in insts]

        # load the model with the system prompt
        model = genai.GenerativeModel(
            "gemini-1.5-pro", system_instruction=final_insts[0])

        country_filter = genai.GenerativeModel(
            "gemini-1.5-pro", system_instruction="You are an AI assistant who is an expert at processing lists of countries. You are tasked with normalizing lists of countries by replacing country names with the shorter generic variants. For example, the short version of the Union of Soviet Socialist Republics is simply Soviet Union, or for the Czech Republic it is simply Czechia. Country name abbreviations and 3-letter codes are not relevant.")

        print(f'Instruction: {i+1}/{len(instructions)}')

        # start processing biographies
        past, present, regions = [[] for _ in range(num_bios)], [[] for _ in range(num_bios)], [[] for _ in range(num_bios)]
        for j, bio in enumerate(bios['field_biography_value'].tolist()):
            re1_dict = {"present": [], "past": []}
            re11_dict = {"present": [], "past": []}
            re125_dict = {"territories": []}
            re15_dict = {"czech_towns": []}
            re2_dict = {"czech_regions": []}
            print(f'Bio: {j+1}/{len(bios)}')
            try:
                # start a chat
                chat = model.start_chat()

                # prompt the model for a list of countries
                response1 = chat.send_message(f'{final_insts[1]}\n\nBiography: {bio}',
                                              generation_config=genai.GenerationConfig(response_mime_type="application/json",
                                                                                       response_schema=CountryList))
                # print(response1.text)
                if final_insts[2] is not None:
                    response1_1 = chat.send_message(final_insts[2],
                                                generation_config=genai.GenerationConfig(response_mime_type="application/json",
                                                                                        response_schema=CountryList))
                    # print(response1_1.text)
                if final_insts[3] is not None:
                    response1_25 = chat.send_message(final_insts[3],
                                                generation_config=genai.GenerationConfig(response_mime_type="application/json",
                                                                                        response_schema=TerritoryList))
                    re125_dict = json.loads(response1_25.text)
                
                # save pre-filtered output
                final_country_list = response1.text if final_insts[2] is None else response1_1.text
                # with open(f'output/{out_file}_nofilter.txt', 'a', encoding='utf-8') as file:
                #     print(final_country_list, file=file)
                

                # read the first output, prompt for czech regions if czechia is labelled
                # Given the following JSON formatted string, respond with an identical JSON object, but replace all country names with the generic shortened version of the country name if necessary. Do not split country names into two, or replace country names with modern variants in the past field.
                # Given the following JSON formatted string, respond with an identical JSON object, but replace all country names with the generic shortened version of the country name if necessary. **Do not under any circumstances add any new countries to the list. Only replace existing countries in the list if necessary. Do not split country names into two, or replace country names with modern variants in the past field. Do not move countries from the field the are currently in.**
                # filter_response1 = chat.send_message(f'Given the following JSON formatted string, respond with an identical JSON object, but replace all country names with the generic shortened version of the country name if necessary. Do not split country names into two, or replace country names with modern variants in the past field.\n{response1.text}\n{final_country_list}',
                #                                                    generation_config=genai.GenerationConfig(response_mime_type="application/json", response_schema=CountryList))
                # add territories to countries
                re1_dict = json.loads(final_country_list)
                re1_dict['past'] = re1_dict['past'] + re125_dict['territories']
                
                # check for czech and prompt for towns/regions
                if 'Czechia' in re1_dict['present'] or 'Czechoslovakia' in re1_dict['past']:
                    if final_insts[2] is None:
                        response2 = chat.send_message(final_insts[5],
                                                      generation_config=genai.GenerationConfig(response_mime_type="application/json",
                                                                                               response_schema=RegionList))
                    else:
                        response1_5 = chat.send_message(final_insts[4],
                                                        generation_config=genai.GenerationConfig(response_mime_type="application/json",
                                                                                                 response_schema=TownList))
                        response2 = chat.send_message(final_insts[5],
                                                      generation_config=genai.GenerationConfig(response_mime_type="application/json",
                                                                                               response_schema=RegionList))
                        re15_dict = json.loads(response1_5.text)
                    re2_dict = json.loads(response2.text)

                # merge dictionaries for output
                merged_dict = {**re1_dict, **re15_dict, **re2_dict}

                # sleep a given amount of time
                if int(sleep) > 0:
                    print('Sleeping')
                    for i in range(int(sleep)):
                        print(f"\r{' ' * len(sleep)}", end='', flush=True)
                        print(f"\r{int(sleep)-i}", end='', flush=True)
                        time.sleep(1)
                    print()

                # write to file
                past[j] = merged_dict['past']
                present[j] = merged_dict['present']
                regions[j] = merged_dict['czech_regions']
                
                bios['past'] = past
                bios['present'] = present
                bios['czech_regions'] = regions
                
                if j % 10 == 0:
                    bios.to_csv(f'{out_file}.csv', index=False)

            except ResourceExhausted as error:
                print(f"Possibly out of free requests, or too many requests on this API key ({
                      key_file}).")
                print(f'\n{error}\n')
                input("Press enter to exit.")
                break
    bios.to_csv(f'{out_file}.csv', index=False)
