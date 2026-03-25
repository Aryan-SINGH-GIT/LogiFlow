import fitz

doc = fitz.open('uploads/empty_logbook.pdf')
page = doc[7]
for b in page.get_text('blocks'):
    text = b[4].lower()
    if 'date' in text or 'tim' in text or 'partm' in text or 'day' in text:
        print(f"X: {b[0]:.1f}, Y: {b[1]:.1f} - {b[4].strip()}")
