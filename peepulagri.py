import streamlit as st
import folium
import geopandas as gpd
import numpy as np
import json
from shapely.geometry import Polygon, LineString, shape
from streamlit_folium import st_folium

# 🌍 Function to create a base map
def create_map():
    m = folium.Map(location=[16.50, 80.65], zoom_start=15)
    folium.plugins.Draw(export=True).add_to(m)
    return m

# 📍 Compute the center of a polygon
def get_center(coords):
    lats, lons = zip(*coords)
    return [np.mean(lats), np.mean(lons)]

# 🛠 Calculate area in square meters
def calculate_area(polygon):
    gdf = gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:4326")
    gdf = gdf.to_crs(epsg=3857)
    return gdf.area.iloc[0]

# 🚜 Generate parallel paths inside the polygon
def generate_paths(field_polygon, row_width=100):
    """Generate parallel paths within the polygon, ensuring correct projections."""
    gdf = gpd.GeoDataFrame(geometry=[field_polygon], crs="EPSG:4326").to_crs(epsg=3857)
    polygon_metric = gdf.geometry.iloc[0]

    min_x, min_y, max_x, max_y = polygon_metric.bounds
    paths = []
    x = min_x

    while x <= max_x:
        line = LineString([(x, min_y), (x, max_y)])
        clipped_line = polygon_metric.intersection(line)
        if not clipped_line.is_empty:
            paths.append(clipped_line)

        x += row_width

    path_gdf = gpd.GeoDataFrame(geometry=paths, crs="EPSG:3857").to_crs(epsg=4326)
    return path_gdf.geometry.tolist()

# 🎯 Streamlit App UI
st.title("🗺️ Field Area & Path Generator")
st.write("Draw a polygon on the map or upload a GeoJSON file.")

# Option 1️⃣: Draw on Map
st.subheader("📍 Draw a Polygon on the Map")
m = create_map()
map_data = st_folium(m, width=700, height=500)

# Option 2️⃣: Upload GeoJSON File
st.subheader("📂 Upload GeoJSON File")
uploaded_file = st.file_uploader("Upload a GeoJSON file", type=["geojson"])

polygon = None

if uploaded_file:
    try:
        geojson_data = json.load(uploaded_file)
        st.success("✅ GeoJSON file loaded successfully!")

        if "features" in geojson_data and len(geojson_data["features"]) > 0:
            geometry = geojson_data["features"][0]["geometry"]
            if geometry["type"] == "Polygon":
                coords = geometry["coordinates"][0]
                polygon = Polygon(coords)
            else:
                st.error("❌ Uploaded file is not a valid Polygon!")

    except json.JSONDecodeError:
        st.error("❌ Invalid GeoJSON file!")

elif map_data and "last_draw" in map_data and map_data["last_draw"]:
    geojson_data = map_data["last_draw"]
    if "geometry" in geojson_data and geojson_data["geometry"]["type"] == "Polygon":
        coords = geojson_data["geometry"]["coordinates"][0]
        polygon = Polygon(coords)
    else:
        st.warning("⚠️ No valid polygon detected in drawn shape!")

# 🏁 Process Polygon
if polygon:
    st.success("✅ Polygon detected! Processing...")

    # Extracting relevant details
    bounds = polygon.bounds
    area = calculate_area(polygon)
    paths = generate_paths(polygon, row_width=100)
    center = get_center(list(polygon.exterior.coords))
    coordinates = list(polygon.exterior.coords)

    # Displaying results
    st.write(f"**🌍 Field Area:** `{area:.2f} square meters`")
    st.write(f"**🚜 Paths Generated:** `{len(paths)} paths` (Row width = 100m)")
    st.write(f"**📍 Polygon Bounds:** {bounds}")
    st.write(f"**🗺️ Polygon Coordinates:**")
    for coord in coordinates:
        st.write(f"- {coord}")

    # 📌 Show updated map with polygon & paths
    result_map = folium.Map(location=center, zoom_start=15)

    # 🟢 Draw Polygon
    folium.Polygon(
        locations=[(lat, lon) for lon, lat in polygon.exterior.coords],
        color="green",
        fill=True
    ).add_to(result_map)

    # 🔵 Draw Paths
    for path in paths:
        if path and isinstance(path, LineString):
            folium.PolyLine(
                locations=[(lat, lon) for lon, lat in path.coords],
                color="blue",
                weight=2
            ).add_to(result_map)

    st_folium(result_map, width=700, height=500)

else:
    st.warning("⚠️ No polygon detected! Please draw on the map or upload a GeoJSON file.")
