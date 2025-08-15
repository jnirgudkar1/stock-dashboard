/mnt/data/stock-dashboard
├── __MACOSX
│   └── stock-dashboard
│       ├── backend
│       │   ├── api
│       │   │   ├── db
│       │   │   ├── services
│       │   │   ├── ._.DS_Store
│       │   │   ├── .___init__.py
│       │   │   ├── ._db
│       │   │   ├── ._routes.py
│       │   │   └── ._services
│       │   ├── ._.DS_Store
│       │   ├── ._api
│       │   ├── ._main.py
│       │   └── ._requirement.txt
│       ├── frontend
│       │   ├── public
│       │   │   └── ._vite.svg
│       │   ├── src
│       │   │   ├── assets
│       │   │   ├── components
│       │   │   ├── pages
│       │   │   ├── services
│       │   │   ├── ._App.css
│       │   │   ├── ._App.jsx
│       │   │   ├── ._assets
│       │   │   ├── ._components
│       │   │   ├── ._index.css
│       │   │   ├── ._input.css
│       │   │   ├── ._main.jsx
│       │   │   ├── ._pages
│       │   │   └── ._services
│       │   ├── ._.DS_Store
│       │   ├── ._eslint.config.js
│       │   ├── ._index.html
│       │   ├── ._package-lock.json
│       │   ├── ._package.json
│       │   ├── ._public
│       │   ├── ._README.md
│       │   ├── ._src
│       │   ├── ._tailwind.config.js
│       │   └── ._vite.config.js
│       ├── training_pipeline
│       │   ├── data
│       │   │   ├── historical_prices
│       │   │   ├── ._fundamentals.csv
│       │   │   ├── ._historical_prices
│       │   │   └── ._training_data.csv
│       │   ├── fetch
│       │   │   ├── ._fetch_fundamentals.py
│       │   │   └── ._fetch_prices.py
│       │   ├── models
│       │   │   └── ._price_direction_model.pkl
│       │   ├── process
│       │   │   └── ._build_training_set.py
│       │   ├── train
│       │   │   ├── ._predict_direction.py
│       │   │   └── ._train_model.py
│       │   ├── utils
│       │   │   └── ._sentiment_store.py
│       │   ├── ._.DS_Store
│       │   ├── ._.env
│       │   ├── ._data
│       │   ├── ._fetch
│       │   ├── ._models
│       │   ├── ._process
│       │   ├── ._train
│       │   └── ._utils
│       ├── ._.DS_Store
│       ├── ._backend
│       ├── ._frontend
│       ├── ._README.md
│       └── ._training_pipeline
└── stock-dashboard
    ├── backend
    │   ├── api
    │   │   ├── db
    │   │   │   ├── .DS_Store
    │   │   │   └── database.py
    │   │   ├── services
    │   │   │   ├── .DS_Store
    │   │   │   ├── __init__.py
    │   │   │   ├── metadata_services.py
    │   │   │   ├── news.py
    │   │   │   ├── prices.py
    │   │   │   └── valuation.py
    │   │   ├── .DS_Store
    │   │   ├── __init__.py
    │   │   └── routes.py
    │   ├── .DS_Store
    │   ├── main.py
    │   └── requirement.txt
    ├── frontend
    │   ├── public
    │   │   └── vite.svg
    │   ├── src
    │   │   ├── assets
    │   │   │   └── react.svg
    │   │   ├── components
    │   │   │   ├── AssetChart.jsx
    │   │   │   ├── DataContext.jsx
    │   │   │   ├── Navigation.jsx
    │   │   │   ├── NewsFeed.jsx
    │   │   │   ├── SymbolContext.jsx
    │   │   │   ├── SymbolSelector.jsx
    │   │   │   └── ValuationResult.jsx
    │   │   ├── pages
    │   │   │   ├── DashboardPage.jsx
    │   │   │   ├── InsightsPage.jsx
    │   │   │   ├── PortfolioPage.jsx
    │   │   │   └── ValuationPage.jsx
    │   │   ├── services
    │   │   │   └── api.js
    │   │   ├── App.css
    │   │   ├── App.jsx
    │   │   ├── index.css
    │   │   ├── input.css
    │   │   └── main.jsx
    │   ├── .DS_Store
    │   ├── eslint.config.js
    │   ├── index.html
    │   ├── package-lock.json
    │   ├── package.json
    │   ├── README.md
    │   ├── tailwind.config.js
    │   └── vite.config.js
    ├── training_pipeline
    │   ├── data
    │   │   ├── historical_prices
    │   │   │   ├── .DS_Store
    │   │   │   ├── AAPL.csv
    │   │   │   ├── AMD.csv
    │   │   │   ├── AMZN.csv
    │   │   │   ├── BKSY.csv
    │   │   │   ├── GOOGL.csv
    │   │   │   ├── NVDA.csv
    │   │   │   ├── PLTR.csv
    │   │   │   ├── RCAT.csv
    │   │   │   ├── RKLB.csv
    │   │   │   └── TSLA.csv
    │   │   ├── fundamentals.csv
    │   │   └── training_data.csv
    │   ├── fetch
    │   │   ├── fetch_fundamentals.py
    │   │   └── fetch_prices.py
    │   ├── models
    │   │   └── price_direction_model.pkl
    │   ├── process
    │   │   └── build_training_set.py
    │   ├── train
    │   │   ├── predict_direction.py
    │   │   └── train_model.py
    │   ├── utils
    │   │   └── sentiment_store.py
    │   ├── .DS_Store
    │   └── .env
    ├── .DS_Store
    └── README.md
    
    
# 1. Fetch historical prices (2015–today)
python training_pipeline/fetch/fetch_prices.py

# 2. Fetch latest fundamentals (PE ratio, EPS, revenue growth)
python training_pipeline/fetch/fetch_fundamentals.py

# 3. Build training dataset with labels (rise/fall in 7 days)
python training_pipeline/process/build_training_set.py

# 4. Train model and save as price_direction_model.pkl
python training_pipeline/train/train_model.py


Quick Start (Optional Shortcut)
Run the full pipeline in one go:

bash
Copy
Edit
chmod +x run_pipeline.sh
./run_pipeline.sh
🧪 Test a Prediction (CLI)
bash
Copy
Edit
python training_pipeline/train/predict_direction.py --symbol AAPL
Output:

bash
Copy
Edit
Prediction for AAPL: Buy
Confidence: 84.2%
Inputs: { price, pe_ratio, eps, revenue_growth }
🔌 API Integration
The trained model is available via:

h
Copy
Edit
GET /api/predict/{symbol}
Example response:

json
Copy
Edit
{
  "symbol": "AAPL",
  "verdict": "Buy",
  "confidence": 84.0,
  "inputs": {
    "close_price": 213.25,
    "pe_ratio": 32.85,
    "eps": 6.57,
    "revenue_growth": 0.0
  }
}
This API is consumed by the Valuation tab in the dashboard.