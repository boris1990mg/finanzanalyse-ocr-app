
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Finanzanalyse – Excel robust", layout="wide")
st.title("Finanzanalyse App – robust für BWA-Excel-Vorlagen")

uploaded_file = st.file_uploader("Lade deine BWA als Excel, CSV oder PDF hoch", type=["xlsx", "csv", "pdf"])

def steuer_hochrechnung(gewinn_monatlich, form):
    jahresgewinn = gewinn_monatlich * 12
    steuer = jahresgewinn * (0.30 if form == "Einzelunternehmen" else 0.15 + 0.15)
    return steuer, jahresgewinn - steuer

form = st.selectbox("Unternehmensform", ["Einzelunternehmen", "Kapitalgesellschaft (GmbH/UG)"])

if uploaded_file:
    df = None

    if uploaded_file.name.endswith(".xlsx"):
        xls = pd.ExcelFile(uploaded_file)
        df_raw = xls.parse(xls.sheet_names[0])

        try:
            # Robust: Extrahiere Spalte A und C ab Zeile 4
            df = df_raw.iloc[3:20, [0, 2]].copy()
            df.columns = ["Position", "Juli 2021"]
            df = df.dropna()
            df = df[df["Position"].astype(str).str.strip() != ""]
        except Exception as e:
            st.error(f"Fehler beim Einlesen: {e}")

    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    elif uploaded_file.name.endswith(".pdf"):
        import pdfplumber
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            lines = text.splitlines()
            data = []
            for line in lines:
                parts = [p.strip() for p in line.split(";")]
                if len(parts) > 1:
                    data.append(parts)
            df = pd.DataFrame(data[1:], columns=["Position"] + data[0][1:])
        except Exception as e:
            st.error(f"PDF konnte nicht gelesen werden: {e}")

    if df is not None:
        st.write("Vorschau der Daten:")
        st.dataframe(df)

        try:
            match_row = df[df["Position"].astype(str).str.lower().str.contains("gewinn|überschuss|ergebnis")]
            if not match_row.empty:
                monatswert = pd.to_numeric(match_row.iloc[0, 1], errors="coerce")
                steuer, netto = steuer_hochrechnung(monatswert, form)

                st.markdown(f"### Monatlicher Durchschnittsgewinn: {monatswert:,.2f} €")
                st.markdown(f"### Jährliche Steuer (geschätzt): {steuer:,.2f} €")
                st.markdown(f"### Netto-Gewinn nach Steuern: {netto:,.2f} €")

                fig, ax = plt.subplots()
                ax.bar(["Monatsgewinn", "Steuer", "Netto"], [monatswert, steuer, netto])
                ax.set_title("Finanzübersicht")
                st.pyplot(fig)

                if netto / 12 > 2500:
                    st.success("Kapitaldienstfähig")
                else:
                    st.warning("Kapitaldienst unsicher")
            else:
                st.warning("Keine Gewinn-Zeile gefunden.")
        except Exception as e:
            st.error(f"Analysefehler: {e}")
