"""
This module contains the business logic for generating white-label PDF reports
for agencies.
"""

import io
from sqlalchemy.orm import Session
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from datetime import datetime

from ..crud import agency_crud, analytics_crud


class ReportingService:
    def __init__(self, db: Session):
        self.db = db

    def generate_agency_report(
        self, agency_id: int, start_date: datetime, end_date: datetime
    ) -> bytes:
        """
        Generates a PDF report for an agency, summarizing client activity
        within a given date range.
        """
        agency = agency_crud.get_agency(self.db, agency_id)
        if not agency:
            raise ValueError("Agency not found")

        clients = agency_crud.get_clients_for_agency(self.db, agency_id)

        clients_data = []
        for client in clients:
            # Assuming client.shop relationship is loaded or accessible
            shop = client.shop
            if not shop:
                continue

            generations = analytics_crud.get_content_generation_count(
                self.db, shop_id=shop.id, start_date=start_date, end_date=end_date
            )
            ab_tests = analytics_crud.get_completed_ab_tests_count(
                self.db, shop_id=shop.id, start_date=start_date, end_date=end_date
            )
            clients_data.append(
                {
                    "domain": shop.shopify_domain,
                    "generations": generations,
                    "ab_tests": ab_tests,
                }
            )

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # --- Header ---
        if agency.logo_url:
            # Placeholder for fetching and drawing an image from a URL
            # from reportlab.lib.utils import ImageReader
            # try:
            #     response = requests.get(agency.logo_url)
            #     logo = ImageReader(io.BytesIO(response.content))
            #     p.drawImage(logo, inch, height - 1.5 * inch, width=1.5*inch, preserveAspectRatio=True)
            # except Exception:
            #     # Fallback to text if logo fails
            p.setFont("Helvetica-Bold", 16)
            p.drawString(inch, height - inch, f"Performance Report for {agency.name}")
        else:
            p.setFont("Helvetica-Bold", 16)
            p.drawString(inch, height - inch, f"Performance Report for {agency.name}")

        p.setFont("Helvetica", 10)
        p.drawString(
            inch,
            height - 1.2 * inch,
            f"Reporting Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        )
        p.line(inch, height - 1.3 * inch, width - inch, height - 1.3 * inch)

        # --- Body ---
        y_position = height - 2 * inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(inch, y_position, "Client Activity Summary")
        y_position -= 0.3 * inch

        p.setFont("Helvetica", 10)
        if not clients_data:
            p.drawString(inch, y_position, "No client activity in this period.")
        else:
            for client in clients_data:
                p.setFont("Helvetica-Bold", 10)
                p.drawString(inch, y_position, f"Client: {client['domain']}")
                y_position -= 0.2 * inch
                p.setFont("Helvetica", 10)
                p.drawString(
                    inch * 1.2,
                    y_position,
                    f"Content Generations: {client['generations']}",
                )
                y_position -= 0.2 * inch
                p.drawString(
                    inch * 1.2, y_position, f"A/B Tests Completed: {client['ab_tests']}"
                )
                y_position -= 0.3 * inch

        # --- Footer ---
        p.line(inch, 0.8 * inch, width - inch, 0.8 * inch)
        p.drawString(
            inch,
            0.6 * inch,
            f"Report Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        )

        p.showPage()
        p.save()

        buffer.seek(0)
        return buffer.getvalue()
