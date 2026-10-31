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
    page_title="Terminale Analisi Investimenti",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# KNOWLEDGE BASE: MAPPATURA ENTITÀ E DOMINI WEB UFFICIALI AUTORIZZATI
# -----------------------------------------------------------------------------
FONTI_KB = {
    "SGR & Banche d'Affari Italiane (Buy-Side)": {
        "Intesa Sanpaolo / IMI CIB": "intesasanpaolo.com",
        "Eurizon Capital SGR": "eurizoncapital.com",
        "Poste SGR": "postevita.poste.it",
        "Generali Investments / Plenisfer": "generali-investments.com",
        "Euro SGR": "eurosgr.it",
        "Arca Fondi SGR": "arcafondi.it",
        "Azimut Investments": "azimut-group.com",
        "Kairos Partners SGR": "kairospartners.com",
        "AcomeA SGR": "acomea.it",
        "Etica SGR": "eticasgr.com",
        "Anthilia Capital Partners": "anthilia.it",
        "Sella SGR / Banca Patrimoni Sella": "sella.it",
        "Zenit SGR": "zenitsgr.it",
        "Ersel": "ersel.it",
        "Banor SIM": "banor.it",
        "Fideuram Asset Management": "fideuramireland.com",
        "Mediolanum Gestione Fondi": "bancamediolanum.it"
    },
    "Broker & SIM Italiane (Sell-Side / Equity Research)": {
        "Equita SIM": "equita.eu",
        "Intermonte SIM": "intermonte.it",
        "Banca Akros": "bancaakros.it",
        "UniCredit Research": "unicreditresearch.eu",
        "Alantra Italy": "alantra.com",
        "Banca Profilo": "bancaprofilo.it",
        "Value Track": "value-track.com",
        "IR Top Consulting": "irtop.com",
        "Integrae SIM": "integraesim.it",
        "KT&Partners": "ktpartners.it",
        "CFO SIM": "cfosim.com",
        "SCM SIM": "scmsim.it",
        "Banca Finnat Euramerica": "bancafinnat.it",
        "EnVent Capital Markets": "enventcapitalmarkets.co.uk",
        "Mediobanca Securities": "mediobanca.com"
    },
    "Analisti Indipendenti & SCF": {
        "Consultique SCF": "consultique.com",
        "IoInvesto SCF": "ioinvesto.com",
        "NoRisk SCF": "norisk.it",
        "SoldiExpert SCF": "soldiexpert.com",
        "Cicli e Mercati (Caruso)": "cicliemercati.it",
        "MDOTM": "mdotm.ai",
        "Lixi Invest / Plutus": "lixinvest.com",
        "Affari Miei": "affarimiei.biz",
        "AdviseOnly": "adviseonly.com",
        "Phastidio.net (Seminerio)": "phastidio.net"
    },
    "Media Finanziari Italiani": {
        "Il Sole 24 Ore / Plus24": "ilsole24ore.com",
        "Class CNBC / Milano Finanza": "milanofinanza.it",
        "We Wealth": "we-wealth.com",
        "Radio 24": "radio24.ilsole24ore.com",
        "FocusRisparmio": "focusrisparmio.com",
        "Citywire Italia": "citywire.com",
        "Bluerating": "bluerating.com",
        "Funds People Italia": "fundspeople.com",
        "Wall Street Italia": "wallstreetitalia.com",
        "Morningstar Italia": "morningstar.it"
    },
    "Istituzioni & Uffici Studi Italiani": {
        "Banca d'Italia": "bancaditalia.it",
        "CONSOB": "consob.it",
        "AIPB": "aipb.it",
        "Assogestioni": "assogestioni.it",
        "OCF": "organismocf.it",
        "Prometeia": "prometeia.it",
        "Cerved Group": "cerved.com",
        "ABI": "abi.it",
        "ISTAT": "istat.it",
        "Assosim": "assosim.it",
        "CER": "cerricerche.it"
    },
    "Banche d'Affari & Asset Manager Globali": {
        "Goldman Sachs Research": "goldmansachs.com",
        "J.P. Morgan Research": "jpmorgan.com",
        "BlackRock Investment Institute": "blackrock.com",
        "Morgan Stanley Research": "morganstanley.com",
        "PIMCO": "pimco.com",
        "Bridgewater Associates": "bridgewater.com"
    },
    "Boutique di Ricerca Globale & Sell-Side": {
        "Gavekal Research": "gavekal.com",
        "Ned Davis Research (NDR)": "ndr.com",
        "BCA Research": "bcaresearch.com",
        "Kepler Cheuvreux": "keplercheuvreux.com",
        "Redburn Atlantic": "redburn.com",
        "Berenberg": "berenberg.de",
        "TS Lombard": "tslombard.com",
        "High Frequency Economics": "hfe.com",
        "Cornerstone Macro": "pipersandler.com"
    },
    "Emittenti ETF & Provider Indici": {
        "Vanguard ISG": "vanguard.com",
        "State Street (SPDR)": "ssga.com",
        "Invesco Global Strategy": "invesco.com",
        "WisdomTree Research": "wisdomtree.eu",
        "MSCI Research": "msci.com",
        "S&P Dow Jones Indices (SPIVA)": "spglobal.com"
    },
    "Macroeconomisti Indipendenti Globali": {
        "Capital Economics": "capitaleconomics.com",
        "Ex Uno Plures (Pozsar)": "exunoplures.com",
        "Rosenberg Research": "rosenbergresearch.com",
        "Incrementum AG": "incrementum.li",
        "Yardeni Research": "yardeni.com",
        "The Bear Traps Report": "thebeartrapsreport.com"
    },
    "Media Finanziari Internazionali": {
        "Bloomberg": "bloomberg.com",
        "Financial Times": "ft.com",
        "Reuters": "reuters.com",
        "Wall Street Journal": "wsj.com",
        "The Economist": "economist.com",
        "CNBC Pro": "cnbc.com"
    },
    "Banche Centrali & Istituzioni Internazionali": {
        "CPB Netherlands": "cpb.nl",
        "Bruegel": "bruegel.org",
        "Federal Reserve (FED)": "federalreserve.gov",
        "European Central Bank (ECB)": "ecb.europa.eu",
        "International Monetary Fund (IMF)": "imf.org",
        "OECD / OCSE": "oecd.org",
        "Ifo Institute / ZEW": "ifo.de",
        "Bank for International Settlements (BIS)": "bis.org"
    }
}

