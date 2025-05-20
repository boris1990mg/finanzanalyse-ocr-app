
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Finanzanalyse Basic", layout="wide")
st.title("Finanzanalyse Basic – PDF, Excel & CSV Upload")

uploaded_file = st.file_uploader("Lade eine BWA hoch (PDF mit Text, Excel oder CSV)", type=["csv", "xlsx", "pdf"])

def steuer_hochrechnung(gewinn_monatlich, form):
    jahresgewinn = gewinn_monatlich * 12
    if form == "Einzelunternehmen":
        steuer = jahresgewinn * 0.30
    else:
        steuer = jahresgewinn * 0.15 + jahresgewinn * 0.15
    return steuer, jahresgewinn - steuer

form = st.selectbox("Unternehmensform", ["Einzelunternehmen", "Kapitalgesellschaft (GmbH/UG)"])

df = None
if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
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
                if ";" in line:
                    data.append(line.split(";"))
                else:
                    parts = [p.strip() for p in line.split("  ") if p.strip() != ""]
                    if len(parts) > 1:
                        data.append(parts)

            if len(data) >= 2:
                df = pd.DataFrame(data[1:], columns=["Position"] + data[0][1:])
        except Exception as e:
            st.error(f"PDF konnte nicht gelesen werden: {e}")

if df is not None:
    st.write("Vorschau der BWA-Daten:")
    st.dataframe(df)

    try:
        gewinn_zeile = df[df["Position"].str.contains("Gewinn", case=False, na=False)]
        monatsgewinne = gewinn_zeile.drop(columns=["Position"]).values.flatten().astype(float)
        monatsgewinn_durchschnitt = monatsgewinne.mean()

        steuer, netto = steuer_hochrechnung(monatsgewinn_durchschnitt, form)

        st.markdown(f"### Monatlicher Durchschnittsgewinn: {monatsgewinn_durchschnitt:,.2f} €")
        st.markdown(f"### Jährliche Steuer (geschätzt): {steuer:,.2f} €")
        st.markdown(f"### Netto-Gewinn nach Steuern: {netto:,.2f} €")

        fig, ax = plt.subplots()
        ax.plot(df.columns[1:], monatsgewinne, marker="o")
        ax.set_title("Monatlicher Gewinnverlauf")
        st.pyplot(fig)

        if netto / 12 > 2500:
            st.success("Kapitaldienstfähig")
        else:
            st.warning("Kapitaldienst unsicher")
    except:
        st.warning("Gewinn-Zeile konnte nicht erkannt werden.")
