import streamlit as st
import feedparser
import urllib.parse
from google import genai
from google.genai import types
import streamlit.components.v1 as components

st.set_page_config(page_title="Analisi Investimenti Istituzionale", layout="wide")

st.title("📈 Piattaforma Analisi Finanziaria & Mercati")
st.caption("Intelligence report ad alta profondità basato esclusivamente sulle fonti autorizzate della Knowledge Base.")

# Mappatura analitica completa delle singole fonti dal documento PDF
FONTI_ORGANIZZATE = {
    "📰 Testate & Giornalismo Finanziario": {
        "Milano Finanza (MF / MF Insight)": "milanofinanza.it",
        "Financial Times (FT & Alphaville)": "ft.com"
    },
    "🧠 Ricerca Macroeconomica & Analisi Indipendente": {
        "Phastidio.net (Mario Seminerio)": "phastidio.net",
        "NoRisk SCF (Risk management & advisory)": "norisk.it",
        "CPB Netherlands (World Trade & Macro)": "cpb.nl"
    },
    "🏛️ Banche d'Affari & Ricerca Broker": {
        "Mediobanca Research": "mediobanca.com",
        "Intermonte Research": "intermonte.it",
        "Equita SIM": "equita.it",
        "Goldman Sachs Global Investment": "goldmansachs.com"
    },
    "💼 Società di Gestione del Risparmio (SGR)": {
        "Euro SGR": "eurosgr.it",
        "Zenit SGR": "zenitsgr.it",
        "Eurizon Capital": "eurizoncapital.com",
        "Kairos Partners SGR": "kairospartners.com"
    },
    "📊 Benchmark, Indici & Flussi Istituzionali": {
        "S&P SPIVA Dashboard & Indices": "spglobal.com"
    }
}

# Barra laterale: Configurazione
st.sidebar.header("⚙️ Configurazione")
api_key = st.sidebar.text_input("Inserisci la tua Google API Key:", type="password")

st.sidebar.header("📚 Selezione Analitica Fonti")
seleziona_tutte = st.sidebar.checkbox("Seleziona TUTTE le fonti della Knowledge Base", value=True)

fonti_selezionate = []

for macro_cat, dizionario_fonti in FONTI_ORGANIZZATE.items():
    st.sidebar.markdown(f"**{macro_cat}**")
    for nome_singola_fonte, dominio in dizionario_fonti.items():
        if seleziona_tutte:
            attiva = st.sidebar.checkbox(nome_singola_fonte, value=True, key=nome_singola_fonte)
        else:
            attiva = st.sidebar.checkbox(nome_singola_fonte, value=False, key=nome_singola_fonte)
        if attiva:
            fonti_selezionate.append((nome_singola_fonte, dominio))

# Area Principale: Input Utente
col1, col2 = st.columns([2, 1])

with col1:
    ticker = st.text_input("Ticker o Nome Strumento (es. UCG, Unicredit, ENI, AAPL, SWDA, CSPX):", "Unicredit").strip()

with col2:
    tipo_asset = st.selectbox("Tipologia Asset:", ["Azione / Azienda", "ETF"])

# Sezione Grafico TradingView Interattivo
st.subheader(f"📊 Grafico di Mercato: {ticker.upper()}")
tradingview_html = f"""
<div class="tradingview-widget-container" style="height:460px;width:100%">
  <div id="tradingview_chart" style="height:460px;width:100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "autosize": true,
    "symbol": "{ticker.upper()}",
    "interval": "D",
    "timezone": "Europe/Rome",
    "theme": "light",
    "style": "1",
    "locale": "it",
    "enable_publishing": false,
    "allow_symbol_change": true,
    "studies": [
      "MASimple@tv-basicstudies",
      "Volume@tv-basicstudies"
    ],
    "container_id": "tradingview_chart"
  }});
  </script>
</div>
"""
components.html(tradingview_html, height=480)

# Funzione per estrarre notizie in tempo reale dalle fonti selezionate
def recupera_notizie_live(query_asset, lista_fonti):
    notizie_raccolte = []
    
    # Costruzione stringa OR per i soli domini autorizzati
    domini = " OR ".join([f"site:{d}" for _, d in lista_fonti])
    query = f"{query_asset} ({domini})"
    query_encoded = urllib.parse.quote(query)
    
    rss_url = f"https://news.google.com/rss/search?q={query_encoded}&hl=it&gl=IT&ceid=IT:it"
    feed = feedparser.parse(rss_url)
    
    for entry in feed.entries[:10]:
        titolo = entry.get('title', '')
        link = entry.get('link', '')
        data = entry.get('published', '')
        notizie_raccolte.append(f"- Titolo: {titolo}\n  Data: {data}\n  Fonte Web: {link}")
        
    return notizie_raccolte

