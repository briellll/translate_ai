"""Gera um PDF de teste em inglês com formatação variada para testar a tradução."""
import os
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image,
)
from reportlab.lib import colors
from PIL import Image as PILImage, ImageDraw


def create_chart_png() -> str:
    path = os.path.join(tempfile.gettempdir(), "test_chart.png")
    img = PILImage.new("RGB", (400, 200), "#f0f0f0")
    draw = ImageDraw.Draw(img)
    bars = [(40, 80), (100, 120), (160, 60), (220, 150), (280, 90)]
    colors_list = ["#22c55e", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"]
    for i, (x, h) in enumerate(bars):
        for y in range(200 - int(h), 200):
            draw.point((x, y), fill=colors_list[i])
        draw.text((x + 10, 190), f"Q{i+1}", fill="black")
    img.save(path)
    return path


def generate_test_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=60,
        bottomMargin=60,
        leftMargin=50,
        rightMargin=50,
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontSize=26, leading=32, spaceAfter=20,
        textColor=HexColor("#1a365d"),
    )
    
    heading1 = ParagraphStyle(
        "CustomH1", parent=styles["Heading1"],
        fontSize=18, leading=24, spaceBefore=16, spaceAfter=8,
        textColor=HexColor("#2d3748"),
    )
    
    heading2 = ParagraphStyle(
        "CustomH2", parent=styles["Heading2"],
        fontSize=14, leading=20, spaceBefore=12, spaceAfter=6,
        textColor=HexColor("#4a5568"),
    )
    
    code_style = ParagraphStyle(
        "CustomCode", parent=styles["Code"],
        fontSize=9, fontName="Courier", leading=14,
        leftIndent=12, backColor=HexColor("#edf2f7"),
        spaceAfter=8,
    )

    story = []

    # --- Page 1 ---
    story.append(Spacer(1, 30))
    story.append(Paragraph("Sample Technical Document", title_style))
    story.append(Paragraph(
        "<i>A demonstration PDF for testing the translation tool</i>",
        ParagraphStyle("Subtitle", fontSize=12, leading=16, textColor=HexColor("#718096"),
                       spaceAfter=20))
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Introduction", heading1))
    story.append(Paragraph(
        "This document is a sample PDF created specifically to test the <b>formatting preservation</b> "
        "features of the Tradutor AI tool. It contains <i>various</i> text styles, code snippets, "
        "headings, and even a chart image to verify that both text and images are properly handled "
        "during the translation process.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("2. Technical Overview", heading1))
    story.append(Paragraph("2.1 System Architecture", heading2))
    story.append(Paragraph(
        "The system is built using a <b>microservices architecture</b> with the following components: "
        "<i>API Gateway</i>, <i>Translation Engine</i>, and <i>Storage Service</i>. "
        "Each component can be scaled independently based on demand.",
        styles["Normal"]
    ))

    story.append(Paragraph("2.2 Configuration Example", heading2))
    story.append(Paragraph(
        "Below is a sample configuration file in <b>YAML</b> format:",
        styles["Normal"]
    ))
    story.append(Spacer(1, 4))

    code_text = """<font face='Courier' size='9'>server:
  host: "0.0.0.0"
  port: 8080
  debug: <b>false</b>

database:
  url: "postgresql://localhost:5432/app"
  pool_size: <i>10</i>

logging:
  level: "INFO"
  format: "json"</font>"""
    story.append(Paragraph(code_text, code_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("3. Performance Metrics", heading1))
    story.append(Paragraph(
        "The chart below shows the <b>quarterly performance</b> metrics for the fiscal year 2024. "
        "As you can see, <i>Q4</i> had the highest growth rate at 150%.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 8))

    chart_path = create_chart_png()
    story.append(Image(chart_path, width=300, height=150))

    story.append(PageBreak())

    # --- Page 2 ---
    story.append(Paragraph("4. Code Implementation", heading1))
    story.append(Paragraph("4.1 Main Function", heading2))
    story.append(Paragraph(
        "The core translation function is implemented in <b>Python</b> using the <i>OpenAI API</i>. "
        "Here is the main processing loop:",
        styles["Normal"]
    ))
    story.append(Spacer(1, 6))

    python_code = """<font face='Courier' size='9'><b>def</b> translate_document(
    input_path: str,
    output_format: str = <i>"pdf"</i>
) -> str:
    <i># Extract text from source</i>
    content = extract_text(input_path)
    
    <b>if not</b> content:
        <b>raise</b> ValueError(<i>"Empty document"</i>)
    
    <i># Split into chunks</i>
    chunks = chunk_text(content)
    
    <i># Translate each chunk</i>
    translated = []
    <b>for</b> chunk <b>in</b> chunks:
        result = translate(chunk)
        translated.append(result)
    
    <b>return</b> export(translated, output_format)</font>"""
    story.append(Paragraph(python_code, code_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("4.2 Error Handling", heading2))
    story.append(Paragraph(
        "The system implements <b>exponential backoff</b> retry logic for <i>transient failures</i>. "
        "Up to <b>3 retries</b> are attempted with increasing delays of 2, 4, and 8 seconds.",
        styles["Normal"]
    ))

    story.append(Spacer(1, 8))
    story.append(Paragraph("5. Data Comparison", heading1))
    story.append(Paragraph(
        "The table below compares <b>different translation engines</b> across key metrics:",
        styles["Normal"]
    ))
    story.append(Spacer(1, 6))

    table_data = [
        ["Engine", "Speed", "Accuracy", "Cost"],
        ["OpenAI GPT-4", "Fast", "95%", "$$$"],
        ["DeepSeek", "Medium", "88%", "$$"],
        ["Groq", "Very Fast", "82%", "$"],
        ["Together AI", "Fast", "85%", "$$"],
    ]
    table = Table(table_data, colWidths=[100, 80, 80, 60])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2d3748")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cbd5e0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#ffffff"), HexColor("#f7fafc")]),
    ]))
    story.append(table)

    story.append(PageBreak())

    # --- Page 3 ---
    story.append(Paragraph("6. Conclusion", heading1))
    story.append(Paragraph(
        "This sample document demonstrates various <b>formatting features</b> that should be "
        "preserved during translation: <i>italic text</i>, <b>bold text</b>, "
        "<font face='Courier' size='10'>code blocks</font>, "
        "headings at multiple levels, tables with data, and embedded images.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "The translation tool should also <b>remove repeated headers and footers</b> automatically, "
        "keeping only the meaningful content for translation.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<i>End of sample document. Happy testing!</i>",
        ParagraphStyle("ItalicEnd", fontSize=11, leading=15,
                       textColor=HexColor("#718096"), alignment=1)
    ))

    # Build with header/footer
    def add_header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(HexColor("#a0aec0"))
        canvas.drawString(50, A4[1] - 30, "Sample Technical Document")
        canvas.drawRightString(A4[0] - 50, A4[1] - 30, "CONFIDENTIAL")
        canvas.setStrokeColor(HexColor("#e2e8f0"))
        canvas.line(50, A4[1] - 35, A4[0] - 50, A4[1] - 35)
        canvas.line(50, 45, A4[0] - 50, 45)
        canvas.drawCentredString(A4[0] / 2, 30, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    print(f"PDF gerado: {output_path}")
    print(f"Tamanho: {os.path.getsize(output_path) / 1024:.1f} KB")


if __name__ == "__main__":
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    output = os.path.join(downloads, "sample_technical_document.pdf")
    generate_test_pdf(output)
