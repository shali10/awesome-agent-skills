---
name: large-file-data-analysis
description: Use when analyzing, transforming, or extracting insights from massive Excel spreadsheets (10k-100k+ rows) and large PDF/Word documents without causing context overflow.
version: 1.0.0
author: shali10
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [data-analysis, excel, streaming, large-files, openpyxl, parquet]
  related_skills: [markdown-to-html-report]
---

# Large File & Spreadsheet Data Analysis Engine

## Overview

High-performance data analysis skill tailored for AI Agents. It provides streaming ingestion pipelines via `openpyxl(read_only=True)` and automatic Parquet conversion, enabling memory-safe querying of 100,000+ row datasets in constant <50MB RAM.

## When to Use & When NOT to Use

### When to Use
- Excel spreadsheets (`.xlsx`/`.xls`) with ≥10,000 rows or multiple dense sheets.
- Multi-megabyte PDF, Word, or CSV datasets requiring statistical aggregation.
- Generating schema summaries and targeted slices without loading raw data into LLM context.

### When NOT to Use
- Small tables (<100 rows) where standard markdown tables or direct pandas reads are fine.
- Visual chart rendering without data extraction (use image/visualization tools).

## Streaming Extraction Pattern

```python
import openpyxl

def stream_excel_summary(file_path: str, sample_rows: int = 5):
    wb = openpyxl.load_workbook(filename=file_path, read_only=True, data_only=True)
    summary = {}
    
    for sheet in wb.sheetnames:
        ws = wb[sheet]
        rows = ws.iter_rows(values_only=True)
        try:
            header = next(rows)
        except StopIteration:
            continue
            
        row_count = 0
        samples = []
        for row in rows:
            row_count += 1
            if len(samples) < sample_rows:
                samples.append(row)
                
        summary[sheet] = {
            "columns": header,
            "total_rows": row_count,
            "sample_rows": samples
        }
    wb.close()
    return summary
```

## Common Pitfalls

1. **Loading large Excel files in write/full mode**: Standard `load_workbook` builds a massive DOM in memory. Always use `read_only=True` and `data_only=True`.
2. **Dumping thousands of rows into prompt context**: Extract aggregates, schemas, and summary distributions in code first; return only the high-signal findings to LLM context.
3. **Mismatched data types in columns**: Large datasets often have mixed type cells (e.g. numeric IDs parsed as floats); sanitize column types during streaming.

## Verification Checklist

- [ ] Memory footprint remains < 50MB during streaming iteration.
- [ ] Summary output reports total row count, column list, and non-null distributions.
- [ ] No raw multi-megabyte payloads are passed directly into prompt context.
