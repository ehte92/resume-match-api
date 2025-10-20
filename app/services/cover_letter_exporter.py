"""
Cover letter export service for generating PDF, DOCX, and TXT files.
Provides professional formatting for different export formats.
"""

import io
import logging
from datetime import datetime
from typing import Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.models.cover_letter import CoverLetter

logger = logging.getLogger(__name__)


class CoverLetterExporter:
    """Export cover letters to various formats with professional styling."""

    @staticmethod
    def export_to_txt(cover_letter: CoverLetter) -> bytes:
        """
        Export cover letter as plain text file.

        Args:
            cover_letter: CoverLetter model instance

        Returns:
            UTF-8 encoded text bytes
        """
        # Build header with job details
        header_lines = []
        if cover_letter.job_title:
            header_lines.append(f"Position: {cover_letter.job_title}")
        if cover_letter.company_name:
            header_lines.append(f"Company: {cover_letter.company_name}")
        header_lines.append(f"Generated: {cover_letter.created_at.strftime('%B %d, %Y')}")
        header_lines.append("")  # Empty line

        # Assemble full content
        content = "\n".join(header_lines) + "\n" + cover_letter.cover_letter_text

        return content.encode("utf-8")

    @staticmethod
    def export_to_pdf(
        cover_letter: CoverLetter, include_metadata: bool = False
    ) -> bytes:
        """
        Export cover letter as professionally formatted PDF.

        Args:
            cover_letter: CoverLetter model instance
            include_metadata: Whether to include generation metadata in footer

        Returns:
            PDF file as bytes
        """
        buffer = io.BytesIO()

        # Create PDF with standard letter size and margins
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        # Build story (content elements)
        story = []
        styles = getSampleStyleSheet()

        # Create custom styles
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        )

        subheading_style = ParagraphStyle(
            "CustomSubheading",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.grey,
            spaceAfter=12,
            fontName="Helvetica",
        )

        body_style = ParagraphStyle(
            "CustomBody",
            parent=styles["Normal"],
            fontSize=11,
            leading=16,
            textColor=colors.black,
            fontName="Helvetica",
            alignment=WD_ALIGN_PARAGRAPH.LEFT,
        )

        # Add header with job details
        if cover_letter.job_title:
            story.append(Paragraph(cover_letter.job_title, heading_style))
        if cover_letter.company_name:
            story.append(Paragraph(cover_letter.company_name, subheading_style))
        else:
            story.append(Spacer(1, 12))

        story.append(Spacer(1, 0.2 * inch))

        # Add cover letter text with paragraph breaks
        paragraphs = cover_letter.cover_letter_text.split("\n\n")
        for para_text in paragraphs:
            if para_text.strip():
                # Escape HTML special characters and replace line breaks
                safe_text = para_text.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                safe_text = safe_text.replace("\n", "<br/>")
                para = Paragraph(safe_text, body_style)
                story.append(para)
                story.append(Spacer(1, 12))

        # Add metadata footer if requested
        if include_metadata:
            story.append(Spacer(1, 0.3 * inch))
            metadata_style = ParagraphStyle(
                "Metadata",
                parent=styles["Normal"],
                fontSize=8,
                textColor=colors.grey,
                fontName="Helvetica-Oblique",
            )
            metadata_text = (
                f"Generated on {cover_letter.created_at.strftime('%B %d, %Y')} | "
                f"Tone: {cover_letter.tone.capitalize()} | "
                f"Length: {cover_letter.length.capitalize()} | "
                f"Words: {cover_letter.word_count}"
            )
            story.append(Paragraph(metadata_text, metadata_style))

        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"Generated PDF export for cover letter {cover_letter.id}")
        return pdf_bytes

    @staticmethod
    def export_to_docx(cover_letter: CoverLetter) -> bytes:
        """
        Export cover letter as Microsoft Word document (.docx).

        Args:
            cover_letter: CoverLetter model instance

        Returns:
            DOCX file as bytes
        """
        doc = Document()

        # Set document margins (1 inch all sides)
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

        # Add header with job details
        if cover_letter.job_title:
            heading = doc.add_heading(cover_letter.job_title, level=1)
            heading.alignment = WD_ALIGN_PARAGRAPH.LEFT

        if cover_letter.company_name:
            company_para = doc.add_paragraph(cover_letter.company_name)
            company_para.runs[0].font.size = Pt(11)
            company_para.runs[0].font.color.rgb = None  # Default color

        # Add spacing
        doc.add_paragraph()

        # Add cover letter text with paragraph breaks
        paragraphs = cover_letter.cover_letter_text.split("\n\n")
        for para_text in paragraphs:
            if para_text.strip():
                para = doc.add_paragraph(para_text.strip())
                # Set font and spacing
                for run in para.runs:
                    run.font.name = "Calibri"
                    run.font.size = Pt(11)
                para.paragraph_format.line_spacing = 1.15
                para.paragraph_format.space_after = Pt(10)

        # Save to bytes
        buffer = io.BytesIO()
        doc.save(buffer)
        docx_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"Generated DOCX export for cover letter {cover_letter.id}")
        return docx_bytes

    @staticmethod
    def get_filename(
        cover_letter: CoverLetter, export_format: str
    ) -> str:
        """
        Generate appropriate filename for exported cover letter.

        Args:
            cover_letter: CoverLetter model instance
            export_format: File format (pdf, docx, txt)

        Returns:
            Filename string (e.g., "Google-Software-Engineer-cover-letter.pdf")
        """
        parts = []

        # Add company name
        if cover_letter.company_name:
            # Remove non-ASCII characters for HTTP header compatibility
            safe_company = ''.join(c if ord(c) < 128 else '' for c in cover_letter.company_name)
            safe_company = safe_company.strip().replace(" ", "-")
            if safe_company:  # Only add if there's something left after sanitization
                parts.append(safe_company)

        # Add job title
        if cover_letter.job_title:
            # Remove non-ASCII characters for HTTP header compatibility
            safe_title = ''.join(c if ord(c) < 128 else '' for c in cover_letter.job_title)
            safe_title = safe_title.strip().replace(" ", "-")
            if safe_title:  # Only add if there's something left after sanitization
                parts.append(safe_title)

        # Default if no details provided
        if not parts:
            parts.append("cover-letter")

        # Add format extension
        filename = "-".join(parts) + f".{export_format}"

        # Clean filename (remove invalid characters)
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, "-")

        logger.info(f"Generated filename: {filename}")
        return filename
