# stock-dashboard
Lets start with the basics

Project structure:
investment-dashboard/
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── input.css
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── components/
│       │   ├── SymbolContext.jsx
│       │   ├── SymbolSelector.jsx
│       │   ├── AssetChart.jsx
│       │   ├── AssetSummary.jsx
│       │   ├── AssetMetadata.jsx
│       │   ├── AssetTabs.jsx
│       │   ├── NewsFeed.jsx
│       │   └── Navigation.jsx
│       ├── pages/
│       │   ├── DashboardPage.jsx
│       │   ├── InsightsPage.jsx
│       │   ├── PortfolioPage.jsx
│       │   └── ValuationPage.jsx
│       └── services/
│           └── API.js
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── api/
│       ├── __init__.py
│       ├── routes.py
│       └── services/
│           ├── price_services.py
│           ├── news_services.py
│           └── summary_services.py
│
├── .gitignore
├── README.md
└── run_all_tests.sh
├── training_pipeline/
    ├── data/
    │   ├── historical_prices/          # Daily stock prices per symbol
    │   ├── fundamentals.csv            # PE, EPS, revenue growth
    │   └── training_data.csv           # Merged, labeled dataset
    ├── models/
    │   └── price_direction_model.pkl   # Trained model file
    ├── fetch/
    │   ├── fetch_prices.py             # Downloads historical price data
    │   └── fetch_fundamentals.py       # Downloads fundamentals via Finnhub
    ├── process/
    │   └── build_training_set.py       # Joins + labels dataset for training
    └── train/
        ├── train_model.py              # Trains and saves the model
        └── predict_direction.py        # CLI tool to test predictions
    
    
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