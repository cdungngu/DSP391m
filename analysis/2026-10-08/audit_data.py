"""Read-only audit of original Decagon CSVs. Run from project root."""
import json, hashlib, time
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
start = time.time()
paths = {k: ROOT / 'data' / 'decagon' / ('bio-decagon-' + k + '.csv') for k in ('combo','targets','ppi')}
frames = {k: pd.read_csv(p, dtype='category' if k == 'combo' else None) for k,p in paths.items()}
c,t,p = (frames[k] for k in ('combo','targets','ppi'))
result = {'audit_date':'2026-10-08', 'files':{}}
for k,f in frames.items():
 result['files'][k] = {'bytes':paths[k].stat().st_size, 'sha256':hashlib.file_digest(paths[k].open('rb'),'sha256').hexdigest(), 'rows':len(f), 'columns':list(f.columns), 'missing':f.isna().sum().to_dict(), 'exact_duplicates':int(f.duplicated().sum())}
drugs = sorted(set(c.iloc[:,0].astype(str)) | set(c.iloc[:,1].astype(str)))
dmap={d:i for i,d in enumerate(drugs)}
a=c.iloc[:,0].astype(str).map(dmap).to_numpy(np.int32)
b=c.iloc[:,1].astype(str).map(dmap).to_numpy(np.int32)
pair=np.minimum(a,b).astype(np.int64)*len(drugs)+np.maximum(a,b)
r=c.iloc[:,2].cat.codes.to_numpy(np.int64)
key=pair*c.iloc[:,2].nunique()+r
unique,counts=np.unique(key,return_counts=True)
pair_counts=pd.Series(pair).value_counts()
freq=c.iloc[:,2].value_counts()
names=c.iloc[:,[2,3]].drop_duplicates()
names.columns=['effect_id','effect_name']
names['rows']=names.effect_id.map(freq).astype(int)
names.sort_values('rows',ascending=False).to_csv(OUT/'effect_frequencies.csv',index=False)
result['combo']={'drugs':len(drugs),'effects':int(c.iloc[:,2].nunique()), 'names':int(c.iloc[:,3].nunique()), 'distinct_effect_name_pairs':len(names), 'unordered_pairs':int(len(pair_counts)), 'self_rows':int((a==b).sum()), 'unique_unordered_triples':len(unique),'duplicate_unordered_triples':len(c)-len(unique),'labels_at_least_500_rows':int((freq>=500).sum()), 'rows_in_labels_at_least_500':int(freq[freq>=500].sum()), 'label_frequency_quantiles':freq.quantile([0,.25,.5,.75,.9,.95,.99,1]).to_dict(), 'labels_per_pair_quantiles':pair_counts.quantile([0,.25,.5,.75,.9,.95,.99,1]).to_dict(), 'top_effects':names.sort_values('rows',ascending=False).head(10).astype({'effect_id':str,'effect_name':str}).to_dict('records')}
targets=defaultdict(set)
for d,g in t.itertuples(index=False,name=None): targets[d].add(int(g))
td=set(targets); cd=set(drugs)
pg=set(p.iloc[:,0])|set(p.iloc[:,1]); tg=set(t.iloc[:,1])
pa=p.iloc[:,0].to_numpy(np.int64);pb=p.iloc[:,1].to_numpy(np.int64)
canonical=np.column_stack([np.minimum(pa,pb),np.maximum(pa,pb)])
unique_pp=np.unique(canonical,axis=0)
adj=defaultdict(set)
for x,y in unique_pp:
 if x!=y: adj[int(x)].add(int(y));adj[int(y)].add(int(x))
degree=pd.Series({g:len(v) for g,v in adj.items()})
result['targets']={'drugs':len(td),'genes':len(tg),'combo_drugs_with_targets':len(td&cd),'combo_drugs_without_targets':len(cd-td),'target_only_drugs':len(td-cd),'target_genes_in_ppi':len(tg&pg),'target_genes_not_in_ppi':len(tg-pg),'targets_per_drug_quantiles':pd.Series({d:len(v) for d,v in targets.items()}).quantile([0,.5,.9,.95,.99,1]).to_dict()}
result['ppi']={'genes':len(pg),'unordered_edges_including_loops':len(unique_pp),'self_rows':int((pa==pb).sum()),'duplicate_or_reverse_rows':len(p)-len(unique_pp),'degree_quantiles':degree.quantile([0,.5,.9,.95,.99,1]).to_dict(),'top_degrees':degree.nlargest(10).to_dict()}
np.random.seed(391)
sampling={}
for k in (3,5,10):
 rows=[]
 for _ in range(1000):
  regimen=np.random.choice(drugs,k,replace=False)
  ts=[targets.get(d,set()) for d in regimen]
  counter=Counter(g for s in ts for g in s)
  rows.append([sum(bool(s) for s in ts),len(counter),sum(v>=3 for v in counter.values()),sum(pair_counts.get(min(dmap[x],dmap[y])*len(drugs)+max(dmap[x],dmap[y]),0) for i,x in enumerate(regimen) for y in regimen[i+1:])])
 x=np.array(rows)
 sampling[k]={'uniform_random_regimens':len(rows),'all_drugs_have_targets_rate':float(np.mean(x[:,0]==k)),'any_shared_target_at_least_3_rate':float(np.mean(x[:,2]>0)),'union_targets_median':float(np.median(x[:,1])),'known_pairwise_label_rows_median':float(np.median(x[:,3])),'known_pairwise_label_rows_p95':float(np.quantile(x[:,3],.95))}
result['retrieval_synthetic_probe']=sampling
pd.DataFrame([{'drug_id':d,'targets':len(targets.get(d,set())),'has_target':d in td} for d in drugs]).to_csv(OUT/'drug_target_coverage.csv',index=False)
result['seconds']=round(time.time()-start,2)
(OUT/'data_audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,default=int))
print(json.dumps(result,indent=2,ensure_ascii=False,default=int))
