"""Build funds.json from SEC Form N-MFP data (DERA TSV months + EDGAR N-MFP3 XML for the latest month).
Usage: python3 -I build_data.py <out.json> <tickers.json> <edgar_dir_with_list.txt_and_filings/> <dera_dir>...
Each DERA dir = one unzipped monthly data set. Order: oldest first."""
import csv, json, re, sys, os, collections
import xml.etree.ElementTree as ET

out, tick_path, edgar_dir, dera_dirs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
tick = collections.defaultdict(list)
for row in json.load(open(tick_path))['data']:
    tick[row[2]].append(row[3])

EXEMPT_AGENCY = re.compile(r'federal\s+home\s+loan\s+bank|\bfhlb\b|federal\s+farm\s+credit|\bffcb\b|tennessee\s+valley|\btva\b', re.I)

def bucket(cat, issuer):
    c = cat.lower()
    if c.startswith('u.s. treasury debt'): return 'tsy'
    if c.startswith('u.s. treasury repurchase'): return 'tsyRepo'
    if c.startswith('u.s. government agency debt'):
        return 'agyExempt' if EXEMPT_AGENCY.search(issuer or '') else 'agyOther'
    if c.startswith('u.s. government agency repurchase'): return 'agyRepo'
    if 'repurchase' in c: return 'otherRepo'
    if 'municipal' in c or 'tender option' in c or 'variable rate demand' in c: return 'muni'
    return 'other'

def fnum(s):
    try: return float(str(s).strip())
    except Exception: return None

MON = {m: i+1 for i, m in enumerate('JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'.split())}
def iso(d):
    d = d.strip()
    m = re.match(r'(\d\d)-([A-Z]{3})-(\d{4})', d)
    if m: return f"{m.group(3)}-{MON[m.group(2)]:02d}-{m.group(1)}"
    return d

series = {}   # seriesId -> info (latest)
classes = {}  # classId -> info
yields = collections.defaultdict(dict)   # classId -> {date: net}
gross = collections.defaultdict(dict)
comp_by_month = collections.defaultdict(dict)  # seriesId -> {reportDate: {bucket: pct}}

def add_series(sid, rep, info, comp):
    comp_by_month[sid][rep] = comp
    if sid not in series or rep >= series[sid]['reportDate']:
        series[sid] = dict(info, reportDate=rep)

# ---- DERA monthly data sets
for d in dera_dirs:
    rd = lambda n: list(csv.DictReader(open(f"{d}/NMFP_{n}.tsv", encoding='latin-1'), delimiter='\t'))
    sub = rd('SUBMISSION')
    # latest filing per (series, reportDate): prefer amendments filed later
    best = {}
    for r in sub:
        k = (r['SERIESID'], r['REPORTDATE'])
        if k not in best or (r['FILING_DATE'], r['ACCESSION_NUMBER']) > (best[k]['FILING_DATE'], best[k]['ACCESSION_NUMBER']):
            best[k] = r
    keep = {r['ACCESSION_NUMBER']: r for r in best.values()}
    ser = {r['ACCESSION_NUMBER']: r for r in rd('SERIESLEVELINFO') if r['ACCESSION_NUMBER'] in keep}
    comp = collections.defaultdict(lambda: collections.Counter())
    for r in rd('SCHPORTFOLIOSECURITIES'):
        if r['ACCESSION_NUMBER'] in keep:
            p = fnum(r['PERCENTAGEOFMONEYMARKETFUNDNET']) or 0
            comp[r['ACCESSION_NUMBER']][bucket(r['INVESTMENTCATEGORY'], r['NAMEOFISSUER'])] += p
    for acc, r in keep.items():
        s = ser.get(acc)
        if not s: continue
        rep = iso(r['REPORTDATE'])
        info = dict(seriesId=r['SERIESID'], fund=r['NAMEOFSERIES'].strip(), registrant=r['REGISTRANTFULLNAME'].strip(),
                    category=s['MONEYMARKETFUNDCATEGORY'], retailFlag=s['FUNDRETAILMONEYMARKETFLAG'],
                    wam=fnum(s['AVERAGEPORTFOLIOMATURITY']), wal=fnum(s['AVERAGELIFEMATURITY']),
                    seriesAssets=fnum(s['NETASSETOFSERIES']), accession=acc, filingDate=iso(r['FILING_DATE']),
                    source='dera')
        add_series(r['SERIESID'], rep, info, {k: round(v, 4) for k, v in comp[acc].items()})
    cl_acc = {}
    for c in rd('CLASSLEVELINFO'):
        acc = c['ACCESSION_NUMBER']
        if acc not in keep: continue
        sid = keep[acc]['SERIESID']; rep = iso(keep[acc]['REPORTDATE'])
        cid = c['CLASSESID']
        if cid not in classes or rep >= classes[cid]['reportDate']:
            classes[cid] = dict(classId=cid, seriesId=sid, className=c['CLASSFULLNAME'].strip(),
                                minInitial=fnum(c['MININITIALINVESTMENT']), classAssets=fnum(c['NETASSETSOFCLASS']), reportDate=rep)
    for y in rd('SEVENDAYNETYIELD'):
        if y['ACCESSION_NUMBER'] in keep:
            v = fnum(y['SEVENDAYNETYIELDVALUE'])
            if v is not None: yields[y['CLASSESID']][iso(y['SEVENDAYNETYIELDDATE'])] = v
    gpath = f"{d}/NMFP_SEVENDAYGROSSYIELD.tsv"
    for y in csv.DictReader(open(gpath, encoding='latin-1'), delimiter='\t'):
        if y['ACCESSION_NUMBER'] in keep:
            # series-level gross yield table
            v = fnum(y.get('SEVENDAYGROSSYIELDVALUE'))
            dt = y.get('SEVENDAYGROSSYIELDDATE')
            if v is not None and dt: gross[keep[y['ACCESSION_NUMBER']]['SERIESID']][iso(dt)] = v

