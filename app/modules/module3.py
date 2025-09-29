import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.gridspec as gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable
import contextily as ctx
import os

# Pasta raiz do projeto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Caminhos dos arquivos
CSV_FINAL = os.path.join(BASE_DIR, "data", "alqueva_comb_espacial_linear.csv")
CSV_NIVEL = os.path.join(BASE_DIR, "data", "alqueva_nivel.xlsx")
CSV_TEMP = os.path.join(BASE_DIR, "data", "alqueva_temp.xlsx")

def run():
    st.header("Correlação com nível e temperatura")

    top_n = st.slider("Número de pontos a analisar", 1, 10, 1)

    df_final = pd.read_csv(CSV_FINAL)
    df_nivel = pd.read_excel(CSV_NIVEL)
    df_nivel['data'] = pd.to_datetime(df_nivel['data'])
    df_nivel.set_index('data', inplace=True)
    df_temp = pd.read_excel(CSV_TEMP)
    df_temp['data'] = pd.to_datetime(df_temp['data'])
    df_temp.set_index('data', inplace=True)

    df_mean = df_final.groupby(['easting','northing'], as_index=False).mean(numeric_only=True)
    df_mean['std_up'] = df_final.groupby(['easting','northing'])['up'].std().values
    df_top = df_mean.nlargest(top_n, 'std_up')

    gdf_all = gpd.GeoDataFrame(df_mean,
                               geometry=gpd.points_from_xy(df_mean.easting, df_mean.northing),
                               crs="EPSG:3035").to_crs(epsg=3857)
    xmin, ymin, xmax, ymax = gdf_all.total_bounds

    cmap = plt.cm.jet
    norm = plt.Normalize(vmin=df_mean['up'].min(), vmax=df_mean['up'].max())

    for _, row in df_top.iterrows():
        ponto = (row['easting'], row['northing'])
        serie = df_final[(df_final['easting']==ponto[0]) & (df_final['northing']==ponto[1])].sort_values('date')
        datas = pd.to_datetime(serie['date'])
        up_values = serie['up']

        nivel_alinhado = df_nivel.reindex(datas, method='nearest')['nivel'].values
        temp_alinhado = df_temp.reindex(datas, method='nearest')['med'].values

        valid = ~np.isnan(up_values) & ~np.isnan(nivel_alinhado) & ~np.isnan(temp_alinhado)
        if valid.sum() < 3:
            st.warning(f"Ponto {ponto} não tem dados suficientes para análise.")
            continue

        up_clean = up_values[valid]
        nivel_clean = nivel_alinhado[valid]
        temp_clean = temp_alinhado[valid]
        datas_clean = datas[valid]

        corr_nivel = np.corrcoef(up_clean, nivel_clean)[0,1]
        corr_temp = np.corrcoef(up_clean, temp_clean)[0,1]

        fig = plt.figure(figsize=(20,12))
        gs = gridspec.GridSpec(3,2, height_ratios=[2,1.2,1.2], width_ratios=[1.2,1])

        # Mapa
        ax_map = fig.add_subplot(gs[0,0])
        divider = make_axes_locatable(ax_map)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        gdf_all.plot(ax=ax_map, column='up', cmap=cmap, norm=norm, markersize=5, legend=True, cax=cax)
        gpd.GeoDataFrame(geometry=gpd.points_from_xy([ponto[0]],[ponto[1]]),crs="EPSG:3035").to_crs(3857).plot(
            ax=ax_map,color='red', edgecolor='black', markersize=100)
        ctx.add_basemap(ax_map, source=ctx.providers.Esri.WorldImagery)
        ax_map.set_xlim(xmin,xmax)
        ax_map.set_ylim(ymin,ymax)
        ax_map.set_axis_off()
        ax_map.set_title(f"Ponto ({ponto[0]:.0f},{ponto[1]:.0f})")

        # Série temporal
        ax_series = fig.add_subplot(gs[0,1])
        ax_series.plot(datas_clean, up_clean, color="blue", label="up")
        ax_series.axhline(0, color='gray', linestyle='--', linewidth=0.7)
        ax_series.set_title("Série Temporal: up vs Nível vs Temperatura")
        ax_series.set_ylabel("Deslocamento (mm)")
        ax_series.set_xlabel("Data")
        ax_series.grid(True)

        # Dispersão up vs nível
        ax_corr_nivel = fig.add_subplot(gs[1,:])
        sns.scatterplot(x=up_clean, y=nivel_clean, color="blue", label="Pontos", ax=ax_corr_nivel)
        sns.regplot(x=up_clean, y=nivel_clean, scatter=False, color="red", line_kws={"lw":2,"ls":"--"}, ax=ax_corr_nivel)
        ax_corr_nivel.set_title(f'Correlação up vs nível: r = {corr_nivel:.2f}')
        ax_corr_nivel.set_xlabel("Deslocamento (mm)")
        ax_corr_nivel.set_ylabel("Nível (m)")
        ax_corr_nivel.grid(True)

        # Dispersão up vs temperatura
        ax_corr_temp = fig.add_subplot(gs[2,:])
        sns.scatterplot(x=up_clean, y=temp_clean, color="purple", label="Pontos", ax=ax_corr_temp)
        sns.regplot(x=up_clean, y=temp_clean, scatter=False, color="orange", line_kws={"lw":2,"ls":"--"}, ax=ax_corr_temp)
        ax_corr_temp.set_title(f'Correlação up vs temperatura: r = {corr_temp:.2f}')
        ax_corr_temp.set_xlabel("Deslocamento (mm)")
        ax_corr_temp.set_ylabel("Temperatura (°C)")
        ax_corr_temp.grid(True)

        plt.tight_layout()
        st.pyplot(fig)


