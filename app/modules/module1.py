import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib import colors
from scipy.interpolate import griddata
import contextily as ctx
from io import BytesIO
import os

# Pasta raiz do projeto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Caminhos CSV
csv_asc = os.path.join(BASE_DIR, "data", "alqueva_calibrated_asc_desc_2019_2023",
                       "EGMS_L2b_052_0848_IW2_VV_2019_2023_1",
                       "EGMS_L2b_052_0848_IW2_VV_2019_2023_1.csv")
csv_desc = os.path.join(BASE_DIR, "data", "alqueva_calibrated_asc_desc_2019_2023",
                        "EGMS_L2b_147_0224_IW2_VV_2019_2023_1",
                        "EGMS_L2b_147_0224_IW2_VV_2019_2023_1.csv")

def run():
    st.header("Deslocamento médio - ASC + DESC")

    # Parâmetros do usuário
    componente = st.selectbox("Escolha a componente:", ["up", "east", "north"])
    vmin = st.slider("Valor mínimo (mm)", -20, 0, -5)
    vmax = st.slider("Valor máximo (mm)", 0, 20, 5)
    usar_colormap_reverso = st.checkbox("Usar colormap reverso", value=True)

    # --- Funções ---
    def ler_e_filtrar(caminho_csv):
        df = pd.read_csv(caminho_csv)
        norte_min, norte_max = 1855050, 1855850
        este_min, este_max = 2792250, 2793250
        return df[(df['northing'] >= norte_min) & (df['northing'] <= norte_max) &
                  (df['easting'] >= este_min) & (df['easting'] <= este_max)]

    def melt(df, comp):
        static = ['pid', 'easting', 'northing']
        dates = [c for c in df.columns if c.startswith('20')]
        df_temp = df[static + dates].copy()
        df_melt = df_temp.melt(id_vars=static, var_name='date', value_name=comp)
        df_melt['date'] = pd.to_datetime(df_melt['date'], format='%Y%m%d')
        return df_melt

    def get_componentes(df, prefix):
        up = melt(df, f'up_{prefix}')
        east = melt(df, f'east_{prefix}')
        north = melt(df, f'north_{prefix}')
        merged = up.merge(east, on=['pid','easting','northing','date'])
        merged = merged.merge(north, on=['pid','easting','northing','date'])
        return merged

    df_asc = ler_e_filtrar(csv_asc)
    df_desc = ler_e_filtrar(csv_desc)

    asc = get_componentes(df_asc, 'asc')
    desc = get_componentes(df_desc, 'desc')

    datas_comuns = np.intersect1d(asc['date'].unique(), desc['date'].unique())

    resultados = []
    for data in datas_comuns:
        asc_data = asc[asc['date']==data]
        desc_data = desc[desc['date']==data]

        pontos_asc = asc_data[['easting','northing']].values
        pontos_desc = desc_data[['easting','northing']].values

        interp = {comp: griddata(pontos_asc, asc_data[comp].values, pontos_desc, method='linear')
                  for comp in ['up_asc','east_asc','north_asc']}

        df_comb = pd.DataFrame({
            'easting': desc_data['easting'].values,
            'northing': desc_data['northing'].values,
            'date': data,
            'up': np.nanmean([interp['up_asc'], desc_data['up_desc'].values], axis=0),
            'east': np.nanmean([interp['east_asc'], desc_data['east_desc'].values], axis=0),
            'north': np.nanmean([interp['north_asc'], desc_data['north_desc'].values], axis=0),
        })

        resultados.append(df_comb)

    df_final = pd.concat(resultados, ignore_index=True)

    # Salvar CSV final
    csv_out = os.path.join(BASE_DIR, "data", "alqueva_comb_espacial_linear.csv")
    df_final.to_csv(csv_out, index=False)

    # --- GeoDataFrame e plot ---
    df_media = df_final.groupby(['easting','northing'], as_index=False).mean(numeric_only=True)
    gdf = gpd.GeoDataFrame(df_media,
                           geometry=gpd.points_from_xy(df_media['easting'], df_media['northing']),
                           crs="EPSG:3035").to_crs(epsg=3857)

    fig, ax = plt.subplots(figsize=(9,6))
    gdf.plot(ax=ax, column=componente,
             cmap=plt.cm.jet.reversed() if usar_colormap_reverso else plt.cm.jet,
             markersize=10,
             norm=colors.TwoSlopeNorm(vmin=vmin,vcenter=0,vmax=vmax))
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)
    ax.set_axis_off()
    st.pyplot(fig)

    # Botão para download
    csv_buffer = BytesIO()
    df_final.to_csv(csv_buffer, index=False)
    st.download_button("Baixar CSV Processado", csv_buffer.getvalue(),
                       "resultados_alqueva.csv", "text/csv")




