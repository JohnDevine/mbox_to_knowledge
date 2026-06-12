#!/usr/bin/env python3

#!/usr/bin/env python3

"""
mbox_to_knowledge.py

Converts one or more Gmail/Takeout MBOX files into Markdown files suitable
for importing into Open WebUI Knowledge.

FEATURES
========

- Accepts one or more .mbox files as command-line arguments
- Extracts email bodies
- Prefers plain text content
- Falls back to HTML content and converts it to text
- Preserves:
    - Subject
    - From
    - To
    - Cc
    - Date
    - Gmail Labels
    - Thread-ID
    - Email Body
- Includes ALL messages, including Trash
- Ignores attachments
- Ignores embedded images
- Ignores MIME structure
- Groups output by Year and Month

OUTPUT STRUCTURE
================

Knowledge/
├── 2008/
│   ├── 2008-01.md
│   ├── 2008-02.md
│   └── ...
├── 2009/
│   └── ...
├── 2025/
│   ├── 2025-01.md
│   ├── 2025-02.md
│   └── ...
└── 2026/

Each markdown file contains many emails.

EXAMPLE ENTRY
=============

# Subject Line

From: someone@example.com

To: person1@example.com, person2@example.com

Cc: manager@example.com

Date: Tue, 22 Jul 2025 17:07:08 +0700

Labels: Important,Category Personal

Thread-ID: 18b2f4d8f2a12345

Email body text...

WHAT IS NOT INCLUDED
====================

- Attachments
- Images
- PDFs
- Office documents
- MIME metadata
- HTML formatting
- Embedded tracking pixels

These items greatly increase size but provide little value
to an Open WebUI knowledge base.

USAGE
=====

Single mailbox:

    python3 mbox_to_knowledge.py mailbox.mbox

Multiple mailboxes:

    python3 mbox_to_knowledge.py file1.mbox file2.mbox

Example:

    python3 mbox_to_knowledge.py \
        "All mail Including Spam and Trash.mbox" \
        "All mail Including Spam and Trash-002.mbox"

The output will be written to:

    ./Knowledge

Existing files are appended to.

For a fresh run:

    rm -rf Knowledge

then rerun the script.
"""

import argparse
import hashlib
import mailbox
import os
import re
import sys
import html
from email.utils import parsedate_to_datetime

OUTPUT_DIR = "Knowledge"
ATTACHMENTS_DIRNAME = "_attachments"


def print_banner(include_attachments=False, attachment_max_bytes=10 * 1024 * 1024):
    print()
    print("=" * 72)
    print("MBOX TO OPEN WEBUI KNOWLEDGE CONVERTER")
    print("=" * 72)
    print()
    print("Output directory:")
    print(f"  {os.path.abspath(OUTPUT_DIR)}")
    print()
    print("Output format:")
    print("  Knowledge/YYYY/YYYY-MM.md")
    print()
    print("Included:")
    print("  - Subject")
    print("  - From")
    print("  - To")
    print("  - Cc")
    print("  - Date")
    print("  - Gmail Labels")
    print("  - Thread-ID")
    print("  - Email body text")
    if include_attachments:
        print("  - Attachments (saved to disk)")
        print(
            "  - Attachment max size: "
            f"{attachment_max_bytes:,} bytes"
        )
    print()
    print("Excluded:")
    if not include_attachments:
        print("  - Attachments")
    print("  - Images")
    print("  - PDFs")
    print("  - Office documents")
    print("  - HTML formatting")
    print()
    print("Messages are grouped by year/month.")
    print()
    print("=" * 72)
    print()


def header_value(msg, name, default=""):
    try:
        value = msg.get(name, default)

        if value is None:
            return default

        return str(value)

    except Exception:
        return default


def html_to_text(html_content):

    if not html_content:
        return ""

    html_content = re.sub(
        r"<script.*?</script>",
        "",
        html_content,
        flags=re.I | re.S,
    )

    html_content = re.sub(
        r"<style.*?</style>",
        "",
        html_content,
        flags=re.I | re.S,
    )

    html_content = re.sub(
        r"<br\s*/?>",
        "\n",
        html_content,
        flags=re.I,
    )

    html_content = re.sub(
        r"</p>",
        "\n\n",
        html_content,
        flags=re.I,
    )

    html_content = re.sub(
        r"</div>",
        "\n",
        html_content,
        flags=re.I,
    )

    html_content = re.sub(
        r"<[^>]+>",
        " ",
        html_content,
    )

    html_content = html.unescape(html_content)

    html_content = re.sub(r"\r", "", html_content)
    html_content = re.sub(r"[ \t]+", " ", html_content)
    html_content = re.sub(r"\n{3,}", "\n\n", html_content)

    return html_content.strip()


