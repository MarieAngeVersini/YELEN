import math, random, sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; VENDOR=ROOT/"vendor"
if VENDOR.exists():sys.path.insert(0,str(VENDOR))
import joblib, numpy as np
from fastapi import FastAPI,HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from .database import connection,initialize,placeholder,rows_to_dicts,using_postgres
from .train_model import MODEL_FILE,train

app=FastAPI(title="Yelen Salone API",version="1.0.0")
COMMUNITIES={"Congo Cross":(8.4841,-13.2534),"Lumley":(8.4722,-13.2861),"Wilberforce":(8.4741,-13.2715),"Makeni Central":(8.8817,-12.0442),"Bo Town":(7.9647,-11.7383),"Hangha Road":(7.8767,-11.1903),"Koidu":(8.6439,-10.9717)}
CENTERS={"Western Area":(8.4657,-13.2317),"Bo":(7.9647,-11.7383),"Bombali":(8.8817,-12.0442),"Kenema":(7.8767,-11.1903),"Kono":(8.6439,-10.9717)}
class ReportInput(BaseModel):
    district:str=Field(min_length=2,max_length=60); community:str=Field(min_length=2,max_length=80); power_status:str; latitude:float|None=None; longitude:float|None=None
def now_iso():return datetime.now(timezone.utc).isoformat()
def distance(a,b,c,d):
    p1,p2=math.radians(a),math.radians(c); dp=math.radians(c-a); dl=math.radians(d-b); x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 6371*2*math.atan2(math.sqrt(x),math.sqrt(1-x))
def model():
    if not MODEL_FILE.exists():train()
    return joblib.load(MODEL_FILE)["model"]
def recent(lat,lon):
    cutoff=(datetime.now(timezone.utc)-timedelta(minutes=30)).isoformat(); mark=placeholder()
    with connection() as conn: rows=rows_to_dicts(conn.execute(f"SELECT * FROM reports WHERE reported_at >= {mark}",(cutoff,)))
    for row in rows:row["distance_km"]=distance(lat,lon,row["latitude"],row["longitude"])
    return rows
def features(rows):
    near=[r for r in rows if r["distance_km"]<=3]; off=sum(r["power_status"]=="Power off" for r in rows); restored=sum(r["power_status"]=="Power restored" for r in rows); times=[datetime.fromisoformat(r["reported_at"]) for r in rows]
    return [len(rows),len(near),off/len(rows),max(1,(max(times)-min(times)).total_seconds()/60),sum(r["distance_km"] for r in rows)/len(rows),restored/len(rows),datetime.now().hour]
def insert(payload,lat,lon,confidence,likely,cluster):
    mark=placeholder(); values=(payload.district,payload.community,lat,lon,payload.power_status,now_iso(),confidence,int(likely),cluster)
    with connection() as conn:
        cursor=conn.execute(f"INSERT INTO reports (district,community,latitude,longitude,power_status,reported_at,confidence,likely_outage,cluster_size) VALUES ({','.join([mark]*9)})",values); return cursor.lastrowid if not using_postgres() else None
def seed():
    with connection() as conn: count=rows_to_dicts(conn.execute("SELECT COUNT(*) AS count FROM reports"))[0]["count"]
    if count:return
    for district,community,status,confidence,likely,cluster in [("Western Area","Congo Cross","Power off",.91,1,12),("Bombali","Makeni Central","Unstable",.62,0,4),("Bo","Bo Town","Power restored",.18,0,8),("Kenema","Hangha Road","Power off",.78,1,5)]:
        payload=ReportInput(district=district,community=community,power_status=status); insert(payload,*COMMUNITIES[community],confidence,likely,cluster)
@app.on_event("startup")
def startup():initialize();model();seed()
@app.get("/api/health")
def health():
    with connection() as conn: report_count=rows_to_dicts(conn.execute("SELECT COUNT(*) AS count FROM reports"))[0]["count"]
    return {"status":"ok","database":"postgresql" if using_postgres() else "sqlite","model_loaded":MODEL_FILE.exists(),"report_count":report_count,"mode":"local demo"}
@app.get("/api/reports")
def list_reports():
    with connection() as conn:return rows_to_dicts(conn.execute("SELECT * FROM reports ORDER BY reported_at DESC LIMIT 100"))
@app.post("/api/reports")
def create_report(payload:ReportInput):
    if payload.power_status not in {"Power off","Unstable","Power restored"}:raise HTTPException(400,"Unsupported power status")
    if payload.latitude is not None and payload.longitude is not None:lat,lon=payload.latitude,payload.longitude
    elif payload.community in COMMUNITIES:lat,lon=COMMUNITIES[payload.community]
    else:
        lat,lon=CENTERS.get(payload.district,(8.4606,-11.7799)); rng=random.Random(payload.community.lower()); lat+=rng.uniform(-.025,.025);lon+=rng.uniform(-.025,.025)
    rows=recent(lat,lon); candidate={"power_status":payload.power_status,"reported_at":now_iso(),"distance_km":0}; vector=features(rows+[candidate]); confidence=float(model().predict_proba(np.array([vector]))[0,1]); likely=confidence>=.65 and payload.power_status!="Power restored"; cluster=sum(r["distance_km"]<=3 for r in rows)+1; report_id=insert(payload,lat,lon,confidence,likely,cluster)
    return {"id":report_id,"district":payload.district,"community":payload.community,"power_status":payload.power_status,"latitude":lat,"longitude":lon,"confidence":round(confidence,4),"likely_outage":likely,"cluster_size":cluster,"reported_at":now_iso()}
@app.get("/api/outages")
def outages():
    with connection() as conn:return rows_to_dicts(conn.execute("SELECT * FROM reports WHERE likely_outage=1 ORDER BY confidence DESC"))
@app.post("/api/demo/reset")
def reset_demo():
    with connection() as conn: conn.execute("DELETE FROM reports")
    seed()
    return {"status":"reset","report_count":4}
app.mount("/",StaticFiles(directory=ROOT,html=True),name="site")
