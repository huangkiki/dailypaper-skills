#!/usr/bin/env python3
"""Batch-enrich arXiv papers with metadata from HTML/abs pages.

Usage:
    # Linux/Mac
    cat /tmp/daily_papers_top30.json | python3 enrich_papers.py > /tmp/daily_papers_enriched.json

    # Windows (powershell cmd compatible)
    python3 enrich_papers.py input.json output.json

    # Cross-platform (auto-detect paths)
    python3 enrich_papers.py

Input:  JSON array via stdin or auto-detected file
Output: JSON array via stdout or file with enriched fields added

Architecture:
    - asyncio + subprocess curl for concurrent HTTP requests
    - Semaphore(10) to avoid hammering arXiv
    - Pure regex HTML parsing (no WebFetch / no external deps)
    - Per-request timeout via curl --max-time (no Python-level per-paper timeout)
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from collections import Counter
from pathlib import Path

_SHARED_DIR = Path(__file__).resolve().parent.parent / "_shared"
if str(_SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(_SHARED_DIR))

from user_config import temp_file_path

SEMAPHORE_LIMIT = 10
CURL_TIMEOUT = 30

# ── Stop words for method_names extraction ──────────────────────────────────
METHOD_STOP = {
    # Section headings
    "Abstract", "Introduction", "Method", "Methods", "Methodology",
    "Results", "Conclusion", "Conclusions", "Discussion", "Experiments",
    "Experiment", "Evaluation", "Background", "Appendix", "Supplementary",
    "References", "Related", "Overview", "Preliminaries", "Framework",
    "Acknowledgements", "Acknowledgments",
    # Conferences / venues
    "CVPR", "ICCV", "ECCV", "NeurIPS", "ICML", "ICLR", "IEEE", "AAAI",
    "IJCAI", "SIGCHI", "SIGGRAPH", "ICRA", "IROS", "CoRL", "RSS",
    "WACV", "BMVC", "ACCV", "MICCAI", "ACL", "EMNLP", "NAACL",
    # Common abbreviations (not method names)
    "RGB", "GPU", "CPU", "TPU", "CNN", "MLP", "SGD", "ADAM", "GAN",
    "RNN", "LSTM", "GRU", "API", "URL", "HTML", "PDF", "JSON", "XML",
    "FPS", "IoU", "MAP", "FID", "PSNR", "SSIM", "LPIPS", "MSE", "MAE",
    "BCE", "CE", "KL", "GNN", "VAE", "ELBO", "EM",
    "SoTA", "SOTA", "TODO", "NOTE", "TBD",
    # Generic terms
    "Table", "Figure", "Section", "Eq", "Equation", "Algorithm",
    "Step", "Phase", "Stage", "Layer", "Block", "Module", "Head",
    "Loss", "Input", "Output", "Data", "Model", "Network",
    "Training", "Testing", "Inference", "Baseline", "Ablation",
    # Roman numerals
    "II", "III", "IV", "VI", "VII", "VIII", "IX", "XI", "XII",
    # Common LaTeX / HTML artifacts
    "LaTeX", "BibTeX", "ArXiv",
}

# ── Real-world experiment keywords ──────────────────────────────────────────
REAL_WORLD_KEYWORDS = [
    "real robot", "real-world experiment", "physical robot",
    "real world evaluation", "hardware experiment", "deployed on",
    "real-world deployment", "real manipulation", "physical experiment",
    "real-world result", "real-world task", "real-world environment",
]

# ── Institution keywords for HTML affiliation extraction ────────────────────
INST_KEYWORDS = [
    "university", "universite", "università", "universität",
    "institute", "laboratory", "college", "school of",
    "center for", "centre for", "academy", "polytechnic",
    "department of", "faculty of", "research center", "research centre",
    "national lab",
    "google", "nvidia", "meta ai", "meta platforms", "microsoft",
    "deepmind", "openai", "alibaba", "tencent", "baidu", "bytedance",
    "amazon", "apple", "samsung", "huawei", "intel", "qualcomm",
    "adobe", "salesforce", "ibm research", "uber", "waymo", "toyota",
    "sony", "bosch", "damo academy",
    "mit ", "csail", "stanford", "berkeley", "cmu", "caltech",
    "eth zurich", "eth zürich", "epfl", "kaist", "inria", "mpi ",
    "fair ", "max planck", "cnrs",
    "tsinghua", "peking", "westlake", "hkust", "hku ", "fudan",
    "sjtu", "zju", "nju", "ustc", "cuhk", "shanghaitech",
    "chinese academy", "shanghai ai", "nanjing university",
    "nankai", "south china",
]


# ══════════════════════════════════════════════════════════════════════════════
# HTTP helpers
# ══════════════════════════════════════════════════════════════════════════════

async def curl_fetch(url: str, sem: asyncio.Semaphore, timeout: int = CURL_TIMEOUT,
                     retries: int = 3) -> str:
    """Fetch URL content using curl subprocess with retry. Returns empty string on failure."""
    for attempt in range(1, retries + 1):
        async with sem:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "curl", "-sL", "--max-time", str(timeout), url,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout + 5)
                content = stdout.decode("utf-8", errors="replace") if stdout else ""
                if content:
                    return content
            except (asyncio.TimeoutError, Exception) as e:
                print(f"  [curl] attempt {attempt}/{retries} failed {url}: {e}", file=sys.stderr)
        if attempt < retries:
            await asyncio.sleep(3 * attempt)  # 3s, 6s
    return ""



# ══════════════════════════════════════════════════════════════════════════════
# HTML regex extractors
# ══════════════════════════════════════════════════════════════════════════════

def strip_tags(html: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", html)


def extract_figure_url(html: str, arxiv_id: str) -> str:
    """Extract the first non-icon figure image URL from HTML."""
    figures = re.findall(r"<figure[^>]*>.*?<img[^>]+src=[\"']([^\"'>]+)[\"']", html, re.DOTALL)
    skip_words = ["icon", "logo", "badge", "inline", "orcid", "creative"]
    for fig in figures:
        if any(skip in fig.lower() for skip in skip_words):
            continue
        url = fig
        if url.startswith("/"):
            url = "https://arxiv.org" + url
        elif not url.startswith("http"):
            if re.match(r"\d{4}\.\d{4,5}v\d+/", url):
                url = "https://arxiv.org/html/" + url
            else:
                url = f"https://arxiv.org/html/{arxiv_id}/" + url
        return url
    return ""


def extract_authors_html(html: str) -> list[str]:
    """Extract authors from ltx_personname spans."""
    matches = re.findall(r'class="ltx_personname"[^>]*>(.*?)</span>', html, re.DOTALL)
    authors = []
    for m in matches:
        name = strip_tags(m).strip()
        # Skip if it looks like an affiliation or footnote
        if name and len(name) < 80 and not any(kw in name.lower() for kw in ["university", "institute", "department"]):
            authors.append(name)
    return authors


def extract_affiliations_html(html: str) -> list[str]:
    """Extract affiliations from HTML paper using multiple strategies."""
    affils = set()

    # Strategy 1: structured class elements (ltx_role_affil, ltx_contact)
    # Search up to abstract or first 80k chars (some pages have long headers)
    abstract_pos = html.find("ltx_abstract")
    search_end = abstract_pos if abstract_pos > 0 else min(len(html), 80000)
    search_region = html[:search_end]
    for cls in ("ltx_role_affil", "ltx_contact"):
        for m in re.finditer(
            rf'class="[^"]*{cls}[^"]*"[^>]*>(.*?)</(?:span|div|p|td)',
            search_region, re.DOTALL
        ):
            text = strip_tags(m.group(1)).strip(" ,;.")
            if text and 3 < len(text) < 500:
                affils.add(text)

    # Strategy 2: header region plain text (between <article> and ltx_abstract)
    article_start = html.find("<article")
    abstract_start = html.find("ltx_abstract")
    if article_start >= 0 and abstract_start > article_start:
        header_text = strip_tags(html[article_start:abstract_start])
        for line in header_text.split("\n"):
            line = line.strip()
            if not line or len(line) < 5 or len(line) > 500:
                continue
            if any(kw in line.lower() for kw in INST_KEYWORDS):
                affils.add(line.strip(" ,;."))

    return list(affils)


def extract_section_headers(html: str) -> list[str]:
    """Extract h2/h3 section headers."""
    headers = []
    for m in re.finditer(r"<h[23][^>]*>(.*?)</h[23]>", html, re.DOTALL):
        text = strip_tags(m.group(1)).strip()
        text = re.sub(r"^\d+(\.\d+)*\.?\s*", "", text)  # remove "1.2.3 " prefix
        if text and len(text) < 200:
            headers.append(text)
    return headers[:25]


def extract_captions(html: str) -> list[str]:
    """Extract figure/table captions of reasonable length."""
    captions = []
    for m in re.finditer(r"<(?:figcaption|caption)[^>]*>(.*?)</(?:figcaption|caption)>", html, re.DOTALL):
        text = strip_tags(m.group(1)).strip()
        text = re.sub(r"\s+", " ", text)
        if 10 <= len(text) <= 200:
            captions.append(text)
    return captions[:8]


def extract_has_real_world(html: str) -> bool:
    """Check if HTML contains real-world experiment keywords."""
    html_lower = html.lower()
    return any(kw in html_lower for kw in REAL_WORLD_KEYWORDS)


def extract_method_names(html: str, paper_title: str) -> list[str]:
    """Extract method/model names from HTML text using CamelCase + ALLCAPS patterns."""
    text = strip_tags(html)

    # CamelCase: DreamerV3, OpenVLA, ControlNet, MuJoCo
    camel = re.findall(r"\b([A-Z][a-z]+(?:[A-Z][a-z]*)+(?:V?\d+)?)\b", text)
    # ALLCAPS with optional version: DDPM, SAM-2, GPT-4, RT-2
    allcaps = re.findall(r"\b([A-Z]{2,}(?:[-_]\d+)?)\b", text)
    # CamelCase with numbers: GPT4o, Llama3
    camel_num = re.findall(r"\b([A-Z][a-z]+[A-Z][a-z]*\d+[a-z]?)\b", text)
    # Hyphenated: Diffusion-Policy, Stable-Diffusion
    hyphenated = re.findall(r"\b([A-Z][a-z]+-[A-Z][a-z]+(?:-[A-Z][a-z]+)?)\b", text)

    all_names = camel + allcaps + camel_num + hyphenated
    cnt = Counter(all_names)

    # Build stop set including title words
    title_words = set(re.findall(r"\b[A-Za-z]+\b", paper_title))
    stop = METHOD_STOP | {w for w in title_words if len(w) >= 3}

    method_names = []
    seen = set()
    for name, count in cnt.most_common(40):
        if count < 2:
            continue
        if name in stop:
            continue
        if len(name) < 2:
            continue
        name_lower = name.lower()
        if name_lower in seen:
            continue
        seen.add(name_lower)
        method_names.append(name)
        if len(method_names) >= 20:
            break

    return method_names


def extract_method_summary(html: str) -> str:
    """Extract method description from Method/Approach sections (300-500 chars)."""
    # Strategy: find h2/h3 headers containing Method/Approach/Framework/Proposed,
    # then extract text until the next h2/h3.
    # Note: headers may contain inner tags like <span>, so we use .*? not [^<]*
    section_text = ""

    # Primary: find content after Method/Approach header until next header
    m = re.search(
        r"<h[23][^>]*>.*?(?:Method|Approach|Framework|Proposed).*?</h[23]>(.*?)(?:<h[23]|$)",
        html, re.DOTALL | re.IGNORECASE
    )
    if m:
        section_text = strip_tags(m.group(1))

    if not section_text:
        # Last resort: try Introduction's last paragraphs
        m = re.search(
            r"<h[23][^>]*>.*?Introduction.*?</h[23]>(.*?)(?:<h[23]|$)",
            html, re.DOTALL | re.IGNORECASE
        )
        if m:
            intro_text = strip_tags(m.group(1))
            paragraphs = [p.strip() for p in intro_text.split("\n\n") if p.strip()]
            # Take last 2 paragraphs (usually contain method overview)
            section_text = "\n".join(paragraphs[-2:]) if paragraphs else ""

    if not section_text:
        return ""

    # Clean up
    section_text = re.sub(r"\s+", " ", section_text).strip()
    # Remove citation markers like [1], [2,3]
    section_text = re.sub(r"\s*\[\d+(?:,\s*\d+)*\]", "", section_text)

    # Truncate to ~300-500 chars at sentence boundary
    if len(section_text) > 500:
        # Find sentence end near 500 chars
        end = section_text.rfind(". ", 300, 550)
        if end > 0:
            section_text = section_text[:end + 1]
        else:
            section_text = section_text[:500].rsplit(" ", 1)[0] + "..."

    return section_text if len(section_text) >= 100 else ""


# ══════════════════════════════════════════════════════════════════════════════
# Abs page fallback extractor
# ══════════════════════════════════════════════════════════════════════════════

def extract_from_abs(html: str) -> dict:
    """Extract authors and affiliations from arxiv abs page meta tags."""
    authors = re.findall(r'<meta\s+name="citation_author"\s+content="([^"]+)"', html)
    authors = [a.strip() for a in authors if a.strip()]
    affils = set()
    for m in re.findall(r'<meta\s+name="citation_author_institution"\s+content="([^"]+)"', html):
        if m.strip():
            affils.add(m.strip())
    return {"authors": authors, "affiliations": list(affils)}



# ══════════════════════════════════════════════════════════════════════════════
# PDF affiliation extraction
# ══════════════════════════════════════════════════════════════════════════════

EXTRACT_AFFILIATIONS_SCRIPT = str(
    __import__("pathlib").Path(__file__).parent / "extract_affiliations.py"
)

async def extract_affiliations_pdf(arxiv_id: str, sem: asyncio.Semaphore,
                                   retries: int = 3) -> list[str]:
    """Extract affiliations from PDF via pdftotext + extract_affiliations.py."""
    for attempt in range(1, retries + 1):
        async with sem:
            try:
                cmd = (
                    f'curl -sL --max-time {CURL_TIMEOUT} "https://arxiv.org/pdf/{arxiv_id}"'
                    f" | pdftotext -l 2 - -"
                    f" | {sys.executable} {EXTRACT_AFFILIATIONS_SCRIPT}"
                )
                proc = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=CURL_TIMEOUT + 15)
                if stdout:
                    data = json.loads(stdout.decode("utf-8", errors="replace"))
                    affils = data.get("affiliations", [])
                    if affils:
                        return affils
            except (asyncio.TimeoutError, json.JSONDecodeError, Exception) as e:
                print(f"  [pdf] attempt {attempt}/{retries} failed {arxiv_id}: {e}", file=sys.stderr)
        if attempt < retries:
            await asyncio.sleep(3 * attempt)
    return []


# ══════════════════════════════════════════════════════════════════════════════
# Per-paper enrichment
# ══════════════════════════════════════════════════════════════════════════════

async def enrich_one(paper: dict, sem: asyncio.Semaphore) -> dict:
    """Enrich a single paper with metadata from HTML and abs pages."""
    arxiv_id = paper.get("arxiv_id", "")
    if not arxiv_id:
        # Try to extract from URL
        url = paper.get("url", "")
        m = re.search(r"(\d{4}\.\d{4,5})", url)
        arxiv_id = m.group(1) if m else ""
    if not arxiv_id:
        return paper

    title = paper.get("title", "")
    result = dict(paper)  # copy

    try:
        # Fetch HTML page
        html_url = f"https://arxiv.org/html/{arxiv_id}"
        html = await curl_fetch(html_url, sem)

        # Parse HTML if we got content
        html_authors = []
        html_affiliations = []
        figure_url = ""
        section_headers = []
        captions = []
        has_real_world = False
        method_names = []
        method_summary = ""

        if html and len(html) > 1000:
            figure_url = extract_figure_url(html, arxiv_id)
            html_authors = extract_authors_html(html)
            html_affiliations = extract_affiliations_html(html)
            section_headers = extract_section_headers(html)
            captions = extract_captions(html)
            has_real_world = extract_has_real_world(html)
            method_names = extract_method_names(html, title)
            method_summary = extract_method_summary(html)

        # Abs fallback if HTML authors OR affiliations are empty
        abs_authors = []
        abs_affiliations = []
        if not html_authors or not html_affiliations:
            abs_url = f"https://arxiv.org/abs/{arxiv_id}"
            abs_html = await curl_fetch(abs_url, sem)
            if abs_html:
                abs_data = extract_from_abs(abs_html)
                abs_authors = abs_data["authors"]
                abs_affiliations = abs_data["affiliations"]

        # PDF fallback for affiliations if still empty
        pdf_affiliations = []
        if not html_affiliations and not abs_affiliations:
            pdf_affiliations = await extract_affiliations_pdf(arxiv_id, sem)

        # ── Merge with priority rules ──
        # Principle: new extraction > existing input, but never overwrite non-empty with empty

        # figure_url: HTML curl > keep existing
        result["figure_url"] = figure_url or paper.get("figure_url", "")

        # affiliations: HTML > abs fallback > PDF fallback > keep existing input
        if html_affiliations:
            result["affiliations"] = ", ".join(html_affiliations)
        elif abs_affiliations:
            result["affiliations"] = ", ".join(abs_affiliations)
        elif pdf_affiliations:
            result["affiliations"] = ", ".join(pdf_affiliations)
        # else: keep whatever was in the input (supports re-enriching enriched data)

        # authors: HTML > abs fallback > keep existing input
        if html_authors:
            result["authors"] = ", ".join(html_authors)
        elif abs_authors:
            result["authors"] = ", ".join(abs_authors)
        # else: keep original

        # Other enriched fields
        result["section_headers"] = section_headers
        result["captions"] = captions
        result["has_real_world"] = has_real_world
        result["method_names"] = method_names
        result["method_summary"] = method_summary

    except Exception as e:
        print(f"  [error] {arxiv_id}: {e}", file=sys.stderr)

    return result


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

async def enrich_all(papers: list[dict]) -> list[dict]:
    """Enrich all papers concurrently with a semaphore limit."""
    sem = asyncio.Semaphore(SEMAPHORE_LIMIT)
    tasks = [asyncio.create_task(enrich_one(paper, sem)) for paper in papers]

    # gather preserves order and handles exceptions inline
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    ordered = []
    for i, result in enumerate(raw_results):
        if isinstance(result, Exception):
            print(f"  [error] paper #{i} ({papers[i].get('arxiv_id','')}): {result}", file=sys.stderr)
            ordered.append(papers[i])
        else:
            ordered.append(result)

    return ordered


def main():
    """Main entry point with cross-platform path support.

    Usage:
        # Linux/Mac - pipe from stdin
        cat /tmp/daily_papers_top30.json | python3 enrich_papers.py

        # Windows - file arguments
        python3 enrich_papers.py input.json output.json

        # Cross-platform - auto-detect default paths
        python3 enrich_papers.py
    """
    output_path = None
    input_path = None

    # Parse arguments: [input.json] [output.json]
    if len(sys.argv) >= 2:
        if sys.argv[1].endswith('.json'):
            input_path = sys.argv[1]
        else:
            output_path = sys.argv[1]
    if len(sys.argv) >= 3:
        if sys.argv[2].endswith('.json'):
            output_path = sys.argv[2]

    # Auto-detect input path if not provided (Windows/Linux compatible)
    if not input_path:
        auto_input_path = temp_file_path('daily_papers_top30.json')
        if auto_input_path.exists():
            input_path = str(auto_input_path)
            print(f"[enrich_papers] Auto-detected input: {input_path}", file=sys.stderr)

    # Read input from file or stdin
    if input_path:
        try:
            with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
                input_data = f.read()
        except FileNotFoundError:
            print(f"Error: Input file not found: {input_path}", file=sys.stderr)
            _write_output("[]", output_path)
            sys.exit(1)
    else:
        input_data = sys.stdin.read()

    if not input_data.strip():
        _write_output("[]", output_path)
        return

    try:
        papers = json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}", file=sys.stderr)
        _write_output("[]", output_path)
        sys.exit(1)

    if not papers:
        _write_output("[]", output_path)
        return

    print(f"Enriching {len(papers)} papers...", file=sys.stderr)
    enriched = asyncio.run(enrich_all(papers))
    print(f"Done. Enriched {len(enriched)} papers.", file=sys.stderr)

    output = json.dumps(enriched, ensure_ascii=False, indent=2) + "\n"

    # Auto-detect output path if not provided (Windows/Linux compatible)
    if not output_path:
        output_path = str(temp_file_path('daily_papers_enriched.json'))
        print(f"[enrich_papers] Auto-detected output: {output_path}", file=sys.stderr)

    _write_output(output, output_path)


def _write_output(data: str, output_path: str | None):
    """Write output to file (if path given) or stdout with explicit flush."""
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(data)
    else:
        sys.stdout.write(data)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
