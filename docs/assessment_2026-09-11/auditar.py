"""Auditoria local de solo lectura del proyecto; no entrena ni escribe en DB."""
import ast
import contextlib
import hashlib
import importlib.metadata as md
import io
import json
import sys
import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET
import zipfile

warnings.filterwarnings('ignore', category=DeprecationWarning)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT / 'notebooks'))
import pandas as pd
import joblib
import numpy as np

out = {'versions': {}, 'csv': {}, 'syntax': {}, 'notebook': {}, 'artifacts': {}, 'checks': {}, 'docx': {}}
for pkg in ['fastapi','pydantic','pandas','numpy','scikit-learn','joblib','httpx','psycopg2-binary','slowapi','pytest','seaborn','h3','scipy']:
    try: out['versions'][pkg] = md.version(pkg)
    except md.PackageNotFoundError: out['versions'][pkg] = 'NO INSTALADO'
for p in sorted(ROOT.glob('data/*.csv')):
    sep = ';' if p.name.startswith('siniestros_viales_') else ','
    df = pd.read_csv(p, sep=sep, low_memory=False)
    rec = {'rows':len(df), 'columns':df.columns.tolist(), 'duplicates':int(df.duplicated().sum()), 'nulls':{k:int(v) for k,v in df.isna().sum().items() if v}}
    for col in ['anio_siniestro','anio_dataset','gravedad_siniestro','uso_moto','tipo_delito']:
        if col in df: rec[col] = {str(k):int(v) for k,v in df[col].value_counts(dropna=False).items()}
    for col in ['fecha_siniestro','fecha']:
        if col in df:
            d = pd.to_datetime(df[col],errors='coerce')
            rec[col] = {'min':str(d.min()),'max':str(d.max()),'invalid':int(d.isna().sum())}
    if 'id_siniestro' in df: rec['id_duplicates'] = int(df.id_siniestro.duplicated().sum())
    if 'cluster' in df:
        rec['clusters'] = int(df.loc[df.cluster != -1,'cluster'].nunique())
        rec['noise'] = int((df.cluster == -1).sum())
    for col in ['cantidad_siniestros','cantidad_delitos','mortales','graves']:
        if col in df: rec[col] = {'sum':int(df[col].sum()),'min':float(df[col].min()),'max':float(df[col].max())}
    for lat,lon in [('latitud','longitud'),('latitud_siniestro','longitud_siniestro')]:
        if lat in df and lon in df:
            a,b=pd.to_numeric(df[lat],errors='coerce'),pd.to_numeric(df[lon],errors='coerce')
            rec['geo']={'lat_min':float(a.min()),'lat_max':float(a.max()),'lon_min':float(b.min()),'lon_max':float(b.max()),'invalid':int((a.isna()|b.isna()).sum()),'zero_zero':int(((a==0)&(b==0)).sum()),'outside_bbox':int((a.notna()&b.notna()&(~a.between(-35.3,-33.9)|~b.between(-59.5,-57.8))).sum())}
    if p.name=='delitos_caba.csv':
        v=df[df.anio_dataset >= df.anio_dataset.max()-2].dropna(subset=['latitud','longitud'])
        v=v[(v.latitud!=0)|(v.longitud!=0)]
        rec['window_general']=len(v[v.tipo_delito!='Vialidad'])
        rec['window_moto']=len(v[v.uso_moto=='SI'])
    out['csv'][p.name]=rec
for directory in ['backend','notebooks']:
    for p in (ROOT/directory).rglob('*.py'):
        if any(x in p.parts for x in ['venv','__pycache__']): continue
        try: ast.parse(p.read_text(encoding='utf-8-sig')); out['syntax'][str(p.relative_to(ROOT))]='OK'
        except SyntaxError as e: out['syntax'][str(p.relative_to(ROOT))]=str(e)
nb=json.loads((ROOT/'notebooks/01_eda_hotspots_moto.ipynb').read_text(encoding='utf-8'))
for i,c in enumerate(nb['cells']):
    if c['cell_type']!='code':continue
    try: ast.parse(''.join(c['source'])); out['notebook'][i]='OK'
    except SyntaxError as e: out['notebook'][i]=str(e)
for name in ['modelo_final.pkl','columnas_modelo.pkl','hotspots_contexto.csv','indice_inseguridad_comuna.csv']:
    a,b=(ROOT/'data'/name).read_bytes(),(ROOT/'backend'/name).read_bytes()
    out['artifacts'][name]={'same_data_backend':a==b,'sha256_backend':hashlib.sha256(b).hexdigest()}
