"""Audit downloaded source releases without modifying them."""
import ast, hashlib, json
from pathlib import Path
import pandas as pd
from collections import Counter
O=Path(__file__).resolve().parent
S=O/'sources'
out={'date':'2026-10-08','hoddi_commit':'700d0dafc74810fae3d06b1871b20a0f1df60646'}
cov=pd.read_csv(O/'drug_target_coverage.csv')
t=pd.read_csv(S/'bio-decagon-targets-all.csv')
m=pd.read_csv(S/'bio-decagon-mono.csv')
out['targets_all']={'rows':len(t),'drugs':t.iloc[:,0].nunique(),'genes':t.iloc[:,1].nunique(),'combo_drugs_covered':len(set(cov.drug_id)&set(t.iloc[:,0]))}
out['mono']={'rows':len(m),'drugs':m.iloc[:,0].nunique(),'effects':m.iloc[:,1].nunique(),'combo_drugs_covered':len(set(cov.drug_id)&set(m.iloc[:,0]))}
frames={}
for n in ('pos','neg'):
 p=S/f'hoddi_v1_{n}.csv'; f=pd.read_csv(p,dtype={'report_id':str})
 f['drugs']=f.DrugBankID.map(ast.literal_eval)
 f['canonical']=f.drugs.map(lambda x:tuple(sorted(set(x))))
 f['k']=f.canonical.map(len)
 f['record_key']=list(zip(f.canonical,f['SE_above_0.9']))
 f['source_id']=f.report_id.str.replace(r'n$','',regex=True)
 frames[n]=f
 out[n]={'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),'rows':len(f),'unique_report_id':f.report_id.nunique(),'time_min':f.time.min(),'time_max':f.time.max(),'unique_drugs':len(set(d for row in f.canonical for d in row)),'unique_effects':f['SE_above_0.9'].nunique(),'rows_repeated_drug_inside_list':int((f.drugs.map(len)>f.k).sum()),'k_counts':f.k.value_counts().sort_index().to_dict(),'unique_canonical_regimens':f.canonical.nunique(),'duplicate_canonical_regimen_effect_rows':int(f.record_key.duplicated().sum()),'missing':f.iloc[:,:6].isna().sum().to_dict()}
pos,neg=frames['pos'],frames['neg']
ps=set(d for row in pos.canonical for d in row);ns=set(d for row in neg.canonical for d in row)
se=set(pos['SE_above_0.9'])
out['shortcut_check_full_release']={'negative_only_drugs':len(ns-ps),'negative_rows_with_any_drug_absent_from_all_positives':int(neg.canonical.map(lambda ds:any(d not in ps for d in ds)).sum()),'negative_rows_effect_absent_from_all_positives':int((~neg['SE_above_0.9'].isin(se)).sum()),'overlapping_positive_negative_canonical_keys':len(set(pos.record_key)&set(neg.record_key)),'source_ids_shared_pos_neg':len(set(pos.source_id)&set(neg.source_id))}
# Diagnostic protocol for recommendations, not a model performance experiment.
for n,f in frames.items():
 train=f[f.time<='2021Q4'];test=f[f.time>='2023Q1']
 out[n]['temporal_diagnostic']={'train_rows_through_2021Q4':len(train),'test_rows_from_2023Q1':len(test),'test_rows_key_seen_in_train':int(test.record_key.isin(set(train.record_key)).sum()),'test_rows_regimen_seen_in_train':int(test.canonical.isin(set(train.canonical)).sum()),'shared_source_ids':len(set(train.source_id)&set(test.source_id))}
(O/'external_data_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,default=int))
print(json.dumps(out,ensure_ascii=False,indent=2,default=int))
