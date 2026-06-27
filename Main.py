import os
import re
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from datetime import datetime

import pyperclip
from groq import Groq
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Preformatted
)
from reportlab.lib.colors import HexColor


# =====================================================================
# CONFIG  (unchanged)
# =====================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
MODEL = "llama-3.3-70b-versatile"
HISTORY_FILE = "notes_history.json"

SYSTEM_PROMPT = """You are a world-class Professor, Technical Trainer, Researcher, Curriculum Designer, Industry Expert, Technical Writer, and Exam Preparation Specialist.

Your primary goal is to generate COMPLETE, ACCURATE, STRUCTURED, and INDUSTRY-READY study notes that help a student learn a topic from Beginner to Advanced level without needing external resources.

GENERAL RULES

1. If the user enters only a topic name (e.g., Python, Machine Learning, Data Science, Cyber Security, Java, MySQL, Cloud Computing, Networking), automatically generate COMPLETE NOTES covering all major concepts from beginner to advanced.

2. If the user provides a specific sub-topic (e.g., Python Functions, NumPy Arrays, SQL Joins), generate deep and detailed notes focused on that specific topic.

3. Never assume the student has prior knowledge.

4. Explain concepts using simple, clear, beginner-friendly English.

5. Always explain:

   * What
   * Why
   * How
   * When to use
   * Where it is used
   * Advantages
   * Disadvantages
   * Features
   * Applications
   * Industry relevance

6. Use real-world examples whenever possible.

7. Use tables, bullet points, comparisons, and structured formatting whenever useful.

8. Avoid unnecessary complexity and academic jargon.

9. Ensure explanations are accurate, practical, and easy to understand.

10. If the topic is broad, generate highly detailed notes (3000–5000+ words).

11. Ensure the generated notes are detailed enough that a student can learn the topic without referring to external resources.

TOPIC CLASSIFICATION

Before generating notes, internally classify the topic into one of these categories:

* Programming
* Database
* Data Science
* Artificial Intelligence
* Machine Learning
* Deep Learning
* Cyber Security
* Cloud Computing
* Networking
* DevOps
* Software Development
* Web Development
* Mobile Development
* UI/UX Design
* Digital Marketing
* Business
* General Education
* Other

Adapt explanations according to the category.

PROGRAMMING TOPICS REQUIREMENTS

For Programming Topics:

* Explain every concept clearly.
* Include syntax.
* Include code examples.
* Explain code line-by-line.
* Explain input and output.
* Explain common mistakes.
* Explain best practices.
* Explain real-world usage.

For major programming languages (Python, Java, C, C++, JavaScript, etc.), cover:

* Introduction
* Installation
* Environment Setup
* Variables
* Data Types
* Operators
* Conditional Statements
* Loops
* Functions
* Modules
* Packages
* OOP
* File Handling
* Exception Handling
* Libraries
* Frameworks
* Advanced Concepts
* Projects
* Interview Questions

DATABASE TOPICS REQUIREMENTS

For Database Topics:

Cover:

* DBMS Basics
* RDBMS
* Tables
* Keys
* Constraints
* Joins
* Indexing
* Normalization
* Transactions
* SQL Queries
* Optimization
* Real-world Examples

AI / DATA SCIENCE TOPICS REQUIREMENTS

Cover:

* Fundamentals
* Workflow
* Algorithms
* Tools
* Libraries
* Model Training
* Evaluation
* Deployment
* Industry Use Cases
* Projects

TECHNICAL TOPICS REQUIREMENTS

Whenever applicable include:

* Architecture
* Workflow
* Process Flow
* Components
* System Design
* Real-World Implementation

Use text-based diagrams such as:

[Input]
↓
[Processing]
↓
[Output]

or

Client
↓
Server
↓
Database

OUTPUT FORMAT

# Topic Overview

## Introduction

* What is it?
* Why was it created?
* Why is it important?
* Where is it used?

## History and Evolution

## Definition and Core Concepts

## Beginner Level Concepts

Explain every beginner concept in detail.

## Intermediate Level Concepts

Explain every intermediate concept in detail.

## Advanced Level Concepts

Explain advanced concepts thoroughly.

## Architecture / Workflow

Include diagrams and process flow where applicable.

## Components and Features

Use tables whenever appropriate.

## Advantages

## Disadvantages

## Comparison Table

Whenever applicable, provide comparisons such as:

* List vs Tuple
* SQL vs NoSQL
* AI vs ML vs DL
* HTTP vs HTTPS

## Real World Applications

## Industry Use Cases

## Tools, Technologies, and Ecosystem

Mention commonly used tools, frameworks, libraries, and platforms.

## Practical Examples

Provide detailed examples.

## Code Examples

If applicable:

* Syntax
* Sample Code
* Line-by-Line Explanation
* Expected Output

## Common Errors and Solutions

Provide common mistakes and troubleshooting guidance.

## Best Practices

Industry-standard recommendations and guidelines.

## Projects

### Beginner Projects

### Intermediate Projects

### Advanced Projects

Explain project ideas briefly.

## Career Opportunities

Include:

* Job Roles
* Required Skills
* Career Path
* Future Scope

## Learning Roadmap

### Stage 1: Beginner

### Stage 2: Intermediate

### Stage 3: Advanced

### Stage 4: Industry Ready

Provide a clear learning path.

## Interview Questions and Answers

### Beginner Level

Question
Answer
Explanation

### Intermediate Level

Question
Answer
Explanation

### Advanced Level

Question
Answer
Explanation

Generate at least:

* 10 Beginner Questions
* 10 Intermediate Questions
* 10 Advanced Questions

## MCQs

Generate:

* 20 Beginner MCQs
* 20 Intermediate MCQs
* 10 Advanced MCQs

Include answers.

## One Page Cheat Sheet

Provide quick revision notes.

## Key Points for Revision

Provide concise bullet points.

## Summary

Provide a complete conclusion summarizing the topic.

FINAL RULES

* Never provide short notes.
* Never skip important concepts.
* Never generate shallow content.
* Always create structured, detailed, exam-ready, interview-ready, and industry-ready notes.
* Use headings and subheadings properly.
* Use tables wherever useful.
* Use bullet points wherever useful.
* Use examples whenever possible.
* Cover the topic as if creating a complete professional course.
* Focus on clarity, depth, and practical understanding."""


# =====================================================================
# AI HANDLER  (unchanged)
# =====================================================================
def generate_notes(topic: str, points: str) -> str:
    if not GROQ_API_KEY:
        raise ValueError("Groq API key not set.")
    client = Groq(api_key=GROQ_API_KEY)

    if points.strip():
        user_msg = (f"Topic: {topic}\n\nBullet Points to expand:\n{points}\n\n"
                    f"Generate comprehensive study notes following the format exactly.")
    else:
        user_msg = (f"Topic: {topic}\n\n"
                    f"No bullet points provided. Generate full detailed study notes "
                    f"on this topic from scratch, following the format exactly. "
                    f"Cover all important sub-topics a student needs.")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.5,
        max_tokens=4000,
        top_p=0.9,
    )
    return response.choices[0].message.content.strip()


