# Lab 5: Put Uncertainty Into Your Project

**Project:** Transition risk for the EU airline industry: how the phase-out of free EU ETS allowances interacts with carbon and oil prices.
**Role:** Climate Risk Analyst
**Key quantity:** Net EU ETS carbon cost of the aviation sector (EEA scope), in million EUR per year, 2013–2025, projected to 2030.

```
net carbon cost (M EUR) = (verified emissions − free allowances) (Mt) × annual mean EUA auction price (EUR/t)
```

---

## Folder contents

| File | What it is |
|---|---|
| `lab5.ipynb` | The notebook (Parts A–F; Part E skipped, as it is optional) |
| `eea_ets_aviation.csv` | Raw export from the EEA EU ETS data viewer (aviation only) |
| `eua_price_annual.csv` | Annual EUA auction price, computed from EEX auction results |
| `fig_uncertainty.png` | Fan chart for the paper, produced by Part F |
| `make_eua_price.py` | *(optional)* Script that rebuilds `eua_price_annual.csv` from the raw EEX files |

---

## Data sources

### 1. Aviation emissions and free allowances: European Environment Agency (EEA)

- **Source:** EEA, *EU Emissions Trading System (ETS) data viewer*, based on the European Commission's Union Registry (formerly the EU Transaction Log, EUTL).
- **URL:** https://www.eea.europa.eu/data-and-maps/dashboards/emissions-trading-viewer-1
- **File:** `eea_ets_aviation.csv` (exported as `Graph__Aviations.csv` and renamed)

**How we downloaded it**

1. Open the data viewer.
2. **ETS information / activity type:** `10 Aviation` (the default, `20-99 All stationary installations`, covers power plants and industry and is the wrong category).
3. **Countries:** all (the export includes every country plus the `All Countries`, `EU27` and `EU27 + UK` aggregates).
4. **Years:** 2012–2025.
5. **Measures:**
   - `1.1 Freely allocated allowances`
   - `1.2 Correction to freely allocated allowances (not reflected in EUTL)`
   - `1.3 Allowances auctioned or sold (EUAs and EUAAs)`
   - `1. Total supply (EUA or EUAA)`
   - `2. Verified emissions`
   - `2.1b EU-ETS Verified Emissions (expected, gap-filled for latest year)`
6. Click **Download** (bottom right of the viewer).

**Format:** UTF-16, tab-separated. Row 1 holds the country, row 2 the year, and each following row is one measure. Values are in millions (MtCO2 for emissions, million allowances for allocations).

**Variables used in the notebook:** `2. Verified emissions` and `1.1 Freely allocated allowances`, for the `All Countries` aggregate.

### 2. Carbon price: European Energy Exchange (EEX)

- **Source:** EEX, *EUA Primary Market Auction Report*, history 2012–2025.
- **URL:** https://www.eex.com/en/market-data/environmentals/eu-ets-auctions (download section: "History Emission Spot Primary Market Auction Report 2012 – 2025", zip)
- **Raw file:** `emission-spot-primary-market-auction-report-2012-2025-data.zip`, with one Excel file per year, one row per auction (date, contract, auction price in EUR/tCO2, auction volume in tCO2, bids, etc.).
- **Processed file:** `eua_price_annual.csv`

**How we processed it** (`make_eua_price.py`)

1. Read the `Primary Market Auction` sheet of every yearly file and locate the header row (it moves between years).
2. Keep auctions with a valid date, price and volume; from 2020 onwards, keep only rows with status `successful`.
3. Separate general allowances (EUA, contracts `T2PA` / `T3PA`) from aviation allowances (EUAA, contracts `EAA2` / `EAA3`).
4. For each year, compute the **volume-weighted average EUA auction price**:
   `sum(price × volume) / sum(volume)`.

| Column | Meaning |
|---|---|
| `year` | Calendar year |
| `eua_price_vwap` | Volume-weighted mean EUA auction price, EUR/t (**used in the notebook**) |
| `eua_price_mean` | Simple mean of auction prices, EUR/t (check) |
| `n_auctions` | Number of EUA auctions in the year |
| `euaa_price_mean` | Simple mean of EUAA (aviation allowance) auction prices, EUR/t (check) |

The EUAA prices closely track the EUA prices, so we use the EUA series, which covers every year.

To rebuild the file from the raw zip (optional):

```bash
pip install pandas xlrd openpyxl
unzip emission-spot-primary-market-auction-report-2012-2025-data.zip -d eex_raw
python make_eua_price.py eex_raw/emission-spot-primary-market-auction-report-2012-2025-data eua_price_annual.csv
```

---

## How the key quantity is built (Part A)

1. Load the EEA export and keep the **`All Countries`** aggregate, i.e. the full EU ETS scope that airlines actually pay under (EU27 + Iceland, Liechtenstein, Norway, and the UK until 2020).
2. Join it with the annual EUA price on `year`.
3. **Start in 2013.** 2012 was the full-scope "stop the clock" year, with large free allocations later corrected (measure 1.2), so it is not comparable.
4. Compute:
   - `payable_mt = emissions_mt − free_mt`: emissions not covered by free allowances
   - `payable_share = payable_mt / emissions_mt`
   - `net_cost_meur = payable_mt × eua_eur` (Mt × EUR/t = million EUR)
