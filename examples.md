# mbox_to_knowledge Examples

This file shows common ways to run the script and what output layout to expect.

Input file used in all examples:

```text
/Volumes/Work03/Memory/Mail/All mail Including Spam and Trash.mbox
```

## 1. Basic export (no attachments)

Use this when you only want email metadata + body text.

Command:

```bash
python3 mbox_to_knowledge.py "/Volumes/Work03/Memory/Mail/All mail Including Spam and Trash.mbox"
```

What it does:

- Reads the MBOX file
- Exports Subject, From, To, Cc, Date, Labels, Thread-ID, Body
- Does not save attachments
- Deduplicates by default (so overlapping emails are skipped)

Output structure:

```text
Knowledge/
├── 2008/
│   ├── 2008-01.md
│   ├── 2008-02.md
│   └── ...
├── 2009/
│   └── ...
└── 2026/
    └── ...
```

Sample markdown entry structure:

```markdown
---

# Subject Line

From: sender@example.com

To: recipient@example.com

Cc: manager@example.com

Date: Tue, 22 Jul 2025 17:07:08 +0700

Labels: Important,Category Personal

Thread-ID: 18b2f4d8f2a12345

Email body text...
```

## 2. Export with attachments (default max size = 10 MB)

Use this when you want to save attachments and include attachment references in markdown.

Command:

```bash
python3 mbox_to_knowledge.py --include-attachments "/Volumes/Work03/Memory/Mail/All mail Including Spam and Trash.mbox"
```

What it does:

- Saves attachments up to 10 MB each
- Adds an Attachments section in each markdown entry for saved files
- Skips attachments larger than 10 MB

Output structure:

```text
Knowledge/
├── 2008/
│   ├── 2008-01.md
│   └── ...
├── 2026/
│   └── ...
└── _attachments/
    ├── 2008/
    │   ├── 01/
    │   │   ├── msg-00000001/
    │   │   │   ├── invoice-1a2b3c4d5e.pdf
    │   │   │   └── image-1122334455.png
    │   │   └── ...
    │   └── ...
    └── 2026/
        └── ...
```

Sample markdown entry structure:

```markdown
---

# Subject Line

From: sender@example.com

To: recipient@example.com

Cc: manager@example.com

Date: Tue, 22 Jul 2025 17:07:08 +0700

Labels: Important,Category Personal

Thread-ID: 18b2f4d8f2a12345

Email body text...

Attachments:
- invoice.pdf (application/pdf, 248109 bytes)
  Saved: Knowledge/_attachments/2025/07/msg-00000042/invoice-1a2b3c4d5e.pdf
- screenshot.png (image/png, 91342 bytes)
  Saved: Knowledge/_attachments/2025/07/msg-00000042/screenshot-1122334455.png
```

## 3. Export with attachments and custom max size

Use this when you want stricter or larger size control.

Command (2 MB max):

```bash
python3 mbox_to_knowledge.py --include-attachments --attachment-max-bytes 2097152 "/Volumes/Work03/Memory/Mail/All mail Including Spam and Trash.mbox"
```

What it does:

- Saves only attachments that are 2 MB or smaller
- Skips attachments over 2 MB

Output structure:

```text
Knowledge/
├── YYYY/
│   └── YYYY-MM.md
└── _attachments/
    └── YYYY/
        └── MM/
            └── msg-XXXXXXXX/
```

Notes:

- `--attachment-max-bytes` must be >= 1
- The size value is in bytes
- If `--include-attachments` is not set, attachments are not saved regardless of size value

## 4. Multiple runs / append behavior

Use this when processing incrementally.

Command:

```bash
python3 mbox_to_knowledge.py --include-attachments "/Volumes/Work03/Memory/Mail/All mail Including Spam and Trash.mbox"
```

What it does:

- Appends to existing `Knowledge/YYYY/YYYY-MM.md` files
- Creates missing year/month files as needed
- Recreates attachment directories if missing

## 5. Process overlapping MBOX files (dedup enabled by default)

Use this when two or more MBOX files contain the same emails.

Command:

```bash
python3 mbox_to_knowledge.py \
    "/Volumes/Work03/Memory/Mail/All mail Including Spam and Trash.mbox" \
    "/Volumes/Work03/Memory/Mail/All mail Including Spam and Trash-002.mbox"
```

What it does:

- Detects duplicates across input files in the same run
- Skips duplicates instead of writing duplicate markdown entries
- Prints duplicate detection messages during processing
- Prints total duplicates skipped in the final summary

Typical console output lines:

```text
Duplicate detected: message 12,345 skipped
Completed: exported=45,678 skipped=9,999 duplicates=8,765
Done. Exported 123,456 messages.
Duplicates detected/skipped: 8,765
```

Output structure:

```text
Knowledge/
├── YYYY/
│   └── YYYY-MM.md
└── _attachments/
        └── YYYY/
                └── MM/
                        └── msg-XXXXXXXX/
```

## 6. Disable deduplication (allow duplicates)

Use this only when you intentionally want repeated entries.

Command:

```bash
python3 mbox_to_knowledge.py --allow-duplicates \
    "/Volumes/Work03/Memory/Mail/All mail Including Spam and Trash.mbox" \
    "/Volumes/Work03/Memory/Mail/All mail Including Spam and Trash-002.mbox"
```

What it does:

- Disables default deduplication
- Writes all matching messages even if repeated across files

Output structure after repeated runs:

```text
Knowledge/
├── 2024/
│   └── 2024-11.md  (appended)
├── 2025/
│   └── 2025-01.md  (appended)
└── _attachments/
    └── ...
```

For a clean run:

```bash
rm -rf Knowledge
python3 mbox_to_knowledge.py --include-attachments "/Volumes/Work03/Memory/Mail/All mail Including Spam and Trash.mbox"
```