# -----------------------------------------------------------------------------
# DATI QUANTITATIVI DETERMINISTICI (Zero calcoli via LLM)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=900)
def estrai_dati_mercato(ticker_simbolo, periodo="1y"):
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
        vertical_spacing=0.03,
        row_heights=[0.75, 0.25]
    )
    
    # Serie Prezzi e Medie Mobili
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="Prezzo"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA20'],
        line=dict(color='#FFA500', width=1.5),
        name="SMA 20"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA50'],
        line=dict(color='#2962FF', width=1.5),
        name="SMA 50"
    ), row=1, col=1)
    
    # Istogramma Volumi
    colori_vol = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'],
        marker_color=colori_vol,
        name="Volume"
    ), row=2, col=1)
    
    fig.update_layout(
        title=f"Analisi Tecnica: {ticker_simbolo}",
        xaxis_rangeslider_visible=False,
        height=540,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# -----------------------------------------------------------------------------
# SCANSIONE NOTIZIE VINCOLATA AI DOMINI DELLA KNOWLEDGE BASE
# -----------------------------------------------------------------------------
def estrai_notizie_filtrate(query_nome, domini_autorizzati):
    if not domini_autorizzati:
        return []
    
    # Costruzione filtro domini (fino a un massimo di 10 per query per evitare limitazioni di lunghezza URL)
    filtro_siti = " OR ".join([f"site:{d}" for d in domini_autorizzati[:10]])
    query_finale = f"{query_nome} ({filtro_siti})"
    query_encoded = urllib.parse.quote(query_finale)
    
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
# CHIAMATA A GEMINI-3.8-FLASH CON RETRY AUTOMATICO (Backoff per 503)
# -----------------------------------------------------------------------------
def esegui_analisi_qualitativa(prompt, api_key):
    client = genai.Client(api_key=api_key)
    tentativi_max = 5
    attesa = 2.0
    
    for tentativo in range(tentativi_max):
        try:
            risposta = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    system_instruction=(
                        "Sei un Senior Equity Analyst e Macroeconomista. Opera adottando il rigore, "
                        "il livello di profondità e la neutralità istituzionale degli attori della Knowledge Base. "
                        "Non inventare numeri, multipli di bilancio o target price. Occupati unicamente di analizzare "
                        "le notizie fornite, commentare i rischi strategici e spiegare con chiarezza didattica i concetti tecnici."
                    )
                )
            )
            return risposta.text
        except APIError as e:
            if tentativo < tentativi_max - 1:
                time.sleep(attesa)
                attesa *= 2
            else:
                return f"Servizio temporaneamente sovraccarico (Errore 503/Quota): {str(e)}. Riprova tra un istante."
        except Exception as e:
            return f"Errore durante l'elaborazione del report: {str(e)}"