def decode_payload(part):

    try:

        payload = part.get_payload(decode=True)

        if payload is None:
            return ""

        charset = part.get_content_charset()

        if not charset:
            charset = "utf-8"

        return payload.decode(
            charset,
            errors="ignore",
        )

    except Exception:
        return ""


def get_text(msg):

    plain_parts = []
    html_parts = []

    try:

        if msg.is_multipart():

            for part in msg.walk():

                disposition = str(
                    part.get(
                        "Content-Disposition",
                        ""
                    )
                ).lower()

                if "attachment" in disposition:
                    continue

                ctype = part.get_content_type()

                if ctype == "text/plain":

                    text = decode_payload(part)

                    if text.strip():
                        plain_parts.append(text)

                elif ctype == "text/html":

                    text = decode_payload(part)

                    if text.strip():
                        html_parts.append(text)

        else:

            ctype = msg.get_content_type()

            if ctype == "text/plain":
                plain_parts.append(
                    decode_payload(msg)
                )

            elif ctype == "text/html":
                html_parts.append(
                    decode_payload(msg)
                )

    except Exception:
        pass

    if plain_parts:
        return "\n".join(plain_parts)

    if html_parts:
        return html_to_text(
            "\n".join(html_parts)
        )

    return ""


def clean_body(text):

    if not text:
        return ""

    lines = []

    for line in text.splitlines():

        if line.startswith(">"):
            continue

        if re.match(
            r"^On .*wrote:$",
            line
        ):
            break

        lines.append(line)

    text = "\n".join(lines)

    text = re.sub(
        r"\n{4,}",
        "\n\n",
        text,
    )

    return text.strip()


def sanitize_header(value):
    return (
        value
        .replace("\n", " ")
        .replace("\r", " ")
        .strip()
    )


def sanitize_filename(name, fallback="attachment"):

    if not name:
        return fallback

    # Keep filenames filesystem-safe but readable.
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    cleaned = cleaned.strip("._")

    return cleaned or fallback


def extract_attachments(
    msg,
    attachments_root,
    message_key,
    include_attachments,
    attachment_max_bytes,
):

    if not include_attachments:
        return []

    extracted = []

    try:

        if not msg.is_multipart():
            return extracted

        message_dir = os.path.join(
            attachments_root,
            message_key,
        )

        os.makedirs(
            message_dir,
            exist_ok=True,
        )

        for part in msg.walk():

            if part.is_multipart():
                continue

            disposition = str(
                part.get(
                    "Content-Disposition",
                    "",
                )
            ).lower()

            filename = part.get_filename()

            is_attachment = (
                "attachment" in disposition
                or (
                    filename
                    and "inline" not in disposition
                )
            )

            if not is_attachment:
                continue

            payload = part.get_payload(decode=True)

            if payload is None:
                continue

            if len(payload) > attachment_max_bytes:
                continue

            safe_name = sanitize_filename(
                filename or "attachment.bin"
            )

            digest = hashlib.sha256(
                payload
            ).hexdigest()[:10]

            base, ext = os.path.splitext(safe_name)

            output_name = (
                f"{base}-{digest}{ext}"
                if ext else
                f"{safe_name}-{digest}"
            )

            output_path = os.path.join(
                message_dir,
                output_name,
            )

            with open(
                output_path,
                "wb",
            ) as f:
                f.write(payload)

            extracted.append(
                {
                    "name": safe_name,
                    "mime": part.get_content_type(),
                    "size": len(payload),
                    "path": output_path,
                }
            )

    except Exception:
        return extracted

    return extracted


def get_thread_id(msg):
    # Gmail Takeout commonly includes X-GM-THRID.
    # Fallbacks are included for broader mailbox compatibility.
    for header_name in (
        "X-GM-THRID",
        "Thread-ID",
        "Thread-Id",
        "X-Thread-ID",
        "X-Thread-Id",
        "Thread-Index",
    ):
        value = sanitize_header(
            header_value(msg, header_name)
        )
        if value:
            return value
    return ""


