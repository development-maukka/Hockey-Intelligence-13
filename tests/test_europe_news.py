import unittest, datetime
from europe_news import parse_shn, parse_jatko, report_kind, transfer_status, recent_unique, collect_coverage, national_league_report

SHN='<div class="timeline"><article><h4 class="raxo-title"><a href="/en/shn/men/swiss-hockey/nl/a">HC Davos signs a player</a></h4><span class="raxo-date">27.11.2026</span></article><article><h4 class="raxo-title"><a href="/en/shn/men/swiss-hockey/sl/b">Swiss League story</a></h4><span class="raxo-date">27.11.2026</span></article></div>'
JATKO='<div class="article-list-item"><a class="article-list-item--link" href="/Uutiset/test/1"><div class="article-list-item--title">TPS:n pelaaja joutuu leikkaukseen</div><time datetime="2026-11-27T12:00:00+02:00"></time></a></div>'

class NewsTests(unittest.TestCase):
 def test_league_scope_and_date(self):
  r=parse_shn(SHN);self.assertEqual(len(r),1);self.assertEqual(r[0]['date'],'2026-11-27')
 def test_jatko_metadata(self):
  r=parse_jatko(JATKO)[0];self.assertEqual(r['source'],'Jatkoaika');self.assertEqual(r['language'],'fi')
 def test_classification(self):
  self.assertTrue(report_kind('Leikkauksessa käynyt Joona Ikonen joutuu kuukausiksi sivuun')[0])
  self.assertTrue(report_kind('Teemu Engberg solmi kaksivuotisen jatkon Ilvekseen')[1])
  self.assertFalse(report_kind('Liiga vahvistaa: Tässä on ensi kauden sarjamalli')[1])
  self.assertFalse(report_kind('Devils player suspended')[0])
  self.assertEqual(transfer_status('Player to reportedly join club'),'rumour')
  self.assertEqual(transfer_status('Club extends player contract'),'report')
 def test_medical_scope(self):
  self.assertFalse(national_league_report('EHC Olten without Manuel von Rohr',[],[]))
  self.assertTrue(national_league_report('Injury of Asplund not too severe',[],[{'player_name':'Rasmus Asplund'}]))
 def test_stale_future_duplicates(self):
  now=datetime.datetime(2026,11,27,tzinfo=datetime.timezone.utc)
  rows=[dict(title='A',url='https://example/a',date=d) for d in ['2026-11-26','2026-11-26','2026-01-01','2026-11-28']]
  self.assertEqual(len(recent_unique(rows,now)),1)
 def test_failed_fetch(self):
  def fail(url):raise TimeoutError()
  r=collect_coverage('liiga',datetime.datetime.now(datetime.timezone.utc),fetch=fail)
  self.assertTrue(all(x['status']=='error' for x in r.values()))
 def test_fetch_reuse_and_empty_category(self):
  calls=[]
  def page(url):calls.append(url);return JATKO.replace('TPS:n pelaaja joutuu leikkaukseen','Ottelun ennakko')
  r=collect_coverage('liiga',datetime.datetime(2026,11,27,tzinfo=datetime.timezone.utc),fetch=page)
  self.assertEqual(len(calls),1);self.assertEqual(r['transactions']['status'],'ok');self.assertEqual(r['transactions']['items'],[])
 def test_changed_layout(self):
  with self.assertRaises(ValueError):parse_shn('<html>Changed layout</html>')
  with self.assertRaises(ValueError):parse_jatko('<html>Changed layout</html>')

 def test_liiga_publisher_fallback(self):
  calls=[]
  html='<div class="description"><div class="title"><a href="https://www.suomikiekko.com/2026/11/test/">TPS:n tähtihankinta leikkauspöydälle</a></div><time class="publish" datetime="2026-11-27T18:30:00+02:00"></time></div>'
  def fetch(url):
   calls.append(url)
   if 'jatkoaika' in url:raise ConnectionError()
   return html
  r=collect_coverage('liiga',datetime.datetime(2026,11,27,tzinfo=datetime.timezone.utc),fetch=fetch)
  self.assertEqual(len(calls),2)
  self.assertTrue(all(x['status']=='ok' for x in r.values()))
  self.assertEqual(r['injuries']['items'][0]['source'],'SuomiKiekko')
  self.assertEqual(r['transactions']['items'],[])
