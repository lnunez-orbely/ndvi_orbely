import streamlit as st
import geemap.foliumap as geemap
import geopandas as gpd
import pandas as pd
import json
import ee

st.set_page_config(page_title="Inicio",layout="wide")

st.logo("Orbely_Logo2.png",icon_image="Orbely_Logo2.png", link="https://orbely.com/")

st.markdown("""
            <style>
               .block-container {
                    padding-top: 2.5rem;
                    padding-bottom: 1rem;
                    padding-left: 1rem;
                    padding-right: 2rem;
                }
        </style>
        """, unsafe_allow_html=True)

cont1 = st.container()
col001, col002, col003,col004 = cont1.columns([2, 11, 2,4])
im1=col001.image('Sentinel_2_1.png', width=100)
title=col002.title("Visualización y Descarga de :green[NDVI]")
im2=col003.image('Sentinel_2_2.png', width=100)

service_account = st.session_state['cred']['service_account'][0]
os.environ['private_key']=st.session_state['cred']['key_data'][0]
credentials = ee.ServiceAccountCredentials(service_account, key_data=os.environ.get('private_key').replace('\\n', '\n'))
ee.Initialize(credentials)

st.write('')
st.header(":lock: Credenciales :unlock:")
cont0 = st.container()
col01, col02, col03 = cont0.columns([2, 2, 1])
cred=col01.file_uploader("Cargar csv de credenciales", type={"csv"})

st.divider()
st.header(":earth_americas: Carga de Lotes :earth_americas:")
cont = st.container()
col1, col2, col3 = cont.columns([2, 2, 1])

lotes = col1.file_uploader("Cargar Lista Completa de Lotes (csv)", type={"csv"})
lote_shp=col2.file_uploader("Cargar Lote Suelto (shp zipeado o geojson)", type={"zip","geojson"})

if cred:
    cred_df=pd.read_csv(cred)
    st.session_state['cred']=cred_df
    @st.cache_data
    def auth():
                service_account = st.session_state['cred']['service_account'][0]
                os.environ['private_key']=st.session_state['cred']['key_data'][0]
                credentials = ee.ServiceAccountCredentials(service_account, key_data=os.environ.get('private_key').replace('\\n', '\n'))
                ee.Initialize(credentials)
        
if lote_shp:
    gdf=gpd.read_file(lote_shp)
    g = json.loads(gdf.to_json())
    name=lote_shp.name
    coords =[(g['features'][0]['geometry']['coordinates'])]
    dic_lote={
        'cliente':'0_lote_subido',
        'campo':'0_Lote_subido',
        'lote':f'0_{name}',
        'coordenadas':coords
        }
    df2=pd.DataFrame(dic_lote)
    df2['coordenadas'][0]=str(df2['coordenadas'][0])
    fc = geemap.gdf_to_ee(gdf)
    st.session_state['lote']=df2

if lotes:
    clientes_df = pd.read_csv(lotes)
    st.session_state['list_lotes']= clientes_df

if 'lote' in st.session_state and 'list_lotes' in st.session_state :
    frames=[st.session_state['lote'],st.session_state['list_lotes']]
    df_combi=pd.concat(frames)
    st.session_state['lotes']=df_combi
elif 'lote' in st.session_state and 'list_lotes' not in st.session_state :
    st.session_state['lotes']=st.session_state['lote']
elif 'lote' not in st.session_state and 'list_lotes' in st.session_state :
    st.session_state['lotes']=st.session_state['list_lotes']

if 'cred' in st.session_state:st.sidebar.write(':four_leaf_clover: Credenciales Cargadas :four_leaf_clover:')
if 'list_lotes' in st.session_state:st.sidebar.write(':corn: Lista de Lotes Cargada :corn:')
if 'lote' in st.session_state:st.sidebar.write(':fallen_leaf: Lote Cargado :fallen_leaf:')

st.divider()
st.header("Dibujar Lote :pencil2:")

on = st.toggle("Lote Nuevo")
if on:
    multi = '''Instructivo:  
    - Dibujar lote usando las herramientas de dibujo  
    - Apretar el botón Export: se descarga un archivo formato geojson  
    - Cargar este mismo archivo en la página con el "drag and drop" de la derecha'''

    st.markdown(multi)
    Map=geemap.Map(center=[-31.42,-64.19], zoom=10,basemap="HYBRID", Draw_export=True)
    Map.to_streamlit(height=600, width=800)

