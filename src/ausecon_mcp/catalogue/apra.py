from __future__ import annotations

_AASB17_INSURANCE_FRAMEWORK_BREAK = {
    "date": "2023-07-01",
    "label": "AASB 17 transition",
    "description": (
        "AASB 17 changed insurance accounting and APRA insurance reporting "
        "definitions from the September 2023 reference quarter; compare pre- "
        "and post-transition insurance performance series with care."
    ),
}


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
        "fallback_url": (
            "https://www.apra.gov.au/sites/default/files/2026-05/"
            "Monthly%20authorised%20deposit-taking%20institution%20statistics%20"
            "back-series%20March%202019%20-%20April%202026.xlsx"
        ),
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
        "audit": {
            "last_audited": "2026-05-18",
            "upstream_url": (
                "https://www.apra.gov.au/"
                "monthly-authorised-deposit-taking-institution-statistics"
            ),
            "upstream_title": "Monthly Authorised Deposit-taking Institution Statistics",
        },
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
        "fallback_url": (
            "https://www.apra.gov.au/sites/default/files/2026-03/"
            "Quarterly%20authorised%20deposit-taking%20institution%20performance-"
            "September%202004%20to%20December%202025.xlsx"
        ),
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
        "variants": [
            {
                "name": "total_capital_ratio",
                "aliases": ["adi capital ratio", "total capital ratio"],
                "apra_table_id": "key_stats",
                "apra_series_ids": [
                    "ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:total_capital_ratio"
                ],
            },
            {
                "name": "liquidity_coverage_ratio",
                "aliases": ["adi liquidity coverage ratio", "lcr"],
                "apra_table_id": "key_stats",
                "apra_series_ids": [
                    "ADI_QUARTERLY_PERFORMANCE:key_stats:"
                    "key_figures:liquidity_coverage_ratio_lcr"
                ],
            },
        ],
        "audit": {
            "last_audited": "2026-05-18",
            "upstream_url": (
                "https://www.apra.gov.au/"
                "quarterly-authorised-deposit-taking-institution-statistics"
            ),
            "upstream_title": (
                "Quarterly Authorised Deposit-taking Institution Performance Statistics"
            ),
        },
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
        "fallback_url": (
            "https://www.apra.gov.au/sites/default/files/2026-03/"
            "Authorised%20deposit-taking%20institution%20centralised%20publication%20-%20"
            "March%202013%20to%20December%202025.xlsx"
        ),
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
        "audit": {
            "last_audited": "2026-05-18",
            "upstream_url": (
                "https://www.apra.gov.au/"
                "quarterly-authorised-deposit-taking-institution-statistics"
            ),
            "upstream_title": "Authorised Deposit-taking Institution Centralised Publication",
        },
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
        "fallback_url": (
            "https://www.apra.gov.au/sites/default/files/2026-03/"
            "Quarterly%20authorised%20deposit-taking%20institution%20property%20"
            "exposures%20statistics%20December%202025.xlsx"
        ),
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
        "variants": [
            {
                "name": "commercial_property_exposure",
                "aliases": ["commercial property exposure", "commercial property actual exposures"],
                "apra_table_id": "tab_1a",
                "apra_series_ids": [
                    "ADI_PROPERTY_EXPOSURES:tab_1a:"
                    "commercial_property_actual_exposures:total_commercial_property_exposures"
                ],
            },
            {
                "name": "residential_mortgage_exposure",
                "aliases": ["residential mortgage exposure", "residential property exposure"],
                "apra_table_id": "tab_1b",
                "apra_series_ids": [
                    "ADI_PROPERTY_EXPOSURES:tab_1b:"
                    "credit_outstanding:total_credit_oustanding"
                ],
            },
        ],
        "audit": {
            "last_audited": "2026-05-18",
            "upstream_url": (
                "https://www.apra.gov.au/"
                "quarterly-authorised-deposit-taking-institution-statistics"
            ),
            "upstream_title": (
                "Quarterly Authorised Deposit-taking Institution Property Exposures Statistics"
            ),
        },
    },
    "APRA_SUPER_INDUSTRY": {
        "id": "APRA_SUPER_INDUSTRY",
        "name": "Quarterly Superannuation Industry Publication",
        "description": (
            "Quarterly aggregate superannuation industry statistics covering product "
            "counts, member assets, member accounts, and investment options."
        ),
        "category": "superannuation",
        "frequency": "Quarterly",
        "frequencies": ["Q"],
        "geographies": ["aus"],
        "tags": ["apra", "superannuation", "member assets", "member accounts"],
        "aliases": [
            "quarterly superannuation industry publication",
            "superannuation industry statistics",
            "superannuation assets",
        ],
        "landing_url": "https://www.apra.gov.au/quarterly-superannuation-industry-publication",
        "link_patterns": [r"Quarterly Superannuation Industry Publication.*XLSX"],
        "fallback_url": (
            "https://www.apra.gov.au/sites/default/files/2026-03/"
            "Quarterly%20Superannuation%20Industry%20Publication%20-%20December%202025.xlsx"
        ),
        "tables": {
            "table_2": {
                "sheet": "Table 2",
                "layout": "matrix",
                "title": "MySuper products",
                "unit": None,
                "frequency": "Quarterly",
                "date_row": 5,
                "date_start_column": 2,
                "data_start_row": 6,
                "label_column": 1,
            }
        },
        "variants": [
            {
                "name": "total_rse_member_assets",
                "aliases": ["superannuation total assets", "rse member assets"],
                "apra_table_id": "table_2",
                "apra_series_ids": ["APRA_SUPER_INDUSTRY:table_2:total_rse_member_assets"],
            },
            {
                "name": "total_rse_member_accounts",
                "aliases": ["superannuation member accounts", "rse member accounts"],
                "apra_table_id": "table_2",
                "apra_series_ids": ["APRA_SUPER_INDUSTRY:table_2:total_rse_member_accounts"],
            },
        ],
        "audit": {
            "last_audited": "2026-05-18",
            "upstream_url": "https://www.apra.gov.au/quarterly-superannuation-industry-publication",
            "upstream_title": "Quarterly Superannuation Industry Publication",
        },
    },
    "APRA_SUPER_FUND_LEVEL": {
        "id": "APRA_SUPER_FUND_LEVEL",
        "name": "Quarterly Fund-Level Statistics",
        "description": (
            "Quarterly fund-level superannuation statistics covering membership, "
            "member benefits, demographics, and asset allocation."
        ),
        "category": "superannuation",
        "frequency": "Quarterly",
        "frequencies": ["Q"],
        "geographies": ["aus"],
        "tags": ["apra", "superannuation", "fund level", "member benefits"],
        "aliases": ["quarterly fund-level statistics", "superannuation fund statistics"],
        "landing_url": "https://www.apra.gov.au/quarterly-fund-level-statistics",
        "link_patterns": [r"Quarterly Superannuation Fund Statistics.*XLSX"],
        "fallback_url": (
            "https://www.apra.gov.au/sites/default/files/2026-03/"
            "Quarterly%20Superannuation%20Fund%20Statistics%20December%202025.xlsx"
        ),
        "tables": {
            "table_1": {
                "sheet": "Table 1",
                "layout": "row_records",
                "title": "Fund membership profile",
                "unit": None,
                "frequency": "Quarterly",
                "header_row": 4,
                "data_start_row": 7,
                "date_column": 1,
                "dimension_columns": {
                    "fund": 2,
                    "abn": 3,
                    "regulatory_classification": 4,
                    "fund_type": 5,
                    "membership_base": 6,
                    "licensee": 7,
                    "ownership_type": 8,
                    "profit_status": 9,
                    "board_structure": 10,
                },
                "series_start_column": 11,
                "identity_columns": ["abn"],
            }
        },
        "variants": [],
        "audit": {
            "last_audited": "2026-05-18",
            "upstream_url": "https://www.apra.gov.au/quarterly-fund-level-statistics",
            "upstream_title": "Quarterly Fund-Level Statistics",
        },
    },
    "APRA_GENERAL_INSURANCE_PERFORMANCE": {
        "id": "APRA_GENERAL_INSURANCE_PERFORMANCE",
        "name": "Quarterly General Insurance Performance Statistics",
        "description": (
            "Quarterly general-insurance performance database covering revenue, "
            "expenses, capital, assets, liabilities, and class-of-business breakdowns."
        ),
        "category": "insurance",
        "frequency": "Quarterly",
        "frequencies": ["Q"],
        "geographies": ["aus"],
        "tags": ["apra", "general insurance", "premium revenue", "claims"],
        "aliases": ["general insurance performance", "general insurance statistics"],
        "landing_url": (
            "https://www.apra.gov.au/quarterly-general-insurance-performance-statistics"
        ),
        "link_patterns": [r"Quarterly general insurance performance statistics database.*XLSX"],
        "fallback_url": (
            "https://www.apra.gov.au/sites/default/files/2026-05/"
            "Quarterly%20general%20insurance%20performance%20statistics%20database%20"
            "September%202023%20to%20March%202026.xlsx"
        ),
        "tables": {
            "database": {
                "sheet": "Database",
                "layout": "row_records",
                "title": "General insurance performance database",
                "unit": "$",
                "frequency": "Quarterly",
                "header_row": 1,
                "data_start_row": 2,
                "date_column": 1,
                "dimension_columns": {
                    "data_item": 2,
                    "category": 3,
                    "subject": 4,
                    "stock_or_flow": 5,
                    "industry_segment": 6,
                    "industry_segment_group": 7,
                    "class_of_business": 8,
                    "class_of_business_category": 9,
                    "class_of_business_group": 10,
                    "counterparty_grade": 11,
                    "state_or_territory": 12,
                    "stress_scenario_type": 13,
                },
                "series_start_column": 14,
                "identity_columns": [
                    "data_item",
                    "category",
                    "subject",
                    "stock_or_flow",
                    "industry_segment",
                    "industry_segment_group",
                    "class_of_business",
                    "class_of_business_category",
                    "class_of_business_group",
                    "counterparty_grade",
                    "state_or_territory",
                    "stress_scenario_type",
                ],
            }
        },
        "variants": [
            {
                "name": "insurance_revenue",
                "aliases": ["general insurance premium revenue", "general insurance revenue"],
                "apra_table_id": "database",
                "apra_series_ids": [
                    "APRA_GENERAL_INSURANCE_PERFORMANCE:database:"
                    "insurance_revenue:insurance_revenue:financial_performance:"
                    "flow:total_industry:value"
                ],
            },
            {
                "name": "insurance_service_expense",
                "aliases": ["general insurance claims expense", "general insurance claims"],
                "apra_table_id": "database",
                "apra_series_ids": [
                    "APRA_GENERAL_INSURANCE_PERFORMANCE:database:"
                    "insurance_service_expense:insurance_service_expense:"
                    "financial_performance:flow:total_industry:value"
                ],
            },
        ],
        "framework_breaks": [_AASB17_INSURANCE_FRAMEWORK_BREAK],
        "audit": {
            "last_audited": "2026-05-18",
            "upstream_url": (
                "https://www.apra.gov.au/"
                "quarterly-general-insurance-performance-statistics"
            ),
            "upstream_title": "Quarterly General Insurance Performance Statistics",
        },
    },
    "APRA_LIFE_INSURANCE_PERFORMANCE": {
        "id": "APRA_LIFE_INSURANCE_PERFORMANCE",
        "name": "Quarterly Life Insurance Performance Statistics",
        "description": (
            "Quarterly life-insurance performance database covering insurance revenue, "
            "service expenses, capital, assets, liabilities, premiums, and claims."
        ),
        "category": "insurance",
        "frequency": "Quarterly",
        "frequencies": ["Q"],
        "geographies": ["aus"],
        "tags": ["apra", "life insurance", "premium revenue", "claims"],
        "aliases": ["life insurance performance", "life insurance statistics"],
        "landing_url": "https://www.apra.gov.au/quarterly-life-insurance-performance-statistics",
        "link_patterns": [r"Quarterly life insurance performance statistics database.*XLSX"],
        "fallback_url": (
            "https://www.apra.gov.au/sites/default/files/2026-05/"
            "Quarterly%20life%20insurance%20performance%20statistics%20database%20"
            "September%202023%20to%20March%202026.xlsx"
        ),
        "tables": {
            "database": {
                "sheet": "Database",
                "layout": "row_records",
                "title": "Life insurance performance database",
                "unit": "$",
                "frequency": "Quarterly",
                "header_row": 1,
                "data_start_row": 2,
                "date_column": 1,
                "dimension_columns": {
                    "data_item": 2,
                    "subject": 3,
                    "category": 4,
                    "stock_or_flow": 5,
                    "reporting_structure": 6,
                    "product_group": 7,
                    "product_group_type": 8,
                    "superannuation_or_ordinary_business": 9,
                },
                "series_start_column": 10,
                "identity_columns": [
                    "data_item",
                    "subject",
                    "category",
                    "stock_or_flow",
                    "reporting_structure",
                    "product_group",
                    "product_group_type",
                    "superannuation_or_ordinary_business",
                ],
            }
        },
        "variants": [
            {
                "name": "insurance_revenue",
                "aliases": ["life insurance premium revenue", "life insurance revenue"],
                "apra_table_id": "database",
                "apra_series_ids": [
                    "APRA_LIFE_INSURANCE_PERFORMANCE:database:"
                    "insurance_revenue:financial_performance:insurance_revenue:"
                    "flow:total_entity:value"
                ],
            },
            {
                "name": "insurance_service_expense",
                "aliases": ["life insurance claims expense", "life insurance claims"],
                "apra_table_id": "database",
                "apra_series_ids": [
                    "APRA_LIFE_INSURANCE_PERFORMANCE:database:"
                    "insurance_service_expense:financial_performance:"
                    "insurance_service_expense:flow:total_entity:value"
                ],
            },
        ],
        "framework_breaks": [_AASB17_INSURANCE_FRAMEWORK_BREAK],
        "audit": {
            "last_audited": "2026-05-18",
            "upstream_url": (
                "https://www.apra.gov.au/"
                "quarterly-life-insurance-performance-statistics"
            ),
            "upstream_title": "Quarterly Life Insurance Performance Statistics",
        },
    },
    "APRA_PHI_PERFORMANCE": {
        "id": "APRA_PHI_PERFORMANCE",
        "name": "Quarterly Private Health Insurance Performance Statistics",
        "description": (
            "Quarterly private health insurance performance database covering premium "
            "revenue, claims, expenses, assets, liabilities, and capital."
        ),
        "category": "insurance",
        "frequency": "Quarterly",
        "frequencies": ["Q"],
        "geographies": ["aus"],
        "tags": ["apra", "private health insurance", "premium revenue", "claims"],
        "aliases": ["private health insurance performance", "phi performance statistics"],
        "landing_url": (
            "https://www.apra.gov.au/"
            "quarterly-private-health-insurance-performance-statistics"
        ),
        "link_patterns": [
            r"Quarterly private health insurance performance statistics database.*XLSX"
        ],
        "fallback_url": (
            "https://www.apra.gov.au/sites/default/files/2026-05/"
            "Quarterly%20private%20health%20insurance%20performance%20statistics%20"
            "database%20-%20September%202023%20to%20March%202026.xlsx"
        ),
        "tables": {
            "database": {
                "sheet": "Database",
                "layout": "row_records",
                "title": "Private health insurance performance database",
                "unit": "$",
                "frequency": "Quarterly",
                "header_row": 1,
                "data_start_row": 2,
                "date_column": 1,
                "dimension_columns": {
                    "data_item": 2,
                    "subject": 3,
                    "category": 4,
                    "stock_or_flow": 5,
                },
                "series_start_column": 6,
                "identity_columns": ["data_item", "subject", "category", "stock_or_flow"],
            }
        },
        "variants": [
            {
                "name": "hib_premium_revenue",
                "aliases": ["phi premium revenue", "health insurance premium revenue"],
                "apra_table_id": "database",
                "apra_series_ids": [
                    "APRA_PHI_PERFORMANCE:database:"
                    "hib_premium_revenue:financial_performance_supplementary:"
                    "revenue:flow:value"
                ],
            },
            {
                "name": "hib_insurance_claims",
                "aliases": ["phi claims expense", "health insurance claims"],
                "apra_table_id": "database",
                "apra_series_ids": [
                    "APRA_PHI_PERFORMANCE:database:"
                    "hib_insurance_claims:financial_performance_supplementary:"
                    "expenses:flow:value"
                ],
            },
        ],
        "framework_breaks": [_AASB17_INSURANCE_FRAMEWORK_BREAK],
        "audit": {
            "last_audited": "2026-05-18",
            "upstream_url": (
                "https://www.apra.gov.au/"
                "quarterly-private-health-insurance-performance-statistics"
            ),
            "upstream_title": "Quarterly Private Health Insurance Performance Statistics",
        },
    },
    "APRA_PHI_MEMBERSHIP": {
        "id": "APRA_PHI_MEMBERSHIP",
        "name": "Quarterly Private Health Insurance Membership Coverage",
        "description": (
            "Quarterly private health insurance membership coverage by state and "
            "territory, including national hospital-treatment coverage."
        ),
        "category": "insurance",
        "frequency": "Quarterly",
        "frequencies": ["Q"],
        "geographies": ["aus"],
        "tags": ["apra", "private health insurance", "membership", "coverage"],
        "aliases": [
            "private health insurance membership",
            "phi membership",
            "hospital treatment coverage",
        ],
        "landing_url": "https://www.apra.gov.au/quarterly-private-health-insurance-statistics",
        "link_patterns": [r"Quarterly Private Health Insurance Membership Coverage.*XLSX"],
        "fallback_url": (
            "https://www.apra.gov.au/sites/default/files/2026-05/"
            "Quarterly%20Private%20Health%20Insurance%20Membership%20Coverage%20"
            "March%202026.xlsx"
        ),
        "tables": {
            "t1": {
                "sheet": "T1",
                "layout": "period_rows",
                "title": "Hospital treatment membership coverage",
                "unit": "000 persons",
                "frequency": "Quarterly",
                "header_row": 2,
                "data_start_row": 3,
                "month_column": 1,
                "year_column": 2,
                "metric_column": 3,
                "series_start_column": 5,
            }
        },
        "variants": [
            {
                "name": "hospital_coverage",
                "aliases": ["phi membership", "hospital treatment coverage"],
                "apra_table_id": "t1",
                "apra_series_ids": ["APRA_PHI_MEMBERSHIP:t1:aust:coverage_000"],
            }
        ],
        "audit": {
            "last_audited": "2026-05-18",
            "upstream_url": "https://www.apra.gov.au/quarterly-private-health-insurance-statistics",
            "upstream_title": "Quarterly Private Health Insurance Membership Coverage",
        },
    },
}
