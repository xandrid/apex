import json
import os
import random
import re

DATA_PATH = os.path.join(os.path.dirname(__file__), '../apex_data/chunks.json')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'hard_negatives.json')

# Deterministic Substitution Dictionary
# Simple technical antonyms/replacements
SUBSTITUTIONS = {
    # Materials
    r"\bcopper\b": "aluminum",
    r"\baluminum\b": "copper",
    r"\bmetal\b": "plastic",
    r"\bplastic\b": "metal",
    r"\bglass\b": "ceramic",
    r"\bceramic\b": "glass",
    
    # State/Connectivity
    r"\bwireless\b": "wired",
    r"\bwired\b": "wireless",
    r"\bconnected\b": "disconnected",
    r"\bdisconnected\b": "connected",
    r"\bautomatic\b": "manual",
    r"\bmanual\b": "automatic",
    
    # Logic/Quantity
    r"\bplurality\b": "single",
    r"\bsingle\b": "plurality",
    r"\bincrease\b": "decrease",
    r"\bdecrease\b": "increase",
    r"\babove\b": "below",
    r"\bbelow\b": "above",
    
    # Computing
    r"\bserver\b": "client",
    r"\bclient\b": "server",
    r"\bencrypted\b": "unencrypted",
    r"\bunencrypted\b": "encrypted",
}

def load_claims():
    print(f"Loading claims from {DATA_PATH}...")
    with open(DATA_PATH, 'r') as f:
        chunks = json.load(f)
    return [c for c in chunks if c.get('metadata', {}).get('type') == 'claim']

def generate_adversarial_claim(claim):
    text = claim['text']
    original_text = text
    modifications = []

    # Try all substitutions
    # We want to make ONE modification per claim to keep it precise
    potential_mods = []
    
    for pattern, replacement in SUBSTITUTIONS.items():
        if re.search(pattern, text, re.IGNORECASE):
            potential_mods.append((pattern, replacement))
    
    if not potential_mods:
        return None
    
    # Deterministically pick the first one matching (or random seed if we want variety)
    # Let's pick random to get variety across dataset, but seed it for reproducibility
    random.seed(42 + len(text)) 
    pattern, replacement = random.choice(potential_mods)
    
    # Apply substitution (only first occurrence to be subtle)
    modified_text = re.sub(pattern, replacement, text, count=1, flags=re.IGNORECASE)
    
    return {
        "original_id": claim.get('id') or claim.get('metadata', {}).get('id'),
        "patent_id": claim['metadata']['patent_id'],
        "original_text": original_text,
        "modified_text": modified_text,
        "modification": f"{pattern} -> {replacement}",
        "target_chunk_id": claim.get('id') # Ideally we target the description, but knowing source claim is enough for ID check
    }

def main():
    claims = load_claims()
    print(f"Found {len(claims)} claims.")
    
    adversarial_dataset = []
    
    for claim in claims:
        adv = generate_adversarial_claim(claim)
        if adv:
            adversarial_dataset.append(adv)
            
    print(f"Generated {len(adversarial_dataset)} adversarial examples.")
    
    # Save a subset or full? Let's save all valid ones, user can sample in eval
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(adversarial_dataset, f, indent=2)
    print(f"Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
