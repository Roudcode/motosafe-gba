from pathlib import Path
import sys,json,hashlib,importlib.util
import pandas as pd,joblib,numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report,accuracy_score,f1_score
root=Path.cwd(); sys.path.insert(0,str(root/'notebooks'))
from reentrenar_modelo import cargar_motos_extendido
base=cargar_motos_extendido()
ind=pd.read_csv(root/'backend/indice_inseguridad_comuna.csv');ind['comuna']=ind['comuna'].astype(str)
base=base.merge(ind[['comuna','indice_inseguridad']],on='comuna',how='left');base['indice_inseguridad']=base['indice_inseguridad'].fillna(ind.indice_inseguridad.mean())
cat=['dia_semana','comuna','tipo_de_via_siniestro','contraparte_siniestro','sexo_victima','lluvia'];num=['hora','temperatura','humedad','indice_inseguridad']
model=joblib.load(root/'backend/modelo_final.pkl'); cols=joblib.load(root/'backend/columnas_modelo.pkl')
X=pd.get_dummies(base[num+cat],columns=cat).reindex(columns=cols,fill_value=0);y=base.gravedad_siniestro
xt,xv,yt,yv=train_test_split(X,y,test_size=.2,random_state=42,stratify=y);p=model.predict(xv)
r={'model_sha256':hashlib.sha256((root/'backend/modelo_final.pkl').read_bytes()).hexdigest(),'config':model.get_params(),'features':cols,'population':len(base),'train':len(xt),'test':len(xv),'accuracy':accuracy_score(yv,p),'f1_macro':f1_score(yv,p,average='macro'),'report':classification_report(yv,p,output_dict=True),'layers':{f:len(pd.read_csv(root/'data'/f)) for f in ['hotspots_moto_caba.csv','hotspots_inseguridad_general.csv','hotspots_inseguridad_moto.csv','corredores_riesgo.csv']}}
cost=np.array([620,682,750,825,908]); inc=np.array([0,1200,3200,5400,7900]); factors=1.17**np.arange(1,6)
npv=lambda i,c: float(-5640+sum((i-c)/factors))
lo,hi=0.,1.
for _ in range(80):
 mid=(lo+hi)/2
 if -5640+sum((inc-cost)/(1+mid)**np.arange(1,6))>0:lo=mid
 else:hi=mid
r['finance']={'npv_base':npv(inc,cost),'irr':mid,'npv_costs_plus20':npv(inc,cost*1.2),'npv_income_minus20':npv(inc*.8,cost),'npv_optimistic':npv(inc*1.2,cost),'npv_pessimistic':npv(inc*.8,cost*1.2),'discounted_flows':((inc-cost)/factors).tolist(),'internal_f1_gap_pp':(.368-.3032)*100}
print(json.dumps(r,indent=2,ensure_ascii=False))
Path(__file__).with_name('verificaciones.json').write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf-8')
