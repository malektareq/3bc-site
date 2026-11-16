"""The Founder's email signature in the Signal brand (release checklist item 5; intake 001; Cork, board 14214, and Mona, 14216):
an HTML version with inline styles and the system font stack, and a plain-text version that is the canonical fallback and stands
alone with the same identity facts. Only details the site publishes, the mark as an image served from the site, under 10 KB, no
tracking, no external fonts, no JavaScript, no email address. signature/index.html renders both. Dependency-free."""
import html
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAGMENT = (ROOT / 'signature' / 'signature.html').read_text()
TEXT = (ROOT / 'signature' / 'signature.txt').read_text()
PAGE = (ROOT / 'signature' / 'index.html').read_text()
SITE = 'https://3bc.ie'
SYSTEM_FONTS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
PUBLISHED = ''.join((ROOT / p).read_text() for p in ('index.html', 'about.html', 'contact.html', 'what-we-do.html'))


class Html(unittest.TestCase):
    def test_under_10_kb(self):
        self.assertLess(len(FRAGMENT.encode('utf-8')), 10 * 1024)

    def test_no_javascript_no_external_fonts_no_style_blocks(self):
        lowered = FRAGMENT.lower()
        for banned in ('<script', 'javascript:', '<style', '<link', '@import', '@font-face', 'url(', 'fonts.googleapis', 'fonts.gstatic',
                       ' class=', '<iframe', '<form', '<svg'):
            self.assertNotIn(banned, lowered, banned)
        self.assertIsNone(re.search(r'\son\w+\s*=', lowered), 'no event handler attributes')

    def test_inline_styles_with_the_system_font_stack(self):
        self.assertIn('font-family:' + SYSTEM_FONTS, FRAGMENT)
        for tag in re.findall(r'<(div|span|a|td|table)\b([^>]*)>', FRAGMENT):
            if tag[0] in ('div', 'span', 'a', 'table'):
                self.assertIn('style="', tag[1], tag)

    def test_one_image_the_mark_served_from_the_site_and_no_tracking(self):
        images = re.findall(r'<img\b[^>]*>', FRAGMENT)
        self.assertEqual(len(images), 1, images)
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', images[0]))
        self.assertEqual(attrs['src'], SITE + '/brand/email-mark.png')
        self.assertEqual((attrs['width'], attrs['height'], attrs['alt']), ('24', '24', '3BC'))
        png = (ROOT / 'brand' / 'email-mark.png').read_bytes()
        self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('>II', png[16:24]), (48, 48), 'twice its displayed size, for sharp high-density screens')
        self.assertLess(len(png), 2048)
        for url in re.findall(r'(?:src|href)="([^"]*)"', FRAGMENT):
            self.assertNotIn('?', url, 'no query strings: nothing that identifies the reader')
            self.assertTrue(url.startswith(SITE), url)

    def test_details_only_from_the_site(self):
        self.assertIn('Tariq Mehmood <span>Founder</span>', PUBLISHED, 'the name and title as the About page gives them')
        for part in ('Tariq Mehmood', 'Founder', '3BC', '3bc.ie', 'London, United Kingdom'):
            self.assertIn(part, FRAGMENT, part)
        self.assertEqual((ROOT / 'CNAME').read_text().strip(), '3bc.ie')
        self.assertIn('London, United Kingdom', PUBLISHED)
        self.assertIsNone(re.search(r'@|mailto:', FRAGMENT + TEXT), 'no email line until hello at 3bc.ie is set up (Cork and Mona)')
        self.assertNotIn('Registration pending', FRAGMENT + TEXT, 'the registered name and number come later, in both versions')
        self.assertIsNone(re.search(r'\d[\d ()+.-]{6,}\d', html.unescape(re.sub(r'<[^>]+>', ' ', FRAGMENT)) + TEXT), 'no phone number')

    def test_one_link_a_signal_tint_underlined(self):
        # Cork and Mona: #7B66F8 (about 4.1:1 on white and on dark mail backgrounds), underlined so the link is not shown by colour
        # alone. Text takes the mail app's own colour (a fixed dark ink measured 1.09:1 on a dark mail background).
        self.assertEqual(re.findall(r'href="([^"]*)"', FRAGMENT), ['https://3bc.ie'])
        styles = re.findall(r'<(\w+)\b[^>]*style="([^"]*)"', FRAGMENT)
        coloured = [(tag, style) for tag, style in styles if re.search(r'(?<![-\w])color:', style)]
        self.assertEqual(coloured, [('a', 'color:#7B66F8;text-decoration:underline')])


class PlainText(unittest.TestCase):
    def test_the_canonical_fallback_stands_alone(self):
        self.assertEqual(TEXT.splitlines(), ['Tariq Mehmood', 'Founder, 3BC', 'https://3bc.ie', 'London, United Kingdom'])

    def test_the_html_and_the_plain_text_carry_the_same_facts(self):
        # Cork and Mona: the plain text is the canonical fallback, so the HTML may say nothing it does not.
        lines = [html.unescape(re.sub(r'<[^>]+>', '', d)) for d in re.findall(r'<div\b[^>]*>(.*?)</div>', FRAGMENT)]
        site = re.search(r'href="([^"]*)"', FRAGMENT).group(1)
        self.assertEqual([site if line == '3bc.ie' else line for line in lines], TEXT.splitlines())

    def test_short_ascii_lines(self):
        self.assertTrue(TEXT.isascii())
        self.assertTrue(all(len(line) <= 72 for line in TEXT.splitlines()))


class Preview(unittest.TestCase):
    def test_the_page_renders_both_versions_as_they_are(self):
        self.assertEqual(PAGE.count(FRAGMENT), 2, 'light and dark backgrounds, the same markup')
        self.assertIn('<pre>' + html.escape(TEXT) + '</pre>', PAGE)

    def test_the_page_is_not_indexed_and_runs_no_script(self):
        self.assertIn('<meta name="robots" content="noindex,nofollow">', PAGE)
        self.assertNotIn('<script', PAGE.lower())
        self.assertNotIn('http://', PAGE)


if __name__ == '__main__':
    unittest.main()
