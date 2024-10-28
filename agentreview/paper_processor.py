"""
Read papers from a PDF file and extract the title, abstract, figures and tables captions, and main content. These
functions work best with ICLR / NeurIPS papers.

"""

from io import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage


def extract_text_from_pdf(path: str) -> str:
    """Extracts text from a PDF file.

    Args:
        path (str): A string specifying the path to the PDF file.

    Returns:
        A string containing the extracted text from the PDF.
    """

    with open(path, 'rb') as file_handle:
        # Initialize a PDF resource manager to store shared resources.
        resource_manager = PDFResourceManager()

        # Set up a StringIO instance to capture the extracted text.
        text_output = StringIO()

        # Create a TextConverter to convert PDF pages to text.
        converter = TextConverter(resource_manager, text_output, laparams=LAParams())

        # Initialize a PDF page interpreter.
        interpreter = PDFPageInterpreter(resource_manager, converter)

        # Process each page in the PDF.
        for page in PDFPage.get_pages(file_handle, caching=True, check_extractable=True):
            interpreter.process_page(page)

        # Retrieve the extracted text and close the StringIO instance.
        extracted_text = text_output.getvalue()
        text_output.close()

        # Finalize the converter.
        converter.close()

    # Replace form feed characters with newlines.
    extracted_text = extracted_text.replace('\x0c', '\n')

    return extracted_text


def convert_text_into_dict(text: str) -> dict:
    """Converts the extracted text into a dictionary.

    Args:
        text (str): the extracted text from the PDF.

    Returns:
        A json object containing the extracted fields from the paper.

    """

    lines = text.split('\n')

    # Create a filtered list to store non-matching lines
    filtered_lines = [line for line in lines if not (line.startswith('Under review') or
                                                     line.startswith('Published as') or
                                                     line.startswith('Paper under double-blind review'))]

    # Remove the first few empty lines before the title
    while filtered_lines[0].strip() == "":
        filtered_lines.pop(0)

    # Get title
    title = ""
    while filtered_lines[0] != "":
        title += filtered_lines.pop(0) + ' '

    title = title.strip().capitalize()

    # Remove the author information between the title and the abstract
    while filtered_lines[0].lower() != "abstract":
        filtered_lines.pop(0)
    filtered_lines.pop(0)

    # Get abstract
    abstract = ""
    while filtered_lines[0].lower() != "introduction":
        abstract += filtered_lines.pop(0) + ' '

    main_content = ""

    figures_captions = []
    tables_captions = []

    while filtered_lines != [] and not filtered_lines[0].lower().startswith("references"):
        figure_caption = ""
        table_caption = ""

        if filtered_lines[0].lower().startswith("figure"):
            while not filtered_lines[0] == "":
                figure_caption += filtered_lines.pop(0) + ' '


        elif filtered_lines[0].lower().startswith("Table"):
            while not filtered_lines[0] == "":
                table_caption += filtered_lines.pop(0) + ' '

        else:
            main_content += filtered_lines.pop(0) + ' '

        if figure_caption != "":
            figures_captions.append(figure_caption)

        if table_caption != "":
            tables_captions.append(table_caption)


    figures_captions = "\n".join(figures_captions) + "\n" + "\n".join(tables_captions)

    # Get the first section title in the Appendix
    # Example section title: "A ENVIRONMENT DETAILS"
    while filtered_lines != [] and not (filtered_lines[0].isupper() and filtered_lines[0][0] == "A"):
        filtered_lines.pop(0)


    appendix = ""

    while filtered_lines != []:
        appendix += filtered_lines.pop(0) + ' '

    # Now we have reached the "References" section
    # Skip until we reach


    paper = {
        "Title": title.strip(),
        "Abstract": abstract.strip(),
        "Figures/Tables Captions": figures_captions.strip(),
        "Main Content": main_content.strip(),
        "Appendix": appendix.strip(),
    }

    return paper


if __name__ == "__main__":
    from agentreview.utility.authentication_utils import read_and_set_openai_key
    from agentreview.review import get_lm_review

    read_and_set_openai_key()

    path = "data/rejected/6359.pdf"
    text = extract_text_from_pdf(path)

    parsed_paper = convert_text_into_dict(text)

    review_generated = get_lm_review(parsed_paper)

    print(review_generated["review_generated"])
