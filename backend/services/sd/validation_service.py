import csv
import json
import pandas as pd
from typing import List, Dict, Any, Tuple
from models.sd.upcoming_project import BOQItem, BOMItem, ValidationDiscrepancy, ValidationResult
import logging

logger = logging.getLogger(__name__)

class ValidationService:
    """Service for BOQ/BOM validation and file processing"""
    
    @staticmethod
    def parse_csv_file(file_path: str, file_type: str) -> List[Dict[str, Any]]:
        """Parse CSV file and return list of items"""
        try:
            df = pd.read_csv(file_path)
            
            # Standardize column names for BOQ files
            if file_type == "boq":
                expected_columns = ['sku', 'item_name', 'quantity', 'unit_price', 'total_price']
                # Map common variations
                column_mapping = {
                    'SKU': 'sku',
                    'Item Code': 'sku',
                    'Product Code': 'sku',
                    'Item Name': 'item_name',
                    'Description': 'item_name',
                    'Product Name': 'item_name',
                    'Qty': 'quantity',
                    'Quantity': 'quantity',
                    'Unit Price': 'unit_price',
                    'Price': 'unit_price',
                    'Total': 'total_price',
                    'Total Price': 'total_price',
                    'Amount': 'total_price'
                }
            else:  # bom
                expected_columns = ['sku', 'item_name', 'quantity', 'unit_cost', 'total_cost']
                column_mapping = {
                    'SKU': 'sku',
                    'Item Code': 'sku',
                    'Product Code': 'sku',
                    'Item Name': 'item_name',
                    'Description': 'item_name',
                    'Product Name': 'item_name',
                    'Qty': 'quantity',
                    'Quantity': 'quantity',
                    'Unit Cost': 'unit_cost',
                    'Cost': 'unit_cost',
                    'Total': 'total_cost',
                    'Total Cost': 'total_cost',
                    'Amount': 'total_cost'
                }
            
            # Rename columns using mapping
            df = df.rename(columns=column_mapping)
            
            # Check if required columns exist
            missing_columns = [col for col in expected_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns in {file_type.upper()} file: {missing_columns}")
            
            # Convert to list of dictionaries
            items = df[expected_columns].to_dict('records')
            
            # Clean and validate data
            cleaned_items = []
            for item in items:
                # Skip empty rows
                if pd.isna(item['sku']) or str(item['sku']).strip() == '':
                    continue
                
                # Clean and convert data types
                cleaned_item = {
                    'sku': str(item['sku']).strip().upper(),
                    'item_name': str(item['item_name']).strip(),
                    'quantity': int(float(item['quantity'])) if pd.notna(item['quantity']) else 0
                }
                
                if file_type == "boq":
                    cleaned_item.update({
                        'unit_price': float(item['unit_price']) if pd.notna(item['unit_price']) else 0.0,
                        'total_price': float(item['total_price']) if pd.notna(item['total_price']) else 0.0
                    })
                else:
                    cleaned_item.update({
                        'unit_cost': float(item['unit_cost']) if pd.notna(item['unit_cost']) else 0.0,
                        'total_cost': float(item['total_cost']) if pd.notna(item['total_cost']) else 0.0
                    })
                
                cleaned_items.append(cleaned_item)
            
            return cleaned_items
            
        except Exception as e:
            logger.error(f"Error parsing {file_type.upper()} file {file_path}: {str(e)}")
            raise ValueError(f"Failed to parse {file_type.upper()} file: {str(e)}")
    
    @staticmethod
    def validate_boq_bom_match(boq_items: List[Dict[str, Any]], bom_items: List[Dict[str, Any]]) -> ValidationResult:
        """
        Validate BOQ vs BOM for discrepancies
        Returns validation result with detailed discrepancies
        """
        discrepancies = []
        
        # Create lookup dictionaries for faster searching
        boq_lookup = {item['sku']: item for item in boq_items}
        bom_lookup = {item['sku']: item for item in bom_items}
        
        # Check for missing SKUs in BOM
        for boq_item in boq_items:
            sku = boq_item['sku']
            if sku not in bom_lookup:
                discrepancies.append(ValidationDiscrepancy(
                    type="missing_sku_in_bom",
                    sku=sku,
                    message=f"SKU {sku} ({boq_item['item_name']}) exists in BOQ but missing in BOM",
                    boq_quantity=boq_item['quantity'],
                    bom_quantity=None,
                    severity="High"
                ))
        
        # Check for missing SKUs in BOQ
        for bom_item in bom_items:
            sku = bom_item['sku']
            if sku not in boq_lookup:
                discrepancies.append(ValidationDiscrepancy(
                    type="missing_sku_in_boq",
                    sku=sku,
                    message=f"SKU {sku} ({bom_item['item_name']}) exists in BOM but missing in BOQ",
                    boq_quantity=None,
                    bom_quantity=bom_item['quantity'],
                    severity="High"
                ))
        
        # Check for quantity mismatches
        for sku in set(boq_lookup.keys()) & set(bom_lookup.keys()):
            boq_item = boq_lookup[sku]
            bom_item = bom_lookup[sku]
            
            if boq_item['quantity'] != bom_item['quantity']:
                discrepancies.append(ValidationDiscrepancy(
                    type="quantity_mismatch",
                    sku=sku,
                    message=f"Quantity mismatch for SKU {sku}: BOQ={boq_item['quantity']}, BOM={bom_item['quantity']}",
                    boq_quantity=boq_item['quantity'],
                    bom_quantity=bom_item['quantity'],
                    severity="Medium"
                ))
        
        # Generate validation summary
        total_discrepancies = len(discrepancies)
        is_valid = total_discrepancies == 0
        
        if is_valid:
            summary = f"✅ Validation passed. {len(boq_items)} BOQ items matched with {len(bom_items)} BOM items."
        else:
            high_severity = len([d for d in discrepancies if d.severity == "High"])
            medium_severity = len([d for d in discrepancies if d.severity == "Medium"])
            summary = f"❌ Validation failed. {total_discrepancies} discrepancies found: {high_severity} high severity, {medium_severity} medium severity."
        
        return ValidationResult(
            is_valid=is_valid,
            discrepancies=discrepancies,
            total_discrepancies=total_discrepancies,
            validation_summary=summary
        )
    
    @staticmethod
    def requires_gc_signoff(order_value: float, has_third_party: bool = False) -> bool:
        """Determine if GC signoff is required based on business rules"""
        return order_value > 500000 or has_third_party
    
    @staticmethod
    def calculate_setup_cost(boq_items: List[Dict[str, Any]]) -> float:
        """Calculate total setup cost from BOQ items"""
        try:
            total_cost = sum(item.get('total_price', 0) for item in boq_items)
            return float(total_cost)
        except Exception as e:
            logger.error(f"Error calculating setup cost: {str(e)}")
            return 0.0