model=joblib.load(ROOT/'backend/modelo_final.pkl')
cols=joblib.load(ROOT/'backend/columnas_modelo.pkl')
out['model']={'class':type(model).__name__,'params':model.get_params(),'classes':model.classes_.tolist(),'features':cols,'feature_importance':sorted(zip(cols,model.feature_importances_.tolist()),key=lambda x:-x[1])}
from reentrenar_modelo import cargar_motos_extendido
with contextlib.redirect_stdout(io.StringIO()): df=cargar_motos_extendido()
out['training_data']={'rows':len(df),'years':df.anio_siniestro.value_counts().to_dict(),'classes':df.gravedad_siniestro.value_counts().to_dict(),'by_year_class':pd.crosstab(df.anio_siniestro,df.gravedad_siniestro).to_dict(),'unknown_age_by_class':pd.crosstab(df.gravedad_siniestro,df.edad_desconocida).to_dict(),'sex_by_class':pd.crosstab(df.gravedad_siniestro,df.sexo_victima).to_dict()}
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
idx=pd.read_csv(ROOT/'data/indice_inseguridad_comuna.csv')
idx['comuna']=idx['comuna'].astype(str)
df=df.merge(idx[['comuna','indice_inseguridad']],on='comuna',how='left')
df['indice_inseguridad']=df['indice_inseguridad'].fillna(idx.indice_inseguridad.mean())
cats=['dia_semana','comuna','tipo_de_via_siniestro','contraparte_siniestro','sexo_victima','lluvia']
nums=['hora','edad_victima','edad_desconocida','temperatura','humedad','indice_inseguridad']
X=pd.get_dummies(df[nums+cats],columns=cats).reindex(columns=cols,fill_value=0)
_,xt,_,yt=train_test_split(X,df.gravedad_siniestro,test_size=.2,random_state=42,stratify=df.gravedad_siniestro)
yp=model.predict(xt)
out['stored_model_random_split_reconstruction']={'caveat':'Reconstruccion del split declarado, no test independiente ni prueba de procedencia del artefacto','rows':len(yt),'report':classification_report(yt,yp,output_dict=True),'confusion_matrix':confusion_matrix(yt,yp,labels=model.classes_).tolist(),'labels':model.classes_.tolist()}
import main
main.limiter.enabled=False
from fastapi.testclient import TestClient
client=TestClient(main.app)
with patch('main.obtener_clima_actual',return_value=main._CLIMA_FALLBACK):
    invalid={'hora':99,'dia_semana':'NO_EXISTE','comuna':'999','tipo_de_via':'OVNI','contraparte':'OVNI','edad_victima':-50,'sexo_victima':'X'}
    r=client.post('/predecir',json=invalid)
    out['checks']['invalid_prediction']={'status':r.status_code,'body':r.json()}
conn=MagicMock();conn.closed=False
with patch('main.psycopg2.connect',return_value=conn) as connect:
    pool=main._PoolConexiones(maxsize=2)
    borrowed=[pool.getconn() for _ in range(5)]
    out['checks']['pool_maxsize_2_borrow_5']={'connect_calls':connect.call_count,'borrowed':len(borrowed)}
conn=MagicMock();conn.cursor.return_value.fetchall.return_value=[]
with patch('main._pool_conexiones.getconn',return_value=conn),patch('main._pool_conexiones.putconn'),patch('main.obtener_clima_actual',return_value=main._CLIMA_FALLBACK):
    try: out['checks']['empty_hotspots']={'status':client.get('/hotspots').status_code}
    except Exception as e: out['checks']['empty_hotspots']={'exception':type(e).__name__,'message':str(e)}
out['checks']['invalid_coordinates_accepted']=main.ReporteNuevo(lat=999,lng=999,categoria='robo',autor_id='11111111-1111-4111-8111-111111111111').model_dump()
import scrapear_noticias_robos as scraper
out['checks']['scraper_false_positive']={t:{'category':scraper.categoria_de(t,''),'location':scraper.extraer_ubicacion(t,'')} for t in ['Robaron en San Martin de los Andes','Robaron flores en una casa de Quilmes','Choque en San Martin y Belgrano, Moron','Aprobo el examen en Palermo']}
out['checks']['source_count']=sum(len(getattr(scraper,n)) for n in ['FUENTES_SITEMAP','FUENTES_SECCION','FUENTES_RSS','FUENTES_SITEMAP_SECCIONADO','FUENTES_MULTIESTRATEGIA'])
for p in (ROOT/'docs').glob('*.docx'):
    with zipfile.ZipFile(p) as z:
        root=ET.fromstring(z.read('word/document.xml'))
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paras=[''.join(n.itertext()) for n in []]
        paras=[''.join(t.text or '' for t in n.findall('.//w:t',ns)) for n in root.findall('.//w:p',ns)]
        out['docx'][p.name]={'paragraphs':len(paras),'text':'\n'.join(paras)}
print(json.dumps(out,ensure_ascii=True,indent=2,default=str))
