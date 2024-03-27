from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
import os

import logging

from typing import Any, Dict

def generate_pdf(workdir: str, text: str, var: Dict[str, Any]):
  lines = text.split("\n")
  try:
    i = 0
    lines = [l.format(**var) for l in lines if l]
  except Exception as e:
    logging.error(e)
    return b''

  buffer = BytesIO()
  doc = SimpleDocTemplate(buffer, pagesize=letter)

  flowables = []
  styles = getSampleStyleSheet()

  for line in lines:
    if line[0] == "[":
      flowable = Image(os.path.join(workdir, line[1:-1]))
    else:
      heading = 0
      for char in line[:6]:
        if char == "#":
          heading += 1
        else:
          break
      if line[0] == "-":
        bulletText = "\u2022"
        line = line[1:]
      else:
        bulletText = None
      flowable = Paragraph(line[heading:], styles[f"h{heading}" if heading else "Normal"], bulletText=bulletText)
    
    flowables.append(flowable)

  doc.build(flowables)
  pdf_binary = buffer.getvalue()
  buffer.close()
  return pdf_binary
