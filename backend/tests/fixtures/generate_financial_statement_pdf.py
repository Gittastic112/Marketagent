from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


OUTPUT = Path(__file__).with_name("financial_statement_table.pdf")


def main() -> None:
    pdf = canvas.Canvas(str(OUTPUT), pagesize=letter)
    pdf.setTitle("Financial Statement Table Fixture")
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(72, 740, "Consolidated Financial Statements")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(72, 720, "Amounts in INR million")

    x_positions = [72, 300, 410, 520]
    top = 690
    row_height = 28
    rows = [
        ["Metric", "FY2025", "FY2026"],
        ["Revenue", "1,000", "1,250"],
        ["Operating income", "180", "240"],
        ["Net income", "120", "165"],
        ["Cash and cash equivalents", "300", "380"],
        ["Total debt", "500", "460"],
        ["Diluted shares", "100", "102"],
    ]

    for row_index in range(len(rows) + 1):
        y = top - row_index * row_height
        pdf.line(x_positions[0], y, x_positions[-1], y)
    for x in x_positions:
        pdf.line(x, top, x, top - len(rows) * row_height)

    for row_index, row in enumerate(rows):
        y = top - row_index * row_height - 18
        pdf.setFont("Helvetica-Bold" if row_index == 0 else "Helvetica", 9)
        for column_index, value in enumerate(row):
            pdf.drawString(x_positions[column_index] + 6, y, value)

    pdf.showPage()
    pdf.save()


if __name__ == "__main__":
    main()
