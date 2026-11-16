"""Dependency-free checks for the buildless, review-only 3BC site."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import re
import unittest
ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'what-we-do.html', 'about.html', 'contact.html', 'privacy.html', 'terms.html', '404.html']
REDIRECT = 'services.html'
ALL = PAGES + [REDIRECT]
NAV = ('Home', 'What we do', 'About', 'Contact')
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True); self.tags=[]; self.text=[]; self.feed(text)
    def handle_starttag(self, tag, attrs): self.tags.append((tag, dict(attrs)))
    def handle_startendtag(self, tag, attrs): self.tags.append((tag, dict(attrs)))
    def handle_data(self, data): self.text.append(data)
def load(name):
    return Page((ROOT/name).read_text())
class SiteTests(unittest.TestCase):
    def test_exact_pages_redirect_and_single_stylesheet(self):
        self.assertEqual(sorted(p.name for p in ROOT.glob('*.html')), sorted(ALL))
        self.assertEqual([p.name for p in ROOT.glob('*.css')], ['style.css'])
        for name in ALL:
            self.assertLess((ROOT/name).stat().st_size, 100 * 1024, name)
        self.assertLess((ROOT/'style.css').stat().st_size, 100 * 1024)
    def test_every_page_has_accessible_structure_and_release_hold(self):
        for file in ALL:
            with self.subTest(page=file):
                page=load(file); tags=page.tags; text=' '.join(page.text)
                self.assertEqual(sum(t=='h1' for t,a in tags),1)
                self.assertEqual(sum(t=='main' and a.get('id')=='main' for t,a in tags),1)
                self.assertTrue(any(t=='html' and a.get('lang')=='en' for t,a in tags))
                self.assertTrue(any(t=='a' and a.get('href')=='#main' for t,a in tags))
                self.assertTrue(any(t=='meta' and a.get('name')=='viewport' for t,a in tags))
                self.assertTrue(any(t=='meta' and a.get('name')=='robots' and a.get('content')=='noindex, nofollow' for t,a in tags))
                self.assertIn('3BC (registration pending)', text)
                self.assertIn("3BC's officers are AI systems under human oversight.", text)
                self.assertIn('Draft for Founder review', text)
                self.assertTrue(all(a.get('aria-label') for t,a in tags if t=='nav'))
                ids=[a['id'] for t,a in tags if 'id' in a]; self.assertEqual(len(ids),len(set(ids)))
                levels=[int(t[1]) for t,a in tags if t in ('h1','h2','h3','h4','h5','h6')]
                self.assertEqual(levels[0], 1)
                self.assertTrue(all(b <= a + 1 for a,b in zip(levels, levels[1:])))
                self.assertLessEqual(sum(t=='a' and 'primary' in (a.get('class') or '').split() for t,a in tags), 1)
                self.assertNotIn('>Services</a>', (ROOT/file).read_text())
    def test_main_nav_and_services_redirect(self):
        raw=(ROOT/REDIRECT).read_text()
        self.assertIn('http-equiv="refresh"', raw)
        self.assertIn('content="0; url=/what-we-do.html"', raw)
        self.assertIn('href="/what-we-do.html"', raw)
        self.assertNotIn('Capabilities in development', raw)
        self.assertNotIn('for a quote', raw)
        for file in PAGES:
            text=(ROOT/file).read_text()
            with self.subTest(page=file):
                for label in NAV: self.assertIn('>'+label+'</a>', text)
                self.assertNotIn('services.html', text)
                self.assertNotIn('>Services</a>', text)
    def test_all_internal_links_fragments_and_assets_exist(self):
        for file in ALL:
            page=load(file)
            for tag,attrs in page.tags:
                for key in ('href','src'):
                    if key not in attrs: continue
                    url=urlparse(attrs[key])
                    with self.subTest(page=file,url=attrs[key]):
                        self.assertIn(url.scheme, ['', 'mailto'])
                        if url.scheme=='mailto':
                            self.assertIn(url.path, ['hello@team.malektareq.com','privacy@team.malektareq.com']);continue
                        self.assertFalse(url.netloc)
                        path=ROOT/(unquote(url.path).lstrip('/') or file)
                        self.assertTrue(path.is_file())
                        if url.fragment:
                            self.assertIn(url.fragment,[a.get('id') for t,a in load(path.name).tags])
    def test_no_scripts_forms_tracking_or_external_fonts(self):
        for file in ALL:
            for tag,attrs in load(file).tags:
                self.assertNotIn(tag, ['script','iframe','form','input','object','embed'])
                self.assertFalse(any(k.startswith('on') for k in attrs))
        css=(ROOT/'style.css').read_text()
        self.assertNotIn('@import',css); self.assertNotIn('url(',css)
        self.assertNotIn('#235e90', css)
        for ms in (int(n) for n in re.findall(r'(\d+)ms', css)):
            self.assertLessEqual(ms, 150)
        self.assertIn('transition:none!important', css.replace(' ', ''))
    def test_founder_facts(self):
        text={f:' '.join(load(f).text) for f in PAGES}
        self.assertIn('Launching soon', text['index.html']); self.assertIn('We are not taking on clients yet.',text['index.html'])
        self.assertIn('Register your interest', text['index.html']); self.assertIn('Register your interest', text['what-we-do.html'])
        self.assertNotIn('for a quote', text['what-we-do.html'])
        self.assertIn('How 3BC works', text['index.html'])
        for step in ('Defined roles', 'Transparent records', 'Human accountability'): self.assertIn(step, text['index.html'])
        self.assertIn('founded in 2026',text['about.html']);self.assertIn('United Kingdom',text['about.html'])
        self.assertIn('Tariq Mehmood',text['about.html'])
        for person in ['Sarah Malik','Daniel Hayes','Omar Rahman','Rida Nasser','Amira Hassan','Nadia Karim','Layla Haddad','Arjun Thakker','Pedro Alfanso','Charlotte Theron','Chair (advisory board)','Strategy Director (advisory board)']:self.assertIn(person,text['about.html'])
        self.assertIn('We reply within 2 business days',text['contact.html']);self.assertIn('London, United Kingdom',text['contact.html'])
        self.assertIn('hello@team.malektareq.com', text['contact.html']); self.assertIn('privacy@team.malektareq.com', text['contact.html'])
        for term in ['UK GDPR',"Information Commissioner's Office",'EU GDPR','Irish Data Protection Commission']:self.assertIn(term,text['privacy.html'])
        self.assertIn('courts are those of England and Wales',text['terms.html'])
    def test_cork_type_and_spacing_tokens(self):
        css=(ROOT/'style.css').read_text().replace(' ', '')
        for token in ('font:17px/1.6', 'font-size:20px', 'clamp(36px,6vw,56px)', 'line-height:1.05',
                      'font-size:28px', 'font-size:22px', 'max-width:68ch', 'flex:0028px', 'width:28px',
                      'background:var(--accent)', 'color:var(--accent-ink)', 'margin-top:96px', 'margin-top:56px',
                      '150ms'):
            self.assertIn(token, css)
        self.assertNotIn('filter:brightness', css)
    def test_404_links_are_root_absolute(self):
        for tag,attrs in load('404.html').tags:
            if 'href' in attrs:self.assertTrue(attrs['href'].startswith(('/', '#','mailto:')))
    def test_existing_domain_unchanged(self):self.assertEqual((ROOT/'CNAME').read_text().strip(),'3bc.ie')
    def test_review_notes_are_not_a_published_file(self):
        self.assertFalse((ROOT/'REVIEW.txt').exists())
        self.assertFalse(any(p.name.lower().startswith('review') for p in ROOT.iterdir()))
        self.assertTrue((ROOT/'style.css').read_text().startswith('/* 3BC site styles */\n'))
if __name__=='__main__':unittest.main(verbosity=2)
