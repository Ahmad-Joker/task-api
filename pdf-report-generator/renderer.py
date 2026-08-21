from datetime import date
from html import escape
from pathlib import Path

from playwright.sync_api import sync_playwright

from db import REPORTS_DIR


def money(value):
    return f"${value:,.2f}"


def build_report_html(report):
    totals = report["totals"]
    top_product_rows = "\n".join(
        f"""
        <tr>
          <td>{escape(row["product"])}</td>
          <td>{row["order_count"]}</td>
          <td>{money(row["revenue"])}</td>
        </tr>
        """
        for row in report["top_products"]
    )
    daily_rows = "\n".join(
        f"""
        <tr>
          <td>{escape(row["day"])}</td>
          <td>{row["order_count"]}</td>
          <td>{money(row["revenue"])}</td>
        </tr>
        """
        for row in report["orders_per_day"]
    )
    order_rows = "\n".join(
        f"""
        <tr>
          <td>{row["id"]}</td>
          <td>{escape(row["created_at"])}</td>
          <td>{escape(row["customer"])}</td>
          <td>{escape(row["product"])}</td>
          <td>{money(row["amount"])}</td>
        </tr>
        """
        for row in report["orders"]
    )

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Little Shop Sales Report</title>
  <style>
    @page {{
      size: A4;
      margin: 20mm 14mm;
      @bottom-center {{
        content: "Little Shop Sales Report - Page " counter(page) " of " counter(pages);
        font-size: 9px;
        color: #64748b;
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: #111827;
      font-family: Arial, sans-serif;
      font-size: 12px;
      line-height: 1.4;
    }}
    h1 {{
      margin: 0 0 4px;
      font-size: 28px;
      letter-spacing: -0.02em;
    }}
    h2 {{
      margin: 24px 0 8px;
      font-size: 15px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: #0f766e;
    }}
    .subtitle {{ color: #64748b; margin-bottom: 18px; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin-bottom: 10px;
    }}
    .metric {{
      border: 1px solid #d1d5db;
      border-radius: 8px;
      padding: 12px;
      background: #f8fafc;
    }}
    .metric span {{ display: block; color: #64748b; font-size: 10px; text-transform: uppercase; }}
    .metric strong {{ display: block; margin-top: 4px; font-size: 20px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 12px;
    }}
    thead {{ display: table-header-group; }}
    tr {{ break-inside: avoid; page-break-inside: avoid; }}
    th {{
      background: #0f172a;
      color: white;
      text-align: left;
      font-size: 10px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 7px 8px;
    }}
    td {{
      border-bottom: 1px solid #e5e7eb;
      padding: 6px 8px;
      vertical-align: top;
    }}
    tbody tr:nth-child(even) td {{ background: #f8fafc; }}
    .two-col {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }}
  </style>
</head>
<body>
  <h1>Little Shop Sales Report</h1>
  <div class="subtitle">Generated on {date.today().isoformat()} from SQLite order data.</div>

  <section class="metrics">
    <div class="metric"><span>Total orders</span><strong>{totals["total_orders"]}</strong></div>
    <div class="metric"><span>Total revenue</span><strong>{money(totals["total_revenue"])}</strong></div>
    <div class="metric"><span>Average order</span><strong>{money(totals["average_order_value"])}</strong></div>
  </section>

  <section class="two-col">
    <div>
      <h2>Top 5 products by revenue</h2>
      <table>
        <thead><tr><th>Product</th><th>Orders</th><th>Revenue</th></tr></thead>
        <tbody>{top_product_rows}</tbody>
      </table>
    </div>
    <div>
      <h2>Orders per day</h2>
      <table>
        <thead><tr><th>Day</th><th>Orders</th><th>Revenue</th></tr></thead>
        <tbody>{daily_rows}</tbody>
      </table>
    </div>
  </section>

  <h2>All orders</h2>
  <table>
    <thead><tr><th>ID</th><th>Date</th><th>Customer</th><th>Product</th><th>Amount</th></tr></thead>
    <tbody>{order_rows}</tbody>
  </table>
</body>
</html>"""


def render_pdf(report, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = build_report_html(report)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            margin={"top": "14mm", "right": "10mm", "bottom": "16mm", "left": "10mm"},
        )
        browser.close()
    return output_path


def test_pdf_path():
    return REPORTS_DIR / "test.pdf"
