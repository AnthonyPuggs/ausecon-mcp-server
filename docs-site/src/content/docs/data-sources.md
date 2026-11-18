---
title: Data Sources and Licensing
description: Where ausecon's data comes from, the licences the ABS, RBA and APRA publish it under, and how to attribute it.
---

Last updated: 19 November 2026.

ausecon does not own or generate any economic data. Every value it returns is fetched from data
that three Australian government agencies publish openly, and is passed through with its source
attached. ausecon is an independent, open-source project. It is not operated by, affiliated with,
or endorsed by any of these agencies.

## Sources

| Source | What ausecon reads | Licence |
| :----- | :----------------- | :------ |
| **Australian Bureau of Statistics (ABS)** | The public ABS Data API (SDMX) and the ABS release calendar | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), per the [ABS copyright notice](https://www.abs.gov.au/website-privacy-copyright-and-disclaimer) |
| **Reserve Bank of Australia (RBA)** | Published RBA statistical tables (CSV) and the RBA release calendar | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), per the [RBA copyright and disclaimer notice](https://www.rba.gov.au/copyright/) |
| **Australian Prudential Regulation Authority (APRA)** | Published APRA statistical publications (XLSX) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), per the [APRA copyright notice](https://www.apra.gov.au/copyright) |

ausecon only reads these public endpoints. It needs no account or API key, and it uses the same
files and APIs that anyone can download from the agencies' websites.

## How ausecon passes the source on

Each retrieval response records where its data came from:

- `metadata.retrieval_url` is the exact ABS, RBA or APRA URL the data was read from.
- `metadata.retrieved_at` is when it was fetched.
- Each response names its source (`abs`, `rba` or `apra`) and the agency's own dataset, table or
  series identifiers.

See [Data freshness and provenance](/user-guide/data-freshness-and-provenance/) for how these
fields are produced.

## Attributing data you get through ausecon

If you publish or share figures obtained through ausecon, attribute them to the agency that
published them, not to ausecon. The agencies ask for the following:

- **ABS:** "Source: Australian Bureau of Statistics", with the publication or dataset name. See
  the ABS guidance on [attributing ABS material](https://www.abs.gov.au/website-privacy-copyright-and-disclaimer).
- **RBA:** "Source: Reserve Bank of Australia [year]" or "Source: RBA [year]".
- **APRA:** "© Australian Prudential Regulation Authority [year]".

Attribution must not suggest that the agency endorses you or your use of the data.

## Limits of the licences

The agencies' licences have exceptions, and they continue to apply to data you get through
ausecon:

- **Third-party material.** Some agency tables include data supplied by someone else. The RBA's
  notice, for example, excludes data, graphs and tables that show a third-party source from its
  CC BY licence. Check the source shown in the original table before republishing such data.
- **RBA cash rate and financial data.** The RBA's notice sets separate terms for the cash rate and
  for numerical financial data. Among other things, the RBA does not recommend using its financial
  data as a financial benchmark, and users bear the risk of relying on it.
- **Revisions and withdrawals.** The agencies can revise, amend or withdraw published data.
  ausecon reflects the current published version, not a fixed historical copy.

This page summarises the agencies' terms for convenience. It is not legal advice. The notices
linked above are the authoritative terms.

## ausecon's own licence

ausecon's source code is released under the
[MIT licence](https://github.com/AnthonyPuggs/ausecon-mcp-server/blob/main/LICENSE). That licence
covers the software only, not the data it retrieves.
