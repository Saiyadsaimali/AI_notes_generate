# AI Notes Generator

## Overview

AI Notes Generator is a desktop application developed using Python and Tkinter that leverages the Groq AI API to generate comprehensive, well-structured, and professional study notes on any topic. The application provides an intuitive interface for generating, viewing, managing, and exporting AI-generated notes, making it a valuable tool for students, educators, and self-learners.

---

## Features

* Generate detailed AI-powered study notes on any topic
* Support for optional bullet points to customize note generation
* Professional Markdown rendering with formatted headings, tables, code blocks, and lists
* Built-in Table of Contents for easy navigation
* Search functionality within generated notes
* Light and Dark mode support
* Zoom in and Zoom out for better readability
* Save generated notes to local history
* Pin important notes for quick access
* Search and manage saved notes
* Export notes as PDF with professional formatting
* Export notes as TXT files
* Copy notes directly to the clipboard
* Word count and estimated reading time
* Responsive and user-friendly desktop interface

---

## Technologies Used

* Python 3
* Tkinter
* Groq API (Llama 3.3 70B Versatile)
* ReportLab
* JSON
* Pyperclip
* Threading
* Regular Expressions (re)
* OS Module

---

## Project Structure

```text
AI-Notes-Generator/
│
├── main.py
├── notes_history.json
├── README.md
├── requirements.txt
└── screenshots/
```

---

## Installation

### Clone the Repository

```bash
git clone https://github.com/your-username/AI-Notes-Generator.git
```

### Navigate to the Project Folder

```bash
cd AI-Notes-Generator
```

### Install Required Packages

```bash
pip install -r requirements.txt
```

### Set Your Groq API Key

```bash
GROQ_API_KEY=your_api_key
```

Or replace the API key in the project configuration.

### Run the Application

```bash
python main.py
```

---

## How to Use

1. Enter a topic in the Topic field.
2. Optionally add bullet points to guide the AI.
3. Click **Generate Notes**.
4. Review the generated notes using the built-in Markdown viewer.
5. Search within the notes if needed.
6. Save notes to history.
7. Export notes as PDF or TXT.
8. Copy notes to the clipboard for quick sharing.

---

## Key Functionalities

* AI-powered note generation
* Interactive Markdown viewer
* History management
* PDF export with professional formatting
* Local JSON storage
* Search and navigation
* Theme switching
* Reading statistics

---

## Future Improvements

* Multiple AI model support
* User authentication
* Cloud synchronization
* Note editing before export
* Multiple export formats (DOCX, HTML)
* Image generation inside notes
* Voice input support
* Multi-language note generation

---

## Learning Outcomes

This project demonstrates practical knowledge of:

* Python GUI development with Tkinter
* AI API integration
* Prompt engineering
* Markdown rendering
* PDF generation
* File handling with JSON
* Multithreading
* Desktop application development
* Data management and export functionality



