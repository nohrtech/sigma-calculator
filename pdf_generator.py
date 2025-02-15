#!/usr/bin/env python3
"""
NohrTech Sigma Calculator - PDF Report Generator
A professional GNSS position accuracy analysis tool by NohrTech AS.

This module generates PDF reports containing sigma calculation results
and statistical analysis of GNSS position accuracy data.

Author: NohrTech AS
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime

def generate_pdf(output_path, data, filename):
    """Generate a PDF report of sigma calculation results."""
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    elements.append(Paragraph("RINEX Sigma Calculator Results", title_style))
    
    # File information
    elements.append(Paragraph(f"File: {filename}", styles["Normal"]))
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Summary Statistics for each component
    elements.append(Paragraph("Summary Statistics", styles["Heading2"]))
    
    summary_data = [["Component", "Mean (mm)", "Min (mm)", "Max (mm)", "Std Dev (mm)"]]
    components = ['horizontal', 'vertical', 'E', 'N', 'U']
    
    for comp in components:
        stats = data['summary']['components'][comp]
        summary_data.append([
            comp.capitalize(),
            f"{stats['mean']:.2f}",
            f"{stats['min']:.2f}",
            f"{stats['max']:.2f}",
            f"{stats['std']:.2f}"
        ])
    
    summary_table = Table(summary_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Satellite Results
    elements.append(Paragraph("Satellite Results", styles["Heading2"]))
    
    # Create satellite data table
    sat_data = [["PRN", "Horizontal (mm)", "Vertical (mm)", "E (mm)", "N (mm)", "U (mm)"]]
    for sat in data['satellites']:
        sat_data.append([
            sat['prn'],
            sat['horizontal'],
            sat['vertical'],
            sat['E'],
            sat['N'],
            sat['U']
        ])
    
    sat_table = Table(sat_data, colWidths=[1*inch, 1.2*inch, 1.2*inch, 1*inch, 1*inch, 1*inch])
    sat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
    ]))
    elements.append(sat_table)

    # Build PDF
    doc.build(elements)
