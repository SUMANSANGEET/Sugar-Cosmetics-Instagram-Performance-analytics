# Sugar Cosmetics · Instagram Performance Analytics (Streamlit)

```bash
pip install -r requirements.txt
python preprocess.py sugar_cosmetics_instagram_data.xlsx   # builds data/sugar_cosmetics_clean.csv
streamlit run app.py
```
Deploy: push to GitHub → share.streamlit.io → New app → main file `app.py`.
See `deliverables/` for the insights document, business summary, Streamlit guide and stakeholder deck.

## Jupyter notebook
`Sugar_Cosmetics_Instagram_Analysis.ipynb` — 16 numbered steps from raw Excel to recommendations, with interactive Plotly charts and an ipywidgets filter panel.
```bash
pip install pandas numpy plotly scipy openpyxl ipywidgets jupyterlab
jupyter lab Sugar_Cosmetics_Instagram_Analysis.ipynb   # Restart & Run All
```
