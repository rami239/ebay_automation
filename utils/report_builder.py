from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def _image_data_uri(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def _fmt_money(value: Any) -> str:
    try:
        return f"${float(value):.2f}"
    except (TypeError, ValueError):
        return "—"


def _fmt_variants(variants: Any) -> str:
    if not isinstance(variants, dict) or not variants:
        return "—"
    return ", ".join(
        f"{html.escape(str(name))}: {html.escape(str(value))}"
        for name, value in variants.items()
    )


def write_execution_report(data: dict[str, Any], output_path: Path, screenshots_dir: Path) -> None:
    """Create a self-contained HTML execution report independent of pytest-html."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    status = str(data.get("status", "UNKNOWN"))
    duration = data.get("duration")
    duration_text = f"{float(duration):.2f}s" if isinstance(duration, (int, float)) else "—"

    products = data.get("products") or []
    product_rows = []
    for idx, product in enumerate(products, start=1):
        url = str(product.get("url", ""))
        local_file = Path(urlparse(url).path).name if url else "—"
        added = "Yes" if product.get("added") else "No"
        product_rows.append(
            "<tr>"
            f"<td>{idx}</td>"
            f"<td>{html.escape(str(product.get('name', '—')))}</td>"
            f"<td>{_fmt_money(product.get('price'))}</td>"
            f"<td>{_fmt_variants(product.get('variants'))}</td>"
            f"<td>{added}</td>"
            f"<td><code>{html.escape(local_file)}</code></td>"
            "</tr>"
        )

    if not product_rows:
        product_rows.append('<tr><td colspan="6">No matching products were collected.</td></tr>')

    screenshot_cards = []
    if screenshots_dir.exists():
        for image_path in sorted(screenshots_dir.glob("*.png")):
            try:
                uri = _image_data_uri(image_path)
            except OSError:
                continue
            screenshot_cards.append(
                '<figure class="shot">'
                f'<img src="{uri}" alt="{html.escape(image_path.name)}">'
                f'<figcaption>{html.escape(image_path.stem.replace("_", " "))}</figcaption>'
                '</figure>'
            )

    screenshot_html = "".join(screenshot_cards) or "<p>No screenshots were generated.</p>"

    error = html.escape(str(data.get("error", "")))
    error_html = f'<section><h2>Error</h2><pre>{error}</pre></section>' if error else ""

    query = html.escape(str(data.get("query", "—")))
    limit = html.escape(str(data.get("limit", "—")))
    budget_per_item = _fmt_money(data.get("budget_per_item"))
    items_count = html.escape(str(data.get("items_count", len(products))))
    actual_total = _fmt_money(data.get("actual_total"))
    max_total = _fmt_money(data.get("max_total"))
    login_username = html.escape(str(data.get("login_username", "—")))
    login_status = html.escape(str(data.get("login_status", "Not recorded")))
    login_type = html.escape(str(data.get("login_type", "—")))

    report = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>eBay Mock Automation Report</title>
<style>
body{{font-family:Arial,sans-serif;margin:0;background:#f5f7fa;color:#1f2937}}
main{{max-width:1180px;margin:32px auto;padding:0 20px 40px}}
h1{{margin-bottom:6px}} .sub{{color:#6b7280;margin-top:0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:20px 0}}
.card,section{{background:white;border:1px solid #e5e7eb;border-radius:10px;padding:18px;margin-bottom:18px;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.label{{font-size:12px;text-transform:uppercase;color:#6b7280}} .value{{font-size:24px;font-weight:700;margin-top:5px}}
table{{width:100%;border-collapse:collapse}} th,td{{padding:10px;border-bottom:1px solid #e5e7eb;text-align:left;vertical-align:top}} th{{background:#f9fafb}}
.gallery{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}}
.shot{{margin:0;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;background:#fff}} .shot img{{display:block;width:100%;height:210px;object-fit:contain;background:#fafafa}} .shot figcaption{{padding:9px;font-size:13px}}
.note{{background:#eff6ff;border-left:4px solid #3b82f6;padding:12px 14px;border-radius:6px}}
pre{{white-space:pre-wrap;word-break:break-word}} code{{font-family:Consolas,monospace}}
a{{color:#2563eb}}
</style>
</head>
<body><main>
<h1>eBay Mock E2E Automation Report</h1>
<p class="sub">Persistent execution report generated directly from the automated test run.</p>
<div class="grid">
  <div class="card"><div class="label">Status</div><div class="value">{html.escape(status)}</div></div>
  <div class="card"><div class="label">Duration</div><div class="value">{duration_text}</div></div>
  <div class="card"><div class="label">Login</div><div class="value">{login_status}</div></div>
  <div class="card"><div class="label">Products found</div><div class="value">{len(products)}</div></div>
  <div class="card"><div class="label">Cart total</div><div class="value">{actual_total}</div></div>
</div>
<section>
<h2>Test Data</h2>
<table><tbody>
<tr><th>Login user</th><td>{login_username}</td></tr>
<tr><th>Login type</th><td>{login_type}</td></tr>
<tr><th>Login status</th><td>{login_status}</td></tr>
<tr><th>Search query</th><td>{query}</td></tr>
<tr><th>Max price per item</th><td>{budget_per_item}</td></tr>
<tr><th>Requested limit</th><td>{limit}</td></tr>
<tr><th>Items added</th><td>{items_count}</td></tr>
<tr><th>Maximum allowed cart total</th><td>{max_total}</td></tr>
<tr><th>Actual cart total</th><td>{actual_total}</td></tr>
</tbody></table>
</section>
<section>
<h2>Matching Products & Variants</h2>
<table><thead><tr><th>#</th><th>Product</th><th>Price</th><th>Random variants</th><th>Added</th><th>Mock page</th></tr></thead>
<tbody>{''.join(product_rows)}</tbody></table>
<p class="note">The product pages are local mock pages used by the supplied exercise. The temporary HTTP server stops when pytest finishes, so the report stores page filenames instead of dead localhost links.</p>
</section>
<section><h2>Screenshots</h2><div class="gallery">{screenshot_html}</div></section>
{error_html}
<section><h2>Additional artifacts</h2><p><a href="run.log">run.log</a> contains the persistent execution log. <a href="junit.xml">junit.xml</a> is the standard pytest JUnit XML report.</p></section>
</main></body></html>"""

    output_path.write_text(report, encoding="utf-8")