# =====================================================================
# STORAGE  (unchanged)
# =====================================================================
def load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_history(history: list) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def add_note(topic: str, points: str, notes: str) -> dict:
    history = load_history()
    entry = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "topic": topic,
        "points": points,
        "notes": notes,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pinned": False,
    }
    history.insert(0, entry)
    save_history(history)
    return entry


def delete_note(note_id: str) -> None:
    history = [n for n in load_history() if n["id"] != note_id]
    save_history(history)


def toggle_pin(note_id: str) -> None:
    history = load_history()
    for n in history:
        if n["id"] == note_id:
            n["pinned"] = not n.get("pinned", False)
    save_history(history)


# =====================================================================
# IMPROVED PDF EXPORT
# =====================================================================
def export_to_pdf(topic: str, notes: str, filename: str) -> None:
    """
    Professional PDF export with:
    - Styled headings (H1/H2/H3)
    - Code blocks in monospace with grey background
    - Tables rendered as real PDF tables
    - Horizontal rules between sections
    - Footer with page numbers
    """

    # --- Page number footer ---
    def add_page_number(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(HexColor("#64748B"))
        page_num = f"Page {canvas.getPageNumber()}"
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, page_num)
        canvas.drawString(2 * cm, 1.2 * cm, topic)
        canvas.restoreState()

    doc = SimpleDocTemplate(
        filename, pagesize=A4,
        leftMargin=2.5 * cm, rightMargin=2.5 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
    )

    # --- Style definitions ---
    styles = getSampleStyleSheet()

    s_title = ParagraphStyle(
        "MyTitle",
        fontName="Helvetica-Bold", fontSize=24,
        textColor=HexColor("#1E3A5F"), spaceAfter=16,
        spaceBefore=0, leading=30,
    )
    s_h1 = ParagraphStyle(
        "MyH1",
        fontName="Helvetica-Bold", fontSize=18,
        textColor=HexColor("#1E40AF"), spaceBefore=20,
        spaceAfter=8, leading=24,
        borderPad=4,
    )
    s_h2 = ParagraphStyle(
        "MyH2",
        fontName="Helvetica-Bold", fontSize=14,
        textColor=HexColor("#1D4ED8"), spaceBefore=16,
        spaceAfter=6, leading=20,
    )
    s_h3 = ParagraphStyle(
        "MyH3",
        fontName="Helvetica-Bold", fontSize=12,
        textColor=HexColor("#2563EB"), spaceBefore=12,
        spaceAfter=4, leading=18,
    )
    s_body = ParagraphStyle(
        "MyBody",
        fontName="Helvetica", fontSize=10.5,
        textColor=HexColor("#1E293B"), leading=17,
        spaceAfter=6, alignment=TA_JUSTIFY,
    )
    s_bullet = ParagraphStyle(
        "MyBullet",
        fontName="Helvetica", fontSize=10.5,
        textColor=HexColor("#1E293B"), leading=17,
        spaceAfter=3, leftIndent=18,
        bulletIndent=6,
    )
    s_code = ParagraphStyle(
        "MyCode",
        fontName="Courier", fontSize=9,
        textColor=HexColor("#1E293B"), leading=14,
        leftIndent=12, rightIndent=12,
        spaceAfter=2, spaceBefore=2,
        backColor=HexColor("#F1F5F9"),
    )
    s_quote = ParagraphStyle(
        "MyQuote",
        fontName="Helvetica-Oblique", fontSize=10.5,
        textColor=HexColor("#475569"), leading=17,
        leftIndent=20, spaceAfter=6,
        borderPad=4,
    )

    story = []

    # Title
    story.append(Paragraph(topic, s_title))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=HexColor("#1E40AF"), spaceAfter=14))
    story.append(Spacer(1, 0.2 * cm))

    lines = notes.split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        # --- Code block (``` fences) ---
        if stripped.startswith("```"):
            i += 1
            code_lines = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i].rstrip())
                i += 1
            # Wrap code in a table for the grey box effect
            code_text = "\n".join(code_lines) if code_lines else " "
            code_data = [[Preformatted(code_text, s_code)]]
            code_table = Table(code_data, colWidths=["100%"])
            code_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F1F5F9")),
                ("BOX",        (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
                ("TOPPADDING",    (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ]))
            story.append(code_table)
            story.append(Spacer(1, 0.2 * cm))
            i += 1
            continue

        # --- Markdown table (lines with | separators) ---
        if stripped.startswith("|") and stripped.endswith("|"):
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row_line = lines[i].strip()
                # Skip separator rows (|---|---|)
                if re.match(r"^\|[-| :]+\|$", row_line):
                    i += 1
                    continue
                cells = [c.strip() for c in row_line.strip("|").split("|")]
                table_rows.append(cells)
                i += 1
            if table_rows:
                # Normalize column count
                max_cols = max(len(r) for r in table_rows)
                for r in table_rows:
                    while len(r) < max_cols:
                        r.append("")

                # Convert cells to Paragraphs
                def make_cell(txt, bold=False):
                    safe = txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
                    sty = ParagraphStyle(
                        "TC", fontName="Helvetica-Bold" if bold else "Helvetica",
                        fontSize=9.5, leading=14, textColor=HexColor("#1E293B")
                    )
                    return Paragraph(safe, sty)

                pdf_table_data = []
                for row_idx, row in enumerate(table_rows):
                    pdf_row = [make_cell(c, bold=(row_idx == 0)) for c in row]
                    pdf_table_data.append(pdf_row)

                col_width = (A4[0] - 5 * cm) / max_cols
                tbl = Table(pdf_table_data, colWidths=[col_width] * max_cols)
                tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1E40AF")),
                    ("TEXTCOLOR",  (0, 0), (-1, 0), rl_colors.white),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                     [HexColor("#F8FAFC"), HexColor("#EFF6FF")]),
                    ("GRID",    (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")),
                    ("TOPPADDING",    (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]))
                story.append(tbl)
                story.append(Spacer(1, 0.3 * cm))
            continue

        # --- Headings ---
        if stripped.startswith("# ") and not stripped.startswith("## "):
            text = stripped[2:].strip()
            safe = _pdf_safe(text)
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph(safe, s_h1))
            story.append(HRFlowable(width="100%", thickness=1,
                                     color=HexColor("#BFDBFE"), spaceAfter=6))
            i += 1
            continue

        if stripped.startswith("### "):
            text = stripped[4:].strip()
            safe = _pdf_safe(text)
            story.append(Paragraph(safe, s_h3))
            i += 1
            continue

        if stripped.startswith("## "):
            text = stripped[3:].strip()
            safe = _pdf_safe(text)
            story.append(Paragraph(safe, s_h2))
            i += 1
            continue

        # --- Blockquote ---
        if stripped.startswith("> "):
            text = stripped[2:].strip()
            safe = _pdf_safe(text)
            story.append(Paragraph(safe, s_quote))
            i += 1
            continue

        # --- Bullet list ---
        if stripped.startswith(("* ", "- ", "• ")):
            text = re.sub(r"^[*\-•]\s+", "", stripped)
            safe = _pdf_safe(text)
            story.append(Paragraph(f"• &nbsp; {safe}", s_bullet))
            i += 1
            continue

        # --- Numbered list ---
        if re.match(r"^\d+\.\s", stripped):
            safe = _pdf_safe(stripped)
            story.append(Paragraph(safe, s_bullet))
            i += 1
            continue

        # --- Empty line ---
        if not stripped:
            story.append(Spacer(1, 0.15 * cm))
            i += 1
            continue

        # --- Regular paragraph ---
        safe = _pdf_safe(stripped)
        story.append(Paragraph(safe, s_body))
        i += 1

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)


