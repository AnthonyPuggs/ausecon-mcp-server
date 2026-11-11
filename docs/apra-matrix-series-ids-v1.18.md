# APRA matrix tables: series ids changed in 1.18.0

Version 1.18.0 changes how series ids are built for the seven APRA tables that are laid
out as a matrix (one row per series, one column per date). Before 1.18.0 the parser built
an id from the row label and the last heading above it, so different worksheet rows could
share one id and come back as a single series with several values per date.

136 ids changed. Old ids are not aliased: a request for one matches nothing, as any
unknown id does. The curated concepts (`adi_capital_ratio`, `adi_liquidity_coverage_ratio`,
`adi_commercial_property_exposure`, `adi_residential_mortgage_exposure`,
`superannuation_member_accounts`) are unaffected.

## How an id is built now

```text
PUBLICATION:table[:block][:section][:parent...]:metric
```

- **block**: a heading APRA writes in the date columns, such as `Assets ($m)` or
  `Number of entities`. A unit in the heading is left out of the id.
- **section**: the nearest heading in the label column, such as `Banks`. A section ends
  when the rows stop being indented under it.
- **parent**: the row or rows a label sits under. It appears only where the label would
  otherwise repeat, as with the three `Other` rows in the performance table.
- **metric**: the row label, without footnote markers.

Where an old id appears more than once below, it used to merge those rows.

## Quarterly ADI performance, Key Stats

`ADI_QUARTERLY_PERFORMANCE:key_stats`: 66 of 66 series ids changed.

