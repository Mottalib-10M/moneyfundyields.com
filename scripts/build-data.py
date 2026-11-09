#!/usr/bin/env python3
"""Turn the raw SEC and Treasury downloads (data/raw/, see fetch-nmfp.sh) into the site's data files.

  src/data/funds.json    every share class open to individual investors (ticker on file, minimum initial
                         investment as filed of $100,000 or less, government fund or fund flagged retail)
  src/data/history.json  daily 7-day net yields of the share classes that have their own page
  src/data/tbills.json   latest Treasury bill rates (coupon-equivalent) and their date

Rerun: python3 -I scripts/build-data.py   (reads data/raw/, writes src/data/)
"""
import csv, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'data', 'raw')
OUT = os.path.join(ROOT, 'src', 'data')

# Share classes with a page of their own (a ticker people search for). Order = order on the site.
PAGE_TICKERS = ['VMFXX', 'VUSXX', 'VMRXX', 'VMSXX', 'VCTXX', 'VYFXX',
                'SPAXX', 'FDRXX', 'FZFXX', 'FDLXX', 'SPRXX', 'FZDXX', 'FTEXX',
                'SWVXX', 'SNSXX', 'SNOXX', 'SNVXX', 'SWTXX']
STATES = {'California': 'CA', 'New York': 'NY', 'Massachusetts': 'MA', 'New Jersey': 'NJ', 'Pennsylvania': 'PA',
          'Connecticut': 'CT', 'Ohio': 'OH', 'Michigan': 'MI', 'Virginia': 'VA', 'Minnesota': 'MN', 'Arizona': 'AZ',
          'Maryland': 'MD', 'North Carolina': 'NC', 'Oregon': 'OR', 'Georgia': 'GA', 'Missouri': 'MO'}

dera = sorted(d for d in os.listdir(RAW) if d.startswith('dera-'))
merged = os.path.join(RAW, 'nmfp-merged.json')
subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'scripts', 'nmfp_parse.py'), merged,
                os.path.join(RAW, 'tickers', 'company_tickers_mf.json'), os.path.join(RAW, 'edgar')]
               + [os.path.join(RAW, d) for d in dera], check=True)
d = json.load(open(merged))
S, C, Y, G, CO, T = d['series'], d['classes'], d['yields'], d['gross'], d['comp'], d['tickers']

latest_rep = max(s['reportDate'] for s in S.values())
month = latest_rep[:7]
from collections import Counter
_qc = Counter(r for c in CO.values() for r in c if r[5:7] in ('03', '06', '09', '12'))
# Quarter ends that a full monthly data set covers (a stray amended filing does not make a quarter).
QUARTERS = sorted(r for r, n in _qc.items() if n >= 100)


def shares(comp):
    tot = sum(comp.values()) or 1
    return {k: round(v / tot, 4) for k, v in sorted(comp.items())}


def usob(comp):
    s = shares(comp)
    return round(s.get('tsy', 0) + s.get('agyExempt', 0), 4)


def kind(series, fund):
    cat = series['category']
    if cat == 'Single State': return 'state-muni'
    if cat == 'Other Tax Exempt': return 'muni'
    if cat == 'Prime': return 'prime'
    sh = shares(CO[series['seriesId']].get(series['reportDate'], {}))
    if sh.get('tsy', 0) >= 0.99: return 'treasury-only'
    if sh.get('tsy', 0) + sh.get('tsyRepo', 0) >= 0.99: return 'treasury'
    return 'government'


def fund_state(name):
    for k, v in STATES.items():
        if k.lower() in name.lower(): return v
    return None


funds = []
for cid, c in C.items():
    s = S.get(c['seriesId'])
    if not s or s['reportDate'][:7] != month: continue
    tk = T.get(cid) or []
    if not tk: continue
    mi = c['minInitial']
    if mi is None or mi > 100000: continue
    if s['category'] != 'Government' and s['retailFlag'] != 'Y': continue
    if not c['classAssets'] or c['classAssets'] < 50e6: continue
    ys = Y.get(cid) or {}
    if not ys: continue
    yd = max(ys)
    gs = G.get(c['seriesId']) or {}
    comp = CO[c['seriesId']].get(s['reportDate'], {})
    k = kind(s, s['fund'])
    tick = sorted(tk, key=lambda t: (t not in PAGE_TICKERS, len(t), t))[0]
    funds.append(dict(
        t=tick, cid=cid, sid=c['seriesId'], name=s['fund'], cls=c['className'], reg=s['registrant'],
        cat=s['category'], k=k, st=fund_state(s['fund']) if k == 'state-muni' else None,
        min=mi, assets=round(c['classAssets']), fundAssets=round(s['seriesAssets'] or 0),
        y=ys[yd], yDate=yd, g=gs.get(yd), wam=s['wam'], wal=s['wal'],
        comp=shares(comp), usob=usob(comp),
        q={},
        rep=s['reportDate'], filed=s['filingDate'], acc=s['accession'],
    ))
# Quarter-end dates differ by a day or two between funds (last business day): match by month.
for f in funds:
    byMonth = {r[:7]: r for r in CO[f['sid']]}
    f['q'] = {q[:7]: usob(CO[f['sid']][byMonth[q[:7]]]) for q in QUARTERS if q[:7] in byMonth}
funds.sort(key=lambda f: -f['assets'])
missing = [t for t in PAGE_TICKERS if t not in {f['t'] for f in funds}]
if missing: sys.exit(f'page funds missing from the data: {missing}')

hist = {}
for t in PAGE_TICKERS:
    f = next(x for x in funds if x['t'] == t)
    ys = Y[f['cid']]
    hist[t] = [[k, ys[k]] for k in sorted(ys)]

rows = list(csv.DictReader(open(os.path.join(RAW, 'treasury', 'bills.csv'))))
last = rows[0]
m, dd, yy = last['Date'].split('/')
tb = dict(date=f'{yy}-{m}-{dd}', w4=float(last['4 WEEKS COUPON EQUIVALENT']) / 100,
          w13=float(last['13 WEEKS COUPON EQUIVALENT']) / 100, w26=float(last['26 WEEKS COUPON EQUIVALENT']) / 100,
          w52=float(last['52 WEEKS COUPON EQUIVALENT']) / 100,
          source='https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_bill_rates&field_tdr_date_value=2026')

meta = dict(month=latest_rep, quarters=sorted({q[:7] for q in QUARTERS}), classes=len(funds),
            series=len({f['sid'] for f in funds}), filedFrom=min(f['filed'] for f in funds if f['rep'][:7] == month),
            filedTo=max(f['filed'] for f in funds if f['rep'][:7] == month),
            firstYieldDate=min(k for t in hist for k, _ in hist[t]), dera=[x[5:] for x in dera])
json.dump(dict(meta=meta, funds=funds), open(os.path.join(OUT, 'funds.json'), 'w'), separators=(',', ':'))
json.dump(hist, open(os.path.join(OUT, 'history.json'), 'w'), separators=(',', ':'))
json.dump(tb, open(os.path.join(OUT, 'tbills.json'), 'w'), indent=1)
print(json.dumps(meta), len(funds), 'classes')
