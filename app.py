import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import feedparser
import time
import urllib.parse
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Configurazione pagina
st.set_page_config(
    page_title="Terminal Investimenti",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# KNOWLEDGE BASE: MAPPATURA COMPLETA DELLE FONTI
# -----------------------------------------------------------------------------
FONTI_KB = {
    "SGR & Banche d'Affari Italiane (Buy-Side)": [
        "Intesa Sanpaolo / IMI CIB", "Eurizon Capital SGR", "Poste SGR",
        "Generali Investments / Plenisfer", "Euro SGR", "Arca Fondi SGR",
        "Azimut Investments", "Kairos Partners SGR", "AcomeA SGR", "Etica SGR",
        "Anthilia Capital Partners", "Sella SGR", "Zenit SGR", "Ersel",
        "Banor SIM", "Fideuram Asset Management", "Mediolanum Gestione Fondi"
    ],
    "Broker & SIM Italiane (Sell-Side / Equity Research)": [
        "Equita SIM", "Intermonte SIM", "Banca Akros", "UniCredit Research",
        "Alantra Italy", "Banca Profilo", "Value Track", "IR Top Consulting",
        "Integrae SIM", "KT&Partners", "CFO SIM", "SCM SIM",
        "Banca Finnat Euramerica", "EnVent Capital Markets", "Mediobanca Securities"
    ],
    "Analisti Indipendenti & SCF": [
        "Consultique SCF", "IoInvesto SCF", "NoRisk SCF", "SoldiExpert SCF",
        "Cicli e Mercati (Caruso)", "MDOTM", "Lixi Invest / Plutus",
        "Affari Miei", "AdviseOnly", "Phastidio.net (Seminerio)"
    ],
    "Media Finanziari Italiani": [
        "Il Sole 24 Ore / Plus24", "Class CNBC / Milano Finanza", "We Wealth",
        "Radio 24", "FocusRisparmio", "Citywire Italia", "Bluerating",
        "Funds People Italia", "Wall Street Italia", "Morningstar Italia"
    ],
    "Istituzioni & Uffici Studi Italiani": [
        "Banca d'Italia", "CONSOB", "AIPB", "Assogestioni", "OCF",
        "Prometeia", "Cerved Group", "ABI", "ISTAT", "Assosim", "CER"
    ],
    "Banche d'Affari & Asset Manager Globali": [
        "Goldman Sachs Research", "J.P. Morgan Research", "BlackRock Investment Institute",
        "Morgan Stanley Research", "PIMCO", "Bridgewater Associates"
    ],
    "Boutique di Ricerca Globale & Sell-Side": [
        "Gavekal Research / Dragonomics", "Ned Davis Research (NDR)", "BCA Research",
        "Kepler Cheuvreux", "Redburn Atlantic", "Berenberg", "TS Lombard",
        "High Frequency Economics", "Cornerstone Macro"
    ],
    "Emittenti ETF & Provider Indici": [
        "Vanguard ISG", "State Street (SPDR)", "Invesco Global Strategy",
        "WisdomTree Research", "MSCI Research", "S&P Dow Jones Indices (SPIVA)"
    ],
    "Macroeconomisti Indipendenti Globali": [
        "Capital Economics", "Ex Uno Plures (Pozsar)", "Rosenberg Research",
        "Incrementum AG", "Yardeni Research", "The Bear Traps Report"
    ],
    "Media Finanziari Internazionali": [
        "Bloomberg / Bloomberg Intelligence", "Financial Times / Alphaville",
        "Reuters Breakingviews", "Wall Street Journal / Markets",
        "The Economist", "CNBC Pro"
    ],
    "Banche Centrali & Istituzioni Internazionali": [
        "CPB Netherlands", "Bruegel", "Federal Reserve (FED)", "European Central Bank (ECB)",
        "International Monetary Fund (IMF)", "OECD / OCSE", "Ifo Institute / ZEW",
        "Bank for International Settlements (BIS)"
    ]
}

# -----------------------------------------------------------------------------
# FUNZIONI DATI QUANTITATIVI (Deterministiche)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=900)
def scarica_dati_mercato(ticker_simbolo, periodo="1y"):
    ticker = yf.Ticker(ticker_simbolo)
    storico = ticker.history(period=periodo)
    info = ticker.info
    return storico, info

def calcola_indicatori(df):
    if df.empty:
        return df
    df = df.copy()
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    return df

def crea_grafico_candele(df, ticker_simbolo):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.75, 0.25]
    )
    
    # Prezzo e Medie Mobili
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="Prezzo"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA20'],
        line=dict(color='orange', width=1.5),
        name="SMA 20"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA50'],
        line=dict(color='blue', width=1.5),
        name="SMA 50"
    ), row=1, col=1)
    
    # Volumi
    colori_vol = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'],
        marker_color=colori_vol,
        name="Volume"
    ), row=2, col=1)
    
    fig.update_layout(
        title=f"Analisi Tecnica: {ticker_simbolo}",
        xaxis_rangeslider_visible=False,
        height=520,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# -----------------------------------------------------------------------------
# RACCOLTA NOTIZIE LIVE
# -----------------------------------------------------------------------------
def estrai_notizie_live(query, fonti_selezionate):
    query_encoded = urllib.parse.quote(f"{query} finance news")
    rss_url = f"https://news.google.com/rss/search?q={query_encoded}&hl=it&gl=IT&ceid=IT:it"
    feed = feedparser.parse(rss_url)
    
    notizie = []
    for entry in feed.entries[:8]:
        notizie.append({
            "titolo": entry.title,
            "link": entry.link,
            "data": entry.get("published", "")
        })
    return notizie

# -----------------------------------------------------------------------------
# CHIAMATA AI CON RETRY E BACKOFF (Protezione 503 e Quota)
# -----------------------------------------------------------------------------
def esegui_analisi_qualitativa(prompt, api_key):
    client = genai.Client(api_key=api_key)
    max_tentativi = 4
    ritardo = 2.0
    
    for tentativo in range(max_tentativi):
        try:
            risposta = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    system_instruction=(
                        "Sei un Senior Equity Analyst e Macroeconomista. Il tuo compito è analizzare notizie, "
                        "valutare rischi di mercato e spiegare concetti per investitori retail con estrema neutralità "
                        "e rigore accademico. Non inventare dati numerici o target price; commenta solo il contesto qualitativo "
                        "allineandoti ai canoni metodologici della Knowledge Base selezionata."
                    )
                )
            )
            return risposta.text
        except APIError as e:
            if tentativo < max_tentativi - 1:
                time.sleep(ritardo)
                ritardo *= 2
            else:
                return f"Errore temporaneo nei server AI (503/Quota): {str(e)}. Riprova tra pochi istanti."
        except Exception as e:
            return f"Errore durante l'elaborazione del report: {str(e)}"