def _pdf_safe(text: str) -> str:
    """Escape HTML chars and convert Markdown bold/italic for ReportLab."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r'<font name="Courier">\1</font>', text)
    return text


# =====================================================================
# COLOR THEMES
# =====================================================================
THEMES = {
    "light": {
        "bg":          "#F8FAFC",
        "panel":       "#FFFFFF",
        "header_bg":   "#1E3A5F",
        "header_fg":   "#FFFFFF",
        "accent":      "#2563EB",
        "text":        "#1E293B",
        "subtext":     "#475569",
        "code_bg":     "#F1F5F9",
        "code_fg":     "#0F172A",
        "border":      "#CBD5E1",
        "h1_fg":       "#1E3A5F",
        "h2_fg":       "#1D4ED8",
        "h3_fg":       "#2563EB",
        "bullet_fg":   "#2563EB",
        "quote_bg":    "#EFF6FF",
        "quote_fg":    "#1E40AF",
        "toc_bg":      "#F0F9FF",
        "toc_fg":      "#1E40AF",
        "search_hl":   "#FDE68A",
        "tip_bg":      "#ECFDF5",
        "tip_fg":      "#065F46",
        "warn_bg":     "#FFFBEB",
        "warn_fg":     "#92400E",
        "entry_bg":    "#FFFFFF",
        "listbox_bg":  "#FFFFFF",
        "listbox_sel": "#DBEAFE",
        "status_bg":   "#F1F5F9",
        "separator":   "#E2E8F0",
        "pin_fg":      "#F59E0B",
    },
    "dark": {
        "bg":          "#0F172A",
        "panel":       "#1E293B",
        "header_bg":   "#020617",
        "header_fg":   "#E2E8F0",
        "accent":      "#3B82F6",
        "text":        "#E2E8F0",
        "subtext":     "#94A3B8",
        "code_bg":     "#0F172A",
        "code_fg":     "#7DD3FC",
        "border":      "#334155",
        "h1_fg":       "#BFDBFE",
        "h2_fg":       "#93C5FD",
        "h3_fg":       "#60A5FA",
        "bullet_fg":   "#60A5FA",
        "quote_bg":    "#1E3A5F",
        "quote_fg":    "#93C5FD",
        "toc_bg":      "#1E2D40",
        "toc_fg":      "#93C5FD",
        "search_hl":   "#78350F",
        "tip_bg":      "#052E16",
        "tip_fg":      "#86EFAC",
        "warn_bg":     "#1C1004",
        "warn_fg":     "#FCD34D",
        "entry_bg":    "#1E293B",
        "listbox_bg":  "#1E293B",
        "listbox_sel": "#1E3A5F",
        "status_bg":   "#1E293B",
        "separator":   "#334155",
        "pin_fg":      "#FBBF24",
    },
}


# =====================================================================
# MARKDOWN RENDERER  (the heart of the new notes display)
# =====================================================================
class MarkdownViewer(tk.Frame):
    """
    A custom Markdown-to-Tkinter renderer.
    Supports: H1/H2/H3, bold, italic, inline-code, code blocks,
    bullet lists, numbered lists, blockquotes, tables,
    tip/warning/important callouts, horizontal rules.
    """

    BASE_SIZE = 11  # base font size (zoom changes this)

    def __init__(self, parent, theme: dict, **kwargs):
        super().__init__(parent, bg=theme["bg"], **kwargs)
        self.theme = theme
        self.zoom = 0          # zoom offset (±2 per step)
        self._toc_items = []   # list of (level, text, mark) for TOC
        self._search_positions = []
        self._search_idx = -1

        # The actual text widget
        self.text = tk.Text(
            self,
            wrap="word",
            relief="flat",
            bd=0,
            padx=28, pady=18,
            cursor="arrow",
            state="disabled",
            bg=theme["bg"],
            fg=theme["text"],
            insertbackground=theme["text"],
            selectbackground=theme["accent"],
            font=("Segoe UI", self.BASE_SIZE),
        )
        self.vsb = ttk.Scrollbar(self, orient="vertical",
                                  command=self.text.yview)
        self.text.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

        self._configure_tags()

    # ------------------------------------------------------------------ tags
    def _configure_tags(self):
        t = self.theme
        s = self.BASE_SIZE + self.zoom

        self.text.tag_configure("h1", font=("Segoe UI", s + 9, "bold"),
                                foreground=t["h1_fg"], spacing1=18, spacing3=8)
        self.text.tag_configure("h2", font=("Segoe UI", s + 5, "bold"),
                                foreground=t["h2_fg"], spacing1=14, spacing3=6)
        self.text.tag_configure("h3", font=("Segoe UI", s + 2, "bold"),
                                foreground=t["h3_fg"], spacing1=10, spacing3=4)
        self.text.tag_configure("h1_rule", font=("Segoe UI", 2),
                                background=t["border"], spacing3=8)

        self.text.tag_configure("body", font=("Segoe UI", s),
                                foreground=t["text"], spacing3=4, lmargin1=4)
        self.text.tag_configure("bold", font=("Segoe UI", s, "bold"),
                                foreground=t["text"])
        self.text.tag_configure("italic", font=("Segoe UI", s, "italic"),
                                foreground=t["subtext"])
        self.text.tag_configure("inline_code",
                                font=("Consolas", s - 1),
                                foreground=t["code_fg"],
                                background=t["code_bg"])

        self.text.tag_configure("bullet", font=("Segoe UI", s),
                                foreground=t["text"],
                                lmargin1=24, lmargin2=38, spacing3=3)
        self.text.tag_configure("bullet_dot", font=("Segoe UI", s, "bold"),
                                foreground=t["bullet_fg"])
        self.text.tag_configure("numbered", font=("Segoe UI", s),
                                foreground=t["text"],
                                lmargin1=24, lmargin2=42, spacing3=3)

        self.text.tag_configure("code_block",
                                font=("Consolas", s - 1),
                                foreground=t["code_fg"],
                                background=t["code_bg"],
                                lmargin1=16, lmargin2=16,
                                spacing1=10, spacing3=10,
                                relief="flat")

        self.text.tag_configure("blockquote",
                                font=("Segoe UI", s, "italic"),
                                foreground=t["quote_fg"],
                                background=t["quote_bg"],
                                lmargin1=24, lmargin2=24,
                                spacing1=6, spacing3=6)

        self.text.tag_configure("table_header",
                                font=("Segoe UI", s, "bold"),
                                foreground="#FFFFFF",
                                background=t["accent"],
                                spacing1=4, spacing3=4,
                                lmargin1=8)
        self.text.tag_configure("table_row_even",
                                font=("Consolas", s - 1),
                                foreground=t["text"],
                                background=t["bg"],
                                lmargin1=8, spacing3=2)
        self.text.tag_configure("table_row_odd",
                                font=("Consolas", s - 1),
                                foreground=t["text"],
                                background=t["code_bg"],
                                lmargin1=8, spacing3=2)

        self.text.tag_configure("tip",
                                font=("Segoe UI", s),
                                foreground=t["tip_fg"],
                                background=t["tip_bg"],
                                lmargin1=20, spacing1=6, spacing3=6)
        self.text.tag_configure("warning",
                                font=("Segoe UI", s),
                                foreground=t["warn_fg"],
                                background=t["warn_bg"],
                                lmargin1=20, spacing1=6, spacing3=6)

        self.text.tag_configure("hr",
                                font=("Segoe UI", 3),
                                background=t["border"],
                                spacing1=8, spacing3=8)

        self.text.tag_configure("search_hl",
                                background=t["search_hl"],
                                foreground=t["text"])
        self.text.tag_configure("search_current",
                                background="#F59E0B",
                                foreground="#FFFFFF")

    # ------------------------------------------------------------------ render
    def render(self, markdown_text: str):
        """Parse markdown_text and populate the text widget."""
        self._toc_items.clear()
        self._search_positions.clear()
        self._search_idx = -1

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")

        lines = markdown_text.split("\n")
        i = 0
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()

            # ---- Code fence ----
            if stripped.startswith("```"):
                lang = stripped[3:].strip()
                i += 1
                code_lines = []
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i].rstrip())
                    i += 1
                code = "\n".join(code_lines)
                self.text.insert("end", "\n")
                self.text.insert("end", code + "\n", "code_block")
                self.text.insert("end", "\n")
                i += 1
                continue

            # ---- Markdown table ----
            if stripped.startswith("|") and stripped.endswith("|"):
                table_lines = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    table_lines.append(lines[i].strip())
                    i += 1
                self._render_table(table_lines)
                continue

            # ---- HR ----
            if re.match(r"^[-*_]{3,}\s*$", stripped):
                self.text.insert("end", "\n" + "─" * 72 + "\n", "hr")
                i += 1
                continue

            # ---- H1 ----
            if stripped.startswith("# ") and not stripped.startswith("## "):
                text = stripped[2:].strip()
                mark = f"h_{len(self._toc_items)}"
                self.text.insert("end", "\n")
                self.text.insert("end", text + "\n", "h1")
                self.text.insert("end", "─" * 64 + "\n", "h1_rule")
                self.text.mark_set(mark, f"end - 3 lines")
                self._toc_items.append((1, text, mark))
                i += 1
                continue

            # ---- H2 ----
            if stripped.startswith("## ") and not stripped.startswith("### "):
                text = stripped[3:].strip()
                mark = f"h_{len(self._toc_items)}"
                self.text.insert("end", "\n")
                self.text.insert("end", text + "\n", "h2")
                self.text.mark_set(mark, f"end - 2 lines")
                self._toc_items.append((2, text, mark))
                i += 1
                continue

            # ---- H3 ----
            if stripped.startswith("### "):
                text = stripped[4:].strip()
                mark = f"h_{len(self._toc_items)}"
                self.text.insert("end", "\n")
                self.text.insert("end", text + "\n", "h3")
                self.text.mark_set(mark, f"end - 2 lines")
                self._toc_items.append((3, text, mark))
                i += 1
                continue

            # ---- Blockquote ----
            if stripped.startswith("> "):
                text = stripped[2:]
                self.text.insert("end", "❝  " + text + "\n", "blockquote")
                i += 1
                continue

            # ---- Tip callout ----
            if re.match(r"^\*\*Tip[:\s]", stripped) or stripped.lower().startswith("💡"):
                self.text.insert("end", "💡  " + stripped.lstrip("💡").strip() + "\n", "tip")
                i += 1
                continue

            # ---- Warning callout ----
            if (re.match(r"^\*\*Warning[:\s]", stripped, re.I) or
                    stripped.lower().startswith("⚠")):
                self.text.insert("end", "⚠️  " + stripped.lstrip("⚠️").strip() + "\n", "warning")
                i += 1
                continue

            # ---- Bullet ----
            if stripped.startswith(("* ", "- ", "• ")):
                text = re.sub(r"^[*\-•]\s+", "", stripped)
                self.text.insert("end", "  • ", "bullet_dot")
                self._insert_inline(text, "bullet")
                self.text.insert("end", "\n")
                i += 1
                continue

            # ---- Numbered list ----
            m = re.match(r"^(\d+)\.\s+(.*)", stripped)
            if m:
                num = m.group(1)
                text = m.group(2)
                self.text.insert("end", f"  {num}. ", "bullet_dot")
                self._insert_inline(text, "numbered")
                self.text.insert("end", "\n")
                i += 1
                continue

            # ---- Empty line ----
            if not stripped:
                self.text.insert("end", "\n")
                i += 1
                continue

            # ---- Regular paragraph ----
            self._insert_inline(stripped, "body")
            self.text.insert("end", "\n")
            i += 1

        self.text.configure(state="disabled")

    def _render_table(self, table_lines: list):
        """Render a Markdown pipe table into the text widget."""
        rows = []
        for line in table_lines:
            if re.match(r"^\|[-| :]+\|$", line):
                continue  # skip separator
            cells = [c.strip() for c in line.strip("|").split("|")]
            rows.append(cells)
        if not rows:
            return

        # Compute column widths (chars)
        max_cols = max(len(r) for r in rows)
        col_widths = [8] * max_cols
        for row in rows:
            for ci, cell in enumerate(row):
                col_widths[ci] = max(col_widths[ci], len(cell) + 2)

        self.text.insert("end", "\n")
        for ri, row in enumerate(rows):
            # Pad row to max_cols
            while len(row) < max_cols:
                row.append("")
            tag = "table_header" if ri == 0 else (
                "table_row_even" if ri % 2 == 0 else "table_row_odd"
            )
            parts = []
            for ci, cell in enumerate(row):
                parts.append(cell.ljust(col_widths[ci]))
            line_txt = "  " + " │ ".join(parts) + "\n"
            self.text.insert("end", line_txt, tag)

            # Separator after header
            if ri == 0:
                sep = "  " + "─" * (sum(col_widths) + 3 * (max_cols - 1)) + "\n"
                self.text.insert("end", sep, "table_row_even")
        self.text.insert("end", "\n")

    def _insert_inline(self, text: str, base_tag: str):
        """
        Insert text with inline Markdown (bold, italic, inline-code)
        using alternating tag application.
        """
        pattern = re.compile(r"(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)")
        last = 0
        for m in pattern.finditer(text):
            # Plain text before match
            if m.start() > last:
                self.text.insert("end", text[last:m.start()], base_tag)
            full = m.group(0)
            if full.startswith("**"):
                self.text.insert("end", m.group(2), ("bold",))
            elif full.startswith("*"):
                self.text.insert("end", m.group(3), ("italic",))
            elif full.startswith("`"):
                self.text.insert("end", m.group(4), ("inline_code",))
            last = m.end()
        if last < len(text):
            self.text.insert("end", text[last:], base_tag)

    # ------------------------------------------------------------------ search
    def search(self, query: str):
        """Highlight all occurrences of query and jump to the first."""
        self.text.tag_remove("search_hl", "1.0", "end")
        self.text.tag_remove("search_current", "1.0", "end")
        self._search_positions.clear()
        self._search_idx = -1
        if not query:
            return 0

        start = "1.0"
        while True:
            pos = self.text.search(query, start, stopindex="end",
                                   nocase=True)
            if not pos:
                break
            end_pos = f"{pos}+{len(query)}c"
            self.text.tag_add("search_hl", pos, end_pos)
            self._search_positions.append((pos, end_pos))
            start = end_pos

        if self._search_positions:
            self._search_idx = 0
            self._highlight_current()
        return len(self._search_positions)

    def search_next(self):
        if not self._search_positions:
            return
        self._search_idx = (self._search_idx + 1) % len(self._search_positions)
        self._highlight_current()

    def search_prev(self):
        if not self._search_positions:
            return
        self._search_idx = (self._search_idx - 1) % len(self._search_positions)
        self._highlight_current()

    def _highlight_current(self):
        # Remove previous "current" highlight
        self.text.tag_remove("search_current", "1.0", "end")
        pos, end_pos = self._search_positions[self._search_idx]
        self.text.tag_add("search_current", pos, end_pos)
        self.text.see(pos)

    # ------------------------------------------------------------------ zoom
    def zoom_in(self):
        self.zoom = min(self.zoom + 2, 10)
        self._configure_tags()

    def zoom_out(self):
        self.zoom = max(self.zoom - 2, -4)
        self._configure_tags()

    # ------------------------------------------------------------------ theme
    def apply_theme(self, theme: dict):
        self.theme = theme
        self.text.configure(bg=theme["bg"], fg=theme["text"],
                             selectbackground=theme["accent"],
                             insertbackground=theme["text"])
        self._configure_tags()

    # ------------------------------------------------------------------ TOC
    def get_toc(self):
        return self._toc_items

    def jump_to(self, mark: str):
        self.text.see(mark)

    # ------------------------------------------------------------------ stats
    def word_count(self) -> int:
        content = self.text.get("1.0", "end")
        return len(content.split())


# =====================================================================
# TABLE OF CONTENTS PANEL
# =====================================================================
class TOCPanel(tk.Frame):
    def __init__(self, parent, theme: dict, on_jump, **kwargs):
        super().__init__(parent, bg=theme["toc_bg"], **kwargs)
        self.theme = theme
        self.on_jump = on_jump
        self._buttons = []

        header = tk.Label(
            self, text="📋  Contents",
            font=("Segoe UI", 10, "bold"),
            bg=theme["accent"], fg="#FFFFFF",
            pady=6, padx=10, anchor="w",
        )
        header.pack(fill="x")

        self.inner = tk.Frame(self, bg=theme["toc_bg"])
        self.inner.pack(fill="both", expand=True, pady=4)

        self.vsb = ttk.Scrollbar(self.inner, orient="vertical")
        self.canvas = tk.Canvas(
            self.inner, bg=theme["toc_bg"],
            highlightthickness=0, yscrollcommand=self.vsb.set
        )
        self.vsb.configure(command=self.canvas.yview)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.frame = tk.Frame(self.canvas, bg=theme["toc_bg"])
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.frame, anchor="nw"
        )
        self.frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_frame_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def rebuild(self, toc_items: list):
        for w in self.frame.winfo_children():
            w.destroy()
        self._buttons.clear()

        for level, text, mark in toc_items:
            indent = (level - 1) * 14
            prefix = {1: "●", 2: "○", 3: "▸"}.get(level, "–")
            short = text[:36] + "…" if len(text) > 36 else text

            btn = tk.Button(
                self.frame,
                text=f"  {prefix}  {short}",
                font=("Segoe UI", 9 + (1 if level == 1 else 0),
                      "bold" if level == 1 else "normal"),
                fg=self.theme["toc_fg"],
                bg=self.theme["toc_bg"],
                activebackground=self.theme["accent"],
                activeforeground="#FFFFFF",
                relief="flat",
                anchor="w",
                padx=indent + 4,
                pady=3,
                cursor="hand2",
                command=lambda m=mark: self.on_jump(m),
            )
            btn.pack(fill="x")
            self._buttons.append(btn)

    def apply_theme(self, theme: dict):
        self.theme = theme
        self.configure(bg=theme["toc_bg"])
        self.inner.configure(bg=theme["toc_bg"])
        self.canvas.configure(bg=theme["toc_bg"])
        self.frame.configure(bg=theme["toc_bg"])
        for btn in self._buttons:
            btn.configure(bg=theme["toc_bg"], fg=theme["toc_fg"])


# =====================================================================
# MAIN APPLICATION
# =====================================================================
class NotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Notes Generator  ✦  Professional Edition")
        self.root.geometry("1280x860")
        self.root.minsize(900, 600)

        self.current_notes = ""
        self.current_topic = ""
        self._dark_mode = False
        self.history = []
        self._toc_visible = True

        self.theme = THEMES["light"]
        self._build_ui()
        self._refresh_history()

    # ================================================================ BUILD UI
    def _build_ui(self):
        t = self.theme

        # ---------- ttk style ----------
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=6, font=("Segoe UI", 10),
                        background=t["panel"], foreground=t["text"])
        style.configure("Accent.TButton",
                        background=t["accent"], foreground="#FFFFFF",
                        font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton",
                  background=[("active", "#1D4ED8"), ("pressed", "#1E40AF")])
        style.configure("TEntry", fieldbackground=t["entry_bg"],
                        foreground=t["text"])
        style.configure("Vertical.TScrollbar",
                        background=t["panel"], troughcolor=t["bg"])

        # ---------- Root background ----------
        self.root.configure(bg=t["bg"])

        # ---------- HEADER ----------
        self.header = tk.Frame(self.root, bg=t["header_bg"], height=56)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        tk.Label(
            self.header,
            text="  ✦  AI Notes Generator",
            font=("Segoe UI", 16, "bold"),
            bg=t["header_bg"], fg=t["header_fg"],
        ).pack(side="left", padx=16, pady=10)

        # Right-side header controls
        hbtn_frame = tk.Frame(self.header, bg=t["header_bg"])
        hbtn_frame.pack(side="right", padx=12, pady=8)

        self.dark_btn = tk.Button(
            hbtn_frame, text="🌙 Dark",
            font=("Segoe UI", 9), relief="flat",
            bg=t["header_bg"], fg=t["header_fg"],
            activebackground="#1E40AF", activeforeground="#FFFFFF",
            cursor="hand2", command=self._toggle_dark,
        )
        self.dark_btn.pack(side="right", padx=4)

        for lbl, cmd in [("＋", self._zoom_in), ("－", self._zoom_out)]:
            tk.Button(
                hbtn_frame, text=lbl,
                font=("Segoe UI", 11, "bold"), width=2,
                relief="flat", bg=t["header_bg"], fg=t["header_fg"],
                cursor="hand2", command=cmd,
            ).pack(side="right", padx=2)

        tk.Label(hbtn_frame, text="Zoom:", font=("Segoe UI", 9),
                 bg=t["header_bg"], fg=t["header_fg"]).pack(side="right", padx=4)

        # ---------- MAIN PANED LAYOUT ----------
        self.main_pane = tk.PanedWindow(
            self.root, orient="horizontal", bg=t["bg"],
            sashwidth=5, sashrelief="flat",
        )
        self.main_pane.pack(fill="both", expand=True, padx=0, pady=0)

        # ---- LEFT: Input Panel ----
        self._build_input_panel()

        # ---- CENTRE: Viewer (TOC + Notes) ----
        self._build_viewer_panel()

        # ---- RIGHT: History Panel ----
        self._build_history_panel()

        # ---------- STATUS BAR ----------
        self.status_bar = tk.Frame(self.root, bg=t["status_bg"], height=26)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)

        self.status_lbl = tk.Label(
            self.status_bar, text="Ready",
            font=("Segoe UI", 9), bg=t["status_bg"], fg=t["subtext"],
            anchor="w", padx=12,
        )
        self.status_lbl.pack(side="left")

        self.stats_lbl = tk.Label(
            self.status_bar, text="",
            font=("Segoe UI", 9), bg=t["status_bg"], fg=t["subtext"],
            anchor="e", padx=12,
        )
        self.stats_lbl.pack(side="right")

    # ---------------------------------------------------------- input panel
    def _build_input_panel(self):
        t = self.theme
        self.input_frame = tk.Frame(
            self.main_pane, bg=t["panel"],
            relief="flat", bd=0, width=260,
        )
        self.main_pane.add(self.input_frame, minsize=200, width=260)

        inner = tk.Frame(self.input_frame, bg=t["panel"], padx=14, pady=14)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="Topic", font=("Segoe UI", 9, "bold"),
                 bg=t["panel"], fg=t["subtext"]).pack(anchor="w")
        self.topic_entry = tk.Entry(
            inner, font=("Segoe UI", 11),
            bg=t["entry_bg"], fg=t["text"],
            relief="solid", bd=1,
            insertbackground=t["text"],
        )
        self.topic_entry.pack(fill="x", pady=(2, 10), ipady=5)
        self.topic_entry.bind("<Return>", lambda _e: self.on_generate())

        tk.Label(inner, text="Bullet Points (optional)",
                 font=("Segoe UI", 9, "bold"),
                 bg=t["panel"], fg=t["subtext"]).pack(anchor="w")
        self.points_text = tk.Text(
            inner, height=7,
            font=("Segoe UI", 10),
            bg=t["entry_bg"], fg=t["text"],
            relief="solid", bd=1,
            insertbackground=t["text"],
        )
        self.points_text.pack(fill="x", pady=(2, 10))

        # Generate + Clear
        btn_row = tk.Frame(inner, bg=t["panel"])
        btn_row.pack(fill="x", pady=(0, 14))

        self.gen_btn = tk.Button(
            btn_row, text="⚡  Generate Notes",
            font=("Segoe UI", 10, "bold"),
            bg=t["accent"], fg="#FFFFFF",
            activebackground="#1D4ED8", activeforeground="#FFFFFF",
            relief="flat", cursor="hand2", pady=7,
            command=self.on_generate,
        )
        self.gen_btn.pack(fill="x", pady=(0, 4))

        tk.Button(
            btn_row, text="Clear",
            font=("Segoe UI", 9),
            bg=t["panel"], fg=t["subtext"],
            relief="flat", cursor="hand2",
            command=self.on_clear,
        ).pack(fill="x")

        # Divider
        tk.Frame(inner, bg=t["separator"], height=1).pack(fill="x", pady=10)

        # Action buttons
        tk.Label(inner, text="Export & Share",
                 font=("Segoe UI", 9, "bold"),
                 bg=t["panel"], fg=t["subtext"]).pack(anchor="w", pady=(0, 6))

        for text, cmd in [
            ("💾  Save to History", self.on_save),
            ("📋  Copy to Clipboard", self.on_copy),
            ("📄  Export PDF", self.on_export_pdf),
            ("📝  Export TXT", self.on_export_txt),
        ]:
            tk.Button(
                inner, text=text,
                font=("Segoe UI", 9),
                bg=t["panel"], fg=t["text"],
                activebackground=t["accent"], activeforeground="#FFFFFF",
                relief="flat", anchor="w", pady=4, cursor="hand2",
                command=cmd,
            ).pack(fill="x", pady=1)

        # Store ref for theme updates
        self._input_widgets = [inner, self.input_frame]

    # ---------------------------------------------------------- viewer panel
    def _build_viewer_panel(self):
        t = self.theme
        self.viewer_frame = tk.Frame(self.main_pane, bg=t["bg"])
        self.main_pane.add(self.viewer_frame, minsize=400)

        # -- Search bar (top of viewer) --
        self.search_bar = tk.Frame(self.viewer_frame, bg=t["panel"], height=42)
        self.search_bar.pack(fill="x")
        self.search_bar.pack_propagate(False)

        tk.Label(self.search_bar, text="🔍",
                 font=("Segoe UI", 11), bg=t["panel"], fg=t["subtext"]
                 ).pack(side="left", padx=(10, 4), pady=8)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        self.search_entry = tk.Entry(
            self.search_bar, textvariable=self.search_var,
            font=("Segoe UI", 10),
            bg=t["entry_bg"], fg=t["text"],
            relief="solid", bd=1,
            insertbackground=t["text"],
        )
        self.search_entry.pack(side="left", fill="x", expand=True, pady=8)

        self.search_count_lbl = tk.Label(
            self.search_bar, text="",
            font=("Segoe UI", 9), bg=t["panel"], fg=t["subtext"],
        )
        self.search_count_lbl.pack(side="left", padx=6)

        for txt, cmd in [("▲", self._search_prev), ("▼", self._search_next)]:
            tk.Button(
                self.search_bar, text=txt, font=("Segoe UI", 9),
                bg=t["panel"], fg=t["text"], relief="flat",
                cursor="hand2", command=cmd, width=2,
            ).pack(side="left", padx=2)

        tk.Button(
            self.search_bar, text="TOC",
            font=("Segoe UI", 9, "bold"),
            bg=t["panel"], fg=t["accent"],
            relief="flat", cursor="hand2",
            command=self._toggle_toc,
            padx=8,
        ).pack(side="right", padx=8)

        # -- Content area: TOC + viewer --
        self.content_area = tk.Frame(self.viewer_frame, bg=t["bg"])
        self.content_area.pack(fill="both", expand=True)

        # TOC panel (left side of content_area)
        self.toc_panel = TOCPanel(
            self.content_area, t,
            on_jump=self._on_toc_jump,
        )
        self.toc_panel.pack(side="left", fill="y", padx=(0, 0))

        # Thin separator
        self.toc_sep = tk.Frame(self.content_area, bg=t["separator"], width=1)
        self.toc_sep.pack(side="left", fill="y")

        # Markdown viewer
        self.md_viewer = MarkdownViewer(self.content_area, t)
        self.md_viewer.pack(side="left", fill="both", expand=True)

    # ---------------------------------------------------------- history panel
    def _build_history_panel(self):
        t = self.theme
        self.history_frame = tk.Frame(
            self.main_pane, bg=t["panel"],
            relief="flat", bd=0, width=240,
        )
        self.main_pane.add(self.history_frame, minsize=180, width=240)

        inner = tk.Frame(self.history_frame, bg=t["panel"], padx=10, pady=10)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="📚  History",
                 font=("Segoe UI", 11, "bold"),
                 bg=t["panel"], fg=t["accent"]).pack(anchor="w", pady=(0, 6))

        # History search
        self.hist_search_var = tk.StringVar()
        self.hist_search_var.trace_add("write", self._on_hist_search_change)
        hist_search = tk.Entry(
            inner, textvariable=self.hist_search_var,
            font=("Segoe UI", 9),
            bg=t["entry_bg"], fg=t["text"],
            relief="solid", bd=1,
            insertbackground=t["text"],
        )
        hist_search.insert(0, "Search history…")
        hist_search.bind("<FocusIn>",
                         lambda e: hist_search.delete(0, "end")
                         if hist_search.get() == "Search history…" else None)
        hist_search.pack(fill="x", pady=(0, 6), ipady=4)

        # Listbox with scrollbar
        list_frame = tk.Frame(inner, bg=t["panel"])
        list_frame.pack(fill="both", expand=True)

        self.history_list = tk.Listbox(
            list_frame,
            font=("Segoe UI", 9),
            bg=t["listbox_bg"], fg=t["text"],
            selectbackground=t["accent"],
            selectforeground="#FFFFFF",
            activestyle="none",
            relief="flat", bd=0,
            highlightthickness=0,
        )
        hist_vsb = ttk.Scrollbar(list_frame, orient="vertical",
                                  command=self.history_list.yview)
        self.history_list.configure(yscrollcommand=hist_vsb.set)
        hist_vsb.pack(side="right", fill="y")
        self.history_list.pack(side="left", fill="both", expand=True)
        self.history_list.bind("<<ListboxSelect>>", self.on_history_select)

        # History action buttons
        hbtn = tk.Frame(inner, bg=t["panel"])
        hbtn.pack(fill="x", pady=(8, 0))

        for txt, cmd in [
            ("📌 Pin", self.on_pin),
            ("🗑 Delete", self.on_delete),
            ("↺ Refresh", self._refresh_history),
        ]:
            tk.Button(
                hbtn, text=txt,
                font=("Segoe UI", 8),
                bg=t["panel"], fg=t["text"],
                relief="flat", cursor="hand2",
                activebackground=t["accent"], activeforeground="#FFFFFF",
                pady=3, command=cmd,
            ).pack(fill="x", pady=1)

    # ================================================================ ACTIONS

    def on_generate(self):
        topic = self.topic_entry.get().strip()
        points = self.points_text.get("1.0", tk.END).strip()
        if not topic:
            messagebox.showwarning("Missing Topic", "Please enter a topic first.")
            return

        self._set_status("⚡  Generating notes — please wait…")
        self.gen_btn.configure(state="disabled", text="Generating…")
        self.md_viewer.text.configure(state="normal")
        self.md_viewer.text.delete("1.0", "end")
        self.md_viewer.text.insert("end", "\n\n  ⏳  Generating detailed notes…\n",
                                   "h3")
        self.md_viewer.text.configure(state="disabled")

        def work():
            try:
                notes = generate_notes(topic, points)
                self.root.after(0, lambda: self._on_generate_done(topic, notes))
            except Exception as e:
                self.root.after(0, lambda: self._on_generate_error(str(e)))

        threading.Thread(target=work, daemon=True).start()

    def _on_generate_done(self, topic: str, notes: str):
        self.current_topic = topic
        self.current_notes = notes
        self.md_viewer.render(notes)
        self.toc_panel.rebuild(self.md_viewer.get_toc())
        wc = self.md_viewer.word_count()
        rt = max(1, wc // 200)
        self.stats_lbl.configure(
            text=f"  {wc:,} words  •  ~{rt} min read"
        )
        self._set_status("✓  Notes generated successfully")
        self.gen_btn.configure(state="normal", text="⚡  Generate Notes")

    def _on_generate_error(self, err: str):
        self.md_viewer.text.configure(state="normal")
        self.md_viewer.text.delete("1.0", "end")
        self.md_viewer.text.insert("end", f"\n\n  ❌  Error: {err}\n", "warning")
        self.md_viewer.text.configure(state="disabled")
        self._set_status("Error generating notes")
        self.gen_btn.configure(state="normal", text="⚡  Generate Notes")
        messagebox.showerror("Generation Error", err)

    def on_clear(self):
        self.topic_entry.delete(0, tk.END)
        self.points_text.delete("1.0", tk.END)
        self.md_viewer.text.configure(state="normal")
        self.md_viewer.text.delete("1.0", "end")
        self.md_viewer.text.configure(state="disabled")
        self.toc_panel.rebuild([])
        self.current_notes = ""
        self.current_topic = ""
        self.stats_lbl.configure(text="")
        self._set_status("Cleared")

    def on_save(self):
        if not self.current_notes:
            messagebox.showinfo("Nothing to Save", "Generate notes first.")
            return
        add_note(self.current_topic,
                 self.points_text.get("1.0", tk.END).strip(),
                 self.current_notes)
        self._refresh_history()
        self._set_status("✓  Saved to history")

    def on_copy(self):
        if not self.current_notes:
            messagebox.showinfo("Nothing to Copy", "Generate notes first.")
            return
        pyperclip.copy(self.current_notes)
        self._set_status("✓  Copied to clipboard")

    def on_export_pdf(self):
        if not self.current_notes:
            messagebox.showinfo("Nothing to Export", "Generate notes first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"{self.current_topic[:40] or 'notes'}.pdf",
        )
        if not path:
            return
        try:
            export_to_pdf(self.current_topic or "Notes",
                          self.current_notes, path)
            self._set_status(f"✓  PDF saved: {path}")
            messagebox.showinfo("Exported", f"PDF saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def on_export_txt(self):
        if not self.current_notes:
            messagebox.showinfo("Nothing to Export", "Generate notes first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"{self.current_topic[:40] or 'notes'}.txt",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.current_notes)
            self._set_status(f"✓  TXT saved: {path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    def on_history_select(self, _evt):
        sel = self.history_list.curselection()
        if not sel:
            return
        note = self._filtered_history[sel[0]]
        self.topic_entry.delete(0, tk.END)
        self.topic_entry.insert(0, note["topic"])
        self.points_text.delete("1.0", tk.END)
        self.points_text.insert(tk.END, note.get("points", ""))
        self.current_topic = note["topic"]
        self.current_notes = note["notes"]
        self.md_viewer.render(note["notes"])
        self.toc_panel.rebuild(self.md_viewer.get_toc())
        wc = self.md_viewer.word_count()
        rt = max(1, wc // 200)
        self.stats_lbl.configure(text=f"  {wc:,} words  •  ~{rt} min read")
        self._set_status(f"Loaded: {note['topic']}")

    def on_pin(self):
        sel = self.history_list.curselection()
        if not sel:
            messagebox.showinfo("Select a Note", "Pick a note from history first.")
            return
        note = self._filtered_history[sel[0]]
        toggle_pin(note["id"])
        self._refresh_history()
        self._set_status("📌 Pin toggled")

    def on_delete(self):
        sel = self.history_list.curselection()
        if not sel:
            messagebox.showinfo("Select a Note", "Pick a note from history first.")
            return
        note = self._filtered_history[sel[0]]
        if messagebox.askyesno("Delete Note",
                                f"Delete '{note['topic']}'?"):
            delete_note(note["id"])
            self._refresh_history()
            self._set_status("Deleted")

    # ================================================================ HISTORY
    def _refresh_history(self):
        self.history = load_history()
        # Pinned first, then by date
        self.history.sort(key=lambda n: (not n.get("pinned", False),
                                         n.get("created_at", "")),
                          reverse=False)
        self.history.sort(key=lambda n: not n.get("pinned", False))
        self._apply_hist_filter()

    def _on_hist_search_change(self, *_):
        self._apply_hist_filter()

    def _apply_hist_filter(self):
        q = self.hist_search_var.get().lower().strip()
        if q in ("", "search history…"):
            self._filtered_history = self.history
        else:
            self._filtered_history = [
                n for n in self.history
                if q in n["topic"].lower()
            ]

        self.history_list.delete(0, tk.END)
        for n in self._filtered_history:
            pin = "📌 " if n.get("pinned") else "    "
            date = n.get("created_at", "")[:10]
            label = f"{pin}{n['topic'][:28]}  ({date})"
            self.history_list.insert(tk.END, label)

    # ================================================================ SEARCH
    def _on_search_change(self, *_):
        query = self.search_var.get()
        count = self.md_viewer.search(query)
        if query:
            self.search_count_lbl.configure(
                text=f"{count} match{'es' if count != 1 else ''}"
            )
        else:
            self.search_count_lbl.configure(text="")

    def _search_next(self):
        self.md_viewer.search_next()

    def _search_prev(self):
        self.md_viewer.search_prev()

    # ================================================================ TOC
    def _on_toc_jump(self, mark: str):
        self.md_viewer.jump_to(mark)

    def _toggle_toc(self):
        if self._toc_visible:
            self.toc_panel.pack_forget()
            self.toc_sep.pack_forget()
        else:
            self.toc_panel.pack(side="left", fill="y", before=self.toc_sep)
            self.toc_sep.pack(side="left", fill="y", before=self.md_viewer)
        self._toc_visible = not self._toc_visible

    # ================================================================ ZOOM
    def _zoom_in(self):
        self.md_viewer.zoom_in()

    def _zoom_out(self):
        self.md_viewer.zoom_out()

    # ================================================================ DARK MODE
    def _toggle_dark(self):
        self._dark_mode = not self._dark_mode
        self.theme = THEMES["dark" if self._dark_mode else "light"]
        t = self.theme

        self.dark_btn.configure(
            text="☀️ Light" if self._dark_mode else "🌙 Dark"
        )

        # Root + header
        self.root.configure(bg=t["bg"])
        self.header.configure(bg=t["header_bg"])
        for w in self.header.winfo_children():
            if isinstance(w, (tk.Label, tk.Button)):
                try:
                    w.configure(bg=t["header_bg"], fg=t["header_fg"])
                except Exception:
                    pass

        # Input panel
        self.input_frame.configure(bg=t["panel"])
        self._retheme_widget(self.input_frame, t)

        # Viewer
        self.viewer_frame.configure(bg=t["bg"])
        self.content_area.configure(bg=t["bg"])
        self.search_bar.configure(bg=t["panel"])
        self._retheme_widget(self.search_bar, t)
        self.toc_sep.configure(bg=t["separator"])

        self.md_viewer.apply_theme(t)
        self.toc_panel.apply_theme(t)

        # History panel
        self.history_frame.configure(bg=t["panel"])
        self._retheme_widget(self.history_frame, t)
        self.history_list.configure(
            bg=t["listbox_bg"], fg=t["text"],
            selectbackground=t["accent"],
        )

        # Status bar
        self.status_bar.configure(bg=t["status_bg"])
        self.status_lbl.configure(bg=t["status_bg"], fg=t["subtext"])
        self.stats_lbl.configure(bg=t["status_bg"], fg=t["subtext"])

        self.main_pane.configure(bg=t["bg"])

    def _retheme_widget(self, parent, t):
        """Recursively re-colour child widgets."""
        for w in parent.winfo_children():
            cls = w.__class__.__name__
            try:
                if cls in ("Frame",):
                    # Decide panel vs bg
                    w.configure(bg=t["panel"])
                elif cls == "Label":
                    w.configure(bg=t["panel"], fg=t["text"])
                elif cls == "Button":
                    w.configure(bg=t["panel"], fg=t["text"])
                elif cls == "Entry":
                    w.configure(bg=t["entry_bg"], fg=t["text"],
                                insertbackground=t["text"])
                elif cls == "Text":
                    w.configure(bg=t["entry_bg"], fg=t["text"],
                                insertbackground=t["text"])
            except Exception:
                pass
            self._retheme_widget(w, t)

    # ================================================================ STATUS
    def _set_status(self, msg: str):
        self.status_lbl.configure(text=f"  {msg}")


# =====================================================================
# ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    root = tk.Tk()
    NotesApp(root)
    root.mainloop()