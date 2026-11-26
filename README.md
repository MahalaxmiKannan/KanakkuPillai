# Kanaku Pillai

A personal-finance awareness app for young people in India. Upload a bank statement and it shows where the money goes, what is left each month, and a realistic range of what a monthly SIP could become. It also checks investment messages for scam red flags.

> **Educational tool only, not investment advice.** Statements are processed in memory and never saved.

## Pages

The pages follow one path: look at your money, learn, then decide and try it.

| Step | Page | What it does | Status |
|---|---|---|---|
| 1 | Upload | SBI / HDFC / standard CSV or Excel, masks account numbers, or try a demo statement | Done |
| 2 | My Spending | Rules + ML categoriser, dropdown filters, month chart, merchant drill-down, correct low-confidence rows | Done |
| 3 | Risk Quiz | Short quiz that gives a risk profile | Done |
| 4 | Learn | Money Handbook flipbook: savings account, FD, RD, PPF, index fund SIP, gold, NPS | Done |
| 5 | My Surplus | One screen: income vs essentials vs the rest, a what-if lever, runway to an emergency fund | Done |
| 6 | Simulator | Monte Carlo SIP on real Nifty 50 history, fan chart, FD line, inflation; pre-filled from the surplus | Done |
| 7 | Scam Checker | Red-flag rules with reasons + a text model; highlights the phrases; links never clickable | Done |
| 8 | About | How the models work, numbers, limits | Day 6 |

## How the simulator works

- **Data:** Nifty 50 (`^NSEI`, Yahoo Finance) daily closes from Sep 2007 to Nov 2026 in `data/nifty50_history.csv`, turned into 229 month-end returns (Oct 2007 to Oct 2026) in `data/nifty_monthly.csv` by `scripts/make_nifty_monthly.py`. The unfinished current month is dropped.
- **Block bootstrap:** each of 10,000 paths is made of random real 12-month stretches of returns glued together. This keeps crashes and recoveries together and keeps the fat tails that a normal distribution would smooth away.
- **SIP:** a fixed amount goes in at the start of each month, for 1 to 15 years (capped because the history is only about 19 years long). The page shows the 10th, 50th and 90th percentile, the money put in, the chance of ending below it, and an FD line at an editable rate (default 7%).
- **Inflation:** on by default at 6% a year, so values show buying power today. "Chance below invested" is always judged in plain rupees.
- **Speed:** about 0.2 s per run (cached after that).
- **Limits:** price index only (no dividends), no fees, taxes or expense ratio, and past returns don't predict the future.

## Evaluation

Only numbers from real data are reported here.

**Expense categoriser.** Tested on 72 held-out real transactions from merchant rows. The split keeps every spelling of a merchant on the same side, so the model never sees a test merchant during training.

| | Accuracy | Macro F1 |
|---|---|---|
| Merchant rules only | 0.431 | 0.568 |
| Rules + ML | 0.792 | 0.652 |

Payments to people are never used for training, so names stay out of the model.

**Simulator backtest** (`notebooks/backtest_simulator.ipynb`). For every real SIP window (one per start month), does the real result land inside the simulated 10th to 90th percentile band? Target is about 80%.

| Window | Real windows | Non-overlapping | Inside band |
|---|---|---|---|
| 3 years | 194 | 6 | 99.0% |
| 5 years | 170 | 3 | 99.4% |
| 10 years | 110 | 1 | 100% |

**This does not show the ranges are good.** The bootstrap draws from the same history it is tested on, so the real windows are bound to land inside. High coverage could mean the bands are too wide, or simply that the test is circular, and this check can't distinguish the two. The windows also overlap heavily: there are only 6, 3 and 1 independent windows. A fair test would need data the simulator never saw.

The history is one 19-year stretch that mostly rose (about 8.3% a year in price terms), so the ranges may be kinder than the future.

**Scam checker** (`notebooks/train_scam_checker.ipynb`). The model is trained on **synthetic** messages only (189, written from about 25 scam and genuine templates); it is tested on **32 real messages** it never saw (15 scams, 17 genuine). "Flagged" means the checker says Medium or High. **Recall matters most here**: missing a scam costs far more than a second look at a genuine message.

| | Recall (scams caught) | Precision | False alarms |
|---|---|---|---|
| Red-flag rules only | 0.73 (11/15) | 1.00 | 0/17 |
| Text model only | 0.80 (12/15) | 0.63 | 7/17 |
| **Rules + model (in the app)** | **0.80** (12/15) | 0.75 | 4/17 |

Read these with care: the test set is tiny, the rules were written after the dataset (real messages included) had been read, so the rules-only row is optimistic, and the model learned from templates, so it is weak on real wording. The thresholds and the way rules and model are combined were fixed before the real messages were scored.

- **Synthetic data is marked as synthetic** in `data/scam_messages.csv` (`source` column). Real messages were collected from SMS, WhatsApp screenshots and public posts, with real people's names, a location and a phone number masked and scam links defanged (`scripts/clean_scam_messages.py`).
- **A shortcut removed:** most real genuine SMS contain mask tokens (XXXX) and most scams don't, so a model reading raw text would learn "XXXX means genuine". The model only sees text with masks removed and every number replaced by the word `num`; the rules ignore masks. A test checks the saved model's vocabulary has no digits or mask tokens.
- **Why not sentence embeddings:** the plan's sentence-transformers model needs PyTorch, too heavy for free hosting, so it uses the planned fallback: TF-IDF word and character n-grams + logistic regression.
- "Low risk" means no red flags were found, never that a message is safe.

## Run it

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; use source .venv/bin/activate elsewhere
pip install -r requirements.txt
streamlit run app.py
python -m pytest                # tests
```

To refresh the Nifty data, replace `data/nifty50_history.csv` with a newer yfinance download, then run `python scripts/make_nifty_monthly.py` and re-run `notebooks/backtest_simulator.ipynb`.

## Project layout

```
app.py, home.py          entry point and home page
pages/                   one file per step
core/                    parsers, masking, categorizer, surplus, risk_quiz, simulator, ...
content/                 Learn cards (markdown)
data/                    demo statement, synthetic labels, Nifty history (real statements stay in data/raw, gitignored)
models/                  categoriser model + metrics, simulator backtest results
notebooks/               training and backtest notebooks
scripts/                 data helpers
tests/                   pytest
```

## Disclaimer

This is an educational project. It is not investment, tax or legal advice, and it is not registered with SEBI. Talk to a SEBI-registered adviser before investing.
