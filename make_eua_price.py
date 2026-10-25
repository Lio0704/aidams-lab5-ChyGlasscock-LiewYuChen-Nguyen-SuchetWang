import sys, glob, re, warnings, pandas as pd
warnings.filterwarnings('ignore')
d, out = sys.argv[1], sys.argv[2]
rows=[]
for f in sorted(glob.glob(d+'/*')):
    raw=pd.read_excel(f, sheet_name='Primary Market Auction', header=None)
    hr=[i for i in range(15) if raw.iloc[i].astype(str).str.contains('Auction Price').any()][0]
    df=raw.iloc[hr+1:].copy(); df.columns=[str(c).strip() for c in raw.iloc[hr]]
    col=lambda k:[c for c in df.columns if c.startswith(k)][0]
    sub=pd.DataFrame({'date':pd.to_datetime(df[col('Date')],errors='coerce'),
        'contract':df[col('Contract')].astype(str),
        'price':pd.to_numeric(df[col('Auction Price')],errors='coerce'),
        'vol':pd.to_numeric(df[col('Auction Volume')],errors='coerce')})
    if 'Status' in df.columns: sub=sub[df['Status'].astype(str).str.lower().str.startswith('success').values]
    rows.append(sub.dropna(subset=['date','price','vol']))
a=pd.concat(rows); a['year']=a.date.dt.year
print(a.contract.value_counts().head(10))
a['is_aviation']=a.contract.str.upper().str.startswith('EAA')
g=a[~a.is_aviation].groupby('year')
res=pd.DataFrame({'eua_price_vwap':g.apply(lambda x:(x.price*x.vol).sum()/x.vol.sum()),
                  'eua_price_mean':g.price.mean(),'n_auctions':g.size()})
ga=a[a.is_aviation].groupby('year')
res['euaa_price_mean']=ga.price.mean()
res=res.round(2); print(res.to_string()); res.to_csv(out)
