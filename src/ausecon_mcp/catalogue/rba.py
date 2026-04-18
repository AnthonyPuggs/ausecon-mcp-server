RBA_CATALOGUE = {
    "a1": {
        "id": "a1",
        "source": "rba",
        "name": "RBA Balance Sheet",
        "description": "Reserve Bank of Australia balance sheet — assets and liabilities.",
        "frequency": "Weekly",
        "category": "monetary_policy",
        "aliases": [
            "rba balance sheet",
            "rba assets and liabilities",
            "reserve bank balance sheet",
        ],
        "tags": [
            "balance sheet",
            "central bank assets",
            "liabilities",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "a2": {
        "id": "a2",
        "source": "rba",
        "name": "Changes in Monetary Policy and Administered Rates",
        "description": "Historical changes in the cash rate target and administered policy rates.",
        "frequency": "Event-driven",
        "category": "monetary_policy",
        "aliases": [
            "cash rate",
            "cash rate target",
            "monetary policy",
            "interest rate decisions",
        ],
        "tags": [
            "rba board",
            "policy moves",
            "target rate",
        ],
        "frequencies": ["E"],
        "geographies": ["national"],
        "variants": [
            {
                "name": "target",
                "aliases": ["cash rate target", "new cash rate target"],
                "rba_series_ids": ["ARBAMPCNCRT"],
            }
        ],
    },
    "a3": {
        "id": "a3",
        "source": "rba",
        "name": "Monetary Policy Operations - Current",
        "description": (
            "Current domestic monetary policy operations including open market operations "
            "and liquidity settings."
        ),
        "frequency": "Daily",
        "category": "monetary_policy",
        "aliases": [
            "monetary policy operations",
            "open market operations",
            "liquidity operations",
            "domestic market operations",
        ],
        "tags": [
            "omo",
            "liquidity",
            "market operations",
            "monetary policy",
        ],
        "frequencies": ["D"],
        "geographies": ["national"],
        "variants": [],
    },
    "a5": {
        "id": "a5",
        "source": "rba",
        "name": "Daily Foreign Exchange Market Intervention Transactions",
        "description": (
            "Discontinued daily record of Reserve Bank foreign exchange market "
            "intervention transactions."
        ),
        "frequency": "Daily",
        "category": "exchange_rates",
        "aliases": [
            "foreign exchange market intervention",
            "fx intervention",
            "rba fx intervention",
        ],
        "tags": [
            "discontinued",
            "fx intervention",
            "rba operations",
        ],
        "frequencies": ["D"],
        "geographies": ["national"],
        "variants": [],
        "discontinued": True,
    },
    "b1": {
        "id": "b1",
        "source": "rba",
        "name": "Assets of Financial Institutions",
        "description": (
            "Monthly assets of Australia's financial institutions (banks, building "
            "societies, credit unions, money market corporations, finance companies, "
            "life insurers, superannuation, and managed funds). Headline measure of "
            "the size of the domestic financial sector."
        ),
        "frequency": "Monthly",
        "category": "money_credit",
        "aliases": [
            "financial institutions assets",
            "financial sector assets",
            "banking sector assets",
        ],
        "tags": [
            "banking",
            "financial sector",
            "balance sheet",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "b2": {
        "id": "b2",
        "source": "rba",
        "name": "Banks - Off-Balance Sheet Business",
        "description": (
            "Quarterly notional principal of banks' off-balance-sheet exposures "
            "(derivatives, guarantees, commitments). Useful for tracking "
            "leverage and counterparty exposure trends."
        ),
        "frequency": "Quarterly",
        "category": "money_credit",
        "aliases": [
            "off-balance sheet business",
            "bank derivatives",
            "notional exposures",
        ],
        "tags": [
            "banking",
            "derivatives",
            "off-balance sheet",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
    },
    "b3": {
        "id": "b3",
        "source": "rba",
        "name": "Repurchase Agreements and Stock Lending by Banks and RFCs",
        "description": (
            "Monthly repo and securities lending activity by Australian banks "
            "and registered financial corporations. Relevant for short-term "
            "funding and collateral market analysis."
        ),
        "frequency": "Monthly",
        "category": "money_credit",
        "aliases": [
            "repo",
            "repurchase agreements",
            "securities lending",
            "stock lending",
        ],
        "tags": [
            "repo",
            "funding markets",
            "securities lending",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "c1": {
        "id": "c1",
        "source": "rba",
        "name": "Credit and Charge Card Statistics",
        "description": "Card transaction values, balances, and credit card activity.",
        "frequency": "Monthly",
        "category": "payments",
        "aliases": [
            "credit card statistics",
            "charge card statistics",
            "card payments",
        ],
        "tags": [
            "payments",
            "cards",
            "merchant spending",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "c1.2": {
        "id": "c1.2",
        "source": "rba",
        "name": "Credit and Charge Cards - Original Series - Personal and Commercial",
        "description": (
            "Monthly credit and charge card usage split by personal vs. commercial "
            "card type, on an original (not seasonally adjusted) basis. Finer "
            "detail than C1 for retail payments analysis."
        ),
        "frequency": "Monthly",
        "category": "payments",
        "aliases": [
            "credit cards original series",
            "personal cards",
            "commercial cards",
        ],
        "tags": [
            "payments",
            "cards",
            "personal cards",
            "commercial cards",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "c2": {
        "id": "c2",
        "source": "rba",
        "name": "Debit Cards - Seasonally Adjusted",
        "description": (
            "Monthly debit card transaction volumes and values on a seasonally "
            "adjusted basis. Tracks shift away from cash / cheques."
        ),
        "frequency": "Monthly",
        "category": "payments",
        "aliases": [
            "debit cards",
            "eftpos",
            "debit card statistics",
        ],
        "tags": [
            "payments",
            "debit cards",
            "eftpos",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "c3": {
        "id": "c3",
        "source": "rba",
        "name": "Average Merchant Fees for Debit, Credit and Charge Cards",
        "description": (
            "Quarterly merchant service fees by card scheme. Used for card-payments "
            "competition and interchange analysis."
        ),
        "frequency": "Quarterly",
        "category": "payments",
        "aliases": [
            "merchant fees",
            "card fees",
            "interchange fees",
        ],
        "tags": [
            "payments",
            "merchant fees",
            "interchange",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
    },
    "c4": {
        "id": "c4",
        "source": "rba",
        "name": "ATMs - Seasonally Adjusted",
        "description": (
            "Monthly ATM transaction volumes and values, seasonally adjusted. "
            "Tracks the decline of cash-out usage."
        ),
        "frequency": "Monthly",
        "category": "payments",
        "aliases": [
            "atm withdrawals",
            "atm transactions",
            "cash withdrawals",
        ],
        "tags": [
            "payments",
            "atm",
            "cash",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "c5": {
        "id": "c5",
        "source": "rba",
        "name": "Cheques - Seasonally Adjusted",
        "description": (
            "Monthly cheque transaction volumes and values, seasonally adjusted. "
            "Tracks the long-run decline of paper-based payments."
        ),
        "frequency": "Monthly",
        "category": "payments",
        "aliases": [
            "cheques",
            "cheque statistics",
            "paper payments",
        ],
        "tags": [
            "payments",
            "cheques",
            "paper payments",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "c6": {
        "id": "c6",
        "source": "rba",
        "name": "Direct Entry and NPP - Seasonally Adjusted",
        "description": (
            "Monthly direct entry and New Payments Platform (NPP) transaction "
            "volumes and values, seasonally adjusted. Tracks real-time account-to-"
            "account payments adoption."
        ),
        "frequency": "Monthly",
        "category": "payments",
        "aliases": [
            "npp",
            "new payments platform",
            "direct entry",
            "osko",
            "account to account payments",
        ],
        "tags": [
            "payments",
            "npp",
            "direct entry",
            "real-time payments",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "c7": {
        "id": "c7",
        "source": "rba",
        "name": "Real-time Gross Settlement Statistics",
        "description": (
            "Volumes and values of high-value payments settled through the Reserve Bank's "
            "real-time gross settlement (RTGS) system."
        ),
        "frequency": "Monthly",
        "category": "payments",
        "aliases": [
            "rtgs",
            "real-time gross settlement",
            "high value payments",
            "wholesale payments",
        ],
        "tags": [
            "payments",
            "rtgs",
            "high-value settlements",
            "wholesale",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "c8": {
        "id": "c8",
        "source": "rba",
        "name": "Points of Access to the Australian Payments System",
        "description": (
            "Annual counts of payments-system access points (bank branches, ATMs, "
            "EFTPOS terminals) across Australia."
        ),
        "frequency": "Annual",
        "category": "payments",
        "aliases": [
            "points of access",
            "bank branches",
            "atm count",
            "eftpos terminals",
        ],
        "tags": [
            "payments",
            "access points",
            "branches",
            "atms",
        ],
        "frequencies": ["A"],
        "geographies": ["national"],
        "variants": [],
    },
    "c9": {
        "id": "c9",
        "source": "rba",
        "name": "Domestic Banking Fees Charged",
        "description": (
            "Annual aggregate fees charged by Australian banks to households and "
            "businesses across deposit, loan, and merchant fee categories."
        ),
        "frequency": "Annual",
        "category": "payments",
        "aliases": [
            "bank fees",
            "domestic banking fees",
            "banking fees charged",
            "merchant fees",
        ],
        "tags": [
            "bank fees",
            "household fees",
            "business fees",
            "merchant fees",
        ],
        "frequencies": ["A"],
        "geographies": ["national"],
        "variants": [],
    },
    "d1": {
        "id": "d1",
        "source": "rba",
        "name": "Growth in Selected Financial Aggregates",
        "description": "Growth rates for money, credit, and selected financial aggregates.",
        "frequency": "Monthly",
        "category": "money_credit",
        "aliases": [
            "financial aggregates growth",
            "credit growth",
            "money growth",
        ],
        "tags": [
            "broad money",
            "financial aggregates",
            "credit conditions",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [
            {"name": "credit", "aliases": ["credit growth"], "rba_series_ids": None},
            {"name": "money", "aliases": ["money growth", "broad money"], "rba_series_ids": None},
        ],
    },
    "d2": {
        "id": "d2",
        "source": "rba",
        "name": "Lending and Credit Aggregates",
        "description": "Household and business credit outstanding across major borrower groups.",
        "frequency": "Monthly",
        "category": "money_credit",
        "aliases": [
            "lending and credit aggregates",
            "credit aggregates",
            "credit outstanding",
        ],
        "tags": [
            "housing credit",
            "business credit",
            "household credit",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [
            {"name": "housing", "aliases": ["housing credit"], "rba_series_ids": None},
            {"name": "business", "aliases": ["business credit"], "rba_series_ids": None},
            {"name": "household", "aliases": ["household credit"], "rba_series_ids": None},
        ],
    },
    "d3": {
        "id": "d3",
        "source": "rba",
        "name": "Monetary Aggregates",
        "description": "Currency, deposits, and broad money aggregates.",
        "frequency": "Monthly",
        "category": "money_credit",
        "aliases": [
            "monetary aggregates",
            "broad money",
            "money supply",
        ],
        "tags": [
            "m3",
            "currency",
            "deposits",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [
            {"name": "currency", "aliases": [], "rba_series_ids": None},
            {"name": "deposits", "aliases": [], "rba_series_ids": None},
            {"name": "broad_money", "aliases": ["m3"], "rba_series_ids": None},
        ],
    },
    "d4": {
        "id": "d4",
        "source": "rba",
        "name": "Debt Securities Outstanding",
        "description": (
            "Outstanding debt securities issued by Australian residents by issuer "
            "sector, instrument, and currency."
        ),
        "frequency": "Quarterly",
        "category": "money_credit",
        "aliases": [
            "debt securities outstanding",
            "debt securities",
            "bonds outstanding",
            "fixed income outstanding",
        ],
        "tags": [
            "debt securities",
            "bond issuance",
            "fixed income",
            "capital markets",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
    },
    "d5": {
        "id": "d5",
        "source": "rba",
        "name": "Bank Lending Classified by Sector",
        "description": "Bank lending outstanding by borrower sector and loan purpose.",
        "frequency": "Monthly",
        "category": "money_credit",
        "aliases": [
            "bank lending by sector",
            "sectoral bank lending",
            "bank lending",
        ],
        "tags": [
            "credit by sector",
            "business lending",
            "household lending",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [
            {"name": "business", "aliases": ["business lending"], "rba_series_ids": None},
            {"name": "household", "aliases": ["household lending"], "rba_series_ids": None},
        ],
    },
    "d9": {
        "id": "d9",
        "source": "rba",
        "name": "Rural Debt by Lender",
        "description": (
            "Quarterly outstanding rural debt by lender type (banks vs. pastoral "
            "finance companies). Niche but the only published breakdown of "
            "Australian agricultural-sector credit."
        ),
        "frequency": "Quarterly",
        "category": "money_credit",
        "aliases": [
            "rural debt",
            "agricultural credit",
            "farm debt",
        ],
        "tags": [
            "rural",
            "agriculture",
            "credit",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
    },
    "d10": {
        "id": "d10",
        "source": "rba",
        "name": "Margin Lending",
        "description": (
            "Quarterly margin loan balances, client and facility counts, and "
            "credit limits. Captures household leveraged equity investment."
        ),
        "frequency": "Quarterly",
        "category": "money_credit",
        "aliases": [
            "margin loans",
            "margin lending",
            "equity-backed lending",
        ],
        "tags": [
            "margin loans",
            "household leverage",
            "equity markets",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
    },
    "d14": {
        "id": "d14",
        "source": "rba",
        "name": "Lending to Business - Outstanding by Business Size and Interest Rate Type",
        "description": (
            "Outstanding business lending broken down by borrower size (small, medium, "
            "large) and interest rate type (fixed, variable)."
        ),
        "frequency": "Monthly",
        "category": "money_credit",
        "aliases": [
            "business finance outstanding",
            "business lending by size",
            "business credit by size",
            "fixed vs variable business lending",
        ],
        "tags": [
            "business credit",
            "sme lending",
            "fixed rate lending",
            "variable rate lending",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [
            {"name": "small_business", "aliases": ["sme"], "rba_series_ids": None},
            {"name": "medium_business", "aliases": [], "rba_series_ids": None},
            {"name": "large_business", "aliases": [], "rba_series_ids": None},
        ],
    },
    "e1": {
        "id": "e1",
        "source": "rba",
        "name": "Household and Business Balance Sheets",
        "description": "Household and business balance sheet aggregates including debt and assets.",
        "frequency": "Quarterly",
        "category": "household_finance",
        "aliases": [
            "household balance sheet",
            "business balance sheet",
            "household debt",
        ],
        "tags": [
            "household wealth",
            "household debt",
            "business balance sheet",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [
            {"name": "household", "aliases": ["household debt"], "rba_series_ids": None},
            {"name": "business", "aliases": [], "rba_series_ids": None},
        ],
    },
    "e2": {
        "id": "e2",
        "source": "rba",
        "name": "Selected Household Ratios",
        "description": (
            "Household debt-to-income, assets-to-income, and related wealth indicators."
        ),
        "frequency": "Quarterly",
        "category": "household_finance",
        "aliases": [
            "household ratios",
            "household debt to income",
            "household wealth ratios",
        ],
        "tags": [
            "debt service",
            "household income",
            "household wealth",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
    },
    "e13": {
        "id": "e13",
        "source": "rba",
        "name": "Housing Loan Payments",
        "description": (
            "Aggregate scheduled and excess principal-and-interest payments on "
            "outstanding housing loans."
        ),
        "frequency": "Monthly",
        "category": "household_finance",
        "aliases": [
            "housing loan payments",
            "mortgage payments",
            "scheduled mortgage repayments",
            "excess mortgage repayments",
        ],
        "tags": [
            "mortgage payments",
            "housing loans",
            "household debt servicing",
            "offset accounts",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "f1": {
        "id": "f1",
        "source": "rba",
        "name": "Interest Rates and Yields - Money Market",
        "description": "Short-term money market rates including interbank benchmarks.",
        "frequency": "Daily",
        "category": "interest_rates",
        "aliases": [
            "money market rates",
            "interbank rates",
            "short term interest rates",
        ],
        "tags": [
            "bank bills",
            "overnight rates",
            "money market",
        ],
        "frequencies": ["D"],
        "geographies": ["national"],
        "variants": [
            {"name": "bank_bills", "aliases": ["bank bill"], "rba_series_ids": None},
            {
                "name": "overnight",
                "aliases": ["overnight rates", "overnight indexed swap"],
                "rba_series_ids": None,
            },
        ],
    },
    "f2": {
        "id": "f2",
        "source": "rba",
        "name": "Capital Market Yields - Government Bonds",
        "description": "Australian Government bond yields across key maturities.",
        "frequency": "Daily",
        "category": "interest_rates",
        "aliases": [
            "government bond yields",
            "bond yields",
            "capital market yields",
        ],
        "tags": [
            "yield curve",
            "sovereign yields",
            "long rates",
        ],
        "frequencies": ["D"],
        "geographies": ["national"],
        "variants": [],
    },
    "f3": {
        "id": "f3",
        "source": "rba",
        "name": "Aggregate Measures of Australian Corporate Bond Yields",
        "description": ("Aggregate measures of yields and spreads on Australian corporate bonds."),
        "frequency": "Daily",
        "category": "interest_rates",
        "aliases": [
            "corporate bond yields",
            "corporate bond spreads",
            "non-government yields",
            "credit spreads",
        ],
        "tags": [
            "credit spreads",
            "corporate yields",
            "non-government bonds",
        ],
        "frequencies": ["D"],
        "geographies": ["national"],
        "variants": [],
    },
    "f4": {
        "id": "f4",
        "source": "rba",
        "name": "Advertised Deposit Rates",
        "description": (
            "Advertised retail deposit rates for at-call and term deposit products "
            "across major Australian deposit-taking institutions."
        ),
        "frequency": "Monthly",
        "category": "interest_rates",
        "aliases": [
            "advertised deposit rates",
            "retail deposit rates",
            "advertised savings rates",
            "term deposit advertised rates",
        ],
        "tags": [
            "retail deposits",
            "advertised rates",
            "term deposits",
            "savings accounts",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "f4.1": {
        "id": "f4.1",
        "source": "rba",
        "name": "Paid Deposit Rates",
        "description": (
            "Monthly average interest rates actually paid on deposits by "
            "Australian banks, by deposit type. Complements F4 (advertised "
            "rates) with transaction-weighted measures."
        ),
        "frequency": "Monthly",
        "category": "interest_rates",
        "aliases": [
            "paid deposit rates",
            "actual deposit rates",
            "average deposit rate",
        ],
        "tags": [
            "deposit rates",
            "banking",
            "transaction-weighted",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "f5": {
        "id": "f5",
        "source": "rba",
        "name": "Indicator Lending Rates",
        "description": "Selected lending rates for housing, business, and personal finance.",
        "frequency": "Monthly",
        "category": "interest_rates",
        "aliases": [
            "indicator lending rates",
            "lending rates",
            "loan interest rates",
        ],
        "tags": [
            "business lending rates",
            "housing loan rates",
            "personal loan rates",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [
            {"name": "business", "aliases": ["business lending rates"], "rba_series_ids": None},
            {"name": "housing", "aliases": ["housing loan rates"], "rba_series_ids": None},
            {"name": "personal", "aliases": ["personal loan rates"], "rba_series_ids": None},
        ],
    },
    "f6": {
        "id": "f6",
        "source": "rba",
        "name": "Housing Lending Rates",
        "description": "Owner-occupier and investor mortgage rates across lending products.",
        "frequency": "Monthly",
        "category": "interest_rates",
        "aliases": [
            "housing lending rates",
            "mortgage rates",
            "housing loan rates",
        ],
        "tags": [
            "home loan rates",
            "variable mortgage rates",
            "fixed mortgage rates",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [
            {"name": "owner_occupier", "aliases": ["owner-occupier"], "rba_series_ids": None},
            {"name": "investor", "aliases": ["investment"], "rba_series_ids": None},
        ],
    },
    "f7": {
        "id": "f7",
        "source": "rba",
        "name": "Business Lending Rates",
        "description": "Average interest rates on new and outstanding business loans.",
        "frequency": "Monthly",
        "category": "interest_rates",
        "aliases": [
            "business lending rates",
            "business loan rates",
            "corporate loan rates",
        ],
        "tags": [
            "business loans",
            "small business rates",
            "large business rates",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [
            {"name": "small_business", "aliases": ["sme rates"], "rba_series_ids": None},
            {"name": "large_business", "aliases": [], "rba_series_ids": None},
        ],
    },
    "f8": {
        "id": "f8",
        "source": "rba",
        "name": "Personal Lending Rates",
        "description": (
            "Interest rates on personal loans including credit cards, fixed-term "
            "personal loans, and revolving credit facilities."
        ),
        "frequency": "Monthly",
        "category": "interest_rates",
        "aliases": [
            "personal lending rates",
            "personal loan rates",
            "credit card interest rates",
            "consumer loan rates",
        ],
        "tags": [
            "personal loans",
            "credit cards",
            "consumer credit",
            "revolving credit",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "f11": {
        "id": "f11",
        "source": "rba",
        "name": "Exchange Rates - Historical - Daily and Monthly",
        "description": (
            "Long historical run of Australian dollar exchange rates against major "
            "trading partner currencies, daily and monthly observations."
        ),
        "frequency": "Daily",
        "category": "exchange_rates",
        "aliases": [
            "exchange rates",
            "aud exchange rate",
            "foreign exchange",
        ],
        "tags": [
            "aud",
            "fx",
            "trade weighted index",
        ],
        "frequencies": ["D"],
        "geographies": ["national"],
        "variants": [],
    },
    "f11.1": {
        "id": "f11.1",
        "source": "rba",
        "name": "Exchange Rates - Extended Series",
        "description": (
            "Daily Australian dollar bilateral exchange rates against additional "
            "currencies not covered in F11, including cross-rates and emerging-"
            "market pairs."
        ),
        "frequency": "Daily",
        "category": "exchange_rates",
        "aliases": [
            "exchange rates extended",
            "additional currencies",
            "emerging market currencies",
            "cross rates",
        ],
        "tags": [
            "exchange rates",
            "bilateral",
            "cross rates",
        ],
        "frequencies": ["D"],
        "geographies": ["national"],
        "variants": [],
    },
    "f12": {
        "id": "f12",
        "source": "rba",
        "name": "US Dollar Exchange Rates",
        "description": (
            "Cross exchange rates of major currencies expressed against the US dollar."
        ),
        "frequency": "Daily",
        "category": "exchange_rates",
        "aliases": [
            "us dollar exchange rates",
            "usd cross rates",
            "major currency cross rates",
        ],
        "tags": [
            "usd",
            "cross rates",
            "major currencies",
        ],
        "frequencies": ["D"],
        "geographies": ["national"],
        "variants": [],
    },
    "f15": {
        "id": "f15",
        "source": "rba",
        "name": "Real Exchange Rate Measures",
        "description": "Real and real trade-weighted exchange rate measures.",
        "frequency": "Monthly",
        "category": "exchange_rates",
        "aliases": [
            "real exchange rate",
            "real twi",
            "real trade weighted index",
        ],
        "tags": [
            "real exchange rate",
            "competitiveness",
            "twi",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "f16": {
        "id": "f16",
        "source": "rba",
        "name": "Indicative Mid Rates of Selected Australian Government Securities",
        "description": (
            "Daily indicative mid yields on Australian Government Securities "
            "across the curve (2, 3, 5, 10 year and others). Core input for "
            "fixed-income and monetary-policy analysis."
        ),
        "frequency": "Daily",
        "category": "interest_rates",
        "aliases": [
            "ags yields",
            "government bond yields",
            "commonwealth government securities",
            "cgs",
            "bond curve",
        ],
        "tags": [
            "bond yields",
            "government bonds",
            "yield curve",
            "ags",
        ],
        "frequencies": ["D"],
        "geographies": ["national"],
        "variants": [],
    },
    "f17": {
        "id": "f17",
        "source": "rba",
        "csv_path": "f17-yields.csv",
        "name": "Zero-Coupon Interest Rates - Analytical Series (Yields)",
        "description": (
            "Daily zero-coupon yield curve fitted by the RBA from Australian "
            "Government Securities, at quarter-year maturities from 0 to 10 "
            "years. Published as separate yields, discount-factors, and forward-"
            "rates files; this entry retrieves the yields slice."
        ),
        "frequency": "Daily",
        "category": "interest_rates",
        "aliases": [
            "zero coupon yields",
            "zero-coupon rates",
            "spot yield curve",
            "analytical yields",
        ],
        "tags": [
            "yield curve",
            "zero coupon",
            "analytical",
            "term structure",
        ],
        "frequencies": ["D"],
        "geographies": ["national"],
        "variants": [],
    },
    "g1": {
        "id": "g1",
        "source": "rba",
        "name": "Consumer Price Inflation",
        "description": "CPI, weighted median inflation, and trimmed mean inflation measures.",
        "frequency": "Quarterly",
        "category": "inflation",
        "aliases": [
            "inflation",
            "trimmed mean inflation",
            "core inflation",
            "weighted median inflation",
            "cpi",
        ],
        "tags": [
            "underlying inflation",
            "consumer prices",
            "headline cpi",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [
            {
                "name": "headline",
                "aliases": ["headline cpi", "cpi"],
                "rba_series_ids": ["GCPIAG"],
            },
            {
                "name": "trimmed_mean",
                "aliases": ["core", "trimmed mean inflation"],
                "rba_series_ids": ["GCPIOCPMTMYP"],
            },
            {
                "name": "weighted_median",
                "aliases": ["weighted median inflation"],
                "rba_series_ids": None,
            },
        ],
    },
    "g2": {
        "id": "g2",
        "source": "rba",
        "name": "Consumer Price Inflation - Expenditure Groups",
        "description": "Detailed CPI expenditure group contributions and price movements.",
        "frequency": "Quarterly",
        "category": "inflation",
        "aliases": [
            "cpi expenditure groups",
            "detailed cpi",
            "inflation components",
        ],
        "tags": [
            "expenditure classes",
            "cpi components",
            "price contributions",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
    },
    "g3": {
        "id": "g3",
        "source": "rba",
        "name": "Inflation Expectations",
        "description": ("Consumer, union, market, and business measures of expected inflation."),
        "frequency": "Monthly",
        "category": "inflation",
        "aliases": [
            "inflation expectations",
            "expected inflation",
            "consumer inflation expectations",
        ],
        "tags": [
            "inflation expectations",
            "consumer expectations",
            "market inflation expectations",
        ],
        "frequencies": ["M", "Q"],
        "geographies": ["national"],
        "variants": [
            {"name": "consumer", "aliases": ["consumer expectations"], "rba_series_ids": None},
            {"name": "market", "aliases": ["market expectations"], "rba_series_ids": None},
            {"name": "union", "aliases": [], "rba_series_ids": None},
        ],
    },
    "g4": {
        "id": "g4",
        "source": "rba",
        "name": "Consumer Price Inflation - Monthly Collection",
        "description": (
            "Monthly consumer price inflation measures from the ABS Monthly CPI "
            "collection (added January 2026)."
        ),
        "frequency": "Monthly",
        "category": "inflation",
        "aliases": [
            "monthly cpi",
            "monthly inflation",
            "monthly consumer price inflation",
            "monthly cpi collection",
        ],
        "tags": [
            "monthly inflation",
            "monthly cpi",
            "consumer prices",
            "inflation nowcast",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "h1": {
        "id": "h1",
        "source": "rba",
        "name": "Gross Domestic Product and Income",
        "description": "Output, expenditure, and income indicators from the national accounts.",
        "frequency": "Quarterly",
        "category": "output_labour",
        "aliases": [
            "gdp",
            "output",
            "income",
            "economic growth",
        ],
        "tags": [
            "national accounts",
            "domestic demand",
            "gdp growth",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [
            {"name": "gdp", "aliases": ["output", "economic growth"], "rba_series_ids": None},
            {"name": "income", "aliases": [], "rba_series_ids": None},
        ],
    },
    "h2": {
        "id": "h2",
        "source": "rba",
        "name": "Demand and Income",
        "description": (
            "Components of aggregate demand and income from the national accounts: "
            "consumption, investment, government, and net exports contributions."
        ),
        "frequency": "Quarterly",
        "category": "output_labour",
        "aliases": [
            "demand and income",
            "aggregate demand",
            "expenditure components",
            "national accounts demand",
        ],
        "tags": [
            "consumption",
            "investment",
            "government spending",
            "net exports",
            "aggregate demand",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
    },
    "h3": {
        "id": "h3",
        "source": "rba",
        "name": "Monthly Activity Indicators",
        "description": "Monthly indicators for consumption, production, and business conditions.",
        "frequency": "Monthly",
        "category": "output_labour",
        "aliases": [
            "monthly activity indicators",
            "activity indicators",
            "monthly activity",
        ],
        "tags": [
            "economic activity",
            "high-frequency activity",
            "monthly indicators",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "h4": {
        "id": "h4",
        "source": "rba",
        "name": "Labour Costs and Productivity",
        "description": (
            "Labour cost and productivity indicators including unit labour costs, "
            "real unit labour costs, and labour productivity."
        ),
        "frequency": "Quarterly",
        "category": "output_labour",
        "aliases": [
            "labour costs and productivity",
            "unit labour costs",
            "labour productivity",
            "real unit labour costs",
        ],
        "tags": [
            "labour costs",
            "productivity",
            "unit labour costs",
            "wages",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
    },
    "h5": {
        "id": "h5",
        "source": "rba",
        "name": "Labour Force",
        "description": (
            "Employment, unemployment, and participation indicators from the labour market."
        ),
        "frequency": "Monthly",
        "category": "output_labour",
        "aliases": [
            "labour force",
            "employment",
            "unemployment",
            "unemployment rate",
        ],
        "tags": [
            "jobs",
            "participation",
            "labour market",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [
            {"name": "employment", "aliases": ["employed persons"], "rba_series_ids": None},
            {
                "name": "unemployment_rate",
                "aliases": ["unemployment"],
                "rba_series_ids": None,
            },
            {
                "name": "participation_rate",
                "aliases": ["participation"],
                "rba_series_ids": None,
            },
        ],
    },
    "i1": {
        "id": "i1",
        "source": "rba",
        "name": "International Trade and Balance of Payments",
        "description": "Trade, current account, and external sector aggregates for Australia.",
        "frequency": "Quarterly",
        "category": "external_sector",
        "aliases": [
            "international trade",
            "balance of payments",
            "current account",
        ],
        "tags": [
            "exports",
            "imports",
            "external balance",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [
            {"name": "trade", "aliases": ["international trade"], "rba_series_ids": None},
            {"name": "current_account", "aliases": [], "rba_series_ids": None},
        ],
    },
    "i2": {
        "id": "i2",
        "source": "rba",
        "name": "Commodity Prices",
        "description": (
            "RBA Index of Commodity Prices and component series for major Australian "
            "export commodities."
        ),
        "frequency": "Monthly",
        "category": "external_sector",
        "aliases": [
            "commodity prices",
            "rba commodity index",
            "commodity price index",
            "iron ore prices",
            "coal prices",
        ],
        "tags": [
            "commodity prices",
            "terms of trade",
            "commodity index",
            "export commodities",
        ],
        "frequencies": ["M"],
        "geographies": ["national"],
        "variants": [],
    },
    "i3": {
        "id": "i3",
        "source": "rba",
        "name": "Balance of Payments - Financial Account",
        "description": (
            "Quarterly financial account components of Australia's balance of payments: "
            "direct investment, portfolio investment, and other investment flows."
        ),
        "frequency": "Quarterly",
        "category": "external_sector",
        "aliases": [
            "financial account",
            "balance of payments financial account",
            "capital flows",
            "portfolio investment flows",
        ],
        "tags": [
            "financial account",
            "capital flows",
            "direct investment",
            "portfolio investment",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
    },
    "i4": {
        "id": "i4",
        "source": "rba",
        "name": "Australia's Gross Foreign Assets and Liabilities",
        "description": (
            "Quarterly stocks of Australia's gross foreign assets and liabilities by "
            "instrument and sector."
        ),
        "frequency": "Quarterly",
        "category": "external_sector",
        "aliases": [
            "gross foreign assets",
            "gross foreign liabilities",
            "foreign assets and liabilities",
            "international investment position",
            "iip",
        ],
        "tags": [
            "foreign assets",
            "foreign liabilities",
            "international investment position",
            "external balance sheet",
        ],
        "frequencies": ["Q"],
        "geographies": ["national"],
        "variants": [],
    },
}
