ABS_CATALOGUE = {
    "CPI": {
        "id": "CPI",
        "source": "abs",
        "name": "Consumer Price Index",
        "description": "Consumer prices, headline inflation, and underlying inflation measures.",
        "frequency": "Quarterly",
        "category": "prices_inflation",
        "aliases": [
            "cpi",
            "consumer price index",
            "headline inflation",
            "trimmed mean",
            "weighted median",
        ],
        "tags": [
            "inflation",
            "consumer prices",
            "prices",
            "headline cpi",
            "underlying inflation",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [
            {
                "name": "headline",
                "aliases": ["headline cpi", "all groups"],
                "abs_key": "1.10001.10.50.Q",
            },
            {"name": "trimmed_mean", "aliases": ["core", "trimmed mean"], "abs_key": None},
            {"name": "weighted_median", "aliases": ["weighted median"], "abs_key": None},
        ],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/CPI/latest",
            "upstream_title": "Consumer Price Index (CPI)",
        },
    },
    "CPI_M": {
        "id": "CPI_M",
        "source": "abs",
        "name": "Monthly Consumer Price Index Indicator (Ceased)",
        "description": (
            "Ceased monthly CPI indicator dataflow. Superseded by the ABS monthly CPI "
            "collection under a new dataflow; retained here for historical reference."
        ),
        "frequency": "Monthly",
        "category": "prices_inflation",
        "aliases": [
            "monthly cpi",
            "monthly cpi indicator",
            "monthly inflation",
            "mcpi",
        ],
        "tags": [
            "inflation nowcast",
            "monthly prices",
            "consumer prices",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
        "ceased": True,
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/CPI_M/latest",
            "upstream_title": "Monthly Consumer Price Index (CPI) indicator",
        },
    },
    "PPI": {
        "id": "PPI",
        "source": "abs",
        "name": "Producer Price Indexes",
        "description": "Producer, export, and import price indexes across major industries.",
        "frequency": "Quarterly",
        "category": "prices_inflation",
        "aliases": [
            "ppi",
            "producer price indexes",
            "producer prices",
        ],
        "tags": [
            "import prices",
            "export prices",
            "upstream inflation",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [
            {"name": "producer", "aliases": ["producer prices"], "abs_key": None},
            {"name": "export", "aliases": ["export prices"], "abs_key": None},
            {"name": "import", "aliases": ["import prices"], "abs_key": None},
        ],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/PPI/latest",
            "upstream_title": "Producer Price Indexes by Industry",
        },
    },
    "PPI_FD": {
        "id": "PPI_FD",
        "source": "abs",
        "name": "Producer Price Index by Final Demand",
        "description": "Producer prices through final demand stages of production.",
        "frequency": "Quarterly",
        "category": "prices_inflation",
        "aliases": [
            "ppi final demand",
            "final demand ppi",
            "stage of production prices",
        ],
        "tags": [
            "upstream inflation",
            "production stages",
            "final demand",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/PPI_FD/latest",
            "upstream_title": "Producer Price Indexes, Final Demand",
        },
    },
    "ITPI_EXP": {
        "id": "ITPI_EXP",
        "source": "abs",
        "name": "International Trade Price Index - Exports",
        "description": "Price index for Australian exports by commodity classification.",
        "frequency": "Quarterly",
        "category": "prices_inflation",
        "aliases": [
            "export price index",
            "international trade prices exports",
            "export prices",
        ],
        "tags": [
            "terms of trade",
            "export deflator",
            "external prices",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/ITPI_EXP/latest",
            "upstream_title": "Export Price Index",
        },
    },
    "ITPI_IMP": {
        "id": "ITPI_IMP",
        "source": "abs",
        "name": "International Trade Price Index - Imports",
        "description": "Price index for Australian imports by commodity classification.",
        "frequency": "Quarterly",
        "category": "prices_inflation",
        "aliases": [
            "import price index",
            "international trade prices imports",
            "import prices",
        ],
        "tags": [
            "terms of trade",
            "import deflator",
            "external prices",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/ITPI_IMP/latest",
            "upstream_title": "Import Price Index",
        },
    },
    "WPI": {
        "id": "WPI",
        "source": "abs",
        "name": "Wage Price Index",
        "description": "Wage inflation across sectors and industries in Australia.",
        "frequency": "Quarterly",
        "category": "prices_inflation",
        "aliases": [
            "wpi",
            "wage price index",
            "wage inflation",
        ],
        "tags": [
            "wages",
            "labour costs",
            "earnings",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [
            {
                "name": "headline_wpi",
                "aliases": ["headline", "total hourly rates"],
                "abs_key": "3.THRPEB.7.TOT.20.AUS.Q",
            },
        ],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/WPI/latest",
            "upstream_title": "Wage Price Index",
        },
    },
    "AWE": {
        "id": "AWE",
        "source": "abs",
        "name": "Average Weekly Earnings",
        "description": "Average weekly ordinary-time and total earnings by industry and sector.",
        "frequency": "Biannual",
        "category": "labour",
        "aliases": [
            "average weekly earnings",
            "awe",
            "weekly earnings",
        ],
        "tags": [
            "earnings",
            "wages",
            "pay",
        ],
        "frequencies": ["A"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/AWE/latest",
            "upstream_title": "Average Weekly Earnings",
        },
    },
    "SLCI": {
        "id": "SLCI",
        "upstream_id": "LCI",
        "source": "abs",
        "name": "Selected Living Cost Indexes",
        "description": (
            "Quarterly price indexes tracking changes in living costs for selected "
            "Australian household types (employee, age pensioner, self-funded retiree, "
            "other government transfer recipient, and pensioner & beneficiary)."
        ),
        "frequency": "Quarterly",
        "category": "prices_inflation",
        "aliases": [
            "selected living cost indexes",
            "living cost indexes",
            "living cost index",
            "slci",
            "cost of living",
            "household living costs",
            "pensioner living costs",
            "employee living costs",
        ],
        "tags": [
            "cost of living",
            "household prices",
            "pensioner inflation",
            "employee inflation",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [
            {"name": "employee", "aliases": ["employee households"], "abs_key": None},
            {
                "name": "age_pensioner",
                "aliases": ["age pensioner households"],
                "abs_key": None,
            },
            {
                "name": "self_funded_retiree",
                "aliases": ["self-funded retiree households"],
                "abs_key": None,
            },
            {
                "name": "other_transfer",
                "aliases": ["other government transfer recipient households"],
                "abs_key": None,
            },
            {
                "name": "pensioner_beneficiary",
                "aliases": ["pensioner and beneficiary households"],
                "abs_key": None,
            },
        ],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/LCI/latest",
            "upstream_title": "Selected Living Cost Indexes",
        },
    },
    "LF": {
        "id": "LF",
        "source": "abs",
        "name": "Labour Force Survey",
        "description": "Employment, unemployment, participation, and labour market conditions.",
        "frequency": "Monthly",
        "category": "labour",
        "aliases": [
            "labour force",
            "labour force survey",
            "employment",
            "unemployment",
            "unemployment rate",
            "jobless rate",
        ],
        "tags": [
            "participation",
            "jobs",
            "labour market",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [
            {
                "name": "employment",
                "aliases": ["employed persons"],
                "abs_key": "M3.3.1599.20.AUS.M",
            },
            {
                "name": "unemployment_rate",
                "aliases": ["unemployment", "jobless rate"],
                "abs_key": "M13.3.1599.20.AUS.M",
            },
            {
                "name": "participation_rate",
                "aliases": ["participation"],
                "abs_key": "M12.3.1599.20.AUS.M",
            },
        ],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/LF/latest",
            "upstream_title": "Labour Force",
        },
    },
    "LF_HOURS": {
        "id": "LF_HOURS",
        "source": "abs",
        "name": "Labour Force - Hours Worked",
        "description": "Hours worked by industry, sector, and full-time/part-time status.",
        "frequency": "Monthly",
        "category": "labour",
        "aliases": [
            "hours worked",
            "labour hours",
            "aggregate hours",
        ],
        "tags": [
            "underutilisation",
            "hours",
            "working time",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/LF_HOURS/latest",
            "upstream_title": "Labour Force: Hours worked by sector",
        },
    },
    "LF_UNDER": {
        "id": "LF_UNDER",
        "structure_id": "DS_LF_UNDER",
        "source": "abs",
        "name": "Labour Force - Underutilisation",
        "description": "Underemployment, underutilisation, and slack labour market indicators.",
        "frequency": "Monthly",
        "category": "labour",
        "aliases": [
            "underemployment",
            "underutilisation",
            "labour market slack",
        ],
        "tags": [
            "spare capacity",
            "hours sought",
            "involuntary part-time",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/LF_UNDER/latest",
            "upstream_title": "Labour force - underemployment and underutilisation",
        },
    },
    "LABOUR_ACCT_Q": {
        "id": "LABOUR_ACCT_Q",
        "source": "abs",
        "name": "Australian Labour Account, Quarterly",
        "description": (
            "Integrated labour market indicators reconciling firm and household surveys."
        ),
        "frequency": "Quarterly",
        "category": "labour",
        "aliases": [
            "labour account",
            "quarterly labour account",
            "labour accounts",
        ],
        "tags": [
            "jobs framework",
            "integrated labour",
            "multiple jobholders",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/LABOUR_ACCT_Q/latest",
            "upstream_title": (
                "Labour Account Australia, Final Quarterly Balanced: "
                "Subdivision, Division and Total All Industries"
            ),
        },
    },
    "LABOUR_ACCT_A": {
        "id": "LABOUR_ACCT_A",
        "upstream_id": "ABS_LABOUR_ACCT",
        "source": "abs",
        "name": "Australian Labour Account, Annual Balanced",
        "description": (
            "Annual balanced labour account by industry subdivision, division, and "
            "total all industries. Reconciles employer and household measures of "
            "employment, hours, jobs, and labour income."
        ),
        "frequency": "Annual",
        "category": "labour",
        "aliases": [
            "annual labour account",
            "labour account annual",
            "balanced labour account",
            "labour account by industry",
        ],
        "tags": [
            "industry",
            "balanced",
            "annual",
            "jobs framework",
        ],
        "frequencies": ["A"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/ABS_LABOUR_ACCT/latest",
            "upstream_title": (
                "Labour Account Australia, Annual Balanced: Subdivision, Division "
                "and Total All Industries"
            ),
        },
    },
    "JV": {
        "id": "JV",
        "source": "abs",
        "name": "Job Vacancies",
        "description": "Quarterly job vacancies across industries and states.",
        "frequency": "Quarterly",
        "category": "labour",
        "aliases": [
            "job vacancies",
            "vacancies",
            "hiring demand",
        ],
        "tags": [
            "labour demand",
            "recruitment",
            "vacant positions",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/JV/latest",
            "upstream_title": "Job Vacancies",
        },
    },
    "ANA_AGG": {
        "id": "ANA_AGG",
        "source": "abs",
        "name": "National Accounts - Key Aggregates",
        "description": (
            "Quarterly national accounts aggregates including GDP, gross national income, "
            "and domestic demand."
        ),
        "frequency": "Quarterly",
        "category": "national_accounts",
        "aliases": [
            "gdp",
            "gdp growth",
            "national accounts",
            "national accounts aggregates",
            "economic growth",
        ],
        "tags": [
            "output",
            "aggregates",
            "gni",
            "quarterly growth",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [
            {
                "name": "gdp_growth",
                "aliases": ["gdp growth", "economic growth", "real gdp growth"],
                "abs_key": "M2.GPM.20.AUS.Q",
            }
        ],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/ANA_AGG/latest",
            "upstream_title": "Australian National Accounts Key Aggregates",
        },
    },
    "ANA_EXP": {
        "id": "ANA_EXP",
        "source": "abs",
        "name": "National Accounts - Expenditure",
        "description": (
            "Quarterly national accounts expenditure-side components: consumption, "
            "investment, government, and net exports."
        ),
        "frequency": "Quarterly",
        "category": "national_accounts",
        "aliases": [
            "national accounts expenditure",
            "gdp expenditure",
            "gdpe",
        ],
        "tags": [
            "consumption",
            "investment",
            "expenditure components",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/ANA_EXP/latest",
            "upstream_title": (
                "Australian National Accounts - Expenditure on Gross Domestic Product (GDP (E))"
            ),
        },
    },
    "ANA_INC": {
        "id": "ANA_INC",
        "source": "abs",
        "name": "National Accounts - Income",
        "description": (
            "Quarterly national accounts income-side components: compensation of employees, "
            "gross operating surplus, and gross mixed income."
        ),
        "frequency": "Quarterly",
        "category": "national_accounts",
        "aliases": [
            "national accounts income",
            "gdp income",
            "gdpi",
        ],
        "tags": [
            "labour share",
            "profit share",
            "income components",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/ANA_INC/latest",
            "upstream_title": (
                "Australian National Accounts - Income from Gross Domestic Product (GDP (I))"
            ),
        },
    },
    "ANA_IND_GVA": {
        "id": "ANA_IND_GVA",
        "source": "abs",
        "name": "National Accounts - Production (GVA by Industry)",
        "description": (
            "Quarterly national accounts production-side gross value added by "
            "industry (ANZSIC division). Complements the expenditure and income "
            "measures for cross-checking quarterly GDP."
        ),
        "frequency": "Quarterly",
        "category": "national_accounts",
        "aliases": [
            "gdp production",
            "gdpp",
            "gva by industry",
            "industry gross value added",
            "production measure of gdp",
        ],
        "tags": [
            "production",
            "industry",
            "gross value added",
            "anzsic",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/ANA_IND_GVA/latest",
            "upstream_title": (
                "Australian National Accounts - Production of Gross Domestic Product (GDP (P))"
            ),
        },
    },
    "ANA_SFD": {
        "id": "ANA_SFD",
        "source": "abs",
        "name": "State Final Demand",
        "description": (
            "Quarterly state final demand (household consumption, private and "
            "public investment, government consumption) by state and territory. "
            "Key input for state-level activity analysis."
        ),
        "frequency": "Quarterly",
        "category": "national_accounts",
        "aliases": [
            "state final demand",
            "sfd",
            "state demand",
            "state gdp proxy",
        ],
        "tags": [
            "state",
            "final demand",
            "consumption",
            "investment",
        ],
        "frequencies": ["Q"],
        "geographies": [
            "national",
            "nsw",
            "vic",
            "qld",
            "sa",
            "wa",
            "tas",
            "nt",
            "act",
        ],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/ANA_SFD/latest",
            "upstream_title": "Australian National Accounts - State Final Demand",
        },
    },
    "RT": {
        "id": "RT",
        "source": "abs",
        "name": "Retail Trade (Ceased)",
        "description": (
            "Ceased monthly retail trade dataflow. Superseded by a new ABS monthly "
            "retail indicator; retained here for historical reference."
        ),
        "frequency": "Monthly",
        "category": "activity",
        "aliases": [
            "retail trade",
            "retail sales",
            "retail turnover",
        ],
        "tags": [
            "consumer spending",
            "household demand",
            "shops",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
        "ceased": True,
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/RT/latest",
            "upstream_title": "Retail Trade",
        },
    },
    "BUSINESS_TURNOVER": {
        "id": "BUSINESS_TURNOVER",
        "source": "abs",
        "name": "Monthly Business Turnover Indicator (Ceased)",
        "description": (
            "Ceased 2025-11-10. Previously tracked monthly business turnover growth "
            "across industry divisions; retained here for historical reference."
        ),
        "frequency": "Monthly",
        "category": "activity",
        "aliases": [
            "business turnover",
            "business sales",
            "industry turnover",
        ],
        "tags": [
            "business revenue",
            "activity nowcast",
            "industry growth",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
        "ceased": True,
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/BUSINESS_TURNOVER/latest",
            "upstream_title": "Monthly Business Turnover Indicator",
        },
    },
    "QBIS": {
        "id": "QBIS",
        "source": "abs",
        "name": "Quarterly Business Indicators Survey",
        "description": (
            "Company profits, inventories, sales, and wages indicators for the business sector."
        ),
        "frequency": "Quarterly",
        "category": "activity",
        "aliases": [
            "business indicators",
            "qbis",
            "company profits",
            "inventories",
        ],
        "tags": [
            "sales",
            "profits",
            "private sector activity",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [
            {"name": "profits", "aliases": ["company profits"], "abs_key": None},
            {"name": "inventories", "aliases": [], "abs_key": None},
            {"name": "sales", "aliases": [], "abs_key": None},
            {"name": "wages", "aliases": [], "abs_key": None},
        ],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/QBIS/latest",
            "upstream_title": "Business Indicators",
        },
    },
    "HSI_M": {
        "id": "HSI_M",
        "source": "abs",
        "name": "Monthly Household Spending Indicator",
        "description": "Monthly household spending aggregates across major consumption groups.",
        "frequency": "Monthly",
        "category": "activity",
        "aliases": [
            "household spending",
            "monthly household spending indicator",
            "mhsi",
            "card spending",
        ],
        "tags": [
            "consumer activity",
            "payments",
            "discretionary spending",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/HSI_M/latest",
            "upstream_title": "Monthly Household Spending Indicator",
        },
    },
    "CAPEX": {
        "id": "CAPEX",
        "source": "abs",
        "name": "Private New Capital Expenditure and Expected Expenditure",
        "description": (
            "Actual and expected private business capital expenditure by industry and asset."
        ),
        "frequency": "Quarterly",
        "category": "activity",
        "aliases": [
            "capex",
            "business investment",
            "capital expenditure",
        ],
        "tags": [
            "investment",
            "business capex",
            "expectations",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/CAPEX/latest",
            "upstream_title": "Private New Capital Expenditure and Expected Expenditure",
        },
    },
    "BUILDING_ACTIVITY": {
        "id": "BUILDING_ACTIVITY",
        "source": "abs",
        "name": "Building Activity",
        "description": (
            "Dwelling and non-residential building commencements, completions, and work done."
        ),
        "frequency": "Quarterly",
        "category": "housing_construction",
        "aliases": [
            "building activity",
            "building approvals",
            "dwelling commencements",
            "building completions",
        ],
        "tags": [
            "construction pipeline",
            "residential activity",
            "new dwellings",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/BUILDING_ACTIVITY/latest",
            "upstream_title": "Building Activity",
        },
    },
    "CWD": {
        "id": "CWD",
        "source": "abs",
        "name": "Construction Work Done",
        "description": "Engineering and building construction activity across sectors.",
        "frequency": "Quarterly",
        "category": "housing_construction",
        "aliases": [
            "construction work done",
            "construction activity",
            "building activity value",
        ],
        "tags": [
            "engineering construction",
            "residential building",
            "non-residential building",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [
            {"name": "engineering", "aliases": ["engineering construction"], "abs_key": None},
            {"name": "residential", "aliases": ["residential building"], "abs_key": None},
            {
                "name": "non_residential",
                "aliases": ["non-residential", "non-residential building"],
                "abs_key": None,
            },
        ],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/CWD/latest",
            "upstream_title": "Construction Work Done, Preliminary",
        },
    },
    "EWD": {
        "id": "EWD",
        "source": "abs",
        "name": "Engineering Construction Work Done",
        "description": (
            "Quarterly preliminary engineering construction work done, split by "
            "sector (private / public) and type of activity. Leading indicator "
            "for infrastructure and resource-sector investment."
        ),
        "frequency": "Quarterly",
        "category": "housing_construction",
        "aliases": [
            "engineering construction",
            "engineering construction work done",
            "infrastructure construction",
        ],
        "tags": [
            "engineering construction",
            "infrastructure",
            "resources investment",
            "preliminary",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/EWD/latest",
            "upstream_title": "Engineering Construction Work Done, Preliminary",
        },
    },
    "RES_DWELL": {
        "id": "RES_DWELL",
        "source": "abs",
        "name": "Residential Dwellings - Value and Number",
        "description": "Mean price and number of residential dwellings in Australia.",
        "frequency": "Quarterly",
        "category": "housing_construction",
        "aliases": [
            "residential dwellings",
            "dwelling stock",
            "housing stock",
        ],
        "tags": [
            "dwelling prices",
            "residential stock",
            "property",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/RES_DWELL/latest",
            "upstream_title": (
                "Residential Dwellings: Unstratified Medians and Transfer Counts "
                "by Dwelling Type, GCCSA and Rest of State"
            ),
        },
    },
    "RPPI": {
        "id": "RPPI",
        "source": "abs",
        "name": "Residential Property Price Index (Ceased)",
        "description": (
            "Ceased residential property price index dataflow. Superseded by a new "
            "ABS property prices dataflow; retained here for historical reference."
        ),
        "frequency": "Quarterly",
        "category": "housing_construction",
        "aliases": [
            "residential property price index",
            "rppi",
            "house prices",
        ],
        "tags": [
            "dwelling prices",
            "housing market",
            "property prices",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "ceased": True,
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/RPPI/latest",
            "upstream_title": "Residential Property Price Index",
        },
    },
    "ITGS": {
        "id": "ITGS",
        "source": "abs",
        "name": "International Trade in Goods and Services",
        "description": "Exports, imports, and trade balance indicators for Australia.",
        "frequency": "Monthly",
        "category": "external_sector",
        "aliases": [
            "international trade",
            "trade balance",
            "exports and imports",
        ],
        "tags": [
            "exports",
            "imports",
            "goods and services trade",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [
            {"name": "exports", "aliases": [], "abs_key": None},
            {"name": "imports", "aliases": [], "abs_key": None},
            {
                "name": "trade_balance",
                "aliases": ["net exports"],
                "abs_key": "M1.170.20.AUS.M",
            },
        ],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/ITGS/latest",
            "upstream_title": "International Trade in Goods",
        },
    },
    "MERCH_EXP": {
        "id": "MERCH_EXP",
        "source": "abs",
        "name": "International Merchandise Exports",
        "description": "Monthly merchandise export values by commodity and country.",
        "frequency": "Monthly",
        "category": "external_sector",
        "aliases": [
            "merchandise exports",
            "goods exports",
            "export values",
        ],
        "tags": [
            "exports",
            "commodities",
            "goods trade",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/MERCH_EXP/latest",
            "upstream_title": "Merchandise Exports by Commodity (SITC), Country and State",
        },
    },
    "MERCH_IMP": {
        "id": "MERCH_IMP",
        "source": "abs",
        "name": "International Merchandise Imports",
        "description": "Monthly merchandise import values by commodity and country.",
        "frequency": "Monthly",
        "category": "external_sector",
        "aliases": [
            "merchandise imports",
            "goods imports",
            "import values",
        ],
        "tags": [
            "imports",
            "goods trade",
            "trade partners",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/MERCH_IMP/latest",
            "upstream_title": "Merchandise Imports by Commodity (SITC), Country and State",
        },
    },
    "BOP": {
        "id": "BOP",
        "source": "abs",
        "name": "Balance of Payments",
        "description": "Current account, capital account, and financial account aggregates.",
        "frequency": "Quarterly",
        "category": "external_sector",
        "aliases": [
            "balance of payments",
            "current account",
            "external balance",
        ],
        "tags": [
            "financial account",
            "trade in income",
            "net exports",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [
            {"name": "current_account", "aliases": [], "abs_key": None},
            {"name": "capital_account", "aliases": [], "abs_key": None},
            {"name": "financial_account", "aliases": [], "abs_key": None},
        ],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/BOP/latest",
            "upstream_title": "Balance of Payments",
        },
    },
    "BOP_GOODS": {
        "id": "BOP_GOODS",
        "source": "abs",
        "name": "Balance of Payments - Goods",
        "description": "Quarterly balance of payments on goods basis with adjustments.",
        "frequency": "Quarterly",
        "category": "external_sector",
        "aliases": [
            "balance of payments goods",
            "bop goods",
            "goods trade balance",
        ],
        "tags": [
            "net exports goods",
            "goods account",
            "merchandise balance",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/BOP_GOODS/latest",
            "upstream_title": "Balance of Payments: Goods Exports and Imports",
        },
    },
    "BOP_STATE": {
        "id": "BOP_STATE",
        "source": "abs",
        "name": "Balance of Payments by State",
        "description": (
            "Quarterly balance of payments decomposed by state and territory, "
            "covering goods and services, primary income, and secondary income."
        ),
        "frequency": "Quarterly",
        "category": "external_sector",
        "aliases": [
            "balance of payments by state",
            "state bop",
            "state exports",
        ],
        "tags": [
            "state",
            "current account",
            "goods and services",
        ],
        "frequencies": ["Q"],
        "geographies": [
            "nsw",
            "vic",
            "qld",
            "sa",
            "wa",
            "tas",
            "nt",
            "act",
        ],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/BOP_STATE/latest",
            "upstream_title": "Balance of Payments by State",
        },
    },
    "IIP": {
        "id": "IIP",
        "source": "abs",
        "name": "International Investment Position",
        "description": "Australia's foreign assets, liabilities, and net international investment.",
        "frequency": "Quarterly",
        "category": "external_sector",
        "aliases": [
            "international investment position",
            "iip",
            "foreign assets and liabilities",
        ],
        "tags": [
            "external debt",
            "net foreign liabilities",
            "foreign equity",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/IIP/latest",
            "upstream_title": "International Investment Position",
        },
    },
    "LEND_HOUSING": {
        "id": "LEND_HOUSING",
        "source": "abs",
        "name": "Lending Indicators - Housing",
        "description": "New loan commitments for owner-occupier and investor housing.",
        "frequency": "Monthly",
        "category": "credit_finance",
        "aliases": [
            "housing finance",
            "housing loan commitments",
            "new housing lending",
        ],
        "tags": [
            "mortgage flows",
            "owner-occupier",
            "investor",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [
            {"name": "owner_occupier", "aliases": ["owner-occupier"], "abs_key": None},
            {"name": "investor", "aliases": ["investment"], "abs_key": None},
        ],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/LEND_HOUSING/latest",
            "upstream_title": "Lending Indicators Housing Finance",
        },
    },
    "LEND_BUSINESS": {
        "id": "LEND_BUSINESS",
        "source": "abs",
        "name": "Lending Indicators - Business",
        "description": "New business loan commitments by purpose and industry.",
        "frequency": "Monthly",
        "category": "credit_finance",
        "aliases": [
            "business finance",
            "business lending commitments",
            "new business lending",
        ],
        "tags": [
            "business credit flows",
            "commercial lending",
            "loan commitments",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/LEND_BUSINESS/latest",
            "upstream_title": "Lending Indicators Business Finance",
        },
    },
    "LEND_PERSONAL": {
        "id": "LEND_PERSONAL",
        "source": "abs",
        "name": "Lending Indicators - Personal",
        "description": "New personal loan commitments including fixed-term and credit card.",
        "frequency": "Monthly",
        "category": "credit_finance",
        "aliases": [
            "personal finance",
            "personal lending commitments",
            "new personal lending",
        ],
        "tags": [
            "personal loans",
            "consumer credit flows",
            "loan commitments",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/LEND_PERSONAL/latest",
            "upstream_title": "Lending Indicators Personal Finance",
        },
    },
    "ERP_Q": {
        "id": "ERP_Q",
        "source": "abs",
        "name": "Estimated Resident Population, Quarterly",
        "description": (
            "Quarterly estimates of Australia's resident population by state and territory."
        ),
        "frequency": "Quarterly",
        "category": "demographics",
        "aliases": [
            "estimated resident population",
            "erp",
            "population",
        ],
        "tags": [
            "population growth",
            "states and territories",
            "demography",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/ERP_Q/latest",
            "upstream_title": (
                "Quarterly Population Estimates (ERP), by State/Territory, Sex and Age"
            ),
        },
    },
    "ERP_COMP_Q": {
        "id": "ERP_COMP_Q",
        "source": "abs",
        "name": "Population and Components of Change",
        "description": (
            "Quarterly population components: natural increase (births, deaths), "
            "net overseas migration, and net interstate migration by state and "
            "territory. Decomposes the headline ERP growth rate."
        ),
        "frequency": "Quarterly",
        "category": "demographics",
        "aliases": [
            "population components",
            "births deaths migration",
            "natural increase",
            "net overseas migration",
            "nom",
        ],
        "tags": [
            "natural increase",
            "migration",
            "births",
            "deaths",
            "interstate",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/ERP_COMP_Q/latest",
            "upstream_title": (
                "Population and components of change - national, states and territories"
            ),
        },
    },
    "POP_PROJ": {
        "id": "POP_PROJ",
        "source": "abs",
        "name": "Population Projections, Australia, 2022-2071",
        "description": (
            "Long-run projections of the Australian resident population by age, "
            "sex, and state/territory under multiple fertility, mortality, and "
            "migration scenarios."
        ),
        "frequency": "Annual",
        "category": "demographics",
        "aliases": [
            "population projections",
            "long run population",
            "future population",
        ],
        "tags": [
            "projections",
            "long run",
            "scenarios",
        ],
        "frequencies": ["A"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/POP_PROJ/latest",
            "upstream_title": "Population Projections, Australia, 2022-2071",
        },
    },
    "NOM_FY": {
        "id": "NOM_FY",
        "source": "abs",
        "name": "Net Overseas Migration, Financial Year",
        "description": "Net overseas migration by country of birth, age, and sex.",
        "frequency": "Annual",
        "category": "demographics",
        "aliases": [
            "net overseas migration",
            "nom",
            "migration",
        ],
        "tags": [
            "arrivals",
            "departures",
            "population flows",
        ],
        "frequencies": ["A"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/NOM_FY/latest",
            "upstream_title": (
                "Net overseas migration: Arrivals, departures and net, State/territory, "
                "Age and sex - Financial years, 2004-05 onwards"
            ),
        },
    },
    "OAD_COUNTRY": {
        "id": "OAD_COUNTRY",
        "source": "abs",
        "name": "Overseas Arrivals and Departures by Country",
        "description": "Monthly overseas arrivals and departures by country of residence.",
        "frequency": "Monthly",
        "category": "demographics",
        "aliases": [
            "overseas arrivals",
            "overseas departures",
            "arrivals departures",
        ],
        "tags": [
            "travel",
            "short-term visitors",
            "country of residence",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
        "audit": {
            "last_audited": "2026-04-18",
            "upstream_url": "https://data.api.abs.gov.au/rest/dataflow/ABS/OAD_COUNTRY/latest",
            "upstream_title": (
                "Visitor arrivals and resident "
                "returns, Selected Countries of Residence/Destinations"
            ),
        },
    },
}
