# Girya Storekeeper
AI Automation for storekeeping tasks 

## Description
This project utilises CSV files, Warehouse API and OpenAI API to automate storekeeping tasks.

## Functionality
1. User input:
    - User inputs a Warehouse API Credentials in for of login and password.
    - User uploads a CSV file with positions.
    - User inputs a OpenAI API Token.
2. Creates a demand in Warehouse based on the CSV file.
    - Storekeeper checks positions in the given CSV file and creates a demand for them.
    - Each position consists of several fields: Serial number, Name, Price.
    - If position has non empty price, it is added to the demand.
    - Demand is created in Warehouse API.

## Technical details
Backend: Python, FastAPI, Pydantic, OpenAI API, Warehouse API
Frontend: Streamlit

## Additional details