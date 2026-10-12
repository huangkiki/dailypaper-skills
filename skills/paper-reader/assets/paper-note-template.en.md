---
title: "{Original title}"
method_name: "{MethodName}"
authors: [{Authors}]
year: {Year}
venue: "{Verified venue or preprint status}"
tags: [{tags}]
zotero_collection: "{Existing collection path, if applicable}"
image_source: online
arxiv_html: "{Verified HTML URL, if available}"
created: {date}
language: en
---

# Paper notes: {Title}

## Metadata

| Field | Details |
| --- | --- |
| Affiliations | {Sourced affiliations} |
| Date | {Month Year} |
| Project page | {Verified project URL} |
| Baselines | [[{Compared method}]] |
| Links | [Paper]({paper_url}) / [Code]({verified_code_url}) |

## One-sentence summary

> {Core contribution in one concise sentence.}

## Core contributions

1. **{Contribution}**: {What changed and its supporting evidence.}
2. **{Contribution}**: {Include only contributions supported by the source.}

## Background and motivation

### Problem

{Task, setting, inputs, and desired outcome.}

### Limitations of prior work

{Specific limitations, with [[links]] to existing notes when available.}

### Motivation

{Why the proposed approach addresses the stated problem.}

## Method

### Architecture

- **Inputs**: {Actual input modalities and variables.}
- **Backbone**: {Reported architecture.}
- **Core modules**: [[{Concept}]] for {purpose}.
- **Outputs**: {Actual predictions/actions and their representation.}
- **Parameters**: {Reported count, or not reported.}

### {Module name}

**Motivation**: {Design goal and assumptions.}

**Implementation**: {Mechanism, training/inference details, and inline concept links.}

{Repeat for the paper's actual modules. Do not invent modules to fill the template.}

## Key equations

### Equation 1: [[{Concept target}|{Equation name}]]

$$
{Exact source equation}
$$

**Meaning**: {Role in the method.}

**Symbols**:

- ${symbol}$: {Definition, dimensions, and domain when relevant.}

{Repeat for every source equation, preserving notation and numbering. If the source has no equations, say so.}

## Figures and tables

### Figure 1: {Original caption}

![Figure 1]({Verified image URL})

**Explanation**: {What the figure shows and what it supports.}

{Repeat for every figure. Use local assets if no working external source is available.}

### Table 1: {Original caption}

{Reproduce every row and column with exact source numbers, units, and notes.}

**Interpretation**: {Main comparison and evaluation limits.}

{Repeat for every table, including ablations. Identify extraction gaps explicitly.}

## Experiments

### Datasets and tasks

| Dataset/task | Scale | Properties | Role |
| --- | --- | --- | --- |
| {Dataset} | {Reported scale} | {Relevant properties} | {Training/evaluation} |

### Implementation details

- **Backbone**: {Architecture.}
- **Optimizer**: {Optimizer and learning rate.}
- **Batch size**: {Reported value.}
- **Training duration**: {Steps/epochs.}
- **Hardware**: {Reported model and count.}

{Mark missing details as not reported.}

### Results and qualitative observations

{Reported results, metric definitions, baselines, uncertainty, and real/simulated evaluation settings. Separate the authors' results from any independently verified reproduction.}

## Critical assessment

### Strengths

{Concrete strengths with evidence.}

### Limitations

{Demonstrated limitations and clearly marked open questions.}

### Potential improvements

{Suggestions distinguished from claims made by the paper.}

### Reproducibility

- [ ] Code available
- [ ] Pretrained models available
- [ ] Training details sufficient
- [ ] Datasets accessible

{Check only verified items and cite the relevant source.}

## Related notes

### Built on

- [[{Prior work}]]: {Relationship.}

### Compared against

- [[{Baseline}]]: {Comparison and protocol.}

### Related methods

- [[{Concept}]]: {Role in the method.}

### Hardware and datasets

- [[{Resource}]]: {Use in this paper.}

## Quick reference

> [!summary] {Title}
> - **Core idea**: {One sentence.}
> - **Method**: {Mechanism.}
> - **Result**: {Evidence with scope.}
> - **Code**: {Verified link or unavailable.}

*Notes created: {timestamp}*
