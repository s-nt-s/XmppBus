#!/bin/bash
cd "$(dirname "$0")"


wget http://data-crtm.opendata.arcgis.com/datasets/8ef563f232c244ca9b3a5d2d6a3dc19b_0.csv -O csv/em6.csv
wget http://data-crtm.opendata.arcgis.com/datasets/19884a02ac044270b91fa478d80f7858_0.csv -O csv/em8.csv
wget http://data-crtm.opendata.arcgis.com/datasets/46044e95c2f340e6a9e0790842bbbef2_0.csv -O csv/em9.csv

wget http://data-crtm.opendata.arcgis.com/datasets/8ef563f232c244ca9b3a5d2d6a3dc19b_3.csv -O csv/pm6.csv
wget http://data-crtm.opendata.arcgis.com/datasets/19884a02ac044270b91fa478d80f7858_3.csv -O csv/pm8.csv
wget http://data-crtm.opendata.arcgis.com/datasets/46044e95c2f340e6a9e0790842bbbef2_3.csv -O csv/pm9.csv
