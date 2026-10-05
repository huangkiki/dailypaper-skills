#!/usr/bin/env python3
"""Extract affiliations from PDF text (pdftotext -l 2 output via stdin).

Usage:
    curl -sL "https://arxiv.org/pdf/{arxiv_id}" | pdftotext -l 2 - - | python3 extract_affiliations.py

Output:
    {"affiliations": ["Tsinghua University", "UC Berkeley"]}
"""
import json
import re
import sys


# ── Institution keywords (case-insensitive matching) ──────────────────────
INST_KEYWORDS = [
    # Generic
    "university", "universite", "università", "universität",
    "institute", "laboratory", "college", "school of",
    "center for", "centre for", "academy", "polytechnic",
    "department of", "faculty of", "research center", "research centre",
    "national lab",
    # Companies / Industry
    "google", "nvidia", "meta ai", "meta platforms", "microsoft",
    "deepmind", "openai", "alibaba", "tencent", "baidu", "bytedance",
    "amazon", "apple", "samsung", "huawei", "intel", "qualcomm",
    "adobe", "salesforce", "ibm research", "uber", "waymo", "toyota",
    "sony", "bosch", "damo academy",
    # Well-known abbreviations / names (word-boundary aware)
    "mit ", "csail", "stanford", "berkeley", "cmu", "caltech",
    "eth zurich", "eth zürich", "epfl", "kaist", "inria", "mpi ",
    "fair ", "max planck", "cnrs",
    # Chinese universities / orgs
    "tsinghua", "peking", "westlake", "hkust", "hku ", "fudan",
    "sjtu", "zju", "nju", "ustc", "cuhk", "shanghaitech",
    "chinese academy", "shanghai ai", "nanjing university",
    "nankai", "south china",
]

# Header boundary markers — stop extracting when we see these
HEADER_STOP = [
    r"^abstract\b",
    r"^a\s*b\s*s\s*t\s*r\s*a\s*c\s*t\b",  # spaced-out "ABSTRACT"
    r"^1[\s.]+introduction\b",
    r"^i\.\s+introduction\b",
    r"^introduction\b",
    r"^1[\s.]+related work\b",
    r"^summary\b",
    r"^overview\b",
]


def extract_header(text: str) -> str:
    """Return text from start up to Abstract/Introduction (or first ~80 lines)."""
    lines = text.split("\n")
    header_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip the very first few lines (title) before checking for stop
        if i > 3:
            for pat in HEADER_STOP:
                if re.match(pat, stripped, re.IGNORECASE):
                    return "\n".join(header_lines)
        header_lines.append(line)
        if i > 80:
            break
    return "\n".join(header_lines)


def looks_like_sentence(line: str) -> bool:
    """Return True if the line looks like a natural language sentence, not an affiliation."""
    low = line.lower().strip()
    # Count lowercase words using ORIGINAL casing — affiliations are mostly proper nouns
    orig_words = line.strip().split()
    if len(orig_words) < 2:
        return False
    # Sentences tend to have many lowercase words and verbs
    # Must use original casing, not lowered text, to detect proper nouns vs common words
    lowercase_words = sum(1 for w in orig_words if w[0].islower() and len(w) > 2)
    ratio = lowercase_words / len(orig_words) if orig_words else 0
    if ratio > 0.7 and len(orig_words) > 6:
        return True
    words = low.split()
    # Common sentence starters/patterns
    # Note: "the " is excluded — too common in institution names
    # ("The University of ...", "The Ohio State University")
    sentence_markers = [
        "we ", "our ", "this ", "in this", "to ", "for ",
        "however", "although", "moreover", "furthermore", "specifically",
        "enabling", "based on", "by ", "which ", "that ", "these ",
        "recent", "current", "existing", "proposed", "novel",
        "a ", "an ", "has ", "have ", "can ", "also ",
        "experiments", "results", "demonstrate", "show that",
        "address", "propose", "introduce", "present",
    ]
    if any(low.startswith(m) for m in sentence_markers):
        # Exempt short lines that look like institution names
        # (e.g. "The University of New South Wales")
        if has_inst_keyword(low) and len(words) <= 8:
            return False
        return True
    # Lines with multiple periods mid-text are likely sentences
    if low.count(". ") >= 2:
        return True
    # Lines with parenthetical citations like (Author et al., 2024)
    if re.search(r"\([A-Z][a-z]+ et al\.", line):
        return True
    # Lines containing "et al." citation patterns (even without parentheses)
    if re.search(r"et al\.\s*[,;]?\s*\d{4}", low):
        return True
    # Lines with semicolons separating multiple clauses (academic text)
    if ";" in low and len(words) > 8:
        return True
    return False


