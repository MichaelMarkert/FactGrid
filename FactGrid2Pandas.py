import pandas as pd
from IPython.display import display
from pandas import json_normalize
import re
import locale, datetime
locale.setlocale(locale.LC_TIME, locale.normalize("de"))

import streamlit as st
st.set_page_config(layout="wide")
import streamlit.components.v1 as components
from st_keyup import st_keyup

from itables import init_notebook_mode
init_notebook_mode(all_interactive=True)
from itables import to_html_datatable as DT
import itables.options as opt

from SPARQLWrapper import SPARQLWrapper, JSON

st.markdown("""
            <style>
            h1 {
                font-size:2.5rem;
            }
            div.stDownloadButton {
                text-align:right;
            }
            div.stDownloadButton > button {
                color: green; 
                border-color: green;
            }
            div.stDownloadButton > button:hover {
                color: green; 
                border-color: green;
                background-color: lightgreen;
            }
            .block-container {
                padding-top: 0rem;
            }
            div[data-testid*="column"] {
                padding: 10px;
            }    
        
            </style>""", unsafe_allow_html=True)

#st.slider("Zeitraum", min_value=earliest_date, max_value=latest_date, step=5)

base_df = pd.read_pickle('data.pkl')
df = base_df

st.title("Findbuch des Archivs der evangelisch-lutherischen Stadtkirchengemeinde Gotha")

query_string_list = "^"

col1, col2, col3, col4 = st.columns([2,2,1,1])

#QUERY
with col1:
    st.write("Query String")
    query_string = st_keyup("Suche mit Regex (s. https://regex101.com/) möglich",debounce=250)
    query_string = query_string.split()
    for x in query_string:
        if x.islower():
            x_low = x
            x_cap = x.capitalize()
        else:
            x_cap = x
            x_low = x.lower()
        query_string_element = "(?=.*" + x_low + ")" + "|" + "(?=.*" + x_cap + ")"

        if (bool(re.search('ä|Ä|ö|Ö|ü|Ü|ß',query_string_element))==True):
            query_string_element_umlaut = query_string_element.replace("ä","ae").replace("Ä","Äe").replace("ö","oe").replace("Ö","Oe").replace("ü","ue").replace("Ü","Ue").replace("ß","ss")
            query_string_element = query_string_element + "|" + query_string_element_umlaut
        query_string_list += "(" + str(query_string_element) + ")"     
st.text(query_string_list)

#TIMESLIDER
earliest = int(df['von'].min())
earliest2 = int(df['von'].max())
latest = int(df['bis'].min())
latest2 = int(df['bis'].max())
#st.dataframe(number)
#st.text(str(earliest) + "-" + str(earliest2) + ", " + str(latest) + "-" + str(latest2))
with col2:
    timeframe = st.checkbox("Zeitraum filtern")

    if timeframe:
        values = st.slider(
            'Schieben sie die Slider zu den gewünschten Grenzen',
            earliest, latest2, (earliest, latest2)
            )

        df = df[
            (df['von'] >= values[0]) & (df['bis']<= values[1]) | (df['von'] >= values[0]) & (df['bis'] != df['bis']) | (df['von'] != df['von']) & (df['bis']<= values[1])
            ]

#INVENTORY
with col3:
    st.write("Unterbestand wählen")
    inventory_unit = st.selectbox(
    'Kriterium ist Signaturgruppe',
    ('All', 'A 2', 'A 3', 'A 4', 'A 5', 'A 6', 'A 7', 'A 8', 'A 9', 'A 10', 'A 11'))
    if inventory_unit != "All":
        df = df[df['Signatur'].str.contains(inventory_unit)]

df = df[df['concatenate'].str.contains(query_string_list, regex=True)]
df = df.drop('concatenate', axis=1)

#AGGRID
#from st_aggrid import AgGrid
#from st_aggrid import JsCode
#from st_aggrid.grid_options_builder import GridOptionsBuilder

#builder = GridOptionsBuilder.from_dataframe(df)
#builder.configure_side_bar()
#builder.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc="sum")
#builder.configure_pagination(paginationPageSize=10)
#builder.configure_columns("Titel", wrapText=True, autoHeight=True, width=300)
#builder.configure_columns("Inhalt", wrapText=True, autoHeight=True, width=300)
#builder.configure_columns("Signatur", width=100)
#builder.configure_columns("von", width=150)
#builder.configure_columns("bis", width=150)
#builder.configure_column("FactGrid_ID",
#                    headerName="FactGrid_ID", wrapText=True, autoHeight=True,
#                    cellRenderer=JsCode(
#                        """
#                        function(params) {
#                            return '<a href=' + params.value + ' target="_blank">' + params.value + '</a>'
#                            }
#                        """))
#builder.configure_column("concatenate", hide=True)
#go = builder.build()

