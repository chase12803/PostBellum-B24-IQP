`gui.py` is a simple GUI tool to make manual labeling a CSV of biographies more pleasant. Has pre-defined buttons for the 14 Czech regions and some other common countries/regions.

`testing.py` takes in a JSON-formatted instruction from the `./instructions` folder and labels every biography in an input CSV using Gemini 1.5 Pro [needs paid key]. Uses chain-of-thought prompting — starts with system prompt, then asks for country, then conditionally asks for Czech regions if the answer included Czechia or Czechoslovakia; later prompts include two optional intermediate steps for better labeling.

`testing-gpt.py` is the same as testing.py, but instead using the GPT API [needs paid key].

`evaluate.py` takes in the output of either testing script, compares the two lists for the three categories of locations, and saves precision, recall, and F1 scores to a CSV.