# Elaborazione Report
if st.button("Genera Report Completo ed Esaustivo", type="primary"):
    if not api_key:
        st.error("Inserisci la tua Google API Key nella barra laterale a sinistra per procedere.")
    elif not fonti_selezionate:
        st.error("Seleziona almeno una fonte dalla barra laterale.")
    else:
        with st.spinner("Scansione in tempo reale delle fonti e stesura del dossier istituzionale..."):
            try:
                # 1. Recupero notizie fresche
                notizie = recupera_notizie_live(ticker, fonti_selezionate)
                testo_notizie = "\n\n".join(notizie) if notizie else "Nessuna rassegna istantanea trovata per questa ricerca. Fai affidamento sull'analisi strutturale e sui documenti strategici delle fonti selezionate."

                fonti_nomi = ", ".join([nome for nome, _ in fonti_selezionate])

                # 2. Template per analisi approfondita
                if tipo_asset == "Azione / Azienda":
                    schema_dettagliato = """
                    ## 1. Executive Summary & Posizionamento di Mercato
                    - Descrivi in modo chiaro e dettagliato la tesi di investimento attuale sull'azienda.
                    - Fornisci una panoramica approfondita sullo stato di salute operativa, solidità patrimoniale e trend di redditività recente.

                    ## 2. Piani Strategici & Mosse Future (Dossier Industriale)
                    - Piani industriali, target a medio-lungo termine e progetti strategici dichiarati dal management.
                    - Politiche di allocazione del capitale: investimenti in innovazione/CAPEX, aperture a nuove aree geografiche, operazioni di M&A (fusioni o acquisizioni), sinergie previste.
                    - Politica verso gli azionisti: dividendi, rendimento atteso e piani di riacquisto di azioni proprie (buyback).

                    ## 3. Stime, Target Price & Consensus delle Fonti Autorizzate
                    - Quali sono le stime e le aspettative espresse dalle banche d'affari, broker e analisti presenti nelle fonti selezionate?
                    - Evidenzia se vi sono divergenze o convergenze di visione tra le diverse fonti (es. posizioni rialziste vs caute).

                    ## 4. Matrice dei Rischi & Punti Deboli
                    - Rischi macroeconomici e di mercato (impatto dell'andamento dei tassi d'interesse, inflazione, ciclo economico).
                    - Rischi competitivi e industriali (pressione sui margini, concorrenza, costi operativi).
                    - Rischi legali, regolatori o di governance.

                    ## 5. Dizionario Tecnico per Piccoli Investitori
                    - Per OGNI termine tecnico o finanziario menzionato nel report (es. ROTE, NII, CET1, Guidance, Buyback, CAPEX, EBITDA, Multipli P/E), fornisci una spiegazione chiara, pratica e senza gergo in massimo 1-2 frasi.
                    """
                else:
                    schema_dettagliato = """
                    ## 1. Identikit Strutturale & Politica dell'ETF
                    - Indice benchmark replicato e caratteristiche dell'esposizione (azionario, obbligazionario, settoriale o tematico).
                    - Tipologia di replica (fisica a campionamento/totale vs sintetica), politica di gestione dei proventi (accumulazione vs distribuzione) e costo di gestione annuo (TER indicativo).

                    ## 2. Anatomia dei Sottostanti & Concentrazione
                    - Principali 5-10 aziende in portafoglio e peso relativo.
                    - Suddivisione per aree geografiche e macrosettori industriali (e relativi rischi di concentrazione).

                    ## 3. Scenario Macroeconomico & Visione delle Fonti
                    - Come le fonti selezionate (banche, gestori e analisti macro) valutano il settore, l'area geografica o la classe di attivo coperta da questo ETF.
                    - Prospettive di crescita o rotazione settoriale indicate nei report di ricerca.

                    ## 4. Analisi dei Rischi Specifici per il Risparmiatore
                    - Rischio di cambio (valuta dei sottostanti vs valuta di negoziazione).
                    - Volatilità attesa, rischio di drawdown e tracking error (differenziale di replica rispetto al benchmark).

                    ## 5. Dizionario Tecnico per Piccoli Investitori
                    - Per OGNI termine tecnico menzionato nel report (es. TER, Tracking Error, Replica Fisica Totale, Accumulazione, Drawdown, Benchmark), fornisci una spiegazione chiara e semplice in 1-2 frasi.
                    """

                prompt_completo = f"""
                Sei un consulente e analista finanziario senior di alto livello dedicato a supportare piccoli investitori.
                Il tuo compito è redigere un report COMPLETO, APPROFONDITO, DETTAGLIATO ED ESAUSTIVO (evita riassunti stringati, elenchi banali o risposte sbrigative).
                
                STRUMENTO ANALIZZATO: {ticker} ({tipo_asset})
                FONTI AUTORIZZATE ATTIVE NELL'APP: {fonti_nomi}
                
                NOTIZIE E AGGIORNAMENTI LIVE ESTRATTI DALLE FONTI:
                {testo_notizie}
                
                LINEE GUIDA RIGOROSE:
                1. Sviluppa ogni singola sezione con analisi approfondita, argomentazioni chiare e dettagli concreti.
                2. Cita esplicitamente quali fonti sostengono ciascuna affermazione o previsione.
                3. Mantieni un linguaggio professionale ma comprensibile, delegando i chiarimenti dei vocaboli specialistici alla Sezione 5.
                4. Segui tassativamente questa struttura:
                {schema_dettagliato}
                """

                # Chiamata al modello
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt_completo
                )

                st.markdown("---")
                st.markdown(response.text)

                if notizie:
                    with st.expander("🔗 Visualizza gli aggiornamenti web estratti in tempo reale"):
                        for n in notizie:
                            st.markdown(n)

            except Exception as e:
                st.error(f"Si è verificato un errore durante la chiamata a Gemini: {e}")

            except Exception as e:
                st.error(f"Si è verificato un errore durante la chiamata a Gemini: {e}")
