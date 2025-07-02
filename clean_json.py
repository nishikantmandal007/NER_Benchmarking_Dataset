#!/usr/bin/env python3
import json
import re
import os

def clean_person_name(name):
    """Clean and normalize person names."""
    # Remove extra quotes and apostrophes
    name = re.sub(r'^["\'\s]+|["\'\s]+$', '', name)  # Remove leading/trailing quotes and spaces
    name = re.sub(r'^"([^"]*)"$', r'\1', name)  # Remove surrounding quotes
    name = re.sub(r"^'([^']*)'$", r'\1', name)  # Remove surrounding single quotes
    
    # Remove multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

def is_valid_person_name(name):
    """Filter out non-person entries."""
    # Skip if empty or too short
    if not name or len(name.strip()) < 2:
        return False
    
    # Skip entries that are clearly not person names
    exclude_patterns = [
        r'^familia\s+',  # "familia X"
        r'^duque[s]?\s+',  # "duque de X", "duques de X"  
        r'^marqu[eé]s\s+',  # "marqués de X"
        r'^lord\s+',  # "lord X"
        r'^rey\s+|^reina\s+',  # "rey X", "reina X"
        r'^infanta?\s+',  # "infante X", "infanta X"
        r'^archiduque\s+',  # "archiduque X"
        r'^fray\s+',  # "fray X" (might be valid, but often titles)
        r'^hermanos?\s+',  # "hermanos X"
        r'abogado\s+general',  # legal titles
        r'^doctor\s+|^dr\.\s*',  # doctor titles
        r'^profesor\s+',  # professor titles
        r'^general\s+',  # military titles
        r'^capitán\s+',  # military titles
        r'^comandante\s+',  # military titles
        r'^teniente\s+',  # military titles
        r'^presidente\s+',  # political titles
        r'^ministro\s+',  # political titles
        r'^alcalde\s+',  # political titles
        r'^consejero\s+',  # political titles
        r'^secretario\s+',  # political titles
        r'^director\s+',  # job titles
        r'^delegado\s+',  # job titles
        r'\.com$',  # website addresses
        r'^www\.',  # website addresses
        r'^\d+$',  # pure numbers
        r'^[A-Z]+$',  # all caps abbreviations (like EFECOM)
        r'^\w\.\s*\w\.$',  # initials like "A. B."
        r'^\w\.\s*\w\.\s*\w\.$',  # initials like "A. B. C."
    ]
    
    name_lower = name.lower()
    for pattern in exclude_patterns:
        if re.search(pattern, name_lower):
            return False
    
    # Additional checks for likely non-person entries
    if name_lower in ['efe', 'efecom', 'psoe', 'pp', 'ugt', 'ccoo']:
        return False
        
    return True

def main():
    input_file = '/workspaces/NER_Benchmarking_Dataset/output/json/ground_truth_persons.json'
    output_file = '/workspaces/NER_Benchmarking_Dataset/output/json/ground_truth_persons_cleaned.json'
    
    print("Loading original JSON file...")
    with open(input_file, 'r', encoding='utf-8') as f:
        original_names = json.load(f)
    
    print(f"Original count: {len(original_names)} names")
    
    # Clean and filter names
    cleaned_names = []
    for name in original_names:
        cleaned = clean_person_name(name)
        if is_valid_person_name(cleaned):
            cleaned_names.append(cleaned)
    
    # Remove duplicates and sort
    unique_names = sorted(list(set(cleaned_names)))
    
    print(f"After cleaning and filtering: {len(unique_names)} names")
    print(f"Removed: {len(original_names) - len(unique_names)} entries")
    
    # Save cleaned version
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_names, f, indent=2, ensure_ascii=False)
    
    print(f"Cleaned JSON saved to: {output_file}")
    
    # Show some examples of what was cleaned
    print("\nSample of cleaned names:")
    for i, name in enumerate(unique_names[:10]):
        print(f"  {i+1:2d}. {name}")
    
    print("\nSample of removed entries:")
    removed_examples = []
    for orig in original_names[:50]:  # Check first 50 for examples
        cleaned = clean_person_name(orig)
        if not is_valid_person_name(cleaned):
            removed_examples.append(f"{orig} -> {cleaned}")
            if len(removed_examples) >= 10:
                break
    
    for example in removed_examples:
        print(f"  - {example}")

if __name__ == "__main__":
    main()