# -----------------------------------------------------------------------------
# INTERFACCIA STREAMLIT
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configurazione")
    
    api_key_env = st.secrets.get("GEMINI_API_KEY", "")
    api_key_input = st.text_input("Gemini API Key", value=api_key_env, type="password")
    api_key = api_key_input if api_key_input else api_key_env
    
    st.markdown("---")
    st.subheader("📚 Knowledge Base: Filtro Fonti")
    st.caption("Seleziona le entità autorizzate per il filtraggio web:")
    
    fonti_attive_nomi = []
    domini_attivi = []
    
    for categoria, dict_fonti in FONTI_KB.items():
        with st.expander(categoria, expanded=False):
            seleziona_gruppo = st.checkbox(f"Seleziona tutto ({categoria})", value=True, key=f"all_{categoria}")
            for nome_fonte, dominio in dict_fonti.items():
                attivo = st.checkbox(nome_fonte, value=seleziona_gruppo, key=f"{categoria}_{nome_fonte}")
                if attivo:
                    fonti_attive_nomi.append(nome_fonte)
                    if dominio not in domini_attivi:
                        domini_attivi.append(dominio)

# Finestra Principale
st.title("🏛️ Terminale Investimenti & Ricerca Finanziaria")
st.markdown("Analisi quantitativa automatica combinata con sintesi qualitativa istituzionale (`gemini-3.8-flash`).")

col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    ticker_input = st.text_input("Inserisci Simbolo Ticker (es. ENI.MI, ISP.MI, AAPL, NVDA)", value="ENI.MI").upper().strip()
with col_t2:
    periodo_scelto = st.selectbox("Orizzonte Dati", ["3mo", "6mo", "1y", "2y", "5y"], index=2)