#custom_css = {
#    ".ag-cell-wrap-text": {
#        "word-break": "normal"
#        },
#    ".ag-row-hover": {
#        "background-color": "lightblue"
#        }
#    }

#AgGrid(df, gridOptions=go, fit_columns_on_grid_load=True, allow_unsafe_jscode=True, custom_css=custom_css, enable_enterprise_modules=True)

#ITABLE
html=DT(df, 
    classes="display",
    lengthMenu=[5, 20, 50],
    dom="ltpir", 
    scrollX=True, 
    scrollY="400px", 
    scrollCollapse=True, 
    name="HTML",
    columnDefs=[{"width": "30%", "targets": [2, 5]}],
    style="width:100%;margin:auto")
opt.css = """
.itables table td {
    font-family: "Source Sans Pro", sans-serif;
    font-size: 0.8em
    }
"""
components.html(html, height=600)

#EXPORTER
df['FactGrid_ID'] = df['FactGrid_ID'].str.replace('<a href="','').replace('" target.*a>','', regex=True)

csv = df.to_csv(index=False).encode('utf-8')
tsv = df.to_csv(index=False,sep="\t").encode('utf-8')

from datetime import datetime

now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
filename_csv = "Findbuch-Auswahl, " + dt_string + ".csv"
filename_tsv = "Findbuch-Auswahl, " + dt_string + ".tsv"

with col4:
    st.download_button(
    "Auswahl als CSV-Datei",
    csv,
    filename_csv,
    "text/csv",
    key='download-csv'
    )
with col4:
    st.download_button(
    "Auswahl als TSV-Datei",
    tsv,
    filename_tsv,
    "text/tsv",
    key='download-tsv'
    )

#FACTGRID_QUERY
def query_wikidata(sparql_query, sparql_service_url):
    """
    Query the endpoint with the given query string and return the results as a pandas Dataframe.
    """
    
    sparql = SPARQLWrapper(sparql_service_url, agent="Sparql Wrapper on Jupyter example")  
    
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)

    result = sparql.query().convert()
    return json_normalize(result["results"]["bindings"])

sparql_query = """SELECT ?Signatur ?QLabel ?Inhalt ?von ?bis ?Q ?Nr WHERE {
  SERVICE wikibase:label { bd:serviceParam wikibase:language "de". }
  ?Q wdt:P329 wd:Q35000;
    wdt:P2 wd:Q10672.
  OPTIONAL { ?Q wdt:P49 ?von. }
  OPTIONAL { ?Q wdt:P50 ?bis. }
  OPTIONAL { ?Q (p:P329/pq:P10) ?Signatur. }
  OPTIONAL { ?Q wdt:P499 ?Nr. }
  OPTIONAL { ?Q wdt:P724 ?Inhalt. }
}
ORDER BY (?Nr)
    """

sparql_service_url = "https://database.factgrid.de/sparql"
result_table = query_wikidata(sparql_query, sparql_service_url)
#rt = pd.DataFrame(result_table)
#display(rt)

#RESPONSE_WRANGLING
result_table['von.value'] = pd.to_datetime(result_table['von.value'], errors='coerce')
result_table['bis.value'] = pd.to_datetime(result_table['bis.value'], errors='coerce')

result_table['von.value'] = result_table['von.value'].dt.strftime('%Y')
result_table['bis.value'] = result_table['bis.value'].dt.strftime('%Y')

simple_table = result_table[["Signatur.value", "QLabel.value", "von.value", "bis.value", "Inhalt.value", "Q.value"]]
simple_table = simple_table.rename(columns = lambda col: col.replace(".value", "")).rename(columns = {"QLabel":"Titel", "Q":"FactGrid_ID"})
simple_table['concatenate'] = simple_table['Signatur'].astype(str) + simple_table['Titel'].astype(str) + simple_table['von'].astype(str) + simple_table['bis'].astype(str) + simple_table['Inhalt'].astype(str)

df = pd.DataFrame(simple_table)
df["FactGrid_ID"] = df["FactGrid_ID"].str.replace("https://database.factgrid.de/entity/", "<a href=\"https://database.factgrid.de/viewer/item/").__add__("\" target=\"blank\">" + df["FactGrid_ID"].str.replace("https://database.factgrid.de/entity/","") + "</a>")

df['von'] = pd.to_numeric(df['von'])
df['bis'] = pd.to_numeric(df['bis'])
new_base_df = df

#DF_UPDATE
if not new_base_df.equals(base_df):
    new_base_df.to_pickle('data.pkl')
    with col2:
        m = st.markdown("""
            <style>
            div.stButton > button:first-child {
                background-color: rgb(255, 165, 0);
            }
            </style>""", unsafe_allow_html=True)
        st.button("Der Datenbestand hat sich geändert. Bitte laden Sie das Fenster durch Klick auf diesen Button neu.")