import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Outil Cash Flow Immobilier", layout="wide")
st.title("📊 Outil de Calcul du Cash Flow d'un Projet Immobilier")

# --- Paramètres du projet ---
st.sidebar.header("📁 Paramètres du projet")
n_months = st.sidebar.slider("Durée du projet (mois)", 12, 240, 60)
date_debut = st.sidebar.date_input("Date de début du projet", datetime.today())
taux_croissance_loyer = st.sidebar.number_input("Croissance annuelle des loyers (%)", 0.0, 10.0, 2.0) / 100

# --- Investissements initiaux ---
st.header("1. Investissements initiaux")
capex_items = st.text_area("Liste des investissements (nom, montant, mois)",
    "Achat terrain,100000,0\nFrais notaire,8000,0\nÉtudes,12000,1\nTravaux,300000,0")
capex_data = []
for line in capex_items.strip().split("\n"):
    nom, montant, mois = line.split(",")
    capex_data.append({"Nom": nom, "Montant": float(montant), "Mois": int(mois)})
capex_df = pd.DataFrame(capex_data)

# --- Financement ---
st.header("2. Financement")
apport = st.number_input("Apport personnel (€)", 0, 1000000, 80000)
pret = st.number_input("Montant du prêt (€)", 0, 1000000, 300000)
taux_pret = st.number_input("Taux d'intérêt annuel (%)", 0.0, 10.0, 3.5) / 100
duree_pret = st.slider("Durée du prêt (années)", 1, 30, 20)
debut_pret = st.number_input("Début du prêt (mois)", 0, n_months, 3)

# --- Calcul remboursement prêt ---
def calc_amortissement(montant, taux, duree, n_mois, start):
    mensualite = np.pmt(taux/12, duree*12, -montant)
    remboursements = np.zeros(n_mois)
    for i in range(start, min(n_mois, start + duree * 12)):
        remboursements[i] = mensualite
    return remboursements

remboursements = calc_amortissement(pret, taux_pret, duree_pret, n_months, debut_pret)

# --- Revenus locatifs ---
st.header("3. Revenus locatifs")
loyer_initial = st.number_input("Loyer mensuel initial (€)", 0, 10000, 1500)
debut_loyers = st.number_input("Début des loyers (mois)", 0, n_months, 12)
revenus = np.zeros(n_months)
for i in range(debut_loyers, n_months):
    annee = (i - debut_loyers) // 12
    revenus[i] = loyer_initial * ((1 + taux_croissance_loyer) ** annee)

# --- Dépenses mensuelles ---
st.header("4. Dépenses courantes")
charge_mensuelle = st.number_input("Charges mensuelles (€)", 0, 5000, 200)
taxe_fonciere = st.number_input("Taxe foncière annuelle (€)", 0, 10000, 1200)
depenses = np.full(n_months, charge_mensuelle) + remboursements
for i in range(n_months):
    if i % 12 == 0:
        depenses[i] += taxe_fonciere

for _, row in capex_df.iterrows():
    depenses[int(row['Mois'])] += row['Montant']

# --- Calcul du Cash Flow ---
st.header("5. Synthèse du Cash Flow")
cash_flow = revenus - depenses
cash_cumule = np.cumsum(cash_flow)

synthese = pd.DataFrame({
    "Date": [date_debut + timedelta(days=30*i) for i in range(n_months)],
    "Revenus (€)": revenus,
    "Dépenses (€)": depenses,
    "Cash Flow mensuel (€)": cash_flow,
    "Cash Flow cumulé (€)": cash_cumule
})

st.dataframe(synthese.style.format({col: "{:.0f}" for col in synthese.columns if "€" in col}))
st.line_chart(synthese.set_index("Date")["Cash Flow cumulé (€)"])

# --- Export CSV ---
st.download_button("📥 Télécharger les résultats (CSV)", data=synthese.to_csv(index=False), file_name="cashflow_projet_immobilier.csv")
