import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime

st.set_page_config(page_title="Đánh giá KPI Trạm 3G/4G", layout="wide")

# 1. NHÚNG CSS VÀ JS (ĐIỀU CHỈNH LẠI CÁC CỘT CỐ ĐỊNH TRÁI)
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    html, body, .stApp { max-width: 100vw !important; overflow-x: hidden !important; }

    .kpi-fail { color: #d32f2f; font-weight: bold; }
    .kpi-pass { color: #2e7d32; }
    .badge-pass { background-color: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-fail { background-color: #ffebee; color: #c62828; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-nodata { background-color: #f5f5f5; color: #757575; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    
    .table-responsive-wrapper {
        width: 100%; max-width: 100vw; max-height: 70vh; 
        overflow-x: auto; overflow-y: auto; 
        border: 1px solid #444; border-radius: 6px;
        margin-top: 10px; margin-bottom: 15px;
        cursor: grab; user-select: none;
        -webkit-overflow-scrolling: touch; touch-action: pan-x pan-y; 
    }
    .table-responsive-wrapper:active { cursor: grabbing; }
    
    .table-custom { width: 100%; border-collapse: separate; border-spacing: 0; font-family: sans-serif; font-size: 13px; }
    .table-custom th { 
        position: sticky; background-color: #212529; color: #eee; text-align: left; 
        padding: 8px 10px; border-bottom: 2px solid #555; vertical-align: middle; 
        white-space: nowrap; box-sizing: border-box;
    }
    .table-custom td { padding: 8px 10px; border-bottom: 1px solid #333; white-space: nowrap; }
    
    .combined-table thead tr:first-child th { top: 0; z-index: 5; height: 45px; font-size: 14px; font-weight: bold; }
    .combined-table thead tr:nth-child(2) th { top: 45px; z-index: 4; }
    .detail-table thead tr:first-child th { top: 0; z-index: 5; }

    .th-group-4g { background-color: #0288d1 !important; color: #ffffff !important; text-align: center !important; border-right: 3px solid #ffeb3b !important; font-size: 14px !important; }
    .th-group-3g { background-color: #e65100 !important; color: #ffffff !important; text-align: center !important; font-size: 14px !important; }

    /* CỘT CỐ ĐỊNH CHO BẢNG TRUNG BÌNH */
    .f-col1 { position: sticky !important; left: 0 !important; min-width: 120px; max-width: 120px; white-space: normal !important; word-wrap: break-word; z-index: 3; }
    .f-col2 { position: sticky !important; left: 120px !important; min-width: 160px; max-width: 160px; white-space: normal !important; word-wrap: break-word; border-right: 2px solid #1976d2 !important; z-index: 3; }
    th.f-col1, th.f-col2 { z-index: 6 !important; background-color: #1e293b !important; } 
    td.f-col1, td.f-col2 { background-color: #1e1e1e !important; color: #eee !important; }

    /* CỘT CỐ ĐỊNH CHO BẢNG CHI TIẾT 4G */
    .f-id1 { position: sticky !important; left: 0 !important; min-width: 90px; max-width: 90px; white-space: normal !important; word-wrap: break-word; z-index: 3; }
    .f-id2 { position: sticky !important; left: 90px !important; min-width: 80px; max-width: 80px; white-space: normal !important; word-wrap: break-word; z-index: 3; }
    .f-cell-4g { position: sticky !important; left: 170px !important; min-width: 180px; max-width: 180px; white-space: normal !important; word-wrap: break-word; border-right: 2px solid #1976d2 !important; z-index: 3; }
    th.f-id1, th.f-id2, th.f-cell-4g { z-index: 6 !important; background-color: #1e293b !important; } 
    td.f-id1, td.f-id2, td.f-cell-4g { background-color: #1e1e1e !important; color: #eee !important; }

    /* CỘT CỐ ĐỊNH CHO BẢNG CHI TIẾT 3G */
    .f-ci { position: sticky !important; left: 0 !important; min-width: 80px; max-width: 80px; white-space: normal !important; word-wrap: break-word; z-index: 3; }
    .f-cell-3g { position: sticky !important; left: 80px !important; min-width: 200px; max-width: 200px; white-space: normal !important; word-wrap: break-word; border-right: 2px solid #1976d2 !important; z-index: 3; }
    th.f-ci, th.f-cell-3g { z-index: 6 !important; background-color: #1e293b !important; } 
    td.f-ci, td.f-cell-3g { background-color: #1e1e1e !important; color: #eee !important; }

    .header-station { background-color: #1e293b; padding: 12px 16px; border-left: 5px solid #1976d2; border-radius: 4px; margin: 15px 0 5px 0; color: #fff; }
    .kpi-target { font-size: 11px; color: #ffeb3b; display: block; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# ----------------- ĐỊNH NGHĨA CHỈ TIÊU KPI -----------------
KPI_THRESHOLDS_4G = {
    'CSSR': {'min': 98.0, 'label': 'CSSR 4G (%)<br><span class="kpi-target">≥ 98%</span>', 'kw': ['CSSR', 'CALLSETUPSUCCESS']},
    'SERVICEDROPALL': {'max': 1.5, 'label': 'DROP 4G (%)<br><span class="kpi-target">≤ 1.5%</span>', 'kw': ['SERVICEDROPALL', 'SERVICEDROP', 'DROP']},
    'INTRAFREQUENCYHO': {'min': 98.0, 'label': 'INTRA HO (%)<br><span class="kpi-target">≥ 98%</span>', 'kw': ['INTRAFREQUENCYHO', 'INTRAFREQ']},
    'INTERFREQUENCYHO': {'min': 95.0, 'label': 'INTER HO (%)<br><span class="kpi-target">≥ 95%</span>', 'kw': ['INTERFREQUENCYHO', 'INTERFREQ']},
    'HOSRIRATLTEWCDMA': {'min': 90.0, 'label': 'LTE-UMTS (%)<br><span class="kpi-target">≥ 90%</span>', 'kw': ['HOSRIRATLTEWCDMA', 'LTETOWCDMA', 'RATHOSR']},
    'CSFBSSR': {'min': 98.0, 'label': 'CSFB SR (%)<br><span class="kpi-target">≥ 98%</span>', 'kw': ['CSFBSSR', 'SETUPSUCCESSRATIO', 'CSFB']},
    'ERABSSRATEALL': {'min': 98.5, 'label': 'E-RAB SR (%)<br><span class="kpi-target">≥ 98.5%</span>', 'kw': ['ERABSSRATEALL', 'ERAB']},
}

KPI_THRESHOLDS_3G = {
    'CSVOICECSS': {'min': 99.0, 'label': 'CSSR Voice (%)<br><span class="kpi-target">≥ 99%</span>', 'kw': ['CSVOICECSS', 'CSSRVOICE']},
    'DCR': {'max': 1.0, 'label': 'Drop Voice (%)<br><span class="kpi-target">≤ 1%</span>', 'kw': ['DCR', 'DROPVOICE']},
    'SOFTHOSR': {'min': 99.0, 'label': 'S.HOSR (%)<br><span class="kpi-target">≥ 99%</span>', 'kw': ['SOFTHOSR']},
    'SINTERFREQH': {'min': 95.0, 'label': 'IF HOSR (%)<br><span class="kpi-target">≥ 95%</span>', 'kw': ['SINTERFREQH', 'IFHOSR']},
    'IRATHOSR': {'min': 95.0, 'label': 'IRAT HOSR (%)<br><span class="kpi-target">≥ 95%</span>', 'kw': ['IRATHOSR']},
    'PSCSSR': {'min': 98.0, 'label': 'ASR PS (%)<br><span class="kpi-target">≥ 98%</span>', 'kw': ['PSCSSR', 'ASRPS']},
    'PSDCR': {'max': 1.0, 'label': 'DR PS (%)<br><span class="kpi-target">≤ 1%</span>', 'kw': ['PSDCR', 'DRPS']},
    'SOFTHOSRPS': {'min': 99.0, 'label': 'PS Soft HO (%)<br><span class="kpi-target">≥ 99%</span>', 'kw': ['SOFTHOSRPS', 'PSSOFTHO']},
    'V2INTERFREQ': {'min': 93.0, 'label': 'PS Inter-Freq (%)<br><span class="kpi-target">≥ 93%</span>', 'kw': ['V2INTERFREQ', 'PSINTERFREQ']},
}

def clean_col_name(c): return re.sub(r'[^a-zA-Z0-9]', '', str(c)).upper()

def clean_time_string(raw_time_str):
    if not raw_time_str: return ""
    dates = re.findall(r'\b\d{1,2}/\d{1,2}/\d{4}\b', str(raw_time_str))
    if len(dates) >= 2: return f"{dates[0]} - {dates[1]}"
    elif len(dates) == 1: return dates[0]
    return str(raw_time_str).strip()

def evaluate_val(val, rule):
    if pd.isna(val) or val is None or str(val).strip() in ['', 'nan', 'None']: return None, "null"
    try: v = float(val)
    except: return None, str(val)
    is_ok = not (('min' in rule and v < rule['min']) or ('max' in rule and v > rule['max']))
    return is_ok, f"{v:.2f}"

def clean_numeric_series(series):
    s = series.astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).str.strip()
    return pd.to_numeric(s, errors='coerce')

@st.cache_data
def load_excel_data_with_mtime(file_path, file_mtime): return pd.read_excel(file_path)

@st.cache_data
def parse_mapping_file(df_map):
    # Ffill để xử lý các ô merge (ví dụ ô Khu vực HCM bị merge qua nhiều dòng)
    df_map = df_map.ffill()
    mapping = {}
    region_mapping = {}
    
    ma_cols = [c for c in df_map.columns if 'MÃ' in str(c).upper() or 'MA TR' in str(c).upper() or 'MÃ TR' in str(c).upper()]
    ten_cols = [c for c in df_map.columns if 'TÊN' in str(c).upper() or 'TEN TR' in str(c).upper() or 'TÊN TR' in str(c).upper()]
    
    # Tìm cột khu vực (Thường chứa chữ HCM, VTU, BDG)
    r_col = None
    for c in df_map.columns:
        if df_map[c].astype(str).str.upper().isin(['HCM', 'VTU', 'BDG']).any():
            r_col = c
            break

    if ma_cols and ten_cols:
        for _, row in df_map.iterrows():
            m = str(row[ma_cols[0]]).strip().upper()
            t = str(row[ten_cols[0]]).strip()
            r = str(row[r_col]).strip().upper() if r_col else ""
            if m != 'NAN' and len(m) >= 3 and m.lower() != 'nan':
                mapping[m] = t
                region_mapping[m] = r
    return mapping, region_mapping

def tim_file_excel(tu_khoa):
    for f in os.listdir('.'):
        if f.endswith(('.xlsx', '.xls')) and not f.startswith('~$') and tu_khoa.upper() in f.upper():
            return f
    return None

file_3g = tim_file_excel("3G")
file_4g = tim_file_excel("4G")
file_mapping = tim_file_excel("TRAM") or tim_file_excel("MÃ") or tim_file_excel("MA")

if not (file_mapping and file_3g and file_4g):
    st.title("📊 Kiểm Tra & Đánh Giá KPI VINAPHONE Tuần")
    st.error("⚠️ Chưa tìm đủ file '3G', '4G', 'TRAM'.")
    st.stop()

try:
    mtime_map = os.path.getmtime(file_mapping) if os.path.exists(file_mapping) else 0
    df_map_raw = load_excel_data_with_mtime(file_mapping, mtime_map)
    dict_station, dict_region = parse_mapping_file(df_map_raw)
except Exception as e:
    st.error(f"Lỗi đọc file Danh mục: {e}")
    st.stop()

all_stations_raw = list(dict_station.keys())

# GỘP MÃ TRẠM BV CHỢ RẪY
bv_cr_codes = [k for k, v in dict_station.items() if str(v).strip().lower() == 'bv chợ rẫy']
grouped_cr_key = None
if len(bv_cr_codes) > 1:
    grouped_cr_key = " / ".join(bv_cr_codes)
    dict_station[grouped_cr_key] = "Bv Chợ Rẫy (Gộp chung)"
    all_stations_ui = [k for k in all_stations_raw if k not in bv_cr_codes]
    all_stations_ui.append(grouped_cr_key)
else:
    all_stations_ui = all_stations_raw

all_stations_sorted = sorted(all_stations_raw, key=len, reverse=True)

def match_station_fn(cell_val):
    cell_val_upper = str(cell_val).upper()
    for st_code in all_stations_sorted:
        if st_code in cell_val_upper:
            if grouped_cr_key and st_code in bv_cr_codes: return grouped_cr_key
            return st_code
    return None

def prepare_net_df(file_data, kpi_rules, net_type):
    if not file_data: return None, {}, None, ""
    
    mtime = os.path.getmtime(file_data) if os.path.exists(file_data) else 0
    df = load_excel_data_with_mtime(file_data, mtime)
    
    cell_col = next((c for c in df.columns if 'CELL NAME' in str(c).upper() or 'TÊN CELL' in str(c).upper() or str(c).upper() == 'CELL'), None)
    if not cell_col: cell_col = next((c for c in df.columns if 'CELL' in str(c).upper()), None)
    
    time_col = next((c for c in df.columns if 'THỜI' in str(c).upper() or 'TIME' in str(c).upper()), None)
    
    # Tìm các cột ENodeB ID, Cell ID (4G) hoặc CI (3G)
    extra_cols = {}
    if net_type == '4G':
        for c in df.columns:
            c_up = str(c).upper().replace(' ', '')
            if 'ENODEB' in c_up: extra_cols['ENODEB'] = c
            elif 'CELLID' in c_up and 'NAME' not in c_up: extra_cols['CELLID'] = c
    elif net_type == '3G':
        for c in df.columns:
            if str(c).strip().upper() == 'CI': extra_cols['CI'] = c

    time_str_sample = ""
    if time_col and not df.empty:
        non_null_time = df[time_col].dropna()
        if not non_null_time.empty: time_str_sample = clean_time_string(non_null_time.iloc[0])

    if not cell_col: return None, {}, None, time_str_sample

    df['MATCHED_ST'] = df[cell_col].apply(match_station_fn)
    df = df.dropna(subset=['MATCHED_ST'])

    active_kpis = {}
    for kpi_id, rule in kpi_rules.items():
        for c in df.columns:
            c_clean_name = clean_col_name(c)
            if any(kw in c_clean_name for kw in rule['kw']):
                active_kpis[c] = rule
                df[c] = clean_numeric_series(df[c])
                break

    return df, active_kpis, (cell_col, extra_cols), time_str_sample

df_4g_prep, active_kpis_4g, cols_4g, time_4g_sample = prepare_net_df(file_4g, KPI_THRESHOLDS_4G, '4G')
df_3g_prep, active_kpis_3g, cols_3g, time_3g_sample = prepare_net_df(file_3g, KPI_THRESHOLDS_3G, '3G')

display_time = time_4g_sample or time_3g_sample
if not display_time: display_time = datetime.now().strftime("%d/%m/%Y")

st.title(f"📊 Kiểm Tra & Đánh Giá KPI VINAPHONE Tuần ({display_time})")

# ----------------- 2. BẢNG TRUNG BÌNH GỘP CÓ FILTER KHU VỰC -----------------
with st.expander(f"📊 XEM CHI TIẾT TRUNG BÌNH CỦA {len(all_stations_ui)} TRẠM (GỘP CHUNG 3G & 4G)", expanded=True):
    col_filter1, col_filter2, col_filter3 = st.columns([1, 1, 1.5])
    
    with col_filter1:
        filter_choice = st.radio("Bộ lọc kết quả:", ["Tất cả", "Chỉ các trạm ĐẠT", "Các trạm KHÔNG ĐẠT"], horizontal=True)
        
    with col_filter2:
        # Filter Khu vực
        avail_regions = sorted(list(set(r for r in dict_region.values() if r and r.upper() != 'NAN')))
        if not avail_regions: avail_regions = ["HCM", "VTU", "BDG"]
        region_choice = st.radio("Lọc Khu vực:", ["Tất cả"] + avail_regions, horizontal=True)
        
    with col_filter3:
        search_avg_stations = st.multiselect("🔍 Lọc nhanh theo Mã Trạm:", options=all_stations_ui, format_func=lambda x: f"{x} - {dict_station[x]}")
    
    mean_4g = df_4g_prep.groupby('MATCHED_ST')[list(active_kpis_4g.keys())].mean() if df_4g_prep is not None and not df_4g_prep.empty else pd.DataFrame()
    mean_3g = df_3g_prep.groupby('MATCHED_ST')[list(active_kpis_3g.keys())].mean() if df_3g_prep is not None and not df_3g_prep.empty else pd.DataFrame()

    len_4g = len(active_kpis_4g)
    len_3g = len(active_kpis_3g)

    table_header_html = f"""
    <div class='table-responsive-wrapper'>
    <table class='table-custom combined-table'>
    <thead>
        <tr>
            <th class='f-col1' rowspan='2'>MÃ TRẠM</th>
            <th class='f-col2' rowspan='2'>TÊN TRẠM</th>
            <th rowspan='2' style='text-align:center;'>KQ TỔNG</th>
            <th colspan='{len_4g}' class='th-group-4g'>🌐 HỆ THỐNG 4G</th>
            <th colspan='{len_3g}' class='th-group-3g'>📡 HỆ THỐNG 3G</th>
        </tr>
        <tr>
    """
    for rule in active_kpis_4g.values(): table_header_html += f"<th style='text-align:right;'>{rule['label']}</th>"
    for rule in active_kpis_3g.values(): table_header_html += f"<th style='text-align:right;'>{rule['label']}</th>"
    table_header_html += "</tr></thead><tbody>"

    rows_merged_html = []
    for st_code in all_stations_ui:
        # Áp dụng logic Lọc Khu Vực
        st_region = dict_region.get(st_code, "")
        if grouped_cr_key and st_code == grouped_cr_key: st_region = dict_region.get(bv_cr_codes[0], "")
        if region_choice != "Tất cả" and st_region != region_choice: continue

        if search_avg_stations and st_code not in search_avg_stations: continue
            
        st_name = dict_station.get(st_code, '')
        has_any_data = False
        station_failed = False
        cols_td = ""
        
        for c, rule in active_kpis_4g.items():
            val = mean_4g.loc[st_code, c] if (not mean_4g.empty and st_code in mean_4g.index and c in mean_4g.columns) else None
            is_ok, formatted_val = evaluate_val(val, rule)
            if is_ok is None: cols_td += "<td style='text-align:right; color:#9e9e9e;'>-</td>"
            else:
                has_any_data = True
                if not is_ok:
                    station_failed = True
                    cols_td += f"<td style='text-align:right; color:#d32f2f; font-weight:bold;'>{formatted_val}</td>"
                else: cols_td += f"<td style='text-align:right;'>{formatted_val}</td>"

        for c, rule in active_kpis_3g.items():
            val = mean_3g.loc[st_code, c] if (not mean_3g.empty and st_code in mean_3g.index and c in mean_3g.columns) else None
            is_ok, formatted_val = evaluate_val(val, rule)
            if is_ok is None: cols_td += "<td style='text-align:right; color:#9e9e9e;'>-</td>"
            else:
                has_any_data = True
                if not is_ok:
                    station_failed = True
                    cols_td += f"<td style='text-align:right; color:#d32f2f; font-weight:bold;'>{formatted_val}</td>"
                else: cols_td += f"<td style='text-align:right;'>{formatted_val}</td>"

        if not has_any_data: badge, kq_type = "<span class='badge-nodata'>Chưa có dữ liệu</span>", "NODATA"
        elif station_failed: badge, kq_type = "<span class='badge-fail'>FAIL</span>", "FAIL"
        else: badge, kq_type = "<span class='badge-pass'>ĐẠT</span>", "PASS"

        if filter_choice == "Chỉ các trạm ĐẠT" and kq_type != "PASS": continue
        if filter_choice == "Các trạm KHÔNG ĐẠT" and kq_type != "FAIL": continue

        rows_merged_html.append(f"<tr><td class='f-col1'><b>{st_code}</b></td><td class='f-col2'>{st_name}</td><td style='text-align:center;'>{badge}</td>{cols_td}</tr>")

    full_table_html = table_header_html + "".join(rows_merged_html) + "</tbody></table></div>"
    st.markdown(full_table_html, unsafe_allow_html=True)

# ----------------- 3. BỘ LỌC CHỌN TRẠM CỤ THỂ BẢNG CELL -----------------
selected_stations = st.multiselect(
    "🔍 Chọn Mã Trạm cần xem chi tiết Cell:",
    options=all_stations_ui,
    format_func=lambda x: f"{x} - {dict_station[x]}"
)
target_stations = selected_stations if selected_stations else all_stations_ui

tab4g, tab3g = st.tabs(["Chi tiết Cell 4G", "Chi tiết Cell 3G"])

def render_cell_details(df, active_kpis, cols_info, net_label):
    if df is None or df.empty:
        st.write(f"Chưa có dữ liệu {net_label}.")
        return

    cell_col, extra_cols = cols_info
    df_filtered = df[df['MATCHED_ST'].isin(target_stations)].copy()

    if df_filtered.empty:
        st.warning(f"Không có dữ liệu {net_label} cho trạm đã chọn!")
        return

    html_blocks = []
    for st_code, group in df_filtered.groupby('MATCHED_ST'):
        building_name = dict_station.get(st_code, '')
        cell_count = group[cell_col].nunique()
        group_mean = group[list(active_kpis.keys())].mean()
        
        kpi_headers_html = "".join([f"<th style='text-align:right;'>{rule['label']}</th>" for rule in active_kpis.values()])
        
        # Tùy biến Header cho 3G/4G
        if net_label == '4G': th_id = "<th class='f-id1'>ENODEB ID</th><th class='f-id2'>CELL ID</th><th class='f-cell-4g'>CELL</th>"
        else: th_id = "<th class='f-ci'>CI</th><th class='f-cell-3g'>CELL</th>"
        
        html_blocks.append(f"""
        <div class="header-station">
            <b style="font-size: 16px;">🔬 Chi Tiết Cell — {building_name} ({st_code})</b> 
            <span style="color: #666; font-size: 13px; margin-left: 10px;">• {cell_count} cells</span>
        </div>
        <div class='table-responsive-wrapper'>
        <table class='table-custom detail-table'><thead><tr>
            {th_id}<th style='text-align:center;'>KQ</th>
            {kpi_headers_html}
        </tr></thead><tbody>
        """)

        # TÍNH TRUNG BÌNH TOÀN TRẠM
        avg_cols_html = ""
        avg_is_pass = True
        for col_name, rule in active_kpis.items():
            val = group_mean.get(col_name)
            is_ok, formatted_val = evaluate_val(val, rule)
            if is_ok is False:
                avg_is_pass = False
                avg_cols_html += f"<td style='text-align:right; border-bottom: 2px solid #444;'><span style='color:#ff5252; font-weight:bold;'>{formatted_val}</span></td>"
            else:
                avg_cols_html += f"<td style='text-align:right; border-bottom: 2px solid #444;'><span style='color:#ffffff;'>{formatted_val}</span></td>"

        avg_badge = "<span class='badge-pass'>ĐẠT</span>" if avg_is_pass else "<span class='badge-fail'>FAIL</span>"
        
        if net_label == '4G':
            html_blocks.append(f"<tr style='background-color: #1a1a1a;'><td colspan='2' class='f-id1' style='background-color: #1a1a1a !important; border-bottom: 2px solid #444;'><span style='color:#ffffff;'><b>TRUNG BÌNH TRẠM</b></span></td><td class='f-cell-4g' style='background-color: #1a1a1a !important; border-bottom: 2px solid #444;'><span style='color:#ffffff;'>↳ Toàn Trạm</span></td><td style='text-align:center; border-bottom: 2px solid #444;'>{avg_badge}</td>{avg_cols_html}</tr>")
        else:
            html_blocks.append(f"<tr style='background-color: #1a1a1a;'><td class='f-ci' style='background-color: #1a1a1a !important; border-bottom: 2px solid #444;'><span style='color:#ffffff;'><b>TRUNG BÌNH TRẠM</b></span></td><td class='f-cell-3g' style='background-color: #1a1a1a !important; border-bottom: 2px solid #444;'><span style='color:#ffffff;'>↳ Toàn Trạm</span></td><td style='text-align:center; border-bottom: 2px solid #444;'>{avg_badge}</td>{avg_cols_html}</tr>")

        # HIỂN THỊ TỪNG DÒNG (CELL)
        col_enodeb = extra_cols.get('ENODEB')
        col_cellid = extra_cols.get('CELLID')
        col_ci = extra_cols.get('CI')

        for _, row in group.iterrows():
            cell_name = str(row[cell_col])
            cols_html = ""
            row_is_pass = True
            
            for col_name, rule in active_kpis.items():
                is_ok, formatted_val = evaluate_val(row.get(col_name), rule)
                if is_ok is False:
                    row_is_pass = False
                    cols_html += f"<td style='text-align:right;' class='kpi-fail'>{formatted_val}</td>"
                else: cols_html += f"<td style='text-align:right;'>{formatted_val}</td>"

            status_badge = "<span class='badge-pass'>ĐẠT</span>" if row_is_pass else "<span class='badge-fail'>FAIL</span>"
            
            # Xử lý các cột ID 4G/3G
            if net_label == '4G':
                val_en = str(row[col_enodeb]).replace('.0', '') if col_enodeb and not pd.isna(row[col_enodeb]) else "-"
                val_cid = str(row[col_cellid]).replace('.0', '') if col_cellid and not pd.isna(row[col_cellid]) else "-"
                if val_en == 'nan': val_en = "-"
                if val_cid == 'nan': val_cid = "-"
                html_blocks.append(f"<tr><td class='f-id1'>{val_en}</td><td class='f-id2'>{val_cid}</td><td class='f-cell-4g'>↳ {cell_name}</td><td style='text-align:center;'>{status_badge}</td>{cols_html}</tr>")
            else:
                val_ci = str(row[col_ci]).replace('.0', '') if col_ci and not pd.isna(row[col_ci]) else "-"
                if val_ci == 'nan': val_ci = "-"
                html_blocks.append(f"<tr><td class='f-ci'>{val_ci}</td><td class='f-cell-3g'>↳ {cell_name}</td><td style='text-align:center;'>{status_badge}</td>{cols_html}</tr>")

        html_blocks.append("</tbody></table></div>")

    st.markdown("".join(html_blocks), unsafe_allow_html=True)

with tab4g:
    render_cell_details(df_4g_prep, active_kpis_4g, cols_4g, "4G")

with tab3g:
    render_cell_details(df_3g_prep, active_kpis_3g, cols_3g, "3G")
# AUTO_REBOOT_TIME: 1791811182.4730518
