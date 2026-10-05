#!/usr/bin/env python3
"""
arXiv API XML → JSON 解析器
stdin 接收 arXiv API 的 Atom XML 响应，stdout 输出 JSON 数组。
零外部依赖，仅使用标准库。

用法:
    curl -s "https://export.arxiv.org/api/query?..." | python3 parse_arxiv.py
"""

import json
import sys
import xml.etree.ElementTree as ET

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def parse(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    papers = []

    for entry in root.findall("atom:entry", NS):
        title_el = entry.find("atom:title", NS)
        summary_el = entry.find("atom:summary", NS)
        published_el = entry.find("atom:published", NS)
        id_el = entry.find("atom:id", NS)

        if title_el is None or summary_el is None:
            continue

        title = " ".join(title_el.text.split())
        abstract = " ".join(summary_el.text.split())
        url = id_el.text.strip() if id_el is not None else ""
        date = published_el.text[:10] if published_el is not None else ""

        # arXiv ID from URL
        arxiv_id = url.split("/abs/")[-1] if "/abs/" in url else ""

        # authors (all)
        author_els = entry.findall("atom:author", NS)
        names = []
        affiliations = set()
        for author_el in author_els:
            name_el = author_el.find("atom:name", NS)
            if name_el is not None and name_el.text:
                names.append(name_el.text.strip())
            for aff_el in author_el.findall("arxiv:affiliation", NS):
                if aff_el.text and aff_el.text.strip():
                    affiliations.add(aff_el.text.strip())
        authors = ", ".join(names)

        # primary category
        cat_el = entry.find("arxiv:primary_category", NS)
        category = cat_el.get("term", "") if cat_el is not None else ""

        papers.append({
            "title": title,
            "authors": authors,
            "affiliations": ", ".join(sorted(affiliations)) if affiliations else "",
            "abstract": abstract,
            "url": url,
            "pdf": f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else "",
            "date": date,
            "score": 0,
            "category": category,
            "source": "arxiv",
        })

    return papers


if __name__ == "__main__":
    xml_input = sys.stdin.read()
    if not xml_input.strip():
        print("[]")
        sys.exit(0)
    try:
        result = parse(xml_input)
        print(json.dumps(result, ensure_ascii=False))
    except ET.ParseError as e:
        print(f"XML parse error: {e}", file=sys.stderr)
        print("[]")
        sys.exit(1)