| Row label | 1.17 id | 1.18 id |
| --- | --- | --- |
| Major banks | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:major_banks` | `ADI_QUARTERLY_PERFORMANCE:key_stats:assets:banks:major_banks` |
| Other domestic banks | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:other_domestic_banks` | `ADI_QUARTERLY_PERFORMANCE:key_stats:assets:banks:other_domestic_banks` |
| Foreign subsidiary banks | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:foreign_subsidiary_banks` | `ADI_QUARTERLY_PERFORMANCE:key_stats:assets:banks:foreign_subsidiary_banks` |
| Foreign branch banks | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:foreign_branch_banks` | `ADI_QUARTERLY_PERFORMANCE:key_stats:assets:banks:foreign_branch_banks` |
| All banks | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:all_banks` | `ADI_QUARTERLY_PERFORMANCE:key_stats:assets:banks:all_banks` |
| Credit unions and building societies | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:credit_unions_and_building_societies` | `ADI_QUARTERLY_PERFORMANCE:key_stats:assets:credit_unions_and_building_societies` |
| Other ADIs | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:other_adis` | `ADI_QUARTERLY_PERFORMANCE:key_stats:assets:other_adis` |
| All ADIs | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:all_adis_a` | `ADI_QUARTERLY_PERFORMANCE:key_stats:assets:all_adis` |
| of which: mutual ADIs | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:of_which_mutual_adis` | `ADI_QUARTERLY_PERFORMANCE:key_stats:assets:of_which_mutual_adis` |
| Major banks | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:major_banks` | `ADI_QUARTERLY_PERFORMANCE:key_stats:number_of_entities:banks:major_banks` |
| Other domestic banks | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:other_domestic_banks` | `ADI_QUARTERLY_PERFORMANCE:key_stats:number_of_entities:banks:other_domestic_banks` |
| Foreign subsidiary banks | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:foreign_subsidiary_banks` | `ADI_QUARTERLY_PERFORMANCE:key_stats:number_of_entities:banks:foreign_subsidiary_banks` |
| Foreign branch banks | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:foreign_branch_banks` | `ADI_QUARTERLY_PERFORMANCE:key_stats:number_of_entities:banks:foreign_branch_banks` |
| All banks | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:all_banks` | `ADI_QUARTERLY_PERFORMANCE:key_stats:number_of_entities:banks:all_banks` |
| Credit unions and building societies | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:credit_unions_and_building_societies` | `ADI_QUARTERLY_PERFORMANCE:key_stats:number_of_entities:credit_unions_and_building_societies` |
| Other ADIs | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:other_adis` | `ADI_QUARTERLY_PERFORMANCE:key_stats:number_of_entities:other_adis` |
| Restricted ADIs | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:restricted_adis` | `ADI_QUARTERLY_PERFORMANCE:key_stats:number_of_entities:restricted_adis` |
| All ADIs | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:all_adis` | `ADI_QUARTERLY_PERFORMANCE:key_stats:number_of_entities:all_adis` |
| of which: mutual ADIs | `ADI_QUARTERLY_PERFORMANCE:key_stats:banks:of_which_mutual_adis` | `ADI_QUARTERLY_PERFORMANCE:key_stats:number_of_entities:of_which_mutual_adis` |
| Net interest income ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:net_interest_income_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:net_interest_income_m` |
| Other operating income ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:other_operating_income_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:other_operating_income_m` |
| Total operating income ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:total_operating_income_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:total_operating_income_m` |
| Operating expenses ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:operating_expenses_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:operating_expenses_m` |
| Net profit (loss) after tax ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:net_profit_loss_after_tax_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:net_profit_loss_after_tax_m` |
| Total assets ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:total_assets_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:total_assets_m` |
| Total shareholders' equity ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:total_shareholders_equity_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:total_shareholders_equity_m` |
| Return on assets (after tax) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:return_on_assets_after_tax_a` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:return_on_assets_after_tax` |
| Return on equity (after tax) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:return_on_equity_after_tax_a` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:return_on_equity_after_tax` |
| Total non-performing exposures ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:total_non_performing_exposures_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:total_non_performing_exposures_m` |
| Total capital base ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:total_capital_base_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:total_capital_base_m` |
| Total risk-weighted assets ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:total_risk_weighted_assets_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:total_risk_weighted_assets_m` |
| Total capital ratio | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:total_capital_ratio` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:total_capital_ratio` |
| Liquidity coverage ratio (LCR) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:liquidity_coverage_ratio_lcr` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:liquidity_coverage_ratio_lcr` |
| Minimum liquidity holdings (MLH) ratio | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:minimum_liquidity_holdings_mlh_ratio` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:minimum_liquidity_holdings_mlh_ratio` |
| Number of entities | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:number_of_entities` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures:adis_excludes_other_adis:number_of_entities` |
| Net interest income ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:net_interest_income_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:net_interest_income_m` |
| Other operating income ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:other_operating_income_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:other_operating_income_m` |
| Total operating income ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_operating_income_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:total_operating_income_m` |
| Operating expenses ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:operating_expenses_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:operating_expenses_m` |
| Net profit (loss) after tax ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:net_profit_loss_after_tax_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:net_profit_loss_after_tax_m` |
| Total assets ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_assets_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:total_assets_m` |
| Total shareholders' equity ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_shareholders_equity_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:total_shareholders_equity_m` |
| Return on assets (after tax) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:return_on_assets_after_tax_a` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:return_on_assets_after_tax` |
| Return on equity (after tax) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:return_on_equity_after_tax_a` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:return_on_equity_after_tax` |
| Total non-performing exposures ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_non_performing_exposures_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:total_non_performing_exposures_m` |
| Total capital base ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_capital_base_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:total_capital_base_m` |
| Total risk-weighted assets ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_risk_weighted_assets_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:total_risk_weighted_assets_m` |
| Total capital ratio | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_capital_ratio` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:total_capital_ratio` |
| Liquidity coverage ratio (LCR) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:liquidity_coverage_ratio_lcr` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:liquidity_coverage_ratio_lcr` |
| Minimum liquidity holdings (MLH) ratio | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:minimum_liquidity_holdings_mlh_ratio` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:minimum_liquidity_holdings_mlh_ratio` |
| Number of entities | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:number_of_entities` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:banks:number_of_entities` |
| Net interest income ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:net_interest_income_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:net_interest_income_m` |
| Other operating income ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:other_operating_income_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:other_operating_income_m` |
| Total operating income ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_operating_income_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:total_operating_income_m` |
| Operating expenses ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:operating_expenses_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:operating_expenses_m` |
| Net profit (loss) after tax ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:net_profit_loss_after_tax_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:net_profit_loss_after_tax_m` |
| Total assets ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_assets_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:total_assets_m` |
| Total shareholders' equity ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_shareholders_equity_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:total_shareholders_equity_m` |
| Return on assets (after tax) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:return_on_assets_after_tax_a` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:return_on_assets_after_tax` |
| Return on equity (after tax) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:return_on_equity_after_tax_a` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:return_on_equity_after_tax` |
| Total non-performing exposures ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_non_performing_exposures_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:total_non_performing_exposures_m` |
| Total capital base ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_capital_base_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:total_capital_base_m` |
| Total risk-weighted assets ($m) | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_risk_weighted_assets_m` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:total_risk_weighted_assets_m` |
| Total capital ratio | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:total_capital_ratio` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:total_capital_ratio` |
| Minimum liquidity holdings (MLH) ratio | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:minimum_liquidity_holdings_mlh_ratio` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:minimum_liquidity_holdings_mlh_ratio` |
| Number of entities | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:number_of_entities` | `ADI_QUARTERLY_PERFORMANCE:key_stats:key_figures_banks_and_credit_unions_and_building_societies:credit_unions_and_building_societies:number_of_entities` |

## Quarterly ADI performance, Tab 1a

`ADI_QUARTERLY_PERFORMANCE:tab_1a`: 4 of 28 series ids changed.

| Row label | 1.17 id | 1.18 id |
| --- | --- | --- |
| Other | `ADI_QUARTERLY_PERFORMANCE:tab_1a:other` | `ADI_QUARTERLY_PERFORMANCE:tab_1a:interest_income:loans_and_advances:other` |
| Other | `ADI_QUARTERLY_PERFORMANCE:tab_1a:other` | `ADI_QUARTERLY_PERFORMANCE:tab_1a:other_operating_income:other` |
| Other | `ADI_QUARTERLY_PERFORMANCE:tab_1a:other` | `ADI_QUARTERLY_PERFORMANCE:tab_1a:total_operating_expenses:other` |
| Net profit (loss) after tax | `ADI_QUARTERLY_PERFORMANCE:tab_1a:net_profit_loss_after_taxa` | `ADI_QUARTERLY_PERFORMANCE:tab_1a:net_profit_loss_after_tax` |

## ADI property exposures, Tab 1a (commercial)

`ADI_PROPERTY_EXPOSURES:tab_1a`: 21 of 39 series ids changed.

| Row label | 1.17 id | 1.18 id |
| --- | --- | --- |
| Impaired Commercial property exposures | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:impaired_commercial_property_exposures` | `ADI_PROPERTY_EXPOSURES:tab_1a:impaired_commercial_property_exposures` |
| of which: Exposures in Australia | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:of_which_exposures_in_australia` | `ADI_PROPERTY_EXPOSURES:tab_1a:impaired_commercial_property_exposures:of_which_exposures_in_australia` |
| Specific provisions | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:specific_provisions` | `ADI_PROPERTY_EXPOSURES:tab_1a:impaired_commercial_property_exposures:specific_provisions` |
| of which: Exposures in Australia | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:of_which_exposures_in_australia` | `ADI_PROPERTY_EXPOSURES:tab_1a:impaired_commercial_property_exposures:specific_provisions:of_which_exposures_in_australia` |
| Specific provisions and security | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:specific_provisions_and_security` | `ADI_PROPERTY_EXPOSURES:tab_1a:impaired_commercial_property_exposures:specific_provisions_and_security` |
| of which: Exposures in Australia | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:of_which_exposures_in_australia` | `ADI_PROPERTY_EXPOSURES:tab_1a:impaired_commercial_property_exposures:specific_provisions_and_security:of_which_exposures_in_australia` |
| Impaired assets to exposures | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:impaired_assets_to_exposures` | `ADI_PROPERTY_EXPOSURES:tab_1a:impaired_assets_to_exposures` |
| Specific provisions to exposures | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:specific_provisions_to_exposures` | `ADI_PROPERTY_EXPOSURES:tab_1a:specific_provisions_to_exposures` |
| Specific provisions to impaired exposures | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:specific_provisions_to_impaired_exposures` | `ADI_PROPERTY_EXPOSURES:tab_1a:specific_provisions_to_impaired_exposures` |
| Specific provisions and security held to impaired exposures | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:specific_provisions_and_security_held_to_impaired_exposures` | `ADI_PROPERTY_EXPOSURES:tab_1a:specific_provisions_and_security_held_to_impaired_exposures` |
| Non-performing commercial property exposures | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:non_performing_commercial_property_exposures` | `ADI_PROPERTY_EXPOSURES:tab_1a:non_performing_commercial_property_exposures` |
| of which: Exposures in Australia | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:of_which_exposures_in_australia` | `ADI_PROPERTY_EXPOSURES:tab_1a:non_performing_commercial_property_exposures:of_which_exposures_in_australia` |
| Specific provisions | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:specific_provisions` | `ADI_PROPERTY_EXPOSURES:tab_1a:non_performing_commercial_property_exposures:specific_provisions` |
| of which: Exposures in Australia | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:of_which_exposures_in_australia` | `ADI_PROPERTY_EXPOSURES:tab_1a:non_performing_commercial_property_exposures:specific_provisions:of_which_exposures_in_australia` |
| Specific provisions and security | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:specific_provisions_and_security` | `ADI_PROPERTY_EXPOSURES:tab_1a:non_performing_commercial_property_exposures:specific_provisions_and_security` |
| of which: Exposures in Australia | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:of_which_exposures_in_australia` | `ADI_PROPERTY_EXPOSURES:tab_1a:non_performing_commercial_property_exposures:specific_provisions_and_security:of_which_exposures_in_australia` |
| Non-performing to total exposures | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:non_performing_to_total_exposures` | `ADI_PROPERTY_EXPOSURES:tab_1a:non_performing_to_total_exposures` |
| Specific provisions to total exposures | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:specific_provisions_to_total_exposures` | `ADI_PROPERTY_EXPOSURES:tab_1a:specific_provisions_to_total_exposures` |
| Specific provisions to non-performing exposures | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:specific_provisions_to_non_performing_exposures` | `ADI_PROPERTY_EXPOSURES:tab_1a:specific_provisions_to_non_performing_exposures` |
| Specific provisions and security held to non-performing exposures | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:specific_provisions_and_security_held_to_non_performing_exposures` | `ADI_PROPERTY_EXPOSURES:tab_1a:specific_provisions_and_security_held_to_non_performing_exposures` |
| Number of entities | `ADI_PROPERTY_EXPOSURES:tab_1a:commercial_property_actual_exposures:number_of_entitiesa` | `ADI_PROPERTY_EXPOSURES:tab_1a:number_of_entities` |

## ADI property exposures, Tab 1b (residential)

`ADI_PROPERTY_EXPOSURES:tab_1b`: 1 of 66 series ids changed.

| Row label | 1.17 id | 1.18 id |
| --- | --- | --- |
| Number of entities | `ADI_PROPERTY_EXPOSURES:tab_1b:non_performing_term_loans_by_lvr:number_of_entities` | `ADI_PROPERTY_EXPOSURES:tab_1b:number_of_entities` |

## ADI property exposures, Tab 1c (new housing loans)

`ADI_PROPERTY_EXPOSURES:tab_1c`: 13 of 43 series ids changed.

| Row label | 1.17 id | 1.18 id |
| --- | --- | --- |
| New loans funded | `ADI_PROPERTY_EXPOSURES:tab_1c:new_loans_funded` | `ADI_PROPERTY_EXPOSURES:tab_1c:new_loans_funded_total_committed_amount:new_loans_funded` |
| Term loans | `ADI_PROPERTY_EXPOSURES:tab_1c:term_loans` | `ADI_PROPERTY_EXPOSURES:tab_1c:new_loans_funded_total_committed_amount:term_loans` |
| Owner-occupied | `ADI_PROPERTY_EXPOSURES:tab_1c:owner_occupied` | `ADI_PROPERTY_EXPOSURES:tab_1c:new_loans_funded_total_committed_amount:owner_occupied` |
| Investment | `ADI_PROPERTY_EXPOSURES:tab_1c:investment` | `ADI_PROPERTY_EXPOSURES:tab_1c:new_loans_funded_total_committed_amount:investment` |
| Non-housing | `ADI_PROPERTY_EXPOSURES:tab_1c:non_housing` | `ADI_PROPERTY_EXPOSURES:tab_1c:new_loans_funded_total_committed_amount:non_housing` |
| Revolving credits | `ADI_PROPERTY_EXPOSURES:tab_1c:revolving_credits` | `ADI_PROPERTY_EXPOSURES:tab_1c:new_loans_funded_total_committed_amount:revolving_credits` |
| Owner-occupied | `ADI_PROPERTY_EXPOSURES:tab_1c:owner_occupied_and_investor_loans:owner_occupied` | `ADI_PROPERTY_EXPOSURES:tab_1c:owner_occupied_and_investor_loans:debt_to_income_4x_6x:owner_occupied` |
| Investment | `ADI_PROPERTY_EXPOSURES:tab_1c:owner_occupied_and_investor_loans:investment` | `ADI_PROPERTY_EXPOSURES:tab_1c:owner_occupied_and_investor_loans:debt_to_income_4x_6x:investment` |
| Owner-occupied | `ADI_PROPERTY_EXPOSURES:tab_1c:owner_occupied_and_investor_loans:owner_occupied` | `ADI_PROPERTY_EXPOSURES:tab_1c:owner_occupied_and_investor_loans:debt_to_income_6x:owner_occupied` |
| Investment | `ADI_PROPERTY_EXPOSURES:tab_1c:owner_occupied_and_investor_loans:investment` | `ADI_PROPERTY_EXPOSURES:tab_1c:owner_occupied_and_investor_loans:debt_to_income_6x:investment` |
| Weighted average variable rate of new loans funded | `ADI_PROPERTY_EXPOSURES:tab_1c:investment_term_loans_by_lvr:weighted_average_variable_rate_of_new_loans_funded` | `ADI_PROPERTY_EXPOSURES:tab_1c:interest_rates_for_new_loans_funded:weighted_average_variable_rate_of_new_loans_funded` |
| Weighted average assessment rate used for serviceability | `ADI_PROPERTY_EXPOSURES:tab_1c:investment_term_loans_by_lvr:weighted_average_assessment_rate_used_for_serviceability` | `ADI_PROPERTY_EXPOSURES:tab_1c:interest_rates_for_new_loans_funded:weighted_average_assessment_rate_used_for_serviceability` |
| Number of entities | `ADI_PROPERTY_EXPOSURES:tab_1c:investment_term_loans_by_lvr:number_of_entities` | `ADI_PROPERTY_EXPOSURES:tab_1c:number_of_entities` |

Heading rows that are no longer returned as series:

- New loans funded - total committed amount (`ADI_PROPERTY_EXPOSURES:tab_1c:new_loans_funded_total_committed_amount`)
- Interest rates for new loans funded (`ADI_PROPERTY_EXPOSURES:tab_1c:investment_term_loans_by_lvr:interest_rates_for_new_loans_funded`)

## Superannuation industry, Table 2 (MySuper products)

`APRA_SUPER_INDUSTRY:table_2`: 29 of 29 series ids changed.

| Row label | 1.17 id | 1.18 id |
| --- | --- | --- |
| MySuper products - generic | `APRA_SUPER_INDUSTRY:table_2:mysuper_products_generic` | `APRA_SUPER_INDUSTRY:table_2:mysuper_products:mysuper_products_generic` |
| MySuper products - material goodwill | `APRA_SUPER_INDUSTRY:table_2:mysuper_products_material_goodwill` | `APRA_SUPER_INDUSTRY:table_2:mysuper_products:mysuper_products_material_goodwill` |
| MySuper products - large employer | `APRA_SUPER_INDUSTRY:table_2:mysuper_products_large_employer` | `APRA_SUPER_INDUSTRY:table_2:mysuper_products:mysuper_products_large_employer` |
| Total number of MySuper products | `APRA_SUPER_INDUSTRY:table_2:total_number_of_mysuper_products` | `APRA_SUPER_INDUSTRY:table_2:mysuper_products:total_number_of_mysuper_products` |
| of which: MySuper products with a lifecycle strategy | `APRA_SUPER_INDUSTRY:table_2:of_which_mysuper_products_with_a_lifecycle_strategy` | `APRA_SUPER_INDUSTRY:table_2:mysuper_products:of_which_mysuper_products_with_a_lifecycle_strategy` |
| Number of lifecycle stages | `APRA_SUPER_INDUSTRY:table_2:number_of_lifecycle_stages` | `APRA_SUPER_INDUSTRY:table_2:mysuper_products:number_of_lifecycle_stages` |
| Number of RSEs | `APRA_SUPER_INDUSTRY:table_2:number_of_rses` | `APRA_SUPER_INDUSTRY:table_2:mysuper_products:number_of_rses` |
| Number of entities offering a MySuper product | `APRA_SUPER_INDUSTRY:table_2:number_of_entities_offering_a_mysuper_product` | `APRA_SUPER_INDUSTRY:table_2:mysuper_products:number_of_entities_offering_a_mysuper_product` |
| Proportion of entities offering a MySuper product | `APRA_SUPER_INDUSTRY:table_2:proportion_of_entities_offering_a_mysuper_product` | `APRA_SUPER_INDUSTRY:table_2:mysuper_products:proportion_of_entities_offering_a_mysuper_product` |
| Number of entities offering more than one MySuper product | `APRA_SUPER_INDUSTRY:table_2:number_of_entities_offering_more_than_one_mysuper_product` | `APRA_SUPER_INDUSTRY:table_2:mysuper_products:number_of_entities_offering_more_than_one_mysuper_product` |
| MySuper products - generic | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:mysuper_products_generic` | `APRA_SUPER_INDUSTRY:table_2:mysuper_member_assets:members_with_100_per_cent_mysuper_interest:mysuper_products_generic` |
| MySuper products - material goodwill | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:mysuper_products_material_goodwill` | `APRA_SUPER_INDUSTRY:table_2:mysuper_member_assets:members_with_100_per_cent_mysuper_interest:mysuper_products_material_goodwill` |
| MySuper products - large employer | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:mysuper_products_large_employer` | `APRA_SUPER_INDUSTRY:table_2:mysuper_member_assets:members_with_100_per_cent_mysuper_interest:mysuper_products_large_employer` |
| Total member assets in MySuper products | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:total_member_assets_in_mysuper_products` | `APRA_SUPER_INDUSTRY:table_2:mysuper_member_assets:members_with_100_per_cent_mysuper_interest:total_member_assets_in_mysuper_products` |
| of which: MySuper products with a lifecycle strategy | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:of_which_mysuper_products_with_a_lifecycle_strategy` | `APRA_SUPER_INDUSTRY:table_2:mysuper_member_assets:members_with_100_per_cent_mysuper_interest:of_which_mysuper_products_with_a_lifecycle_strategy` |
| Total RSE member assets | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:total_rse_member_assets` | `APRA_SUPER_INDUSTRY:table_2:mysuper_member_assets:members_with_100_per_cent_mysuper_interest:total_rse_member_assets` |
| Proportion of member assets in a MySuper product | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:proportion_of_member_assets_in_a_mysuper_product` | `APRA_SUPER_INDUSTRY:table_2:mysuper_member_assets:members_with_100_per_cent_mysuper_interest:proportion_of_member_assets_in_a_mysuper_product` |
| MySuper products - generic | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:mysuper_products_generic` | `APRA_SUPER_INDUSTRY:table_2:number_of_member_accounts:members_with_100_per_cent_mysuper_interest:mysuper_products_generic` |
| MySuper products - material goodwill | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:mysuper_products_material_goodwill` | `APRA_SUPER_INDUSTRY:table_2:number_of_member_accounts:members_with_100_per_cent_mysuper_interest:mysuper_products_material_goodwill` |
| MySuper products - large employer | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:mysuper_products_large_employer` | `APRA_SUPER_INDUSTRY:table_2:number_of_member_accounts:members_with_100_per_cent_mysuper_interest:mysuper_products_large_employer` |
| Total members in MySuper products | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:total_members_in_mysuper_products` | `APRA_SUPER_INDUSTRY:table_2:number_of_member_accounts:members_with_100_per_cent_mysuper_interest:total_members_in_mysuper_products` |
| of which: MySuper products with a lifecycle strategy | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:of_which_mysuper_products_with_a_lifecycle_strategy` | `APRA_SUPER_INDUSTRY:table_2:number_of_member_accounts:members_with_100_per_cent_mysuper_interest:of_which_mysuper_products_with_a_lifecycle_strategy` |
| Total RSE member accounts | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:total_rse_member_accounts` | `APRA_SUPER_INDUSTRY:table_2:number_of_member_accounts:members_with_100_per_cent_mysuper_interest:total_rse_member_accounts` |
| Proportion of members in a MySuper product | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:proportion_of_members_in_a_mysuper_product` | `APRA_SUPER_INDUSTRY:table_2:number_of_member_accounts:members_with_100_per_cent_mysuper_interest:proportion_of_members_in_a_mysuper_product` |
| MySuper products - generic | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:mysuper_products_generic` | `APRA_SUPER_INDUSTRY:table_2:average_member_account_balance:members_with_100_per_cent_mysuper_interest:mysuper_products_generic` |
| MySuper products - material goodwill | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:mysuper_products_material_goodwill` | `APRA_SUPER_INDUSTRY:table_2:average_member_account_balance:members_with_100_per_cent_mysuper_interest:mysuper_products_material_goodwill` |
| MySuper products - large employer | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:mysuper_products_large_employer` | `APRA_SUPER_INDUSTRY:table_2:average_member_account_balance:members_with_100_per_cent_mysuper_interest:mysuper_products_large_employer` |
| All MySuper products | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:all_mysuper_products` | `APRA_SUPER_INDUSTRY:table_2:average_member_account_balance:members_with_100_per_cent_mysuper_interest:all_mysuper_products` |
| of which: MySuper products with a lifecycle strategy | `APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:of_which_mysuper_products_with_a_lifecycle_strategy` | `APRA_SUPER_INDUSTRY:table_2:average_member_account_balance:members_with_100_per_cent_mysuper_interest:of_which_mysuper_products_with_a_lifecycle_strategy` |

Heading rows that are no longer returned as series:

- Members with 100 per cent MySuper interest, two rows (`APRA_SUPER_INDUSTRY:table_2:members_with_100_per_cent_mysuper_interest:members_with_100_per_cent_mysuper_interest`)

## Superannuation industry, Table 5 (member accounts)

`APRA_SUPER_INDUSTRY:table_5`: 2 of 15 series ids changed.

| Row label | 1.17 id | 1.18 id |
| --- | --- | --- |
| Small funds | `APRA_SUPER_INDUSTRY:table_5:by_fund_type:small_funds_a` | `APRA_SUPER_INDUSTRY:table_5:by_fund_type:small_funds` |
| Total APRA-regulated | `APRA_SUPER_INDUSTRY:table_5:of_which_single_member_approved_deposit_funds:total_apra_regulated` | `APRA_SUPER_INDUSTRY:table_5:by_regulatory_classification_apra_regulated:total_apra_regulated` |
