import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
# Cargamos configuración
r = requests.get(url='https://ciherraiz.pythonanywhere.com/conf')
cfg = json.loads(r.text)

# Asignamos parámetros
longitud = int(cfg['longitud_serie'])
max_medidas_gr = int(cfg['medidas_grafico_agrupacion'])

# https://share.streamlit.io/streamlit/emoji-shortcodes
EMOJI = {0: ':neutral_face:',
        1: ':confused:',
        2: ':confounded:'}

st.set_page_config(
     page_title="Cuadro de mandos MLC",
     page_icon=":chart_with_upwards_trend:",
     layout="wide",
     initial_sidebar_state="expanded",
     menu_items={
         'Get help': 'https://www.fitbit.com/global/es/home',
         'About': "Cuadros de mandos para MLC con Fitbit"
     }
 )

#Creamos menú de la izquierda
with st.sidebar:
    menu = st.selectbox('Opción', ('Individuo', 'Agrupado', 'Tiempo real', 'Configuración'))

if menu == 'Tiempo real':
    # Creamos un espacio vacío
    espacio = st.empty()

    df_total = pd.DataFrame()
    dfs = []

    while True:
    #for seconds in range(10):
        st.markdown('')
        try:
            df_tmp = pd.read_csv("https://ciherraiz.pythonanywhere.com/ultimas")[['momento', 'id', 'fc', 'accx', 'accy', 'accz']]          
        except:
            continue

        df_total = pd.concat([df_total, df_tmp]).drop_duplicates()
        
        with espacio.container():
            participantes = df_tmp['id'].unique()
            
            try:
                df_tmp_grp = pd.read_csv("https://ciherraiz.pythonanywhere.com/ultimasgrp")[['id', 'grupo', 'grupo_recod', 'etiqueta_recod']]
                for i, p in df_tmp_grp.iterrows():
                    st.markdown(EMOJI[p['grupo_recod']] + ' ' + str(p['id']) + '('+p['etiqueta_recod']+')')
            except:
                st.markdown('Datos de agrupamiento aún no disponibles :hourglass_flowing_sand:')

            kpi1, kpi2 = st.columns(2)

            kpi1.metric(label='Participantes ', value = len(participantes))
            kpi2.metric(label='Mediciones ', value = len(df_total))

            gr1, gr2 = st.columns(2)

            if len(df_total) > max_medidas_gr:
                df_gr = df_total[-max_medidas_gr:]
                
            else:
                df_gr = df_total

            df_gr['acc'] = df_gr['accx'].abs() + df_gr['accy'].abs() + df_gr['accz'].abs()

            with gr1:
                fig1 = px.line(df_gr, x="momento", y="fc", title='Frecuencia cardiaca', color='id', template="plotly_white") 
                fig1.update_layout(paper_bgcolor="rgb(255,255,255)", plot_bgcolor="rgb(255,255,255)")
                st.write(fig1)

            with gr2:
                fig2 = px.line(df_gr, x="momento", y="acc", title='Aceleración', color='id', template="plotly_white") 
                fig2.update_layout(paper_bgcolor="rgb(255,255,255)", plot_bgcolor="rgb(255,255,255)")
                st.write(fig2)

        time.sleep(1)

