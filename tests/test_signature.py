"""The Founder's email signature in the Signal brand (release checklist item 5; intake 001): an HTML version with inline styles
and the system font stack, and a plain-text version, both carrying only details the site already publishes, with the mark as
an image served from the site. Under 10 KB, no tracking, no external fonts, no JavaScript. signature/index.html renders both.
Dependency-free."""
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
            self.assertTrue(url.startswith((SITE, 'mailto:')), url)

    def test_details_only_from_the_site(self):
        self.assertIn('Tariq Mehmood <span>Founder</span>', PUBLISHED, 'the name and title as the About page gives them')
        for part in ('Tariq Mehmood', 'Founder', 'hello@team.malektareq.com', 'London, United Kingdom', 'Registration pending'):
            self.assertIn(part, FRAGMENT, part)
        self.assertEqual((ROOT / 'CNAME').read_text().strip(), '3bc.ie')
        self.assertIn('Registration pending', PUBLISHED)
        for address in set(re.findall(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+', FRAGMENT + TEXT)):
            self.assertIn(address, PUBLISHED, 'an address the site publishes: ' + address)
        self.assertIsNone(re.search(r'\d[\d ()+.-]{6,}\d', html.unescape(re.sub(r'<[^>]+>', ' ', FRAGMENT)) + TEXT), 'no phone number')

    def test_text_takes_the_mail_app_s_colour(self):
        # A fixed dark text colour vanished on dark mail backgrounds (1.09:1 measured on the preview): text inherits the client's
        # own colour, which adapts to dark mode; only the links keep Signal (6.1:1 on white).
        styles = re.findall(r'<(\w+)\b[^>]*style="([^"]*)"', FRAGMENT)
        coloured = [(tag, style) for tag, style in styles if re.search(r'(?<![-\w])color:', style)]
        self.assertEqual([tag for tag, _ in coloured], ['a', 'a'])
        self.assertTrue(all('color:#5B3DF5' in style for _, style in coloured))

    def test_links(self):
        self.assertEqual(sorted(re.findall(r'href="([^"]*)"', FRAGMENT)), ['https://3bc.ie', 'mailto:hello@team.malektareq.com'])


class PlainText(unittest.TestCase):
    def test_the_same_details(self):
        self.assertEqual(TEXT.splitlines(), ['Tariq Mehmood', 'Founder, 3BC', 'hello@team.malektareq.com | https://3bc.ie',
                                             'London, United Kingdom', 'Registration pending'])

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
