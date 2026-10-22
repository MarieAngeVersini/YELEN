# YELEN

YELEN is an electricity outage reporting and simulation prototype for exploring community powered electricity visibility in Sierra Leone.

Also presented as **Yelen Salone**, the project explores how community reports could help identify power disruptions where utility data is difficult to access. Users can submit reports, filter them by district, and explore an illustrative outage map. A Python backend stores reports and uses a Random Forest model to estimate whether they indicate an outage.

The project includes a browser interface, FastAPI service, persistent local database, and synthetic data training pipeline. It is a research prototype: its reports, map activity, and model results do not establish real world electricity conditions.

[View the website](https://yelensalone.netlify.app/) · [Browse the source](https://github.com/MarieAngeVersini/YELEN)

## Table of Contents

- [Install](#install)
- [Usage](#usage)
- [Features](#features)
- [How It Works](#how-it-works)
- [Technology](#technology)
- [Data and Limitations](#data-and-limitations)
- [API](#api)
- [Maintainers](#maintainers)
- [Credits](#credits)

## Install

### Prerequisites

Use Python **3.10 or newer**, Git, and a current browser with JavaScript enabled. SQLite is included with standard Python installations; no separate database server is needed for the default setup.

```sh
python --version
git --version
```

Both commands should print a version. If your system uses `python3` or Windows's `py`, substitute that command for `python` when creating the environment below.

### Get the project

```sh
git clone https://github.com/MarieAngeVersini/YELEN.git
cd YELEN
python -m venv .venv
```

Activate the environment using the command for your terminal:

| Terminal | Command |
| --- | --- |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |

### Dependencies

With the environment active, install the packages listed in the repository:

```sh
python -m pip install -r requirements.txt
```

These include FastAPI, Uvicorn, scikit-learn, NumPy, Joblib, and the PostgreSQL driver Psycopg. The frontend uses plain HTML, CSS, and JavaScript, so it has no Node.js build step.

Confirm that the core dependencies load:

```sh
python -c "import fastapi, uvicorn, sklearn, numpy, joblib; print('YELEN dependencies ready')"
```

Expected output:

```text
YELEN dependencies ready
```

## Usage

### CLI

From the repository root, start the application:

```sh
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
```

On first startup, the service generates training data and trains a model if no saved model exists. It also creates the SQLite database and inserts four demonstration reports when the report table is empty. After initialization, Uvicorn prints startup messages including:

```text
Application startup complete.
Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
```

Open **http://127.0.0.1:8765** in your browser. Keep the terminal running; press **Ctrl+C** to stop the server.

In a second terminal, check the service:

```sh
curl http://127.0.0.1:8765/api/health
```

For a fresh SQLite database, the response is:

```json
{"status":"ok","database":"sqlite","model_loaded":true,"report_count":4,"mode":"local demo"}
```

The count changes as reports are added. In Windows PowerShell, use `curl.exe` if `curl` resolves to a PowerShell command.

**Error example:** using an unsupported power status returns HTTP 400. For example, in a macOS or Linux terminal:

```sh
curl -i -X POST http://127.0.0.1:8765/api/reports -H 'Content-Type: application/json' -d '{"district":"Western Area","community":"Congo Cross","power_status":"Unknown"}'
```

The response body is:

```json
{"detail":"Unsupported power status"}
```

Fix the request by choosing `Power off`, `Unstable`, or `Power restored`. The interactive API page at **http://127.0.0.1:8765/docs** also lets you submit requests without shell quoting.

**Alternative launcher:** `python start_yelen.py` starts the service and opens a browser. The direct Uvicorn command above keeps the server in the foreground, making logs and shutdown easier to manage.

### Explore the interface

1. Select **Open night map** and click a marker to view a sample community status.
2. Switch between **Reports** and **Heat**, or select **Run simulation** to animate the scripted feed.
3. Filter the report list by district.
4. Select **Report an outage**, choose a district, enter a community, and select a power status.
5. Submit the report to store it and display the model confidence. Reload the page to confirm the report persists.

Open the interface through the local server to use storage and predictions. Opening `index.html` directly provides a temporary frontend preview; its reports disappear on reload. A static hosted preview needs a separately connected API to provide backend features.

## Features

- **Persistent community reports:** store power off, unstable power, and restoration reports in SQLite.
- **Model predictions:** estimate outage likelihood from recent reports and geographic features.
- **Nearby report counts:** count reports within three kilometers over the last thirty minutes.
- **District filters:** narrow the report list by area.
- **Illustrative map and feed:** explore predefined locations and animated sample events.
- **Reproducible training:** generate synthetic data, train a Random Forest, and export evaluation metrics.

## How It Works

The browser sends a report to FastAPI. The backend uses supplied coordinates, a known community location, or an approximate location derived from the community and district.

For each submission, it examines reports from the previous thirty minutes and constructs seven features: total reports, nearby reports within three kilometers, power off ratio, time span, average distance, restoration ratio, and hour of day. The Random Forest produces an outage probability. A report is marked as a likely outage when its probability is at least **0.65**, unless its status is `Power restored`.

Reports and prediction results are saved to the database. The report list loads stored records; the map markers and animated feed remain scripted demonstrations and do not automatically reflect new reports.

## Technology

| Component | Technology | Role |
| --- | --- | --- |
| Interface | HTML, CSS, JavaScript | Layout, form, filters, map interactions, and simulation |
| API | Python, FastAPI, Uvicorn | Serve the interface and process reports |
| Machine learning | scikit-learn, NumPy, Joblib | Generate features, train, evaluate, and save the model |
| Default storage | SQLite | Persist reports without a separate database server |
| Optional storage | PostgreSQL, Psycopg | Alternative database selected through `YELEN_DATABASE_URL` |

## Data and Limitations

### Training and evaluation

Run the training script from the repository root:

```sh
python backend/train_model.py
```

It generates **6,000 synthetic feature records** with seed 42, trains on 4,500 records, and evaluates on a held out set of 1,500. Outage labels come from a simulated scoring rule with random noise, not observed utility outages. The script prints accuracy, precision, recall, ROC-AUC, a confusion matrix, and training metadata as JSON.

| Generated file | Contents |
| --- | --- |
| `data/simulated_reports.csv` | Synthetic training and evaluation records |
| `data/yelen.db` | Reports saved by the application, including demonstration seed reports |
| `models/outage_detector.joblib` | Trained classifier and feature names |
| `models/metrics.json` | Evaluation results and training metadata |

The training command regenerates the CSV and overwrites the saved model and metrics. Use `models/metrics.json` for scores from your run; results can vary with dependency versions. Synthetic data performance does not establish real world accuracy.

A verification run of the included training code produced these held out synthetic data results:

| Metric | Result |
| --- | --- |
| Accuracy | 93.07% |
| Precision | 89.40% |
| Recall | 94.78% |
| ROC-AUC | 0.9820 |

### Storage and current scope

SQLite is the default. `YELEN_DATABASE_URL` selects PostgreSQL when it starts with `postgresql://` or `postgres://`; that option requires an existing accessible database and has not been validated here. Environment variables must be set before starting the service; the code does not automatically load a `.env` file.

The `.gitignore` excludes generated `data/` and `models/` directories, Python caches, `.venv/`, and `.env`. These generated files do not need to be uploaded to run a fresh copy.

Community coordinates may be approximated, and the map is illustrative. The API is intended for a local demonstration and has no authentication. Future work includes connecting reports to map updates, improving geographic validation, and evaluating against appropriate real world data.

## API

Base URL for the local application: `http://127.0.0.1:8765`. Interactive schemas and request examples are available at `/docs`.

| Method | Route | Returns |
| --- | --- | --- |
| `GET` | `/api/health` | Status, database type, model file presence, report count, and mode |
| `GET` | `/api/reports` | Up to 100 reports, ordered by newest timestamp |
| `POST` | `/api/reports` | Newly stored report, coordinates, prediction, and nearby count |
| `GET` | `/api/outages` | Stored reports marked as likely outages, ordered by confidence |
| `POST` | `/api/demo/reset` | Deletes all reports, restores four sample records, and returns `{"status":"reset","report_count":4}` |

`GET /api/outages` returns individual flagged reports, including older records; it is not a deduplicated list of currently active outages.

### Submit a report

`POST /api/reports` accepts JSON:

| Field | Type | Requirement |
| --- | --- | --- |
| `district` | string | Required; 2–60 characters |
| `community` | string | Required; 2–80 characters; the browser form limits entry to 40 |
| `power_status` | string | Required; `Power off`, `Unstable`, or `Power restored` |
| `latitude` | number or null | Optional; supply together with longitude to override location lookup |
| `longitude` | number or null | Optional; supply together with latitude |

With the local server running, this complete Python example submits a simulated report:

```python
import json
from urllib.request import Request, urlopen

payload = {
    "community": "Congo Cross",
    "district": "Western Area",
    "power_status": "Power off",
}
request = Request(
    "http://127.0.0.1:8765/api/reports",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urlopen(request, timeout=10) as response:
    print(json.load(response))
```

A successful submission returns HTTP 200 with `id`, `district`, `community`, `power_status`, `latitude`, `longitude`, `confidence`, `likely_outage`, `cluster_size`, and `reported_at`. Confidence is the model probability between 0 and 1; `likely_outage` is a boolean; `cluster_size` includes the new report. Retrieved SQLite records represent `likely_outage` as 0 or 1.

An unsupported status returns **400** with `{"detail":"Unsupported power status"}`. Missing required fields or invalid field types or lengths return **422** with validation details. The Python example raises `HTTPError` for HTTP errors or `URLError` when it cannot reach the service.

### Customize the demonstration

The frontend functions are internal application code, not a public library API. To add a sample report for local file preview, insert an object into `sampleReports` in `app.js`:

```javascript
{
  community: 'Wilberforce',
  district: 'Western Area',
  status: 'Power off',
  reports: 3,
  time: 'just now',
  confidence: 'Possible issue',
  level: 'Monitoring',
},
```

When the backend is available, stored reports replace that initial sample list. Map markers and feed events are defined separately. Backend community coordinates can be extended through the `COMMUNITIES` dictionary in `backend/main.py`; use verified coordinates and restart the server after changes.

## Maintainers

[Marie Ange Versini](https://github.com/MarieAngeVersini): project creator and README maintainer.

For questions or bug reports, [open a repository issue](https://github.com/MarieAngeVersini/YELEN/issues).

## Credits

CICS 305, Fall 2026: *Tackling the README: Section by Section* slides.
