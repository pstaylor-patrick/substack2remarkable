#!/usr/bin/env python3
"""Simple web server to view markdown files as HTML."""

import http.server
import socketserver
import os
import urllib.parse
from pathlib import Path

PORT = 8000

# Simple markdown to HTML conversion
def md_to_html(md_content, title="Document"):
    """Convert markdown to HTML with basic styling."""
    import re

    html = md_content

    # Escape HTML first
    html = html.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # Headers
    html = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', html, flags=re.MULTILINE)
    html = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold and italic
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # Images (must be before links since ![...] contains [...])
    html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" style="max-width:100%">', html)

    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

    # Unordered lists
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # Ordered lists
    html = re.sub(r'^\d+\.\s+(.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # Code blocks
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

    # Paragraphs (double newlines)
    html = re.sub(r'\n\n+', '</p><p>', html)
    html = '<p>' + html + '</p>'

    # Clean up empty paragraphs and fix list items
    html = re.sub(r'<p>\s*</p>', '', html)
    html = re.sub(r'<p>(<li>)', r'<ul>\1', html)
    html = re.sub(r'(</li>)</p>', r'\1</ul>', html)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #fafafa;
        }}
        h1, h2, h3, h4, h5, h6 {{ color: #111; margin-top: 1.5em; }}
        a {{ color: #0066cc; }}
        code {{ background: #f0f0f0; padding: 0.2em 0.4em; border-radius: 3px; font-size: 0.9em; }}
        img {{ max-width: 100%; height: auto; }}
        blockquote {{ border-left: 4px solid #ddd; margin-left: 0; padding-left: 1rem; color: #666; }}
        ul, ol {{ padding-left: 2rem; }}
        li {{ margin: 0.5em 0; }}
        .nav {{ margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid #ddd; }}
        .nav a {{ margin-right: 1rem; }}
    </style>
</head>
<body>
    <nav class="nav"><a href="/">← Home</a></nav>
    {html}
</body>
</html>'''


class MarkdownHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.unquote(self.path)

        # Home page - list all files with PDF download links
        if path == '/' or path == '':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            # Find all markdown and PDF files
            md_files = sorted(Path('.').rglob('*/dist/md/*.md'))

            links = []
            for md in md_files:
                pdf = Path(str(md).replace('/md/', '/pdf/').replace('.md', '.pdf'))
                pdf_link = f' <a href="/{pdf}" class="pdf">📄 PDF</a>' if pdf.exists() else ''
                links.append(f'<li><a href="/{md}">{md.stem}</a>{pdf_link}</li>')

            links_html = ''.join(links) if links else '<li>No files found. Run ./html2md.sh first.</li>'

            html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Articles</title>
<style>
    body {{ max-width: 800px; margin: 2rem auto; padding: 0 2rem; font-family: -apple-system, sans-serif; }}
    h1 {{ color: #333; }}
    ul {{ list-style: none; padding: 0; }}
    li {{ margin: 1rem 0; display: flex; gap: 1rem; align-items: center; }}
    a {{ color: #0066cc; text-decoration: none; font-size: 1.1rem; }}
    a:hover {{ text-decoration: underline; }}
    .pdf {{ font-size: 0.9rem; background: #f0f0f0; padding: 4px 8px; border-radius: 4px; }}
</style>
</head><body>
<h1>Articles</h1>
<ul>{links_html}</ul>
</body></html>'''
            self.wfile.write(html.encode())
            return

        # Serve markdown files as HTML
        if path.endswith('.md'):
            file_path = Path('.' + path)
            if file_path.exists():
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()

                md_content = file_path.read_text()
                html = md_to_html(md_content, file_path.stem)
                self.wfile.write(html.encode())
                return

        # Fall back to default handler
        super().do_GET()


if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), MarkdownHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