def is_noise(line: str) -> bool:
    low = line.lower().strip()
    if len(low) < 4:
        return True
    if len(low) > 200:
        return True
    # Pure numbers / emails / URLs
    if re.match(r"^[\d\s.,;:†‡∗*]+$", low):
        return True
    if re.match(r"^[a-zA-Z0-9_.+-]+@", low):
        return True
    if re.match(r"^(https?://|mailto:|arxiv:)", low):
        return True
    if re.match(r"^\d{4}\.\d{4,5}", low):
        return True
    # Common non-affiliation patterns
    noise_starts = [
        "keywords", "preprint", "under review", "published",
        "accepted", "submitted", "proceedings", "project",
        "code:", "model:", "correspondence", "equal contribution",
        "project lead", "corresponding author",
    ]
    if any(low.startswith(ns) for ns in noise_starts):
        return True
    # Sentence-like text is noise
    if looks_like_sentence(line):
        return True
    return False


# Short keywords that need word-boundary matching to avoid false positives
# e.g. "intel" in "intelligence", "nju" in "conjunction"
_WORD_BOUNDARY_KEYWORDS = {"intel", "nju", "uber", "fair "}

_BOUNDARY_PATTERNS = {
    kw: re.compile(r"\b" + re.escape(kw.strip()) + r"\b", re.IGNORECASE)
    for kw in _WORD_BOUNDARY_KEYWORDS
}


def has_inst_keyword(line: str) -> bool:
    low = line.lower()
    for kw in INST_KEYWORDS:
        if kw in _WORD_BOUNDARY_KEYWORDS:
            if _BOUNDARY_PATTERNS[kw].search(low):
                return True
        elif kw in low:
            return True
    return False


def clean_affiliation(s: str) -> str:
    """Clean up a raw affiliation string."""
    s = s.strip()
    # Remove leading footnote markers like "1", "1,2", "†", "*", "∥", "1)"
    s = re.sub(r"^[\d,†‡∗*§¶∥∥ ]+[)\].]?\s*", "", s)
    # Remove trailing footnote markers
    s = re.sub(r"\s*[\d,†‡∗*§¶]+$", "", s)
    # Remove curly braces, extra whitespace
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r"\s+", " ", s).strip()
    # Remove leading/trailing punctuation
    s = s.strip(".,;:- ")
    # Remove "intern" suffix
    s = re.sub(r"\s+intern$", "", s, flags=re.IGNORECASE)
    return s


def split_numbered_affiliations(line: str) -> list:
    """Split 'N University A, N+1 University B' style lines.

    Handles both comma-separated and space-separated numbered formats:
    - "1 Foo University, 2 Bar Institute, 3 Baz Lab"
    - "University of Michigan 2 Nvidia 3 Amazon 4 UC Berkeley"
    """
    # Pattern 1: comma-separated with numbers "1 Foo, 2 Bar"
    parts = re.split(r",\s*(?=\d+\s+[A-Z])", line)
    if len(parts) > 1:
        return parts
    # Pattern 2: space-separated with numbers between institutions
    # "Uni of A 2 Nvidia 3 Amazon 4 UC Berkeley 5 Uni of B 6 Microsoft"
    # Split on " N " where N is a digit followed by a capital letter
    parts = re.split(r"\s+(?=\d+\s+[A-Z])", line)
    if len(parts) > 1:
        return parts
    return [line]


def add_candidate(affiliations: set, text: str):
    """Try to split and add an affiliation candidate to the set."""
    parts = split_numbered_affiliations(text)
    for part in parts:
        cleaned = clean_affiliation(part)
        if cleaned and has_inst_keyword(cleaned) and len(cleaned) > 3:
            if not looks_like_sentence(cleaned) and len(cleaned) < 150:
                affiliations.add(cleaned)