5. `series` = `year` + `net_cost_meur`: 13 annual points, 2013–2025.

| Year | Emissions (Mt) | Free (Mt) | EUA (EUR/t) | Payable share | Net cost (M EUR) |
|---|---|---|---|---|---|
| 2013 | 53.49 | 32.13 | 4.38 | 40% | 94 |
| 2019 | 68.18 | 30.14 | 24.64 | 56% | 937 |
| 2020 | 25.26 | 30.61 | 24.52 | −21% | −131 |
| 2022 | 49.23 | 23.06 | 79.75 | 53% | 2,087 |
| 2025 | 62.48 | 11.08 | 73.43 | 82% | 3,775 |

**Known breaks in the series**

- **2020 (COVID):** emissions fell below free allocation, so the net cost is negative (a surplus of allowances). The log-linear model in Part B drops this year, since the log is undefined.
- **2021 (Brexit):** the UK left the EU ETS, which shrinks the scope.
- **2025:** the latest year may still be gap-filled by the EEA (measure 2.1b).

---

## Modelling assumptions (Parts B–D)

**Part B, back-test:** hold out 2021–2025, fit on 2013–2020, using OLS on `value ~ year` (linear) and `log(value) ~ year` (log-linear), with Student-t 90% prediction intervals.

**Part C, simulation for 2030** (N = 5,000, seed 42):

| Input | Distribution | Type | Justification |
|---|---|---|---|
| Emissions growth per year, 2025→2030 | Triangular(−1%, +2%, +4.5%) | Epistemic | +4.5% ≈ pre-COVID 2014–2019 trend; −1% = demand hit from high fares or an oil shock; +2% ≈ traffic growth net of ~1.5%/yr efficiency gains |
| EUA price in 2030 | Lognormal around the scenario median, σ = 0.35 over 5 years | Aleatoric (+ scenario level) | Matches the 2021–2025 swings (EUR 53 → 83 → 65 → 73) |
| Payable share | Fixed at 100% from 2026 | Policy | Free allocation for aviation ends in 2026 |

Starting point: 2025 verified emissions (62.48 Mt) and 2025 EUA price (EUR 73.43/t).

**Part D, scenarios:** 2030 EUA price median of EUR 70/t (low), EUR 90/t (central) and EUR 150/t (high), taken from the carbon-price axis of the project's 3×3 oil × carbon scenario matrix.

**Part F, fan chart:** each year from 2026 to 2030 is simulated along a geometric price path from the 2025 price to the scenario median, with price uncertainty scaled by √(horizon).

---

## Headline results

| Result | Value |
|---|---|
| Back-test, years inside the 90% band (2021–2025) | Linear 1/5, log-linear 4/5 |
| 2030 net cost, central scenario | Median EUR 6.1 bn, 90% interval EUR 3.4–11.1 bn |
| Dominant input | Carbon price (fixing it cuts the half-width from 63% to 9%) |
| Scenario medians (EUR 70 / 90 / 150 per t) | EUR 4.8 / 6.1 / 10.2 bn |
| Largest scenario gap vs central 90% width | EUR 5.5 bn vs EUR 7.7 bn |

---

## How to run

1. Put `lab5.ipynb`, `eea_ets_aviation.csv` and `eua_price_annual.csv` in the **same folder** (in the notebook, `DATA = Path(".")`).
2. Install the dependencies: `pip install numpy pandas matplotlib scipy` (already available on Google Colab).
3. **Kernel → Restart & Run All.** The notebook writes `fig_uncertainty.png` to the same folder.

On Google Colab, upload the two CSV files to the root of the file panel (not into a sub-folder).

---

## Limitations

- **SAF allowances** (free allowances reserved to cover sustainable aviation fuel uptake, 2024–2030) are ignored, so the payable share after 2026 is slightly overstated.
- A possible **extension of the ETS to extra-EEA flights** is not modelled; it would multiply the emissions in scope.
- **Cost pass-through** to ticket prices is not modelled; the figure is the gross cost before any pass-through.
- The annual mean **auction** price is used as a proxy for the price airlines actually paid, which depends on their hedging and purchase timing.
- The **oil price** is not part of this lab's key quantity; it enters the full project through the EBIT-margin scenario matrix.

---

## References

- European Environment Agency, *EU Emissions Trading System (ETS) data viewer*. https://www.eea.europa.eu/data-and-maps/dashboards/emissions-trading-viewer-1
- European Energy Exchange (EEX), *EUA Primary Market Auction Report, history 2012–2025*. https://www.eex.com/en/market-data/environmentals/eu-ets-auctions
- European Commission, *Reducing emissions from aviation*. https://climate.ec.europa.eu/areas-action/transport-decarbonisation/reducing-emissions-aviation_en
