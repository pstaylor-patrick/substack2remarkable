#!/bin/bash
# html2md.sh - Convert HTML files to clean, readable Markdown and PDF

# CSS for PDF styling
PDF_CSS='
body {
    font-family: Georgia, serif;
    max-width: 700px;
    margin: 0 auto;
    padding: 40px;
    line-height: 1.6;
    color: #333;
}
h1 { font-size: 28px; margin-bottom: 20px; }
h2 { font-size: 22px; margin-top: 30px; }
h3 { font-size: 18px; margin-top: 25px; }
p { margin: 15px 0; }
img { max-width: 100%; height: auto; margin: 20px 0; }
a { color: #0066cc; }
ul, ol { padding-left: 30px; }
li { margin: 8px 0; }
blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 20px; color: #666; }
code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }
em { font-style: italic; }
strong { font-weight: bold; }
'

# Find all HTML files matching */src/html/*.html
find . -path "*/src/html/*.html" -type f | while read -r html_file; do
    # Get base name for output files
    base_dir=$(dirname "$html_file" | sed 's|src/html|dist|')
    base_name=$(basename "$html_file" .html)

    md_file="${base_dir}/md/${base_name}.md"
    pdf_file="${base_dir}/pdf/${base_name}.pdf"

    # Create output directories
    mkdir -p "$(dirname "$md_file")"
    mkdir -p "$(dirname "$pdf_file")"

    # Extract title
    title=$(readable -q -p title "$html_file")

    # Extract readable content with Mozilla Readability, then convert to clean markdown
    {
        # Add title as H1
        echo "# $title"
        echo ""

        # Convert content
        readable -q -p html-content "$html_file" \
            | pandoc -f html -t gfm --wrap=none \
            | perl -0777 -pe '
                # Convert <img> tags to markdown images
                s/<img[^>]*src="([^"]+)"[^>]*>/![image]($1)/g;
                # Convert <a> tags to markdown links
                s/<a[^>]*href="([^"]+)"[^>]*>([^<]+)<\/a>/[$2]($1)/g;
                # Remove empty links
                s/<a[^>]*><\/a>//g;
                # Remove empty divs and figures
                s/<\/?div[^>]*>//g;
                s/<\/?figure[^>]*>//g;
                s/<figcaption[^>]*>(.*?)<\/figcaption>/*$1*/g;
                # Clean up excessive blank lines
                s/\n{4,}/\n\n/g;
            '
    } > "$md_file"

    # Generate PDF from readable HTML with styling
    {
        echo "<!DOCTYPE html><html><head><meta charset='UTF-8'><style>${PDF_CSS}</style></head><body>"
        echo "<h1>${title}</h1>"
        readable -q -p html-content "$html_file"
        echo "</body></html>"
    } | weasyprint - "$pdf_file" 2>/dev/null

    echo "Converted: $html_file"
    echo "  -> $md_file"
    echo "  -> $pdf_file"
done
