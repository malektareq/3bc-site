"""Dependency-free checks for the buildless, review-only 3BC site."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote
import unittest
ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'services.html', 'about.html', 'contact.html', 'privacy.html', 'terms.html', '404.html']
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True); self.tags=[]; self.text=[]; self.feed(text)
    def handle_starttag(self, tag, attrs): self.tags.append((tag, dict(attrs)))
    def handle_data(self, data): self.text.append(data)
class SiteTests(unittest.TestCase):
    def test_exact_seven_pages_and_single_stylesheet(self):
        self.assertEqual(sorted(p.name for p in ROOT.glob('*.html')), sorted(PAGES))
        self.assertEqual([p.name for p in ROOT.glob('*.css')], ['style.css'])
    def test_every_page_has_accessible_structure_and_release_hold(self):
        titles=[]
        for file in PAGES:
            with self.subTest(page=file):
                page=Page((ROOT/file).read_text()); tags=page.tags; text=' '.join(page.text)
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
    def test_all_internal_links_fragments_and_assets_exist(self):
        for file in PAGES:
            page=Page((ROOT/file).read_text())
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
                            self.assertIn(url.fragment,[a.get('id') for t,a in Page(path.read_text()).tags])
    def test_no_scripts_forms_tracking_or_external_fonts(self):
        for file in PAGES:
            for tag,attrs in Page((ROOT/file).read_text()).tags:
                self.assertNotIn(tag, ['script','iframe','form','input','object','embed'])
                self.assertFalse(any(k.startswith('on') for k in attrs))
        css=(ROOT/'style.css').read_text()
        self.assertNotIn('@import',css); self.assertNotIn('url(',css)
    def test_founder_facts_and_mona_copy(self):
        text={f:' '.join(Page((ROOT/f).read_text()).text) for f in PAGES}
        self.assertIn('Launching soon', text['index.html']); self.assertIn('We are not taking on clients yet.',text['index.html'])
        self.assertIn('Contact us for a quote',text['services.html'])
        self.assertIn('founded in 2026',text['about.html']);self.assertIn('United Kingdom',text['about.html'])
        self.assertIn('Tariq Mehmood',text['about.html']);self.assertNotIn('MAINT',text['about.html']);self.assertNotIn('CIQA',text['about.html'])
        for person in ['Sarah Malik','Daniel Hayes','Omar Rahman','Rida Nasser','Amira Hassan','Nadia Karim','Layla Haddad','Arjun Thakker']:self.assertIn(person,text['about.html'])
        self.assertIn('We reply within 2 business days',text['contact.html']);self.assertIn('London, United Kingdom',text['contact.html'])
        for term in ['UK GDPR',"Information Commissioner's Office",'EU GDPR','Irish Data Protection Commission']:self.assertIn(term,text['privacy.html'])
        self.assertIn('courts are those of England and Wales',text['terms.html'])
    def test_404_links_are_root_absolute(self):
        for tag,attrs in Page((ROOT/'404.html').read_text()).tags:
            if 'href' in attrs:self.assertTrue(attrs['href'].startswith(('/', '#','mailto:')))
    def test_existing_domain_unchanged(self):self.assertEqual((ROOT/'CNAME').read_text().strip(),'3bc.ie')
if __name__=='__main__':unittest.main(verbosity=2)