# -----------------------------------------------------------------------------
# INTERFACCIA STREAMLIT
# -----------------------------------------------------------------------------
# Sidebar: Setup e Configurazione Fonti
with st.sidebar:
    st.header("⚙️ Configurazione")
    
    # Gestione API Key sicura
    api_key_env = st.secrets.get("GEMINI_API_KEY", "")
    api_key_input = st.text_input("Gemini API Key", value=api_key_env, type="password")
    api_key = api_key_input if api_key_input else api_key_env
    
    st.markdown("---")
    st.subheader("📚 Filtro Knowledge Base")
    st.caption("Seleziona gli istituti di riferimento per guidare la profondità dell'analisi:")
    
    tutte_fonti_selezionate = []
    for categoria, lista_fonti in FONTI_KB.items():
        with st.expander(categoria, expanded=False):
            seleziona_tutto = st.checkbox(f"Tutte ({categoria})", value=True, key=f"all_{categoria}")
            for fonte in lista_fonti:
                attivo = st.checkbox(fonte, value=seleziona_tutto, key=f"{categoria}_{fonte}")
                if attivo:
                    tutte_fonti_selezionate.append(fonte)

# Area Principale
st.title("📊 Terminale di Ricerca & Analisi Titoli")
st.markdown("Analisi fondamentale e tecnica basata su dati di borsa ed elaborazione qualitativa delle fonti istituzionali.")

col_search1, col_search2 = st.columns([3, 1])
with col_search1:
    ticker_input = st.text_input("Inserisci Ticker Azionario (es. ENI.MI, ISP.MI, AAPL, MSFT)", value="ENI.MI").upper().strip()
with col_search2:
    periodo_scelto = st.selectbox("Orizzonte Temporale", ["3mo", "6mo", "1y", "2y", "5y"], index=2)

