import csv
from pathlib import Path
from typing import List
import os

from fastapi import UploadFile, HTTPException

from backend.schemas import CsvRow
from backend.utils.config import get_settings


class CSVService:
    def __init__(self):
        self.upload_folder = Path(get_settings().upload_folder)
        self.upload_folder.mkdir(exist_ok=True)

    async def save_upload_file(self, file: UploadFile) -> str:
        """Save uploaded CSV file and return its path"""
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail="Only CSV files are allowed"
            )

        file_path = self.upload_folder / file.filename
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        return str(file_path)

    def read_csv_data(self, file_path: str) -> List[CsvRow]:
        """Read and parse CSV file into DemandItems"""
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="File not found"
            )

        items = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('÷') == '' or row.get('Товар') == '' or row.get('Цена поставки') == '':
                    continue
                
                item = CsvRow(
                    serial_number=row['÷'],
                    name=row['Товар'],
                    purchase_price=self.parse_price(row['Цена поставки'])
                )
                if item.purchase_price:
                    items.append(item)
        
        return items

    def parse_price(self, row: str | None) -> float:
        if not row:
            return 0.0
        # Remove currency symbol and non-breaking spaces, then convert to float
        cleaned = row.replace('р.', '').replace('\xa0', '').replace(',', '.')
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
