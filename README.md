# Girya Storekeeper
AI Automation for storekeeping tasks 

## Description
This project utilises CSV files, Warehouse API and OpenAI API to automate storekeeping tasks.

## Functionality
1. User input:
    - User inputs a Warehouse Credentials.
    - User uploads a CSV file with positions.
2. Creates a demand in Warehouse based on the CSV file.
    - Storekeeper checks positions in the given CSV file and creates a demand for them.
    - Each position consists of several fields: Serial number, Product name, Purchase price.
    - Demand is created in Warehouse.
3. Searches for stock in Warehouse and Partners site.
    - Storekeeper searches for stock in Warehouse on the base of the predicted parameters.
    - Storekeeper searches for stock in Partners site on the base of warehouse stock.
    - Stocks comparison is displayed in the UI.

## Technical stack
Backend: Python, FastAPI, Pydantic, LiteLLM
Frontend: Streamlit

## Project Structure
```
girya-storekeeper/
├── backend/                # FastAPI backend application
│   ├── services/           # Business logic services
│   │   ├── csv_service.py  # CSV file handling
│   │   ├── llm.py          # LLM integration
│   │   ├── partners.py     # Partners API integration
│   │   └── warehouse.py    # MoySklad API integration
│   ├── utils/              # Utility modules
│   │   ├── auth.py         # Authentication helpers
│   │   ├── config.py       # Configuration management
│   │   └── logger.py       # Logging setup
│   ├── schemas.py          # Pydantic models
│   ├── storekeeper.py      # Main business logic
│   └── main.py             # FastAPI application setup
├── frontend/               # Frontend application
│   ├── api.py              # Backend API client
│   ├── sidebar.py          # Sidebar UI components
│   ├── demand_tab.py       # Demand creation tab
│   ├── stock_tab.py        # Stock view tab
│   └── app.py              # Main Streamlit application
├── docker/                 # Docker configuration
│   ├── backend/            # Backend Dockerfile
│   ├── frontend/           # Frontend Dockerfile
│   └── nginx/              # Nginx configuration
└── requirements/           # Python dependencies
    ├── backend.txt         # Backend requirements
    └── frontend.txt        # Frontend requirements
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/apridachin/girya-storekeeper.git
cd girya-storekeeper
```

2. Create and configure `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run with Docker Compose:
```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost
- Backend API: http://localhost/api/v1

## Production Deployment

### Prerequisites
- Server with Docker and Docker Compose installed
- At least 512MB RAM

### Deployment Steps
First of all, you need to install Docker and Docker Compose on your server.

1. Clone the repository on your server:
```bash
git clone https://github.com/apridachin/girya-storekeeper.git
cd girya-storekeeper
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with production values
```

3. Build and run:
```bash
docker-compose up -d --build
```