if st.button("🚀 Avvia Analisi Completa", type="primary", use_container_width=True):
    if not api_key:
        st.error("Chiave API di Gemini mancante. Inseriscila nella sidebar o nei Secrets di Streamlit.")
        st.stop()
        
    with st.spinner("Estrazione dati di mercato e notizie in corso..."):
        try:
            storico, info = scarica_dati_mercato(ticker_input, periodo=periodo_scelto)
        except Exception as e:
            st.error(f"Errore nel recupero dati per {ticker_input}: {e}")
            st.stop()

    if storico.empty:
        st.warning(f"Nessun dato storico trovato per il simbolo '{ticker_input}'. Verifica che il ticker sia corretto.")
        st.stop()

    nome_azienda = info.get("shortName", ticker_input)
    valuta = info.get("currency", "EUR")
    prezzo_corrente = info.get("currentPrice") or info.get("regularMarketPrice") or (storico['Close'].iloc[-1] if not storico.empty else 0)

    # 1. METRICHE CHIAVE E CONSENSUS DEGLI ANALISTI
    st.subheader(f"📌 {nome_azienda} ({ticker_input}) — Metriche e Consensus di Mercato")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Prezzo Attuale", f"{prezzo_corrente:.2f} {valuta}")
    
    target_mean = info.get("targetMeanPrice")
    m2.metric("Target Price Medio", f"{target_mean:.2f} {valuta}" if target_mean else "N/D")
    
    recommendation = info.get("recommendationKey", "N/D").upper()
    m3.metric("Raccomandazione Consensus", recommendation)
    
    pe_ratio = info.get("trailingPE")
    m4.metric("P/E Ratio", f"{pe_ratio:.2f}" if pe_ratio else "N/D")

    # 2. GRAFICO TECNICO INTERATTIVO
    st.markdown("---")
    st.subheader("📈 Analisi Grafica (Candlestick, Medie Mobili e Volumi)")
    df_indicizzato = calcola_indicatori(storico)
    figura = crea_grafico_candele(df_indicizzato, ticker_input)
    st.plotly_chart(figura, use_container_width=True)

    # 3. NOTIZIE LIVE
    st.markdown("---")
    st.subheader("📰 Ultime Notizie Rilevate")
    notizie_raccolte = estrai_notizie_live(nome_azienda, tutte_fonti_selezionate)
    
    if notizie_raccolte:
        cols_notizie = st.columns(2)
        for idx, n in enumerate(notizie_raccolte[:4]):
            with cols_notizie[idx % 2]:
                st.markdown(f"• **[{n['titolo']}]({n['link']})**")
    else:
        st.info("Nessuna notizia recente individuata.")

    # 4. ELABORAZIONE QUALITATIVA GEMINI
    st.markdown("---")
    st.subheader("🧠 Report Strategico & Glossario Formativo")
    
    prompt_analisi = f"""
    Titolo da analizzare: {nome_azienda} ({ticker_input})
    Prezzo Attuale: {prezzo_corrente} {valuta}
    Consensus Analisti: {recommendation} (Target Price: {target_mean} {valuta})
    
    Fonti e istituzioni di riferimento attivate dall'utente (Knowledge Base):
    {', '.join(tutte_fonti_selezionate[:40])}
    
    Rassegna Notizie Live:
    {chr(10).join(['- ' + n['titolo'] for n in notizie_raccolte])}
    
    Redigi un'analisi strutturata ed esaustiva per un piccolo investitore suddivisa esattamente in:
    1. ANALISI DEL CONTESTO STRATEGICO E SETTORIALE: Sintesi di business, driver industriali e dinamiche competitive.
    2. FATTORI DI RISCHIO CHIAVE: Rischi operativi, tassi, regolatori o macroeconomici evidenziati dalle fonti autorevoli.
    3. GLOSSARIO PER IL PICCOLO INVESTITORE: Spiega in modo chiaro e divulgativo 3 termini tecnici finanziari rilevanti usati in questo report.
    
    Non includere raccomandazioni operative personalizzate ma mantieni un approccio didattico e rigoroso.
    """
    
    with st.spinner("Elaborazione del report qualitativo con AI..."):
        report_generato = esegui_analisi_qualitativa(prompt_analisi, api_key)
        st.markdown(report_generato)

    # 5. ESPORTAZIONE REPORT
    st.markdown("---")
    testo_completo_export = f"""# REPORT ANALISI FINANZIARIA: {nome_azienda} ({ticker_input})
Data: {time.strftime('%Y-%m-%d %H:%M:%S')}
Prezzo Attuale: {prezzo_corrente} {valuta}
Target Price Medio: {target_mean} {valuta}
Raccomandazione Consensus: {recommendation}

## ANALISI STRATEGICA & QUALITATIVA
{report_generato}
"""
    st.download_button(
        label="📥 Scarica Report Completo (.md)",
        data=testo_completo_export,
        file_name=f"Report_{ticker_input}_{time.strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )

            except Exception as e:
                st.error(f"Si è verificato un errore durante la chiamata a Gemini: {e}")
