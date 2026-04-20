"""Regex Analyzer Layer — keyword-based semantic analysis for detecting risky content."""

import sys
import json
import asyncio
import argparse
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple

# Third-party libraries
try:
    import spacy
    from rapidfuzz import process, fuzz
except ImportError:
    print("[!] Error: Missing libraries. Run: pip install spacy rapidfuzz")
    sys.exit(1)

# KEYWORD RISK DICTIONARY: 1.0 = Critical Threat, 0.8 = High Risk, 0.6 = Medium Risk.

DEFAULT_KEYWORDS: Dict[str, float] = {
    
    # ---------------------------------------------------------
    # 1. VIOLENCE & PHYSICAL HARM (Direct Action)
    # ---------------------------------------------------------
    "kill": 1.0, "murder": 1.0, "assassinate": 1.0, "slaughter": 1.0,
    "massacre": 1.0, "execute": 0.8, "decapitate": 1.0, "behead": 1.0,
    "maim": 1.0, "torture": 1.0, "strangle": 1.0, "suffocate": 1.0,
    "poison": 0.9, "annihilate": 0.8, "exterminate": 0.9, "lynch": 1.0,
    "genocide": 1.0, "shoot": 0.7, "stab": 0.9, "slash": 0.7,
    "disembowel": 1.0, "dismember": 1.0, "rape": 1.0, "assault": 0.8,

    # ---------------------------------------------------------
    # 2. WEAPONS, EXPLOSIVES & CHEMICALS
    # ---------------------------------------------------------
    # Generic
    "weapon": 0.8, "gun": 0.8, "knife": 0.7, "blade": 0.6, "bomb": 1.0,
    "explosive": 0.9, "detonate": 0.9, "blast": 0.8,
    
    # Specific Firearms/Ammo
    "glock": 0.8, "ar15": 0.8, "ak47": 0.8, "silencer": 0.8, "suppressor": 0.7,
    "ammo": 0.6, "ammunition": 0.6, "caliber": 0.5,
    
    # Explosives & Precursors (High intent signals)
    "c4": 1.0, "semtex": 1.0, "dynamite": 0.9, "tnt": 0.8, "ied": 1.0,
    "pipebomb": 1.0, "molotov": 1.0, "napalm": 1.0, "shrapnel": 0.8,
    "fertilizer": 0.3, "ammonium": 0.4, "nitrate": 0.4, # Context dependent
    "timer": 0.3, "fuse": 0.4, "detonator": 0.9,
    
    # Biological/Chemical Agents
    "anthrax": 1.0, "ricin": 1.0, "sarin": 1.0, "cyanide": 1.0, 
    "arsenic": 0.9, "mustard gas": 1.0, "nerve agent": 1.0, "pathogen": 0.6,

    # ---------------------------------------------------------
    # 3. SELF-HARM & SUICIDE
    # ---------------------------------------------------------
    "suicide": 1.0, "overdose": 0.9, "self-harm": 1.0, "cutting": 0.6,
    "hang": 0.6, "noose": 0.9, "jump": 0.4, "bleach": 0.5, "end it": 0.5,
    "worthless": 0.4, "hopeless": 0.4, "anorexia": 0.8, "bulimia": 0.8,

    # ---------------------------------------------------------
    # 4. CYBERSECURITY & HACKING (Offensive Security)
    # ---------------------------------------------------------
    # Actions
    "hack": 0.8, "crack": 0.7, "exploit": 0.8, "bypass": 0.6, 
    "breach": 0.7, "infiltrate": 0.7, "spoof": 0.7, "sniff": 0.6,
    "decrypt": 0.6, "bruteforce": 0.9, "phish": 0.9,
    
    # Tools & Malware
    "keylogger": 1.0, "ransomware": 1.0, "malware": 0.9, "spyware": 0.9,
    "rootkit": 1.0, "trojan": 0.8, "worm": 0.7, "virus": 0.6,
    "botnet": 1.0, "ddos": 1.0, "rat": 0.5, # Remote Access Trojan
    "metasploit": 0.9, "wireshark": 0.5, "nmap": 0.5, "kali": 0.5,
    "reverse shell": 1.0, "shellcode": 0.9, "payload": 0.6,
    
    # Vulnerabilities
    "sql injection": 1.0, "sqli": 1.0, "xss": 0.9, "csrf": 0.9, 
    "rce": 1.0, "buffer overflow": 0.9, "zero-day": 0.8,

    # ---------------------------------------------------------
    # 5. ILLICIT GOODS & CRIME
    # ---------------------------------------------------------
    # Drugs
    "cocaine": 0.9, "heroin": 1.0, "meth": 1.0, "fentanyl": 1.0,
    "lsd": 0.8, "mdma": 0.8, "ecstasy": 0.8, "dealer": 0.7,
    "trafficking": 1.0, "smuggle": 0.9, "cartel": 0.8,
    
    # Fraud/Dark Web
    "credit card": 0.4, "cc": 0.3, "dump": 0.5, "fullz": 0.9, # Full identity info
    "darkweb": 0.8, "tor": 0.6, "onion": 0.6, "fake id": 1.0,
    "counterfeit": 0.9, "money laundering": 1.0, "ponzi": 0.9,

    # ---------------------------------------------------------
    # 6. HATE SPEECH & SLURS (Expanded)
    # ---------------------------------------------------------
    # Note: Included for filtering purposes.
    "nigger": 1.0, "nigga": 0.9, "fag": 1.0, "faggot": 1.0, 
    "retard": 0.9, "spic": 1.0, "kike": 1.0, "chink": 1.0, 
    "tranny": 1.0, "shemale": 0.9, "dyke": 1.0, "cunt": 0.9,
    "whore": 0.8, "slut": 0.8, "bitch": 0.7, "mongoloid": 0.9,
    "gook": 1.0, "raghead": 1.0, "wetback": 1.0, "negro": 0.9,

    # ---------------------------------------------------------
    # 7. JAILBREAK & SYSTEM MANIPULATION (Prompt Injection)
    # ---------------------------------------------------------
    # Keywords that suggest an attempt to break AI rules
    "unfiltered": 0.8, "uncensored": 0.8, "jailbreak": 1.0, 
    "dan": 0.4, "gpt": 0.2, "developer mode": 0.8, "god mode": 0.8,
    "override": 0.7, "ignore rules": 0.9, "ignore constraints": 0.9,
    "do anything now": 0.9, "always answer": 0.7, "roleplay": 0.3
}

