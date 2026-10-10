"""Diagnostic of artificial-negative shortcuts; not a drug prediction model."""
import ast,json
from pathlib import Path
import pandas as pd
O=Path(__file__).resolve().parent
rows=[]
for n in ('pos','neg'):
 f=pd.read_csv(O/'sources'/f'hoddi_v1_{n}.csv',dtype={'report_id':str})
 f['drugs']=f.DrugBankID.map(lambda s:set(ast.literal_eval(s)))
 f['k']=f.drugs.map(len)
 f['source']=f.report_id.str.replace(r'n$','',regex=True)
 rows.append(f)
f=pd.concat(rows,ignore_index=True); result={}
for scope in ['all','3_to_5']:
 x=f if scope=='all' else f[f.k.between(3,5)]
 train=x[x.time<='2021Q4']; test=x[x.time>='2023Q1']
 test=test[~test.source.isin(set(train.source))]
 vocab=set(d for ds in train[train.hyperedge_label==1].drugs for d in ds)
 pred=test.drugs.map(lambda ds:all(d in vocab for d in ds))
 y=test.hyperedge_label==1
 tp=int((pred&y).sum()); tn=int((~pred&~y).sum());fp=int((pred&~y).sum());fn=int((~pred&y).sum())
 balanced=.5*(tp/(tp+fn)+tn/(tn+fp))
 result[scope]={'train_rows':len(train),'test_rows_after_source_overlap_purge':len(test),'test_positives':int(y.sum()),'test_negatives':int((~y).sum()),'positive_training_drug_vocabulary':len(vocab),'rule':'positive iff every drug appeared in positive training rows; no chemistry, proteins, or event identity','TP':tp,'TN':tn,'FP':fp,'FN':fn,'accuracy':(tp+tn)/len(test),'balanced_accuracy':balanced,'auroc_binary_score':balanced}
(O/'hoddi_shortcut_probe.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
