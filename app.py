import streamlit as st
import pandas as pd
import snowflake.connector

st.set_page_config(page_title="Dashboard COVID-19", layout="wide")

# Função de Conexão usando st.secrets (ou hardcoded/env para testes no Colab)
@st.cache_resource
def init_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"]
    )

conn = init_connection()

@st.cache_data(ttl=600)
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetch_pandas_all()

st.title("📊 Dashboard COVID-19 (Via Snowflake)")
st.caption("Atividade Prática — Streamlit + Snowflake + Colab")

# Buscar dados do Snowflake
df = run_query("SELECT * FROM COVID_DATA")
df['DATE'] = pd.to_datetime(df['DATE'])

# Filtros
paises = df['LOCATION'].unique().tolist()
paises_sel = st.sidebar.multiselect("Selecione os Países:", paises, default=paises)
df_filtered = df[df['LOCATION'].isin(paises_sel)]

# Visualizações
col1, col2, col3 = st.columns(3)
col1.metric("Total Novos Casos", f"{int(df_filtered['NEW_CASES'].sum()):,}")
col2.metric("Pico de Óbitos", f"{int(df_filtered['TOTAL_DEATHS'].max()):,}")
col3.metric("Máximo de Vacinados", f"{int(df_filtered['PEOPLE_VACCINATED'].max()):,}")

st.markdown("---")

st.subheader("📈 Evolução Temporal de Novos Casos")
df_chart_cases = df_filtered.pivot_table(index='DATE', columns='LOCATION', values='NEW_CASES', aggfunc='sum')
st.line_chart(df_chart_cases)

col_l, col_r = st.columns(2)

with col_l:
    st.subheader("💉 Vacinados por País")
    df_vac = df_filtered.groupby('LOCATION')['PEOPLE_VACCINATED'].max().reset_index()
    st.bar_chart(df_vac.set_index('LOCATION'))

with col_r:
    st.subheader("⚠️ Tendência Acumulada de Óbitos")
    df_chart_deaths = df_filtered.pivot_table(index='DATE', columns='LOCATION', values='TOTAL_DEATHS', aggfunc='max')
    st.area_chart(df_chart_deaths)
