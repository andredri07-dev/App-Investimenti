import streamlit as st
from google import genai
from google.genai import types
import streamlit.components.v1 as components

st.set_page_config(page_title="Analisi Investimenti", layout="wide")

st.title("📈 Analisi Finanziaria & Mercati")
st.caption("Analisi basata esclusivamente sulle fonti autorizzate della tua Knowledge Base.")

# Barra laterale: Configurazione API e Selezione Fonti
st.sidebar.header("⚙️ Configurazione")
api_key = st.sidebar.text_input("Inserisci la tua Google API Key:", type="password")

st.sidebar.header("📚 Seleziona le Fonti da Consultare")

FONTI_KB = [
    "Banche d'Affari & Broker (Goldman Sachs, Mediobanca, Intermonte, Equita)",
    "Società di Gestione (Euro SGR, Zenit SGR, Eurizon, Kairos)",
    "Ricerca Indipendente & Macro (Phastidio.net, NoRisk SCF)",
    "Istituzionali & Dati (Milano Finanza Dossier, Financial Times, CPB Netherlands, S&P SPIVA)"
]

seleziona_tutte = st.sidebar.checkbox("Usa tutte le fonti della Knowledge Base", value=True)

if seleziona_tutte:
    fonti_attive = FONTI_KB
else:
    fonti_attive = [f for f in FONTI_KB if st.sidebar.checkbox(f, value=False)]

# Area Principale: Input Utente
col1, col2 = st.columns([2, 1])

with col1:
    ticker = st.text_input("Ticker o Simbolo Azienda/ETF (es. ENI, AAPL, SWDA, CSPX):", "ENI").upper().strip()

with col2:
    tipo_asset = st.selectbox("Tipo di Strumento:", ["Azione / Azienda", "ETF"])

# Sezione Grafico TradingView
st.subheader(f"📊 Grafico Interattivo: {ticker}")
tradingview_html = f"""
<div class="tradingview-widget-container" style="height:450px;width:100%">
  <div id="tradingview_chart" style="height:450px;width:100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "autosize": true,
    "symbol": "{ticker}",
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

# Pulsante per avviare l'analisi con Gemini
if st.button("Genera Report di Analisi"):
    if not api_key:
        st.error("Inserisci la tua Google API Key nella barra laterale a sinistra per procedere.")
    elif not fonti_attive:
        st.error("Seleziona almeno una fonte dalla barra laterale.")
    else:
        with st.spinner("Ricerca in corso sulle fonti selezionate ed elaborazione del report..."):
            try:
                client = genai.Client(api_key=api_key)

                prompt_fonti = "\n".join([f"- {f}" for f in fonti_attive])

                if tipo_asset == "Azione / Azienda":
                    schema_richiesto = """
                    1. Sintesi Operativa (Executive Summary): Massimo 3 punti chiari su cosa fa l'azienda e la situazione attuale.
                    2. Piani Strategici e Mosse Future: Progetti, investimenti, nuove linee di business o espansioni annunciate.
                    3. Guidance e Prospettive: Stime di ricavi/utili o target price espressi dalle fonti selezionate.
                    4. Fattori di Rischio: Criticità di mercato, debito o concorrenza.
                    5. Dizionario Tecnico: Spiega in 1-2 frasi semplici ogni termine tecnico finanziario utilizzato sopra.
                    """
                else:
                    schema_richiesto = """
                    1. Profilo e Obiettivo dell'ETF: Indice benchmark replicato, politica di distribuzione/accumulazione e costo annuo (TER indicativo).
                    2. Composizione e Sottostanti: Settori e geografie principali su cui investe.
                    3. Prospettive Macro e Trend: Come le fonti selezionate vedono il settore o l'indice replicato dall'ETF.
                    4. Fattori di Rischio Specifici: Rischio cambio valuta, concentrazione o volatilità.
                    5. Dizionario Tecnico: Spiega in 1-2 frasi semplici ogni termine tecnico finanziario utilizzato sopra (es. TER, tracking error).
                    """

                system_instruction = f"""
                Sei un analista finanziario imparziale per piccoli investitori. Il tuo linguaggio deve essere semplice e accessibile.
                DEVI basare le tue informazioni ESCLUSIVAMENTE sulle ricerche web inerenti alle seguenti fonti autorizzate:
                {prompt_fonti}
                
                Se una notizia o stima non proviene da una di queste fonti, NON riportarla. Cita esplicitamente quale fonte ha espresso ciascuna opinione o dato.
                """

                user_prompt = f"""
                Analizza l'asset '{ticker}' ({tipo_asset}). 
                Effettua una ricerca web consultando solo le fonti autorizzate ed elabora il report seguendo rigorosamente questa struttura:
                {schema_richiesto}
                """

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                )

                st.markdown("---")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"Si è verificato un errore durante la chiamata a Gemini: {e}")
