"""PDF renderer: converts a computed context dict into a PDF using xhtml2pdf."""
import os
import io
from xhtml2pdf import pisa
from jinja2 import Environment, FileSystemLoader

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

_env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=True)


def render_html(context: dict) -> str:
    """Render the rental information sheet as an HTML string."""
    template = _env.get_template("rent_info.html")
    return template.render(**context)


def render_pdf(context: dict) -> bytes:
    """Render the rental information sheet as PDF bytes.

    Deterministic: same context always produces the same PDF.
    """
    html_str = render_html(context)
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(
        io.StringIO(html_str),
        dest=result,
    )
    if pisa_status.err:
        raise RuntimeError(f"PDF generation failed with {pisa_status.err} errors")
    return result.getvalue()
