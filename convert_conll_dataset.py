import os
import json
import datetime
from docx import Document

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIRS = [
    os.path.join(BASE_DIR, 'data', 'conll2002'),
    os.path.join(BASE_DIR, 'data', 'conll2003')
]
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
OUTPUT_SUBDIRS = {
    "log": os.path.join(OUTPUT_DIR, 'log'),
    "srt": os.path.join(OUTPUT_DIR, 'srt'),
    "docx": os.path.join(OUTPUT_DIR, 'docx'),
    "json": os.path.join(OUTPUT_DIR, 'json')
}
GROUND_TRUTH_JSON_PATH = os.path.join(OUTPUT_SUBDIRS["json"], 'ground_truth_persons.json')

# --- Helper Functions ---

def ensure_dir(directory):
    """Creates a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def parse_conll_file(file_path):
    """
    Parses a CoNLL-formatted file and yields sentences.
    Each sentence is a list of (token, tag) tuples.
    """
    # Try UTF-8 first, then fall back to Latin-1 for legacy CoNLL files
    encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1']
    
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                sentence = []
                for line in f:
                    line = line.strip()
                    if line.startswith('-DOCSTART-') or line == '':
                        if sentence:
                            yield sentence
                            sentence = []
                    else:
                        parts = line.split()
                        # Format: token pos_tag chunk_tag ner_tag
                        token = parts[0]
                        tag = parts[-1]
                        sentence.append((token, tag))
                if sentence: # Yield the last sentence if file doesn't end with a newline
                    yield sentence
            break  # Successfully processed with this encoding
        except UnicodeDecodeError:
            if encoding == encodings_to_try[-1]:  # Last encoding failed
                raise
            continue  # Try next encoding

def format_time(seconds):
    """Converts seconds to SRT time format HH:MM:SS,ms"""
    delta = datetime.timedelta(seconds=seconds)
    return (datetime.datetime(1, 1, 1) + delta).strftime('%H:%M:%S,000')

def extract_person_names(sentence):
    """Extracts person names from a tagged sentence."""
    names = set()
    current_name = []
    for token, tag in sentence:
        if tag == 'B-PER':
            if current_name:
                names.add(" ".join(current_name))
            current_name = [token]
        elif tag == 'I-PER':
            if current_name:
                current_name.append(token)
        else:
            if current_name:
                names.add(" ".join(current_name))
                current_name = []
    if current_name: # Add the last name if the sentence ends with it
        names.add(" ".join(current_name))
    return names

# --- Main Logic ---

def main():
    """Main function to drive the conversion process."""
    print("Starting CoNLL data conversion...")

    # 1. Create all necessary output directories
    ensure_dir(OUTPUT_DIR)
    for subdir in OUTPUT_SUBDIRS.values():
        ensure_dir(subdir)
    print(f"Output directories created at: {OUTPUT_DIR}")

    all_person_names = set()
    files_to_process = []

    # Find all data files
    for data_dir in DATA_DIRS:
        if not os.path.exists(data_dir):
            print(f"Warning: Data directory not found: {data_dir}")
            continue
        for root, _, files in os.walk(data_dir):
            for file in files:
                # Exclude processed/indexed files from other scripts
                if not file.endswith(('.index', '.torch')):
                    files_to_process.append(os.path.join(root, file))

    print(f"\nFound {len(files_to_process)} files to process.")

    # 2. Process each file
    for file_path in files_to_process:
        relative_path = os.path.relpath(file_path, BASE_DIR).replace(os.path.sep, '_')
        print(f"  - Processing: {relative_path}")

        # Prepare output files
        log_file_path = os.path.join(OUTPUT_SUBDIRS['log'], f"{relative_path}.log")
        srt_file_path = os.path.join(OUTPUT_SUBDIRS['srt'], f"{relative_path}.srt")
        docx_path = os.path.join(OUTPUT_SUBDIRS['docx'], f"{relative_path}.docx")

        doc = Document()
        
        with open(log_file_path, 'w', encoding='utf-8') as log_f, \
             open(srt_file_path, 'w', encoding='utf-8') as srt_f:

            srt_counter = 1
            for sentence in parse_conll_file(file_path):
                # Extract ground truth person names
                person_names_in_sentence = extract_person_names(sentence)
                all_person_names.update(person_names_in_sentence)

                # Get plain text sentence
                sentence_text = " ".join([token for token, tag in sentence])

                # Write to .log file
                log_f.write(sentence_text + '\n')

                # Write to .srt file
                start_time = format_time(srt_counter - 1)
                end_time = format_time(srt_counter)
                srt_f.write(f"{srt_counter}\n")
                srt_f.write(f"{start_time} --> {end_time}\n")
                srt_f.write(f"{sentence_text}\n\n")
                srt_counter += 1
                
                # Add to .docx document
                doc.add_paragraph(sentence_text)
        
        doc.save(docx_path)

    # 3. Save the collected unique person names to the ground truth JSON file
    sorted_names = sorted(list(all_person_names))
    with open(GROUND_TRUTH_JSON_PATH, 'w', encoding='utf-8') as json_f:
        json.dump(sorted_names, json_f, indent=4)

    print(f"\nSuccessfully extracted {len(sorted_names)} unique person names.")
    print(f"Ground truth JSON saved to: {GROUND_TRUTH_JSON_PATH}")
    print("\nConversion process complete!")


if __name__ == "__main__":
    main()