# ---- EDGAR N-MFP3 XML (latest month)
dates = {}
for line in open(os.path.join(edgar_dir, 'index-lines.txt')):
    p = line.split()
    dates[os.path.basename(p[-1])] = f"{p[-2][:4]}-{p[-2][4:6]}-{p[-2][6:]}"
NS = '{http://www.sec.gov/edgar/nmfp3}'
def tx(e, path):
    x = e.find(path.replace('/', '/' + NS).join(['', '']) if False else NS + path.replace('/', '/' + NS))
    return x.text.strip() if x is not None and x.text else None
latest_edgar = {}
for f in sorted(os.listdir(os.path.join(edgar_dir, 'filings'))):
    t = open(os.path.join(edgar_dir, 'filings', f), errors='ignore').read()
    m = re.search(r'<XML>\s*(.*?)\s*</XML>', t, re.S)
    if not m: continue
    root = ET.fromstring(m.group(1).encode())
    fd = root.find(NS + 'formData')
    g = fd.find(NS + 'generalInfo'); s = fd.find(NS + 'seriesLevelInfo')
    sid = tx(g, 'seriesId'); rep = tx(g, 'reportDate')
    acc = f.replace('.txt', '')
    k = (sid, rep)
    if k in latest_edgar and latest_edgar[k] > acc: continue
    latest_edgar[k] = acc
    comp = collections.Counter()
    for sec in fd.findall(NS + 'scheduleOfPortfolioSecuritiesInfo'):
        p = fnum(tx(sec, 'percentageOfMoneyMarketFundNetAssets')) or 0
        comp[bucket(tx(sec, 'investmentCategory') or '', tx(sec, 'nameOfIssuer') or '')] += p
    info = dict(seriesId=sid, fund=tx(g, 'nameOfSeries'), registrant=tx(g, 'registrantFullName'),
                category=tx(s, 'moneyMarketFundCategory'), retailFlag=tx(s, 'fundRetailMoneyMarketFlag') or '',
                wam=fnum(tx(s, 'averagePortfolioMaturity')), wal=fnum(tx(s, 'averageLifeMaturity')),
                seriesAssets=fnum(tx(s, 'netAssetOfSeries')), accession=acc, filingDate=dates.get(f), source='edgar')
    add_series(sid, rep, info, {k2: round(v, 4) for k2, v in comp.items()})
    for gy in s.findall(NS + 'sevenDayGrossYield'):
        v = fnum(tx(gy, 'sevenDayGrossYieldValue')); dt = tx(gy, 'sevenDayGrossYieldDate')
        if v is not None and dt: gross[sid][dt] = v
    for c in fd.findall(NS + 'classLevelInfo'):
        cid = tx(c, 'classesId')
        if cid not in classes or rep >= classes[cid]['reportDate']:
            classes[cid] = dict(classId=cid, seriesId=sid, className=tx(c, 'classFullName'),
                                minInitial=fnum(tx(c, 'minInitialInvestment')), classAssets=fnum(tx(c, 'netAssetsOfClass')), reportDate=rep)
        for y in c.findall(NS + 'sevenDayNetYield'):
            v = fnum(tx(y, 'sevenDayNetYieldValue')); dt = tx(y, 'sevenDayNetYieldDate')
            if v is not None and dt: yields[cid][dt] = v

json.dump(dict(series=series, classes=classes, yields=yields, gross=gross, comp=comp_by_month, tickers={c: tick.get(c, []) for c in classes}),
          open(out, 'w'))
print('series', len(series), 'classes', len(classes), 'with yields', sum(1 for c in classes if yields.get(c)))
