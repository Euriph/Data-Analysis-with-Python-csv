# Data Analysis with Python (CSV)

A small full-stack project for collecting time-series data, fitting a trend line to it, and generating plain-language insights. Users submit data points one at a time or as a CSV file through a web page; a Flask back end stores everything in MySQL, keeps an **incremental linear regression** model up to date, draws an "actual vs. predicted" chart, and can ask OpenAI's GPT-3.5 to describe the data.

The sample data is roughly 45 years of Dow Jones–style daily index values (1977 onward).

---

## How it works

```
┌────────────────────┐        ┌───────────────────────────┐        ┌──────────┐
│  Web Application   │  HTTP  │   Python Server (Flask)   │  SQL   │  MySQL   │
│  HTML / CSS / JS   ├───────►│  :5000                    ├───────►│          │
└────────────────────┘        │  • incremental regression │        └──────────┘
┌────────────────────┐        │  • matplotlib plots       │        ┌──────────┐
│  SwaggerNetCore    │  HTTP  │  • OpenAI insights        ├───────►│  OpenAI  │
│  ASP.NET Core 8    ├───────►│                           │        │   API    │
└────────────────────┘        └───────────────────────────┘        └──────────┘
```

1. A data point (date + value) or a CSV file arrives at the Flask server.
2. Each date is converted to "days since the earliest date in the database" and fed into the model.
3. The regression never re-reads the full history. It keeps four running sums (Σx, Σy, Σx², Σxy) and a count in `TblRegressionState`, so each new point updates the line in constant time:

   ```
   b1 = (n·Σxy − Σx·Σy) / (n·Σx² − (Σx)²)
   b0 = (Σy − b1·Σx) / n
   ```

4. Every recalculation saves the coefficients (`b0`, `b1`) with a timestamp in `TblCoefficients`, giving a history of how the trend changed.
5. The front end requests a chart (base64 PNG) with the mean squared error, and can send a summary of up to 100 sampled points to GPT-3.5 for a written insight.

## Repository layout

| Path | What's in it |
|---|---|
| `Python Server/server.py` | **Main back end.** Single-file Flask app with all models, regression classes and routes. |
| `Python Server/project/` | The same server split into modules (`models.py`, `routes/`, `Regressions/`, `utils.py`, `config.py`), plus `requirements.txt`. |
| `Web Application/` | Plain HTML/CSS/JS front end: single-entry form, CSV upload, chart + MSE report, "Generate Insights" button. |
| `SwaggerNetCore/` | ASP.NET Core 8 Web API with Swagger UI that forwards single entries and CSV uploads to the Flask server. Entity Framework Core models mirror the MySQL tables. |
| `Python Swagger Api/` | An earlier version of the API built with Flask-RESTX (auto-generated Swagger docs). |
| `Data Values/` | Sample data: `Combined_Data.csv` (~102k daily rows), `DowJones.done` (~2k weekly closes), and small test files. |
| `Test Codes (Not working probably)/` | Early experiments with a hand-written `swagger.yaml`. Not maintained. |

## API endpoints (Flask, port 5000)

| Method | Route | Body | Returns |
|---|---|---|---|
| POST | `/submit_single_data` | JSON `{date, value, username}` | Updated coefficients |
| POST | `/upload_csv` | multipart `file` (columns `Date`, `Value`; dates `YYYY-MM-DD`) | Updated coefficients |
| GET | `/get_data_plot` | – | `{image, mse}` (image is a base64 PNG) |
| GET | `/get_data_summary` | – | Coefficients, MSE, plot and up to 100 sampled points |
| POST | `/generate_insights` | JSON `{summary}` | `{insight, token_count}` from GPT-3.5 |
| POST | `/submit_multi_data` | JSON `{date, values[], target, username}` | Experimental |
| POST | `/submit_logistic_data` | JSON `{values[], target, username}` | Experimental |

The .NET API exposes `POST /Data/submit-single-data` and `POST /Data/upload-csv`, which forward to the first two routes above.

## Database

MySQL database `dataanalysisproject`. Tables are created automatically on first run (`Base.metadata.create_all`):

- `TblWebAppRequestMaster`: one row per submission (timestamp, record count, file name, user)
- `TblWebAppRequest`: individual data points (date, value), linked to their submission
- `TblCoefficients`: history of fitted `b0` / `b1` values
- `TblRegressionState`: running sums for the linear model
- `TblMultiLinearRegressionState`, `TblLogisticRegressionState`: state for the experimental models

## Getting started

**Requirements:** Python 3.10+, a MySQL server, an OpenAI API key (only needed for insights), and the .NET 8 SDK if you want the Swagger gateway.

```bash
# 1. Create the database
mysql -u root -p -e "CREATE DATABASE dataanalysisproject;"

# 2. Install dependencies
cd "Python Server/project"
pip install -r requirements.txt numpy

# 3. Configure credentials (see "Configuration" below), then start the server
cd ..
python server.py          # serves on http://localhost:5000
```

Then open `Web Application/interface.html` in a browser and upload `Data Values/Combined_Data.csv` or submit single values.

Optional .NET gateway:

```bash
cd SwaggerNetCore
dotnet run                # Swagger UI at /swagger
```

## Configuration

Set your MySQL connection string and OpenAI key before running. Keep them in environment variables or an untracked `.env` file, never in committed code:

```python
import os
DATABASE_URI = os.environ["DATABASE_URI"]       # e.g. mysql+pymysql://user:pass@localhost/dataanalysisproject
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
```

For the .NET project, use `dotnet user-secrets` or an environment variable for `ConnectionStrings:MySqlConnectionString`.

## Tech stack

**Back end:** Python, Flask, Flask-CORS, SQLAlchemy, PyMySQL, pandas, matplotlib, OpenAI SDK, tiktoken
**Gateway:** C#, ASP.NET Core 8, Swashbuckle (Swagger), Entity Framework Core with Pomelo MySQL
**Front end:** HTML, CSS, vanilla JavaScript
**Database:** MySQL

## Known limitations

This was a learning project, and a few parts are unfinished:

- **Experimental models.** The multi-linear and logistic regression classes are incomplete. They use `numpy`/`scikit-learn` without importing them and don't keep the statistics needed for a correct fit, so those two endpoints will fail.
- **Double counting.** `/get_data_plot` and `/get_data_summary` feed every stored point back into the persisted model on each call, so the running sums grow every time the chart is refreshed. Plotting should only read the coefficients.
- **Inconsistent imports.** The modular `project/` package mixes `from models import …` with `from project.models import …`. `server.py` is the version that runs as-is.
- **Hard-coded URLs.** The front end and .NET gateway point to `http://localhost:5000`.
- **No authentication or input validation.**

## Author

ilyas · 2024
