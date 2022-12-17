#!/bin/bash
cd "$(dirname "$0")"

# https://data-crtm.opendata.arcgis.com/search?collection=Dataset

# M4 = Metro
# M5 = Cercanias
# M6 = Autobus urbano
# M8 = Autobuses Interurbanos
# M10 = Metro ligero / Tranvia

# MX_Estaciones
wget http://data-crtm.opendata.arcgis.com/datasets/8ef563f232c244ca9b3a5d2d6a3dc19b_0.csv -O csv/estaciones_6.csv
wget http://data-crtm.opendata.arcgis.com/datasets/19884a02ac044270b91fa478d80f7858_0.csv -O csv/estaciones_8.csv
wget http://data-crtm.opendata.arcgis.com/datasets/46044e95c2f340e6a9e0790842bbbef2_0.csv -O csv/estaciones_9.csv

# MX_Tramos
wget http://data-crtm.opendata.arcgis.com/datasets/8ef563f232c244ca9b3a5d2d6a3dc19b_2.csv -O csv/lineas_6.csv
wget http://data-crtm.opendata.arcgis.com/datasets/19884a02ac044270b91fa478d80f7858_2.csv -O csv/lineas_8.csv
wget http://data-crtm.opendata.arcgis.com/datasets/46044e95c2f340e6a9e0790842bbbef2_2.csv -O csv/lineas_9.csv

# MX_ParadasPorItinerario
wget http://data-crtm.opendata.arcgis.com/datasets/8ef563f232c244ca9b3a5d2d6a3dc19b_3.csv -O csv/itinerario_6.csv
wget http://data-crtm.opendata.arcgis.com/datasets/19884a02ac044270b91fa478d80f7858_3.csv -O csv/itinerario_8.csv
wget http://data-crtm.opendata.arcgis.com/datasets/46044e95c2f340e6a9e0790842bbbef2_3.csv -O csv/itinerario_9.csv
