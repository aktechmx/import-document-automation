# Import Document Automation

Python application created to automate part of a temporary import documentation process.

The project started from a real task where information had to be reviewed and transferred manually between different documents. The goal was to reduce repetitive work, avoid transcription errors, and make the process easier for the person responsible for preparing the documentation.

The application reads information from PDF files, processes the extracted data, performs the required calculations, and generates a Word document with the information organized in the required format.

## Why I Built This

The original process required reviewing different PDF documents and manually identifying information such as certificate numbers, shipment information, material details, weights, prices, and chemical composition.

After collecting the information, some values also had to be converted or calculated before preparing the final document.

Since most of these steps followed the same process every time, I saw an opportunity to automate them with Python.

Instead of manually searching and copying the information, the user can select the required PDF files and let the application process the documents.

## How It Works

The basic workflow is:

```text
Invoice PDF
     +
Certificate PDF
     |
     v
PDF Data Extraction
     |
     v
Data Processing
     |
     +--> Weight conversions
     +--> Price calculations
     +--> HEAT identification
     +--> Chemical composition
     |
     v
Structured Data
     |
     v
Word Document Generation
```

The application includes a simple graphical interface where the user selects:

1. The invoice PDF.
2. The certificate PDF.
3. The folder where the generated document will be saved.

The application then extracts and processes the information automatically.

## Main Features

- PDF data extraction using `pdfplumber`
- Table processing with `pandas`
- Pattern detection using regular expressions
- Automatic extraction of shipment and certificate information
- Material and diameter identification
- HEAT number identification
- Chemical composition extraction
- Weight conversion from pounds to kilograms
- Unit price conversion
- Total value calculation
- Automatic Word document generation
- Simple desktop interface using Tkinter
- Manual input fallback when some information cannot be detected automatically

## Technologies Used

- Python
- pdfplumber
- pandas
- Regular Expressions (Regex)
- Tkinter
- python-docx

## Project Structure

```text
import-document-automation/
│
├── interface.py
├── pdf_extractor.py
├── create_document.py
├── requirements.txt
├── app.ico
├── logo.png
├── .gitignore
└── README.md
```

### `interface.py`

Contains the Tkinter graphical interface and controls the main application workflow.

### `pdf_extractor.py`

Reads the PDF documents, extracts the required information, processes tables, identifies patterns, and prepares the data used by the document generator.

### `create_document.py`

Receives the processed information and generates the final Word document.

## Installation

Clone the repository:

```bash
git clone https://github.com/aktechmx/import-document-automation.git
```

Move into the project directory:

```bash
cd import-document-automation
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the application with:

```bash
python interface.py
```

Select the two PDF documents required by the process and choose the destination folder.

The application will extract the available information, process the data, and generate the Word document automatically.

If some required information cannot be detected from the documents, the application can request the value manually instead of stopping the entire process.

## Data Privacy

This project was originally developed to solve a real business process.

For this public version, company names, supplier information, addresses, original documents, and other sensitive information have been removed or replaced.

The repository does not contain the original invoices, certificates, or business documents used during development.

## Current Status

The current version represents the original working implementation after removing sensitive business information.

I am keeping this version as the baseline of the project before continuing with code refactoring, better separation of responsibilities, validation, and additional improvements.

## What I Learned

This project helped me combine different areas that I had been learning and using separately.

Instead of only extracting information from a PDF, I had to think about the complete workflow: reading documents, handling different table structures, validating missing information, performing calculations, organizing the extracted data, and finally generating a document that could actually be used.

It was also a good example of how a relatively small Python application can remove repetitive manual work from a real process.