def process_mbox(
    mbox_file,
    include_attachments=False,
    attachment_max_bytes=10 * 1024 * 1024,
):

    print()
    print(f"Processing: {mbox_file}")
    print()

    exported = 0
    skipped = 0

    mbox = mailbox.mbox(mbox_file)

    for i, msg in enumerate(mbox, start=1):

        if i % 1000 == 0:

            print(
                f"  scanned={i:,} "
                f"exported={exported:,} "
                f"skipped={skipped:,}"
            )

        try:

            date_header = header_value(
                msg,
                "Date"
            )

            if not date_header:
                skipped += 1
                continue

            try:
                dt = parsedate_to_datetime(
                    date_header
                )
            except Exception:
                skipped += 1
                continue

            body = clean_body(
                get_text(msg)
            )

            year = str(dt.year)
            month = f"{dt.month:02d}"

            year_dir = os.path.join(
                OUTPUT_DIR,
                year
            )

            os.makedirs(
                year_dir,
                exist_ok=True
            )

            output_file = os.path.join(
                year_dir,
                f"{year}-{month}.md"
            )

            attachments_root = os.path.join(
                OUTPUT_DIR,
                ATTACHMENTS_DIRNAME,
                year,
                month,
            )

            message_key_raw = sanitize_header(
                header_value(
                    msg,
                    "Message-ID",
                )
            )

            if not message_key_raw:
                message_key_raw = f"msg-{i:08d}"

            message_key = sanitize_filename(
                message_key_raw,
                fallback=f"msg-{i:08d}",
            )

            attachments = extract_attachments(
                msg,
                attachments_root,
                message_key,
                include_attachments,
                attachment_max_bytes,
            )

            if not body and not attachments:
                skipped += 1
                continue

            subject = sanitize_header(
                header_value(
                    msg,
                    "Subject"
                )
            )

            sender = sanitize_header(
                header_value(
                    msg,
                    "From"
                )
            )

            recipient_to = sanitize_header(
                header_value(
                    msg,
                    "To"
                )
            )

            recipient_cc = sanitize_header(
                header_value(
                    msg,
                    "Cc"
                )
            )

            labels = sanitize_header(
                header_value(
                    msg,
                    "X-Gmail-Labels"
                )
            )

            thread_id = get_thread_id(msg)

            with open(
                output_file,
                "a",
                encoding="utf-8"
            ) as f:

                f.write("\n\n---\n\n")

                f.write(
                    f"# {subject or '(No Subject)'}\n\n"
                )

                f.write(
                    f"From: {sender}\n\n"
                )

                f.write(
                    f"To: {recipient_to}\n\n"
                )

                f.write(
                    f"Cc: {recipient_cc}\n\n"
                )

                f.write(
                    f"Date: {date_header}\n\n"
                )

                f.write(
                    f"Labels: {labels}\n\n"
                )

                f.write(
                    f"Thread-ID: {thread_id}\n\n"
                )

                if body:
                    f.write(body)
                else:
                    f.write("(No body text extracted)")

                if attachments:

                    f.write("\n\nAttachments:\n")

                    for item in attachments:
                        rel_path = os.path.relpath(
                            item["path"],
                            start=os.getcwd(),
                        )

                        f.write(
                            f"- {item['name']} "
                            f"({item['mime']}, "
                            f"{item['size']} bytes)\n"
                        )

                        f.write(
                            f"  Saved: {rel_path}\n"
                        )

                f.write("\n")

            exported += 1

        except Exception as e:

            print(
                f"Warning: message "
                f"{i:,} failed: {e}"
            )

            skipped += 1

    print()
    print(
        f"Completed:"
        f" exported={exported:,}"
        f" skipped={skipped:,}"
    )

    return exported


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Convert Gmail/Takeout MBOX files "
            "to markdown grouped by year/month."
        )
    )

    parser.add_argument(
        "--include-attachments",
        action="store_true",
        help=(
            "Save attachments to disk and list them "
            "in each markdown entry."
        ),
    )

    parser.add_argument(
        "--attachment-max-bytes",
        type=int,
        default=10 * 1024 * 1024,
        help=(
            "Maximum attachment size in bytes "
            "when --include-attachments is enabled "
            "(default: 10485760)."
        ),
    )

    parser.add_argument(
        "mbox_files",
        nargs="+",
        help="One or more .mbox files to process.",
    )

    args = parser.parse_args()

    if args.attachment_max_bytes < 1:
        print(
            "ERROR: --attachment-max-bytes must be >= 1"
        )
        sys.exit(1)

    print_banner(
        include_attachments=args.include_attachments,
        attachment_max_bytes=args.attachment_max_bytes,
    )

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    total = 0

    for mbox_file in args.mbox_files:

        if not os.path.isfile(
            mbox_file
        ):

            print(
                f"ERROR: File not found:\n"
                f"  {mbox_file}"
            )

            continue

        total += process_mbox(
            mbox_file,
            include_attachments=args.include_attachments,
            attachment_max_bytes=args.attachment_max_bytes,
        )

    print()
    print("=" * 72)
    print(
        f"Done. Exported {total:,} messages."
    )
    print(
        f"Knowledge directory:\n"
        f"  {os.path.abspath(OUTPUT_DIR)}"
    )
    print("=" * 72)
    print()


if __name__ == "__main__":
    main()
