import streamlit as st
import ee
import geemap.foliumap as geemap
import ast
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import os


st.set_page_config('Buscador', layout="wide")
st.logo("Orbely_Logo2.png",icon_image="Orbely_Logo2.png", link="https://orbely.com/")
st.header('Visualizador de NDVI')

cont0 = st.container()
col01, col02 = cont0.columns([4, 1.1])
with col01:
  tab1, tab2 = st.tabs([":earth_americas: Mapa", "📈 Serie Temporal"])


vis_params_lim = {'color': 'white', 'pointSize': 3,'pointShape': 'circle','width': 3,'lineType': 'solid','fillColor': '#00000000'}
visParams = {'bands':['B4','B3','B2'],'min': 0, 'max': 3000,'gamma':1.5}

st.markdown("""
            <style>
               .block-container {
                    padding-top: 2.3rem;
                    padding-bottom: 1rem;
                    padding-left: 0.5rem;
                    padding-right: 0.5rem;
                }
        </style>
        """, unsafe_allow_html=True)

Map=geemap.Map(center=[-31.42,-64.19], zoom=10,basemap="HYBRID", control_scale=True)
ndvi_name=None

if 'min' not in st.session_state:
    st.session_state['min']= 0.00
if 'max' not in st.session_state:
    st.session_state['max']= 1.00
if 'map' not in st.session_state or ndvi_name==None:
    st.session_state['map']=Map
if 'clouds' not in st.session_state:
  st.session_state['clouds']= 40