def _is_author_line(line: str) -> bool:
    """Heuristic: line looks like author names (proper nouns separated by spaces/commas).

    Requires >= 4 alphabetic words (at least 2 full names = 4 words) to avoid
    misclassifying short institution names like 'Frontier Robotics' as author lines.
    Lines with commas between name-like groups (e.g. "A. Smith, B. Jones") need only 3 words.
    """
    line = line.strip()
    if not line or len(line) < 5:
        return False
    # Skip lines with clear non-author markers
    if re.match(r"^[\d†‡∗*§¶]", line):
        return False
    # Author lines: mostly capitalized words, possibly with commas
    words = re.findall(r"[A-Za-z]+", line)
    if len(words) < 3:
        return False
    capitalized = sum(1 for w in words if w[0].isupper())
    cap_ratio = capitalized / len(words)
    # Comma-separated names pattern (e.g. "A. Smith, B. Jones, C. Lee")
    has_commas = line.count(",") >= 2
    if has_commas and cap_ratio >= 0.6 and len(words) >= 3:
        return True
    # Space-separated names need >= 4 words to distinguish from short institution names
    return cap_ratio >= 0.6 and len(words) >= 4


def extract_positional_affiliations(header: str) -> list:
    """Extract affiliations using positional heuristics.

    Lines between the author block and Abstract that are short and not
    noise are likely affiliations, even without keyword matches.
    """
    lines = header.split("\n")
    affiliations = []

    # Phase 1: Find the title (first non-empty line or first few lines)
    # Phase 2: Find author lines (capitalized name-like lines)
    # Phase 3: Lines after authors but before Abstract = affiliations

    # Find where authors end
    author_end = -1
    found_author = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if i == 0:
            continue  # skip title line
        if _is_author_line(stripped):
            found_author = True
            author_end = i
        elif found_author:
            break  # first non-author line after authors

    if not found_author or author_end < 0:
        return []

    # Collect candidate lines after author block
    for i in range(author_end + 1, min(len(lines), author_end + 10)):
        line = lines[i].strip()
        if not line:
            continue
        # Stop at Abstract or similar
        for pat in HEADER_STOP:
            if re.match(pat, line, re.IGNORECASE):
                return affiliations
        # Skip noise
        if is_noise(line):
            continue
        # Skip lines that look like author names
        if _is_author_line(line):
            continue
        # Short lines (< 100 chars) that aren't sentences = likely affiliations
        if len(line) < 100 and not looks_like_sentence(line):
            cleaned = clean_affiliation(line)
            if cleaned and len(cleaned) > 3:
                affiliations.append(cleaned)

    return affiliations


def extract_affiliations(text: str) -> list:
    """Main extraction logic."""
    header = extract_header(text)
    affiliations = set()

    # Strategy 1: Lines containing institution keywords (non-sentence)
    for line in header.split("\n"):
        line = line.strip()
        if not line or is_noise(line):
            continue
        if has_inst_keyword(line):
            add_candidate(affiliations, line)

    # Strategy 2: Numbered footnote pattern at line start "N] Institution"
    for match in re.findall(
        r"(?:^|\n)\s*[\[({]?\d[\])}.]?\s*([A-Z][^\n]{4,120})",
        header,
    ):
        cleaned = clean_affiliation(match)
        if cleaned and not is_noise(cleaned):
            add_candidate(affiliations, cleaned)

    # Strategy 3: Copyright line "© Year Company/University"
    for match in re.findall(r"©\s*\d{4}\s+(.+?)(?:\.|$)", text, re.MULTILINE):
        cleaned = clean_affiliation(match)
        if cleaned and has_inst_keyword(cleaned) and len(cleaned) > 3:
            affiliations.add(cleaned)

    # Strategy 4: Scan first ~60 lines of full text for institution lines
    # (catches affiliations in two-column papers where pdftotext may put
    # affiliation lines after "Abstract" due to column ordering)
    top_lines = text.split("\n")[:60]
    for line in top_lines:
        line = line.strip()
        if not line or is_noise(line):
            continue
        if has_inst_keyword(line):
            add_candidate(affiliations, line)

    # Strategy 5: Positional heuristic — lines after author names and
    # before Abstract are likely affiliations even without keyword matches
    if not affiliations:
        positional = extract_positional_affiliations(header)
        for aff in positional:
            affiliations.add(aff)

    # Deduplicate: remove substrings (keep longer version)
    result = sorted(affiliations, key=len, reverse=True)
    final = []
    for a in result:
        a_low = a.lower()
        if not any(a_low in b.lower() for b in final if a != b):
            final.append(a)

    return sorted(final)


def main():
    text = sys.stdin.read()
    if not text or len(text.strip()) < 50:
        print(json.dumps({"affiliations": []}))
        return
    affs = extract_affiliations(text)
    print(json.dumps({"affiliations": affs}, ensure_ascii=False))


if __name__ == "__main__":
    main()
