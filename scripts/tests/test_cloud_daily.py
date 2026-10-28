import importlib.util,json,tempfile,unittest,sys
from pathlib import Path
P=Path(__file__).resolve()
script=P.parents[1]/'cloud_daily.py' if P.parent.name=='tests' else P.with_name('cloud_daily.py')
sys.path.insert(0,str(script.parent))
spec=importlib.util.spec_from_file_location('daily',script);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class DailyTests(unittest.TestCase):
 def setup_root(self,p):
  f=p/'public/ai-daily/content.json';f.parent.mkdir(parents=True);f.write_text(json.dumps({'updated':'old','items':[{'id':'topic','kind':'专题','body':'keep'}]}));return f
 def entries(self):
  return [{'kind':'GitHub','repo':'pgvector/pgvector','title':'repo','url':'https://github.com/pgvector/pgvector/commit/test','published':'2026-10-28','stars':1},{'kind':'论文','title':'paper','url':'https://arxiv.org/abs/test','published':'2026-10-28','summary':'reported result'}]
 def test_preserves_topics_and_same_day_dedup(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);f=self.setup_root(p)
   for _ in range(2):m.update(p,'2026-10-28',self.entries(),[])
   data=json.loads(f.read_text(encoding='utf-8'));self.assertEqual(len(data['items']),2);self.assertEqual(data['items'][1]['body'],'keep');self.assertIn('未实测',data['items'][0]['body'])
 def test_quality_gate_never_overwrites(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);f=self.setup_root(p);before=f.read_bytes()
   with self.assertRaises(AssertionError):m.update(p,'2026-10-28',self.entries()[:1],[])
   self.assertEqual(before,f.read_bytes())
 def test_untrusted_html_is_text(self):
  self.assertEqual(m.plain('<script>do_bad()</script><b>A</b>'),'do_bad() A')
 def test_requires_valid_fresh_date(self):
  self.assertEqual(m.feed_rows(b'<rss><channel><item><title>AI test</title><link>https://example.com</link></item></channel></rss>','官方博客','x'),[])
if __name__=='__main__':unittest.main()
