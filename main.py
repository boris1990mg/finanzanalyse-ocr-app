
import streamlit as st
import pytesseract
from PIL import Image
import pdf2image
import pandas as pd
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="Finanzanalyse OCR", layout="wide")
st.title("Finanzanalyse mit OCR (gescannte PDFs)")

uploaded_file = st.file_uploader("Lade eine gescannte BWA als PDF hoch", type=["pdf"])

def steuer_hochrechnung(gewinn_monatlich, form):
    jahresgewinn = gewinn_monatlich * 12
    if form == "Einzelunternehmen":
        steuer = jahresgewinn * 0.30
    else:
        steuer = jahresgewinn * 0.15 + jahresgewinn * 0.15
    return steuer, jahresgewinn - steuer

form = st.selectbox("Unternehmensform", ["Einzelunternehmen", "Kapitalgesellschaft (GmbH/UG)"])

if uploaded_file:
    st.info("Verarbeite PDF... Bitte einen Moment Geduld.")
    images = pdf2image.convert_from_bytes(uploaded_file.read())
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img, lang="deu") + "\n"

    st.text_area("Erkannter Text", text, height=300)

    lines = text.splitlines()
    data = []
    for line in lines:
        if any(char.isdigit() for char in line):
            parts = [p.strip() for p in line.split() if p.strip() != ""]
            if len(parts) > 2:
                data.append(parts)

    if len(data) > 0:
        df = pd.DataFrame(data)
        st.write("Erkannte Rohdaten als Tabelle (manuell anpassbar):")
        st.dataframe(df)

        try:
            # Suche Zeile mit Gewinn
            for i in range(len(df)):
                if "gewinn" in df.iloc[i][0].lower():
                    monatsgewinne = df.iloc[i][1:].astype(float)
                    monatsgewinn_durchschnitt = monatsgewinne.mean()
                    steuer, netto = steuer_hochrechnung(monatsgewinn_durchschnitt, form)

                    st.markdown(f"### Monatlicher Durchschnittsgewinn: {monatsgewinn_durchschnitt:,.2f} €")
                    st.markdown(f"### Jährliche Steuer (geschätzt): {steuer:,.2f} €")
                    st.markdown(f"### Netto-Gewinn nach Steuern: {netto:,.2f} €")

                    fig, ax = plt.subplots()
                    ax.plot(monatsgewinne.values, marker="o")
                    ax.set_title("Monatlicher Gewinn")
                    st.pyplot(fig)

                    if netto / 12 > 2500:
                        st.success("Kapitaldienstfähig")
                    else:
                        st.warning("Kapitaldienst unsicher")
                    break
        except Exception as e:
            st.error("Konnte keine Gewinn-Zeile automatisch erkennen.")
    else:
        st.warning("Keine tabellarischen Werte erkannt.")
