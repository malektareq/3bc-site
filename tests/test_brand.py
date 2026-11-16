"""The 3BC Signal brand (intake 001; the Founder chose Signal; spec checked by Cork, Dev Ops 14123): the mark, its pixel-snapped
16 px form, the tokens the site adopts, the lockup in the header and footer, the favicon set, the app icons, the manifest and
the social image with its tags. Dependency-free: PNG and ICO sizes are read from their own headers."""
import json
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'what-we-do.html', 'about.html', 'contact.html', 'privacy.html', 'terms.html', '404.html', 'services.html']
CONTENT = {'index.html': '', 'what-we-do.html': 'what-we-do.html', 'about.html': 'about.html', 'contact.html': 'contact.html',
           'privacy.html': 'privacy.html', 'terms.html': 'terms.html'}
MASTER = [(6, 36, 14, 22), (25, 22, 14, 36), (44, 6, 14, 52)]
SMALL = [(1, 9, 4, 6), (6, 6, 4, 9), (11, 2, 4, 13)]
TOKENS = {'signal': '#5B3DF5', 'signal-on-dark': '#A99BFF', 'ink': '#12121A', 'paper': '#F4F3FA'}


def rects(svg):
    return [tuple(int(r[k]) for k in ('x', 'y', 'width', 'height'))
            for r in (dict(re.findall(r'(\w+)="([^"]*)"', m)) for m in re.findall(r'<rect ([^>]*)/>', svg))]


def png_size(data):
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'a PNG'
    return struct.unpack('>II', data[16:24])


class Mark(unittest.TestCase):
    def test_the_master_is_the_spec_s_three_rounded_bars(self):
        svg = (ROOT / 'brand/mark.svg').read_text()
        self.assertIn('viewBox="0 0 64 64"', svg)
        self.assertEqual(rects(svg), MASTER)
        self.assertEqual(re.findall(r'rx="(\d+)"', svg), ['3', '3', '3'])
        self.assertIn(TOKENS['signal'], svg)

    def test_the_16_px_mark_is_pixel_snapped(self):
        svg = (ROOT / 'brand/mark-16.svg').read_text()
        self.assertIn('viewBox="0 0 16 16"', svg)
        self.assertEqual(rects(svg), SMALL)   # 4 px bars, 1 px gaps, square corners, heights 6/9/13 on one baseline
        self.assertNotIn('rx=', svg)
        self.assertEqual({y + h for _, y, _, h in SMALL}, {15})

    def test_tokens(self):
        t = json.loads((ROOT / 'brand/tokens.json').read_text())
        self.assertEqual(t['colour'], TOKENS)
        self.assertEqual([(b['x'], b['y'], b['width'], b['height']) for b in t['mark']['master']['bars']], MASTER)
        self.assertEqual([(b['x'], b['y'], b['width'], b['height']) for b in t['mark']['small']['bars']], SMALL)
        self.assertEqual((t['lockup']['min_width_px'], t['app_icon']['corner_radius']), (72, '24/104'))


