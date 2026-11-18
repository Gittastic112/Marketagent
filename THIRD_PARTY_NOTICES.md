# Third-party integration notices

The new adapters are original integration code using upstream public interfaces. Installed distributions retain their own license and notice files, which remain authoritative for their exact versions. Preserve those files when packaging dependencies. This inventory identifies direct integrations and references; it is not a replacement for the complete dependency licenses.

## Direct analysis, extraction and interface dependencies

| Project | Selected version | License reference | Use |
|---|---|---|---|
| [PyPortfolioOpt](https://github.com/PyPortfolio/PyPortfolioOpt) | 1.6.0 | [MIT](https://github.com/PyPortfolio/PyPortfolioOpt/blob/main/LICENSE) | Constrained allocation and HRP |
| [bt](https://github.com/pmorissette/bt) | 1.4.1 | [MIT](https://github.com/pmorissette/bt/blob/master/LICENSE) | Independent research simulation |
| [QuantStats](https://github.com/ranaroussi/quantstats) | 0.0.86 | [Apache-2.0](https://github.com/ranaroussi/quantstats/blob/main/LICENSE.txt) | Return statistics |
| [pandas_market_calendars](https://github.com/rsheftel/pandas_market_calendars) | 5.6.1 | [MIT](https://github.com/rsheftel/pandas_market_calendars/blob/master/LICENSE) | Exchange schedules |
| [EdgarTools](https://github.com/dgunning/edgartools) | 6.3.0 | [MIT](https://github.com/dgunning/edgartools/blob/main/LICENSE.txt) | SEC CompanyFacts parsing |
| [Camelot](https://github.com/camelot-dev/camelot) | 2.0.0 | [MIT](https://github.com/camelot-dev/camelot/blob/master/LICENSE) | PDF table extraction |
| [Docling](https://github.com/docling-project/docling) | 2.150.1 | [MIT](https://github.com/docling-project/docling/blob/main/LICENSE) | Optional isolated document parser |
| [Marker](https://github.com/datalab-to/marker) | Wrapper for published 2.2.0; dependency-conflict guard | [Apache-2.0](https://github.com/datalab-to/marker/blob/master/LICENSE), verified against current repository and release metadata | Current published dependency set is excluded from install profiles; model licenses are separate |
| [SciPy](https://github.com/scipy/scipy) | 1.16.3 in analysis profile | [BSD-3-Clause and bundled notices](https://github.com/scipy/scipy/blob/v1.16.3/LICENSE.txt) | Compatible numerical backend |
| [react-markdown](https://github.com/remarkjs/react-markdown) | 10.1.0 | [MIT](https://github.com/remarkjs/react-markdown/blob/main/license) | Structured memo rendering |
| [remark-gfm](https://github.com/remarkjs/remark-gfm) | 4.0.1 | [MIT](https://github.com/remarkjs/remark-gfm/blob/main/license) | GFM tables and lists |
| [openapi-typescript](https://github.com/openapi-ts/openapi-typescript) | 7.13.0, development only | [MIT](https://github.com/openapi-ts/openapi-typescript/blob/main/LICENSE) | Types generated from registered adapter contracts |

NumPy, pandas, cvxpy, Clarabel, scikit-learn, exchange-calendars and other transitive libraries are pinned in the corresponding lockfiles and retain their packaged licenses. The optional OCR environment has its own dependency tree and notices. This batch does not redistribute model weight files.

## Reference data and service interfaces

FinanceDatabase reference CSVs are fetched from an explicitly chosen upstream commit. Their manifest retains original URLs, hashes and the [MIT license reference](https://github.com/JerBouma/FinanceDatabase/blob/93b872f0e4b4e05e8d35b7f0a39efe9245bcc2c1/LICENSE). The dataset is not bundled into the application repository.

FMP, Massive, official NSE MCP, OpenFIGI, FRED/ALFRED, EarningsCall, SEC and BSE interfaces are independent services. This integration preserves their source identity and observation metadata. A software dependency license is separate from service access, data entitlements and permitted data use.

The workflow research referenced [OpenStock](https://github.com/Open-Dev-Society/OpenStock), [Ghostfolio](https://github.com/ghostfolio/ghostfolio) and [Wealthfolio](https://github.com/afadil/wealthfolio). The implemented palette, evidence review and lab components use the current Marketagent application structure.
