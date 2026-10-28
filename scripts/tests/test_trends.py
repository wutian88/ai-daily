import sys,unittest,datetime as dt
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from trends import record,change,label,ranking,due_rankings
class TrendTests(unittest.TestCase):
 def test_exact_seven_days(self):
  s={'r':{'2026-10-21':100,'2026-10-28':130}}
  self.assertEqual(change(s,'r','2026-10-28'),30)
 def test_missing_day_not_nearest(self):
  s={'r':{'2026-10-20':100,'2026-10-28':130}}
  self.assertIsNone(change(s,'r','2026-10-28'));self.assertIn('已有 2 天',label(s,'r','2026-10-28'))
 def test_negative_growth(self):
  self.assertEqual(change({'r':{'2026-10-21':100,'2026-10-28':90}},'r','2026-10-28'),-10)
 def test_rankings_insufficient(self):
  for period in ['周','月']:self.assertIn('数据不足',ranking({'r':{'2026-11-01':99}},'2026-11-01',period))
 def test_calendar_month(self):
  self.assertIn('+12',ranking({'r':{'2026-10-01':20,'2026-11-01':32}},'2026-11-01','月'))
 def test_sunday_and_first(self):
  self.assertEqual([p for p,_ in due_rankings({},'2026-11-01')],['周','月'])
 def test_trim_45_days(self):
  end=dt.date(2026,10,28);rows={(end-dt.timedelta(days=i)).isoformat():100 for i in range(60)}
  out=record({'r':rows},end.isoformat(),{'r':110},['r']);self.assertEqual(len(out['r']),45);self.assertEqual(out['r'][end.isoformat()],110)
 def test_cap_and_today_overwrite(self):
  names=[str(i) for i in range(50)];out=record({},'2026-10-28',{n:3 for n in names},names);self.assertEqual(len(out),30)
 def test_sufficient_ranking_orders_signed_growth(self):
  s={'a':{'2026-10-21':100,'2026-10-28':95},'b':{'2026-10-21':30,'2026-10-28':40}}
  text=ranking(s,'2026-10-28','周');self.assertLess(text.index('b：+10'),text.index('a：-5'))
if __name__=='__main__':unittest.main()