class Site(unittest.TestCase):
    def test_the_site_adopts_the_tokens_and_drops_the_old_blues(self):
        css = (ROOT / 'style.css').read_text().replace(' ', '')
        for token in ('--accent:#5B3DF5', '--accent:#A99BFF', '--text:#12121A', '--bg:#F4F3FA'):
            self.assertIn(token, css)
        for path in [ROOT / 'style.css', *(ROOT / p for p in PAGES), *ROOT.glob('brand/*.svg'), ROOT / 'favicon.svg']:
            text = path.read_text().lower()
            for old in ('#3b5bdb', '#8da2ff', '#235e90'):
                self.assertNotIn(old, text, path.name)

    def test_the_lockup_is_in_the_header_and_the_footer(self):
        # The Founder chose "Use system font": the wordmark is live HTML text in the site's system stack, beside the SVG mark.
        css = (ROOT / 'style.css').read_text().replace(' ', '')
        self.assertIn('min-width:72px', css)
        self.assertIn('gap:calc(var(--mark)*14/64)', css)   # clear space: one bar width
        word = css[css.index('.wordmark{'):]
        word = word[:word.index('}')]
        for rule in ('font-family:var(--font)', 'font-weight:800', 'letter-spacing:-.02em'):
            self.assertIn(rule, word)
        self.assertIn('-apple-system,BlinkMacSystemFont,"SegoeUI",Roboto,"HelveticaNeue",Arial', css)
        for page in PAGES:
            raw = (ROOT / page).read_text()
            header, footer = raw[raw.index('<header'):raw.index('</header>')], raw[raw.index('<footer'):raw.index('</footer>')]
            for part in (header, footer):
                self.assertEqual(rects(part[part.index('<svg class="brand-mark"'):])[:3], MASTER, page)
                self.assertIn('<span class="wordmark" aria-hidden="true">3BC</span>', part, page)
                self.assertIn('<svg class="brand-mark" viewBox="0 0 64 64" width="28" height="28"', part, page)   # sized without CSS too
                self.assertNotIn('<text', part)
            self.assertIn('aria-label="3BC Home"', header)
        self.assertFalse((ROOT / 'brand/wordmark.svg').exists(), 'no outlined wordmark: live text only')
        self.assertEqual(json.loads((ROOT / 'brand/tokens.json').read_text())['wordmark']['weight'], 800)

    def test_no_web_font_loads(self):
        for path in [ROOT / 'style.css', *(ROOT / p for p in PAGES)]:
            text = path.read_text()
            for banned in ('@font-face', 'fonts.googleapis', 'fonts.gstatic', '.woff'):
                self.assertNotIn(banned, text, path.name)
        self.assertFalse(list(ROOT.rglob('*.woff*')) + list(ROOT.rglob('*.ttf')) + list(ROOT.rglob('*.otf')))


class Icons(unittest.TestCase):
    def test_favicon_ico_holds_the_16_and_32_images(self):
        data = (ROOT / 'favicon.ico').read_bytes()
        reserved, kind, count = struct.unpack('<HHH', data[:6])
        self.assertEqual((reserved, kind, count), (0, 1, 2))
        sizes = []
        for i in range(count):
            w, h, _, _, _, _, length, offset = struct.unpack('<BBBBHHII', data[6 + 16 * i:22 + 16 * i])
            self.assertEqual(png_size(data[offset:offset + length]), (w, h))
            sizes.append(w)
        self.assertEqual(sizes, [16, 32])

    def test_every_png_is_its_stated_size(self):
        for name, size in (('apple-touch-icon.png', (180, 180)), ('brand/icon-192.png', (192, 192)), ('brand/icon-512.png', (512, 512)),
                           ('brand/og.png', (1200, 630))):
            self.assertEqual(png_size((ROOT / name).read_bytes()), size, name)

    def test_the_svg_favicon_is_the_master_and_follows_dark_mode(self):
        svg = (ROOT / 'favicon.svg').read_text()
        self.assertEqual(rects(svg), MASTER)
        self.assertIn('prefers-color-scheme:dark', svg.replace(' ', ''))
        self.assertIn(TOKENS['signal-on-dark'], svg)

    def test_the_manifest(self):
        m = json.loads((ROOT / 'site.webmanifest').read_text())
        self.assertEqual((m['name'], m['theme_color'], m['background_color']), ('3BC', TOKENS['signal'], TOKENS['paper']))
        for icon in m['icons']:
            self.assertEqual(png_size((ROOT / icon['src'].lstrip('/')).read_bytes()), tuple(int(n) for n in icon['sizes'].split('x')))

    def test_every_page_links_the_icons_and_content_pages_carry_the_social_tags(self):
        for page in PAGES:
            raw = (ROOT / page).read_text()
            for tag in ('rel="icon" href="/favicon.ico"', 'rel="icon" href="/favicon.svg"', 'rel="apple-touch-icon" href="/apple-touch-icon.png"',
                        'rel="manifest" href="/site.webmanifest"', 'name="theme-color" content="#5B3DF5"'):
                self.assertIn(tag, raw, page)
            if page in CONTENT:
                self.assertIn('property="og:image" content="https://3bc.ie/brand/og.png"', raw)
                self.assertIn('property="og:url" content="https://3bc.ie/' + CONTENT[page] + '"', raw)
                self.assertIn('name="twitter:card" content="summary_large_image"', raw)
                self.assertIn('name="twitter:image" content="https://3bc.ie/brand/og.png"', raw)
                title = re.search(r'<title>([^<]*)</title>', raw).group(1)
                self.assertIn('property="og:title" content="' + title + '"', raw)
                self.assertIn('name="twitter:title" content="' + title + '"', raw)


if __name__ == '__main__':
    unittest.main()