if 'cred' in st.session_state and 'lotes' in st.session_state:
  select_client=st.sidebar.selectbox('Seleccionar Cliente',st.session_state['lotes'].cliente.unique(),index=None,placeholder='Cliente')
  @st.cache_data
  def auth():
    service_account = st.session_state['cred']['service_account'][0]
    os.environ['private_key']=st.session_state['cred']['key_data'][0]
    credentials = ee.ServiceAccountCredentials(service_account, key_data=os.environ.get('private_key').replace('\\n', '\n'))
    ee.Initialize(credentials)
  
  if select_client:
    campo_df=st.session_state['lotes'][st.session_state['lotes']["cliente"] == select_client]
    select_camp=st.sidebar.selectbox('Seleccionar Campo',campo_df.campo.unique(),index=None,placeholder='Campo')
    if select_camp:
      lote_df=campo_df[campo_df["campo"] == select_camp]
      select_lote=st.sidebar.selectbox('Seleccionar Lote',lote_df.lote.unique(),index=None,placeholder='Lote')
      if select_lote:
        ndvi_name=f"NDVI_{select_camp.replace('0_','').replace('_subido','')}_{select_lote.replace('0_','').replace('.shp','')
                                                  .replace('.geojson','').replace('_poly','').replace('.zip','')}"       
        coord_df=lote_df[lote_df["lote"] == select_lote].reset_index()
        limite2 = ast.literal_eval(coord_df['coordenadas'][0])
        point=ee.FeatureCollection(ee.Geometry.Polygon(limite2))
        point2=ee.FeatureCollection(ee.Geometry.Polygon(limite2).bounds().buffer(3000))
        Map.centerObject(point)
        Map.addLayer(point.style(**vis_params_lim),{},'Limite del Lote')
        st.session_state['map']=Map
 
        with st.sidebar:
          st.sidebar.title("Selección de Fecha")
          fecha11=str(st.date_input("Fecha 1", value=None))
          fecha22=str(st.date_input("Fecha 2", value=None))

        if fecha11!='None' and fecha22!='None':
          with col02:
            st.write("")
            st.write("")
            st.write("")
            centrar=st.button("Centrar sobre lote")
            clouds_input= st.number_input(label='Filtrar por nubosidad (%)', value=40)
            if clouds_input:
                st.session_state['clouds']=clouds_input
          reducer = ee.Reducer.mean().combine(reducer2=ee.Reducer.stdDev(), sharedInputs=True)

          def dates(imagen):
            meanDictionary = imagen.reduceRegion(reducer= reducer,geometry= point,scale= 10)
            return ee.Feature(None ,
                      {'0_name':select_lote,'mean_ndvi':(meanDictionary,imagen.date().format('YYYY-MM-dd'))})
          def clippedCol(_im):
            return _im.clip(point2)
          def addndvi(image):
            return image.addBands(image.normalizedDifference(['B8', 'B4']).rename('NDVI'))

          @st.cache_data(max_entries=1,show_spinner=False)
          def getNDVI(fecha1,fecha2,clouds0):
              Sentinel= (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                              .filterBounds(point)
                              .filterDate(fecha1,fecha2)
                              .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', clouds0))
                              .select('B4','B3','B2','B8'))
              Clipped_Sentinel=Sentinel.map(clippedCol) 
              NDVI_Sentinel=Clipped_Sentinel.map(addndvi)
              list_prom0=(NDVI_Sentinel.map(dates).aggregate_array('mean_ndvi')).getInfo()
              for i in range(len(list_prom0)-1):
                if list_prom0[i][0]['NDVI_mean']==None:
                  im_none = NDVI_Sentinel.toList(NDVI_Sentinel.size()).get(i)
                  im_non_index=im_none.getInfo()['properties']["system:index"]
                  NDVI_Sentinel=NDVI_Sentinel.filter(ee.Filter.neq('system:index',f'{im_non_index}'))
                  list_prom0.pop(i)
              lista0=NDVI_Sentinel.toList(NDVI_Sentinel.size())
              return lista0,list_prom0

          @st.cache_data(show_spinner=False,max_entries=1)
          def time_plot(lista_promedio):
            mean_ndvi,std_ndvi,fecha_list0,coef_var0=[],[],[],[]
            for i in range(0,len(lista_promedio)-1):
              mean_ndvi.append(lista_promedio[i][0]['NDVI_mean'])
              std_ndvi.append(lista_promedio[i][0]['NDVI_stdDev'])
              fecha_list0.append(lista_promedio[i][1])
              if mean_ndvi[i]==0:
                coef=0
              else:
                coef=(std_ndvi[i]/mean_ndvi[i])*100
              coef_var0.append(coef)
            dict1={'fecha':fecha_list0,'fecha':fecha_list0,'NDVI_promedio':mean_ndvi,'NDVI_desvio':std_ndvi,'coef_var':coef_var0}
            ypoints,xpoints, stdpoints = np.array(mean_ndvi),np.array(fecha_list0), np.array(std_ndvi)
            fig0 = go.Figure()
            fig0.add_trace(go.Scatter(x=xpoints,y=ypoints+stdpoints,mode='lines',line_color='indigo',line=dict(width=0.2), name=""))
            fig0.add_trace(go.Scatter(x=xpoints,y=ypoints-stdpoints,
                                    fill='tonexty',fillcolor='rgba(26,150,65,0.5)',mode='lines',line_color='indigo',
                                    line=dict(width=0.2), name="Desvío Estándar"))
            fig0.add_trace(go.Scatter(x=xpoints,
                                    y=ypoints,mode='lines+markers',line_color='rgba(255, 182, 193, 1)', name="Promedio NDVI"))
            fig0.update_layout(xaxis_title="Fecha", yaxis_title="NDVI", width=900, height=500, 
                              legend = dict(orientation = 'h', xanchor = "center", x = 0.5, y= 1.1,font=dict(size=14)))
            fig0.update_xaxes(tickangle = 315, nticks=20,showgrid=True)
            df=pd.DataFrame(dict1)
            csv0=df.to_csv(index=False).encode('utf-8')
            return fig0,fecha_list0,csv0       

          lista, fecha_mean = getNDVI(fecha11,fecha22,st.session_state['clouds'])
          fig,fecha_list,csv= time_plot(fecha_mean)

          with tab2:
            event = st.plotly_chart(fig, on_select="rerun")
            st.download_button("Descargar csv",csv,f'Serie_{ndvi_name}.csv',"text/csv",key='download-csv')
            if event['selection']['points']!=[]:
              indice=event['selection']['point_indices'][0]
            else:
              indice=None

          with col02:           
            select_fecha=st.selectbox('Seleccionar fecha',range(len(fecha_list)),index=indice,placeholder='Seleccionar...',
                                      format_func=lambda x: fecha_list[x])
            cont1=st.container()
            col11, col22 = cont1.columns([1, 1])

            if select_fecha!=None:
              @st.cache_data(show_spinner=False,max_entries=1)
              def getIm(_lista,fecha,min,max,select_index0):               
                ndvi=ee.Image(_lista.get(select_index0))
                visParams_ndvi = {'bands':['NDVI'],'min': min, 'max': max, 
                                  'palette': ['#543005','#6E3F07','#8A5009','#A5681B','#BF812D','#CFA255','#DEC07B',
                                              '#EAD49F','#F6E8C3','#F4F4F4','#DEEFED','#C7EAE5','#A2DBD2','#A2DBD2',
                                              '#7ECBC0','#58B0A6','#35978F','#1A7E76','#00655D','#004F45']}
                Map20=geemap.Map(basemap="HYBRID")
                Map20.centerObject(point)
                Map20.addLayer(ndvi,visParams, f'RGB - {fecha}',shown=True,opacity=1)
                Map20.addLayer(ndvi, visParams_ndvi, f'NDVI - {fecha}', shown=True, opacity=1)
                Map20.addLayer(point.style(**vis_params_lim),{},'Limite del Lote')
                Map20.add_colorbar(visParams_ndvi,label="NDVI",layer_name="clrbr",orientation="vertical",
                                 categorical=True, step=20, background_color=None)
                st.session_state['map']=Map20             
                return ndvi,Map20

              def handle_change_min():
                  st.session_state['min']=st.session_state['change_min']
              def handle_change_max():
                  st.session_state['max']=st.session_state['change_max']

              st.write("")
              min_ndvi= col11.number_input(label='min', value=st.session_state['min'], on_change=handle_change_min,key='change_min')
              max_ndvi= col22.number_input(label='max', value=st.session_state['max'], on_change=handle_change_max,key='change_max')
              ndvi,Map2=getIm(lista,fecha_list[select_fecha],st.session_state['min'],st.session_state['max'],select_fecha) 

              limit1=ee.Geometry.Polygon((point).getInfo()['features'][0]['geometry']['coordinates']).buffer(100)
              ndvi_clip=ndvi.clip(limit1)
              img=ndvi_clip.getDownloadURL({'bands':['NDVI'], 'scale':10,'crs':'EPSG:4326', 'format':"GEO_TIFF"})
              st.link_button('Descargar NDVI',img, type='primary')
              st.code(f'{ndvi_name}_{fecha_list[select_fecha]}', language=None)

              with tab1:
                if centrar:
                  Map2.centerObject(point)
                  st.session_state['map']=Map2
else:
  st.sidebar.write('Cargar Credenciales')

with tab1:
  st.session_state['map'].to_streamlit(height=550, width=930, control_scale=True)

