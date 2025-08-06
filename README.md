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