class SemanticSanitizer:
    """Regex-based semantic analyzer using NLP tokenization and fuzzy matching for keyword detection."""
    
    def __init__(self, merge_file: Path = None, replace_file: Path = None):
        """Initialize the sanitizer. merge_file adds to defaults; replace_file replaces them entirely."""
        print("[*] Loading Regex Analyzer (SemanticSanitizer)...")
        try:
            # Disable parser/ner for speed, we only need tokenizer/lemmatizer
            self.nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
        except OSError:
            print("[!] Error: Model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")
            sys.exit(1)
            
        self.keywords = self._load_vocabulary(merge_file, replace_file)
        print(f"[*] Regex Analyzer loaded with {len(self.keywords)} keywords.")

    def _load_vocabulary(self, merge_file: Path, replace_file: Path) -> Dict[str, float]:
        keywords = {}
        if replace_file and Path(replace_file).exists():
            return self._read_json(replace_file)

        keywords = DEFAULT_KEYWORDS.copy()
        if merge_file and Path(merge_file).exists():
            keywords.update(self._read_json(merge_file))
        return keywords

    def _read_json(self, filepath: str) -> Dict[str, float]:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[!] Warning: Could not read '{filepath}'. Error: {e}")
            return {}

    def _preprocess_text(self, text: str) -> str:
        """Normalization pipeline: Leet -> Unicode -> Separators -> CamelCase -> SmartJoin -> CollapseRepeats."""
        
        # 1. Leetspeak normalization: map numbers/symbols to letter equivalents.
        leetspeak_map = str.maketrans({
            '0': 'o', '1': 'i', '3': 'e', '4': 'a', 
            '5': 's', '@': 'a', '$': 's', '!': 'i', '¡': 'i', '|': 'l'
        })
        text = text.translate(leetspeak_map)

        # 2. Unicode normalization: decompose to ASCII, removing hidden formatting.
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        
        # 3. Replace separators with spaces (k.1.l.l -> k 1 l l).
        text = text.replace("_", " ").replace("-", " ").replace(".", " ")

        # 4. Split CamelCase (SystemKill -> System Kill)
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # 5. Smart join: merge single-char sequences back into words (k i l l -> kill).
        def joiner(match):
            return match.group(0).replace(" ", "")
        
        text = re.sub(r'(?:\b[a-zA-Z0-9]\s+)+[a-zA-Z0-9]\b', joiner, text)
            
        # 6. Collapse repeated chars 3+ times (muuuuurder -> murder).
        text = re.sub(r'(.)\1{2,}', r'\1', text)
        
        return text

    def analyze(self, text: str) -> Tuple[float, List[str]]:
        # Apply the heavy-duty preprocessor
        clean_text = self._preprocess_text(text)
        
        # Tokenize using SpaCy
        doc = self.nlp(clean_text)
        tokens = [token.lemma_.lower() for token in doc]
        
        total_score = 0.0
        triggered_words = set()

        for bad_word, weight in self.keywords.items():
            
            # CHECK 1: Exact Match (Fast)
            if bad_word in tokens:
                triggered_words.add(bad_word)
                total_score += weight
                continue 

            # CHECK 2: Fuzzy Match (Dynamic Threshold)
            match = process.extractOne(bad_word, tokens, scorer=fuzz.ratio)
            
            if match:
                matched_token, score, index = match
                
                # Dynamic threshold: short words (<=4 chars) use 95% to avoid false positives, long words use 85%.
                threshold = 95 if len(bad_word) <= 4 else 85
                
                if score >= threshold: 
                    triggered_words.add(f"{bad_word} (matched: '{matched_token}')")
                    total_score += weight

        return min(total_score, 1.0), sorted(list(triggered_words))

    async def analyze_async(self, text: str) -> Tuple[float, List[str]]:
        """Async version of analyze for parallel execution."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.analyze, text)

    async def get_score_async(self, text: str) -> float:
        """Return just the normalized risk score (0.0-1.0) asynchronously."""
        score, _ = await self.analyze_async(text)
        return score


def main():
    parser = argparse.ArgumentParser(description="AI Semantic Sanitizer")
    parser.add_argument("filename", help="Path to the input text file")
    parser.add_argument("--merge", help="JSON file to ADD to defaults", default=None)
    parser.add_argument("--replace", help="JSON file to REPLACE defaults", default=None)
    
    args = parser.parse_args()

    sanitizer = SemanticSanitizer(merge_file=args.merge, replace_file=args.replace)

    try:
        with open(args.filename, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    except FileNotFoundError:
        print(f"[!] Error: File '{args.filename}' not found.")
        sys.exit(1)

    print("-" * 40)
    print(f"Scanning file: {args.filename}")
    score, triggers = sanitizer.analyze(content)

    print("-" * 40)
    print(f"RISK SCORE:      {score:.2f} / 1.0")
    print(f"TRIGGERS FOUND:  {triggers}")
    print("-" * 40)

    if score > 0.7:
        print("STATUS: HIGH RISK - BLOCK CONTENT")
    elif score > 0.3:
        print("STATUS: MODERATE RISK - FLAGGED FOR REVIEW")
    else:
        print("STATUS: SAFE")

if __name__ == "__main__":
    main()