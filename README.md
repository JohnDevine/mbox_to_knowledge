# mbox_to_knowledge

Convert one or more Gmail/Google Takeout MBOX files into Markdown files grouped by year and month for knowledge ingestion workflows.

## Features

- Accepts one or more `.mbox` files as input
- Extracts message body text
- Prefers `text/plain` and falls back to HTML-to-text conversion
- Preserves these fields in output:
  - Subject
  - From
  - To
  - Cc
  - Date
  - Labels (X-Gmail-Labels)
  - Thread-ID (prefers X-GM-THRID)
  - Body
- Includes all messages (including Trash)
- Ignores attachments and embedded images
- Writes output grouped by `Knowledge/YYYY/YYYY-MM.md`

## Requirements

- Python 3.8+
- Standard library only (no external dependencies)

## Usage

Single mailbox:

```bash
python3 mbox_to_knowledge.py mailbox.mbox
```

Multiple mailboxes:

```bash
python3 mbox_to_knowledge.py file1.mbox file2.mbox
```

Example:

```bash
python3 mbox_to_knowledge.py \
  "All mail Including Spam and Trash.mbox" \
  "All mail Including Spam and Trash-002.mbox"
```

## Output

The script writes to:

```text
./Knowledge
```

Output structure:

```text
Knowledge/
├── 2025/
│   ├── 2025-01.md
│   └── 2025-02.md
└── 2026/
```

Each entry is separated by `---` and includes the preserved headers followed by the cleaned body.

## Notes

- Existing monthly files are appended to.
- For a fresh export, remove the output directory before running:

```bash
rm -rf Knowledge
```
