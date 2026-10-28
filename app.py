import streamlit as st
import feedparser
import urllib.parse
from google import genai
from google.genai import types
import streamlit.components.v1 as components

st.set_page_config(page_title="Analisi Investimenti", layout="wide")

st.title("📈 Analisi Finanziaria & Mercati")
st.caption("Analisi in tempo reale basata esclusivamente sulle fonti autorizzate della tua Knowledge Base.")

# Mappatura delle fonti con i rispettivi domini web ufficiali
FONTI_DOMINI = {
    "Milano Finanza & Dossier": "milanofinanza.it",
    "Financial Times (FT / FT Alphaville)": "ft.com",
    "Phastidio.net (Mario Seminerio)": "phastidio.net",
    "Banche d'Affari & Broker (Mediobanca, Intermonte, Equita)": "mediobanca.com OR intermonte.it OR equita.it",
    "Società di Gestione (Eurizon, Kairos, Zenit)": "eurizoncapital.com OR kairospartners.com OR zenitgr.it",
    "Analisi Macro & Istituzionali (NoRisk, CPB)": "norisk.it OR cpb.nl"
}

# Barra laterale: Configurazione API e Selezione Fonti
st.sidebar.header("⚙️ Configurazione")
api_key = st.sidebar.text_input("Inserisci la tua Google API Key:", type="password")

st.sidebar.header("📚 Seleziona le Fonti da Consultare")

seleziona_tutte = st.sidebar.checkbox("Usa tutte le fonti della Knowledge Base", value=True)

fonti_selezionate = []
for nome_fonte, dominio in FONTI_DOMINI.items():
    if seleziona_tutte:
        attiva = st.sidebar.checkbox(nome_fonte, value=True, key=nome_fonte)
    else:
        attiva = st.sidebar.checkbox(nome_fonte, value=False, key=nome_fonte)
    if attiva:
        fonti_selezionate.append((nome_fonte, dominio))

# Area Principale: Input Utente
col1, col2 = st.columns([2, 1])

with col1:
    ticker = st.text_input("Ticker o Nome Asset (es. UCG, Unicredit, ENI, AAPL, SWDA):", "Unicredit").strip()

with col2:
    tipo_asset = st.selectbox("Tipo di Strumento:", ["Azione / Azienda", "ETF"])

# Sezione Grafico TradingView
st.subheader(f"📊 Grafico Interattivo: {ticker.upper()}")
tradingview_html = f"""
<div class="tradingview-widget-container" style="height:450px;width:100%">
  <div id="tradingview_chart" style="height:450px;width:100%"></div>
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
components.html(tradingview_html, height=470)

# Funzione per estrarre notizie in tempo reale dalle sole fonti selezionate
def recupera_notizie_live(query_asset, lista_fonti):
    notizie_raccolte = []
    
    # Costruisci filtro query per i domini autorizzati
    domini = " OR ".join([f"site:{d}" for _, d in lista_fonti])
    query = f"{query_asset} ({domini})"
    query_encoded = urllib.parse.quote(query)
    
    # Feed RSS Google News mirato esclusivamente ai domini autorizzati
    rss_url = f"https://news.google.com/rss/search?q={query_encoded}&hl=it&gl=IT&ceid=IT:it"
    feed = feedparser.parse(rss_url)
    
    for entry in feed.entries[:8]:  # Prende i primi 8 aggiornamenti più recenti
        titolo = entry.get('title', '')
        link = entry.get('link', '')
        data = entry.get('published', '')
        notizie_raccolte.append(f"- Titolo: {titolo}\n  Data: {data}\n  Link: {link}")
        
    return notizie_raccolte

# Avvio Analisi
if st.button("Genera Report di Analisi"):
    if not api_key:
        st.error("Inserisci la tua Google API Key nella barra laterale a sinistra per procedere.")
    elif not fonti_selezionate:
        st.error("Seleziona almeno una fonte dalla barra laterale.")
    else:
        with st.spinner("Estrazione notizie in tempo reale e analisi in corso con Gemini..."):
            try:
                # 1. Recupero notizie live esterne
                notizie = recupera_notizie_live(ticker, fonti_selezionate)
                
                if notizie:
                    testo_notizie = "\n\n".join(notizie)
                else:
                    testo_notizie = "Nessun articolo recentissimo trovato su queste specifiche fonti per questo ticker. Utilizza la conoscenza istituzionale delle fonti selezionate."

                # 2. Definizione schema
                if tipo_asset == "Azione / Azienda":
                    schema_richiesto = """
                    1. Sintesi Operativa (Executive Summary): Massimo 3 punti chiari sulla situazione attuale dell'azienda.
                    2. Piani Strategici e Mosse Future: Cosa ha intenzione di fare l'azienda (nuovi piani industriali, M&A, investimenti, guidance).
                    3. Target e Prospettive del Settore: Opinione e consensus delle fonti selezionate.
                    4. Fattori di Rischio: Criticità di mercato, tassi, regolamentazione o debito.
                    5. Dizionario Tecnico: Spiega in 1 frase semplice ciascun termine tecnico usato (es. ROTE, NII, CET1, Guidance).
                    """
                else:
                    schema_richiesto = """
                    1. Profilo e Obiettivo dell'ETF: Benchmark replicato, politica di distribuzione/accumulazione e costo annuo (TER).
                    2. Composizione e Sottostanti: Settori e geografie principali.
                    3. Prospettive Macro e Trend: Come le fonti selezionate vedono il settore/indice replicato.
                    4. Fattori di Rischio Specifici: Valuta, concentrazione, volatilità.
                    5. Dizionario Tecnico: Spiega in 1 frase semplice ciascun termine tecnico usato (es. TER, Tracking Error, Replica Fisica).
                    """

                fonti_nomi = ", ".join([nome for nome, _ in fonti_selezionate])

                prompt_completo = f"""
                Sei un analista finanziario imparziale per piccoli investitori. Usa un linguaggio chiaro e accessibile.
                
                ASSET RICHIESTO: {ticker} ({tipo_asset})
                FONTI AUTORIZZATE SELEZIONATE DALL'UTENTE: {fonti_nomi}
                
                ECCO GLI ULTIMI AGGIORNAMENTI TROVATI IN TEMPO REALE DA QUESTE FONTI:
                {testo_notizie}
                
                Istruzioni:
                - Basa la tua risposta su questi aggiornamenti e sulle posizioni note delle fonti selezionate.
                - Cita esplicitamente le fonti che supportano le informazioni.
                - Rispetta scrupolosamente questa struttura:
                {schema_richiesto}
                """

                # 3. Chiamata diretta a Gemini 3.8 senza tool esterni costosi
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt_completo
                )

                st.markdown("---")
                st.markdown(response.text)

                if notizie:
                    with st.expander("🔗 Vedi le notizie estratte in tempo reale"):
                        for n in notizie:
                            st.markdown(n)

            except Exception as e:
                st.error(f"Si è verificato un errore durante la chiamata a Gemini: {e}")

            except Exception as e:
                st.error(f"Si è verificato un errore durante la chiamata a Gemini: {e}")