if st.button("🚀 Avvia Analisi Completa", type="primary", use_container_width=True):
    if not api_key:
        st.error("Chiave API mancante. Inseriscila nel campo laterale o nei Secrets di Streamlit.")
        st.stop()
        
    with st.spinner("Estrazione dati di mercato e scansione fonti autorizzate..."):
        try:
            storico, info = estrai_dati_mercato(ticker_input, periodo=periodo_scelto)
        except Exception as e:
            st.error(f"Errore nel download dei dati per il titolo {ticker_input}: {e}")
            st.stop()

    if storico.empty:
        st.warning(f"Nessun dato di mercato disponibile per il ticker '{ticker_input}'. Verifica il simbolo.")
        st.stop()

    nome_azienda = info.get("shortName", ticker_input)
    valuta = info.get("currency", "EUR")
    prezzo_attuale = info.get("currentPrice") or info.get("regularMarketPrice") or storico['Close'].iloc[-1]

    # 1. CONSENSUS DEGLI ANALISTI E METRICHE FONDAMENTALI
    st.subheader(f"📌 {nome_azienda} ({ticker_input}) — Consensus & Valutazioni di Mercato")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Prezzo Attuale", f"{prezzo_attuale:.2f} {valuta}")
    
    target_mean = info.get("targetMeanPrice")
    col_m2.metric("Target Price Medio", f"{target_mean:.2f} {valuta}" if target_mean else "N/D")
    
    recommendation = info.get("recommendationKey", "N/D").upper()
    col_m3.metric("Raccomandazione Consensus", recommendation)
    
    pe_ratio = info.get("trailingPE")
    col_m4.metric("P/E Ratio", f"{pe_ratio:.2f}" if pe_ratio else "N/D")

    # 2. GRAFICO CANDLESTICK + MEDIE MOBILI + VOLUMI
    st.markdown("---")
    st.subheader("📈 Grafico di Mercato")
    df_tecnico = calcola_indicatori(storico)
    grafico = crea_grafico_candele(df_tecnico, ticker_input)
    st.plotly_chart(grafico, use_container_width=True)

    # 3. NOTIZIE SCANSIONATE SUI DOMINI AUTORIZZATI
    st.markdown("---")
    st.subheader("📰 Ultime Notizie Rilevate dalle Fonti Autorizzate")
    notizie_trovate = estrai_notizie_filtrate(nome_azienda, domini_attivi)
    
    if notizie_trovate:
        col_n1, col_n2 = st.columns(2)
        for idx, n in enumerate(notizie_trovate[:6]):
            with (col_n1 if idx % 2 == 0 else col_n2):
                st.markdown(f"• **[{n['titolo']}]({n['link']})**")
    else:
        st.info("Nessuna notizia recente rilevata sui domini specifici delle fonti attualmente attivate.")

    # 4. REPORT QUALITATIVO TRAMITE GEMINI-3.8-FLASH
    st.markdown("---")
    st.subheader("🧠 Report Strategico & Formativo")
    
    prompt_report = f"""
    Titolo in analisi: {nome_azienda} ({ticker_input})
    Prezzo di Mercato: {prezzo_attuale} {valuta}
    Consensus Ufficiale: {recommendation} | Target Price Medio: {target_mean} {valuta}
    
    Fonti Istituzionali selezionate dall'utente (Knowledge Base):
    {', '.join(fonti_attive_nomi[:30])}
    
    Rassegna Notizie dai domini autorizzati:
    {chr(10).join(['- ' + n['titolo'] for n in notizie_trovate]) if notizie_trovate else 'Nessuna notizia rilevante.'}
    
    Svolgi un'analisi strutturata ad uso di un investitore non professionale, articolando la risposta in 3 sezioni:
    1. CONTESTO STRATEGICO E POSIZIONAMENTO INDUSTRIALE: Descrivi le linee di business e le dinamiche competitive settoriali.
    2. MAPPA DEI FATTORI DI RISCHIO: Identifica i rischi operativi, tassi, regolatori o macroeconomici evidenziati dalla ricerca di settore.
    3. GLOSSARIO PER IL PICCOLO INVESTITORE: Spiega in modo chiaro e comprensibile 3 concetti o metriche finanziarie chiave applicate a questo titolo.
    
    Attieniti unicamente al contesto qualitativo e formativo senza formulare raccomandazioni operative personalizzate.
    """
    
    with st.spinner("Generazione analisi qualitativa con gemini-3.8-flash..."):
        testo_report = esegui_analisi_qualitativa(prompt_report, api_key)
        st.markdown(testo_report)

    # 5. ESPORTAZIONE REPORT
    st.markdown("---")
    export_md = f"""# REPORT STRATEGICO: {nome_azienda} ({ticker_input})
Data Elaborazione: {time.strftime('%Y-%m-%d %H:%M:%S')}
Prezzo: {prezzo_attuale} {valuta}
Target Price: {target_mean} {valuta}
Consensus: {recommendation}

## ANALISI ISTITUZIONALE
{testo_report}
"""
    st.download_button(
        label="📥 Esporta Report Completo (.md)",
        data=export_md,
        file_name=f"Report_{ticker_input}_{time.strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )
