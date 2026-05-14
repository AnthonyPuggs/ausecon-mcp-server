from __future__ import annotations

APRA_CATALOGUE: dict[str, dict] = {
    "ADI_MONTHLY": {
        "id": "ADI_MONTHLY",
        "name": "Monthly Authorised Deposit-taking Institution Statistics",
        "description": (
            "Selected monthly banking-business balance sheet data for authorised "
            "deposit-taking institutions."
        ),
        "category": "banking",
        "frequency": "Monthly",
        "frequencies": ["M"],
        "geographies": ["aus"],
        "tags": ["apra", "adi", "banking", "balance sheet", "deposits", "loans"],
        "aliases": ["monthly adi statistics", "madis", "adi monthly statistics"],
        "landing_url": (
            "https://www.apra.gov.au/monthly-authorised-deposit-taking-institution-statistics"
        ),
        "link_patterns": [r"back-series.*xlsx"],
        "tables": {
            "table_1": {
                "sheet": "Table 1",
                "layout": "row_records",
                "title": "Monthly ADI balance sheet back series",
                "unit": "$ million",
                "frequency": "Monthly",
                "header_row": 2,
                "data_start_row": 3,
                "date_column": 1,
                "dimension_columns": {
                    "abn": 2,
                    "institution": 3,
                },
                "series_start_column": 4,
                "identity_columns": ["abn"],
            }
        },
        "variants": [],
    },
    "ADI_QUARTERLY_PERFORMANCE": {
        "id": "ADI_QUARTERLY_PERFORMANCE",
        "name": "Quarterly Authorised Deposit-taking Institution Performance Statistics",
        "description": (
            "Quarterly aggregate ADI financial performance, financial position, capital "
            "adequacy, asset quality, liquidity, and key ratios."
        ),
        "category": "banking",
        "frequency": "Quarterly",
        "frequencies": ["Q"],
        "geographies": ["aus"],
        "tags": ["apra", "adi", "banking", "performance", "capital", "liquidity"],
        "aliases": ["quarterly adi performance", "adi performance statistics"],
        "landing_url": (
            "https://www.apra.gov.au/quarterly-authorised-deposit-taking-institution-statistics"
        ),
        "link_patterns": [r"performance.*xlsx"],
        "tables": {
            "key_stats": {
                "sheet": "Key Stats",
                "layout": "matrix",
                "title": "Key statistics",
                "unit": None,
                "frequency": "Quarterly",
                "date_row": 7,
                "date_start_column": 2,
                "data_start_row": 9,
                "label_column": 1,
            },
            "tab_1a": {
                "sheet": "Tab 1a",
                "layout": "matrix",
                "title": "ADIs' financial performance",
                "unit": "$ million",
                "frequency": "Quarterly",
                "date_row": 4,
                "date_start_column": 2,
                "data_start_row": 6,
                "label_column": 1,
            },
        },
        "variants": [],
    },
    "ADI_QUARTERLY_CENTRALISED": {
        "id": "ADI_QUARTERLY_CENTRALISED",
        "name": "Authorised Deposit-taking Institution Centralised Publication",
        "description": (
            "Quarterly entity-level APRA publication containing key ADI capital data and "
            "liquidity ratios."
        ),
        "category": "banking",
        "frequency": "Quarterly",
        "frequencies": ["Q"],
        "geographies": ["aus"],
        "tags": ["apra", "adi", "banking", "capital", "liquidity", "entity"],
        "aliases": ["adi centralised publication", "quarterly adi centralised"],
        "landing_url": (
            "https://www.apra.gov.au/quarterly-authorised-deposit-taking-institution-statistics"
        ),
        "link_patterns": [r"centralised publication.*xlsx"],
        "tables": {
            "table_1": {
                "sheet": "Table 1",
                "layout": "row_records",
                "title": "Regulatory capital",
                "unit": "$ million",
                "frequency": "Quarterly",
                "header_row": 3,
                "data_start_row": 4,
                "date_column": 1,
                "dimension_columns": {
                    "entity": 2,
                    "mutual_bank": 3,
                    "sector": 4,
                },
                "series_start_column": 5,
                "identity_columns": ["entity"],
            },
            "table_3": {
                "sheet": "Table 3",
                "layout": "row_records",
                "title": "Liquidity ratios",
                "unit": "ratio",
                "frequency": "Quarterly",
                "header_row": 3,
                "data_start_row": 4,
                "date_column": 1,
                "dimension_columns": {
                    "entity": 2,
                    "mutual_bank": 3,
                    "sector": 4,
                },
                "series_start_column": 5,
                "identity_columns": ["entity"],
            },
        },
        "variants": [],
    },
    "ADI_PROPERTY_EXPOSURES": {
        "id": "ADI_PROPERTY_EXPOSURES",
        "name": "Quarterly Authorised Deposit-taking Institution Property Exposures Statistics",
        "description": (
            "Quarterly aggregate commercial property exposures, residential mortgage "
            "exposures, and new residential mortgage lending for ADIs."
        ),
        "category": "banking",
        "frequency": "Quarterly",
        "frequencies": ["Q"],
        "geographies": ["aus"],
        "tags": ["apra", "adi", "banking", "property", "housing", "mortgages"],
        "aliases": [
            "quarterly adi property exposures",
            "adi property exposures statistics",
            "residential mortgage exposures",
        ],
        "landing_url": (
            "https://www.apra.gov.au/quarterly-authorised-deposit-taking-institution-statistics"
        ),
        "link_patterns": [r"property exposures statistics.*xlsx"],
        "tables": {
            "tab_1a": {
                "sheet": "Tab 1a",
                "layout": "matrix",
                "title": "Commercial property exposures",
                "unit": "$ million",
                "frequency": "Quarterly",
                "date_row": 4,
                "date_start_column": 3,
                "data_start_row": 6,
                "label_column": 1,
            },
            "tab_1b": {
                "sheet": "Tab 1b",
                "layout": "matrix",
                "title": "Residential property exposures",
                "unit": "$ million",
                "frequency": "Quarterly",
                "date_row": 4,
                "date_start_column": 3,
                "data_start_row": 6,
                "label_column": 1,
            },
            "tab_1c": {
                "sheet": "Tab 1c",
                "layout": "matrix",
                "title": "New housing loans funded",
                "unit": None,
                "frequency": "Quarterly",
                "date_row": 4,
                "date_start_column": 3,
                "data_start_row": 6,
                "label_column": 1,
            },
        },
        "variants": [],
    },
}
