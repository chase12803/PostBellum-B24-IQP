import json
import pandas as pd

# Input file paths
generated_file = input("Enter the path to the generated JSON file: ").strip()
labeled_file = input("Enter the path to the labeled CSV file: ").strip()

# Load generated JSON data
generated_data = []

def fix_single_quotes_to_double(json_line):
    """Replace single quotes with double quotes for JSON compatibility."""
    import re
    return re.sub(r"(?<!\\)'", '"', json_line)

with open(generated_file, 'r', encoding='utf-8') as file:
    for line_number, line in enumerate(file, start=1):
        line = line.strip()
        if line_number == 1 or not line:  # Skip the instruction file line and empty lines
            continue
        try:
            fixed_line = fix_single_quotes_to_double(line)
            generated_data.append(json.loads(fixed_line))
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON on line {line_number}: {e}")

# Load labeled CSV data
labeled_data = pd.read_csv(labeled_file)

# Add generated JSON outputs into the CSV with proper formatting
for i, generated in enumerate(generated_data):
    labeled_data.loc[i, 'generated_past'] = json.dumps(generated.get('past', []))
    labeled_data.loc[i, 'generated_present'] = json.dumps(generated.get('present', []))
    labeled_data.loc[i, 'generated_czech_regions'] = json.dumps(generated.get('czech_regions', []))

# Initialize results
results = {
    "past": {"precision": 0, "recall": 0, "f1": 0},
    "present": {"precision": 0, "recall": 0, "f1": 0},
    "czech_regions": {"precision": 0, "recall": 0, "f1": 0},
}

# Evaluate each category
for category, ground_truth_col in [("past", "past_countries"), 
                                   ("present", "present_countries"), 
                                   ("czech_regions", "czech_regions")]:
    ground_truth = labeled_data[ground_truth_col].apply(lambda x: set(eval(x)) if isinstance(x, str) else set())
    generated = labeled_data[f"generated_{category}"].apply(lambda x: set(eval(x)) if isinstance(x, str) else set())

    
    # Calculate true positives, false positives, and false negatives
    true_positives = []
    false_positives = []
    false_negatives = []
    for gt, gen in zip(ground_truth, generated):
        true_positives.append(len(gen & gt))  # Intersection of sets
        false_positives.append(len(gen - gt))  # Items in generated but not in ground truth
        false_negatives.append(len(gt - gen))  # Items in ground truth but not in generated
    
    # Convert lists to pandas Series for aggregation
    true_positives = pd.Series(true_positives)
    false_positives = pd.Series(false_positives)
    false_negatives = pd.Series(false_negatives)
    
    # Compute metrics
    precision = true_positives.sum() / (true_positives.sum() + false_positives.sum()) if true_positives.sum() + false_positives.sum() > 0 else 0
    recall = true_positives.sum() / (true_positives.sum() + false_negatives.sum()) if true_positives.sum() + false_negatives.sum() > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0

    # Store metrics
    results[category]["precision"] = precision
    results[category]["recall"] = recall
    results[category]["f1"] = f1

# Save updated labeled data with generated columns
output_file = input("Enter the name for the output CSV file (with .csv extension): ").strip()
labeled_data.to_csv(output_file, index=False)

# Print metrics
print("Evaluation Metrics:")
for category, metrics in results.items():
    print(f"\n{category.capitalize()} Countries:")
    print(f"  Precision: {metrics['precision']:.2f}")
    print(f"  Recall: {metrics['recall']:.2f}")
    print(f"  F1 Score: {metrics['f1']:.2f}")