if menu == 'Individuo':

    try:
        r = requests.get(url='https://ciherraiz.pythonanywhere.com/id')
        ids = json.loads(r.text)
    except Exception as e:
        st.error(str(e)) 

    if ids:
        individuo = st.selectbox('Seleccione participante', ids)
        url = "https://ciherraiz.pythonanywhere.com/medidas?id=" + individuo

        try:
            df = pd.read_csv(url)
        except:
            st.error('Error al cargar las mediciones de ' + individuo) 
    
        col1, col2, col3, col4 = st.columns(4)
        fc_media_calibrado = df[df['etapa']==1]['fc'].mean()
        fc_media_actividad = df[df['etapa']==2]['fc'].mean()
        fc_max_actividad = df[df['etapa']==2]['fc'].max()
        fc_min_actividad = df[df['etapa']==2]['fc'].min()
        df['acc'] = df['accx'].abs() + df['accy'].abs() + df['accz'].abs()

        col1.metric(label='FC media calibrado', value = f"{fc_media_calibrado:.2f} p/min")
        col2.metric(label='FC media actividad', value = f"{fc_media_actividad:.2f} p/min", delta = f"{(fc_media_actividad - fc_media_calibrado)/fc_media_calibrado * 100:.2f}%")
        col3.metric(label='FC máxima actividad', value = f"{fc_max_actividad:.0f} p/min")
        col4.metric(label='FC mínima actividad', value = f"{fc_min_actividad:.0f} p/min")
        
        fin_calibrado = df[df['etapa']==1][-1:]['tiempo'].squeeze()

        gr1, gr2 = st.columns(2)

        with gr1:
            fig1 = px.line(df, x="tiempo", y="fc", title='Frecuencia cardiaca') 
            fig1.add_vline(x=fin_calibrado, line_width=3, line_dash="dash", line_color="green")
            fig1.update_layout(paper_bgcolor="rgb(255,255,255)", plot_bgcolor="rgb(255,255,255)")
            st.write(fig1)

        with gr2:
            fig2 = px.line(df, x="tiempo", y="acc", title='Aceleración') 
            fig2.add_vline(x=fin_calibrado, line_width=3, line_dash="dash", line_color="green")
            fig2.update_layout(paper_bgcolor="rgb(255,255,255)", plot_bgcolor="rgb(255,255,255)")
            st.write(fig2)
    else:
        st.warning('No hay datos disponibles')

if menu=='Agrupado':
    try:
        r = requests.get(url='https://ciherraiz.pythonanywhere.com/id')
        ids = json.loads(r.text)
    except Exception as e:
        st.error(str(e)) 
    
    if ids:     
        individuo = st.selectbox('Seleccione participante', ids)
        url = "https://ciherraiz.pythonanywhere.com/grupos?id=" + individuo

        try:
            df = pd.read_csv(url)
        except:
            st.error('Error al cargar los grupos de ' + individuo)

        gr1, gr2 = st.columns(2)
        fig1 = go.Figure()
        fig2 = go.Figure()
        for i in range(0, len(df), longitud):
            fig1.add_traces(go.Scatter(x=df.index[i:i+longitud],
                                        y=df[i:i+longitud]['valor'],
                                line_color=px.colors.qualitative.Plotly[df[i:i+longitud]['grupo_recod'].unique().squeeze()],
                                mode='lines'))
            fig1.update_layout(showlegend=False)

            fig2.add_traces(go.Scatter(
                                        y=df[i:i+longitud]['valor'],
                                line_color=px.colors.qualitative.Plotly[df[i:i+longitud]['grupo_recod'].unique().squeeze()],
                                mode='lines'))
            fig2.update_layout(showlegend=False)
        
        with gr1:
            st.write(fig1)
        with gr2:
            st.write(fig2)
    else:
        st.warning("No hay datos disponibles")

if menu == 'Configuración':
    r = requests.get(url='https://ciherraiz.pythonanywhere.com/conf')
    cfg = json.loads(r.text)
    #st.json(cfg)
    cfg['directorio_datos'] = st.text_input('Ruta ficheros de datos', cfg['directorio_datos'])
    cfg['longitud_serie'] = st.text_input('Longitud serie temporal', cfg['longitud_serie'])
    cfg['medidas_grafico_agrupacion'] = st.text_input('Máximo número de medidas en gráfico de agrupación', cfg['medidas_grafico_agrupacion'])
    cfg['numero_grupos'] = st.text_input('Número de grupos a realizar', cfg['numero_grupos'])
    cfg['espera_agrupar'] = st.text_input('Tiempo de espera entre agrupación (seg)', cfg['espera_agrupar'])
    cfg['minimo_medidas_agrupar'] = st.text_input('Mínimo de medidas para comenzar agrupación', cfg['minimo_medidas_agrupar'])

    #st.write(nueva_cfg)
    rp = requests.post('https://ciherraiz.pythonanywhere.com/conf', json=cfg)
    if rp.status_code != 200:
        st.error('Error al almacenar configuracion')
