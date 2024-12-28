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

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return [
                CsvRow(
                    idx=reader.line_num,
                    serial_number=row['÷'],
                    product_name=row['Товар'],
                    purchase_price=self.parse_price(row['Цена поставки']),
                ) for row in reader
            ]
        

    def parse_price(self, row: str) -> int:
        """Parse price string into float, handling various formats.
    
        Handles formats like:
        - "7985,25"    -> 7985.25
        - "7 985,25"   -> 7985.25
        - "7.985,25"   -> 7985.25
        - "р.7985,25"  -> 7985.25
        - "7985.25"    -> 7985.25
        """
        try:
            # Remove currency symbol and any whitespace
            cleaned = row.strip()
            cleaned = cleaned.replace('р.', '').replace('\xa0', '')
            
            # Remove all spaces
            cleaned = cleaned.replace(' ', '')
            
            # Handle both comma and dot as decimal separators
            # If there's a comma, use it as decimal separator
            if ',' in cleaned:
                # Remove dots (thousand separators) and replace comma with dot
                cleaned = cleaned.replace('.', '').replace(',', '.')
            
            # Convert to float
            price_float = float(cleaned) if cleaned else 0.0
            return int(price_float * 100)
        
        except (ValueError, TypeError):
            return 0

