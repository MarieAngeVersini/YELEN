import csv, json
from pathlib import Path
import joblib, numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data"; MODELS=ROOT/"models"
DATASET=DATA/"simulated_reports.csv"; MODEL_FILE=MODELS/"outage_detector.joblib"; METRICS_FILE=MODELS/"metrics.json"
FEATURES=["reports_30m","nearby_reports_3km","off_ratio","minutes_since_first","average_distance_km","restoration_ratio","hour"]

def generate_dataset(rows=6000,seed=42):
    rng=np.random.default_rng(seed); records=[]
    for index in range(rows):
        outage=rng.random()<.46
        if outage:
            count=int(rng.integers(4,35)); nearby=int(rng.integers(max(3,count//3),count+1)); off=float(rng.uniform(.68,1)); minutes=float(rng.uniform(4,50)); distance=float(rng.uniform(.15,3.2)); restored=float(rng.uniform(0,.18))
        else:
            count=int(rng.integers(1,13)); nearby=int(rng.integers(0,min(count,6)+1)); off=float(rng.uniform(.05,.78)); minutes=float(rng.uniform(1,90)); distance=float(rng.uniform(1.2,13)); restored=float(rng.uniform(0,.72))
        score=count*.07+nearby*.13+off*2.4-distance*.12-restored*1.8+rng.normal(0,.9)
        records.append({"report_id":index+1,"reports_30m":count,"nearby_reports_3km":nearby,"off_ratio":round(off,4),"minutes_since_first":round(minutes,2),"average_distance_km":round(distance,3),"restoration_ratio":round(restored,4),"hour":int(rng.integers(24)),"is_outage":int(score>2.55)})
    DATA.mkdir(parents=True,exist_ok=True)
    with DATASET.open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)
    return records

def train():
    rows=generate_dataset(); x=np.array([[r[f] for f in FEATURES] for r in rows]); y=np.array([r["is_outage"] for r in rows])
    xt,xv,yt,yv=train_test_split(x,y,test_size=.25,random_state=42,stratify=y)
    model=RandomForestClassifier(n_estimators=180,max_depth=9,min_samples_leaf=4,random_state=42,class_weight="balanced"); model.fit(xt,yt)
    pred=model.predict(xv); prob=model.predict_proba(xv)[:,1]
    metrics={"dataset_rows":len(rows),"training_rows":len(xt),"testing_rows":len(xv),"accuracy":round(float(accuracy_score(yv,pred)),4),"precision":round(float(precision_score(yv,pred)),4),"recall":round(float(recall_score(yv,pred)),4),"roc_auc":round(float(roc_auc_score(yv,prob)),4),"confusion_matrix":confusion_matrix(yv,pred).tolist(),"features":FEATURES,"model":"RandomForestClassifier","seed":42}
    MODELS.mkdir(parents=True,exist_ok=True); joblib.dump({"model":model,"features":FEATURES},MODEL_FILE); METRICS_FILE.write_text(json.dumps(metrics,indent=2),encoding="utf-8"); print(json.dumps(metrics,indent=2)); return metrics
if __name__=="__main__": train()
