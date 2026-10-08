import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime

st.set_page_config(page_title="Đánh giá KPI Trạm 3G/4G", layout="wide")

# 1. NHÚNG CSS VÀ JS (ĐÃ FIX LỖI KÉO CHUỘT VÀ KHOẢNG TRẮNG)
st.markdown("""
<style>
    .kpi-fail { color: #d32f2f; font-weight: bold; }
    .kpi-pass { color: #2e7d32; }
    .badge-pass { background-color: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-fail { background-color: #ffebee; color: #c62828; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-nodata { background-color: #f5f5f5; color: #757575; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    
    .table-responsive-wrapper {
        width: 100%;
        overflow-x: auto;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        margin-top: 10px;
        margin-bottom: 15px;
        cursor: grab;
        user-select: none;
    }
    .table-responsive-wrapper:active { cursor: grabbing; }
    .table-custom { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 13px; }
    .table-custom th { background-color: #f4f6f8; color: #333; text-align: left; padding: 8px 10px; border-bottom: 2px solid #ddd; vertical-align: top; white-space: nowrap; }
    .table-custom td { padding: 8px 10px; border-bottom: 1px solid #eee; white-space: nowrap; }
    .header-station { background-color: #f0f7ff; padding: 12px 16px; border-left: 5px solid #1976d2; border-radius: 4px; margin: 15px 0 5px 0; }
    .kpi-target { font-size: 11px; color: #1976d2; display: block; margin-top: 2px; }
</style>

<svg style="display:none;" onload="
    function enableDragScroll() {
        const sliders = document.querySelectorAll('.table-responsive-wrapper');
        sliders.forEach(slider => {
            if(slider.dataset.dragEnabled === 'true') return;
            slider.dataset.dragEnabled = 'true';
            let isDown = false;
            let startX;
            let scrollLeft;
            slider.addEventListener('mousedown', (e) => {
                isDown = true;
                slider.style.cursor = 'grabbing';
                startX = e.pageX - slider.offsetLeft;
                scrollLeft = slider.scrollLeft;
            });
            slider.addEventListener('mouseleave', () => { isDown = false; slider.style.cursor = 'grab'; });
            slider.addEventListener('mouseup', () => { isDown = false; slider.style.cursor = 'grab'; });
            slider.addEventListener('mousemove', (e) => {
                if(!isDown) return;
                e.preventDefault();
                const x = e.pageX - slider.offsetLeft;
                const walk = (x - startX) * 1.5;
                slider.scrollLeft = scrollLeft - walk;
            });
        });
    }
    setInterval(enableDragScroll, 1000);
"></svg>
""", unsafe_allow_html=True)

# ----------------- ĐỊNH NGHĨA CHỈ TIÊU KPI -----------------
KPI_THRESHOLDS_4G = {
    'CSSR': {'min': 98.0, 'label': 'CSSR 4G (%)<br><span class="kpi-target">≥ 98%</span>'},
    'SERVICEDROPALL': {'max': 1.5, 'label': 'DROP 4G (%)<br><span class="kpi-target">≤ 1.5%</span>'},
    'INTRAFREQUENCYHO': {'min': 98.0, 'label': 'INTRA HO (%)<br><span class="kpi-target">≥ 98%</span>'},
    'INTERFREQUENCYHO': {'min': 95.0, 'label': 'INTER HO (%)<br><span class="kpi-target">≥ 95%</span>'},
    'HOSRIRATLTEWCDMA': {'min': 90.0, 'label': 'LTE-UMTS (%)<br><span class="kpi-target">≥ 90%</span>'},
    'CSFBSSR': {'min': 98.0, 'label': 'CSFB SR (%)<br><span class="kpi-target">≥ 98%</span>'},
}

KPI_THRESHOLDS_3G = {
    'CSVOICECSS': {'min': 99.0, 'label': 'CSSR Voice (%)<br><span class="kpi-target">≥ 99%</span>'},
    'DCR': {'max': 1.0, 'label': 'Drop Voice (%)<br><span class="kpi-target">≤ 1%</span>'},
    'SOFTHOSR': {'min': 99.0, 'label': 'S.HOSR (%)<br><span class="kpi-target">≥ 99%</span>'},
    'SINTERFREQH': {'min': 95.0, 'label': 'IF HOSR (%)<br><span class="kpi-target">≥ 95%</span>'},
    'IRATHOSR': {'min': 95.0, 'label': 'IRAT HOSR (%)<br><span class="kpi-target">≥ 95%</span>'},
    'PSCSSR': {'min': 98.0, 'label': 'ASR PS (%)<br><span class="kpi-target">≥ 98%</span>'},
    'PSDCR': {'max': 1.0, 'label': 'DR PS (%)<br><span class="kpi-target">≤ 1%</span>'},
    'SOFTHOSRPS': {'min': 99.0, 'label': 'PS Soft HO (%)<br><span class="kpi-target">≥ 99%</span>'},
    'V2INTERFREQ': {'min': 93.0, 'label': 'PS Inter-Freq (%)<br><span class="kpi-target">≥ 93%</span>'},
}

def clean_col_name(c):
    return re.sub(r'[^a-zA-Z0-9]', '', str(c)).upper()

def clean_time_string(raw_time_str):
    if not raw_time_str:
        return ""
    dates = re.findall(r'\b\d{1,2}/\d{1,2}/\d{4}\b', str(raw_time_str))
    if len(dates) >= 2:
        return f"{dates[0]} - {dates[1]}"
    elif len(dates) == 1:
        return dates[0]
    return str(raw_time_str).strip()

def evaluate_val(val, rule):
    if pd.isna(val) or val is None or str(val).strip() in ['', 'nan', 'None']:
        return None, "null"
    try:
        v = float(val)
    except:
        return None, str(val)
    
    is_ok = not (('min' in rule and v < rule['min']) or ('max' in rule and v > rule['max']))
    return is_ok, f"{v:.2f}"

def clean_numeric_series(series):
    s = series.astype(str).str.replace('%', '', regex=False).str.replace(',', '.', regex=False).str.strip()
    return pd.to_numeric(s, errors='coerce')

@st.cache_data
def load_excel_data(file):
    return pd.read_excel(file)

@st.cache_data
def parse_mapping_file(df_map):
    mapping = {}
    ma_cols = [c for c in df_map.columns if 'MÃ' in str(c).upper() or 'MA TR' in str(c).upper() or 'MÃ TR' in str(c).upper()]
    ten_cols = [c for c in df_map.columns if 'TÊN' in str(c).upper() or 'TEN TR' in str(c).upper() or 'TÊN TR' in str(c).upper()]
    
    if ma_cols and ten_cols:
        for m_col, t_col in zip(ma_cols, ten_cols):
            for _, row in df_map.iterrows():
                m = str(row[m_col]).strip().upper()
                t = str(row[t_col]).strip()
                if m != 'NAN' and len(m) >= 3 and m.lower() != 'nan':
                    mapping[m] = t
    else:
        for i in range(len(df_map.columns) - 1):
            for _, row in df_map.iterrows():
                m = str(row.iloc[i]).strip().upper()
                t = str(row.iloc[i+1]).strip()
                if m != 'NAN' and len(m) >= 4 and not m.isnumeric() and ' ' not in m:
                    mapping[m] = t
    return mapping

# ----------------- TỰ ĐỘNG TÌM FILE TỪ GITHUB (KHÔNG DÙNG UPLOADER) -----------------
def tim_file_excel(tu_khoa):
    for f in os.listdir('.'):
        if f.endswith(('.xlsx', '.xls')) and not f.startswith('~$'):
            if tu_khoa.upper() in f.upper():
                return f
    return None

file_3g = tim_file_excel("3G")
file_4g = tim_file_excel("4G")
file_mapping = tim_file_excel("TRAM") or tim_file_excel("MÃ") or tim_file_excel("MA")

if not (file_mapping and file_3g and file_4g):
    st.title("📊 Kiểm Tra & Đánh Giá KPI Trạm Theo Tuần")
    st.error("⚠️ Hệ thống chưa tìm đủ 3 file hoặc tên file không chứa đúng từ khóa ('3G', '4G', 'TRAM'). Vui lòng chờ Admin cập nhật!")
    st.stop()

try:
    df_map_raw = load_excel_data(file_mapping)
    dict_station = parse_mapping_file(df_map_raw)
except Exception as e:
    st.error(f"Lỗi đọc file Danh mục: {e}")
    st.stop()

if not dict_station:
    st.error("Không trích xuất được Mã Trạm từ file danh mục!")
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
            if grouped_cr_key and st_code in bv_cr_codes:
                return grouped_cr_key
            return st_code
    return None

def prepare_net_df(file_data, kpi_rules):
    if not file_data:
        return None, {}, None, ""
    df = load_excel_data(file_data)
    
    cell_col = None
    for c in df.columns:
        c_upper = str(c).upper()
        if 'CELL NAME' in c_upper or 'TÊN CELL' in c_upper or c_upper == 'CELL':
            cell_col = c
            break
    if not cell_col:
        cell_col = next((c for c in df.columns if 'CELL' in str(c).upper()), None)
    
    time_col = next((c for c in df.columns if 'THỜI' in str(c).upper() or 'TIME' in str(c).upper()), None)
    
    time_str_sample = ""
    if time_col and not df.empty:
        non_null_time = df[time_col].dropna()
        if not non_null_time.empty:
            time_str_sample = clean_time_string(non_null_time.iloc[0])

    if not cell_col:
        return None, {}, None, time_str_sample

    df['MATCHED_ST'] = df[cell_col].apply(match_station_fn)
    df = df.dropna(subset=['MATCHED_ST'])

    active_kpis = {}
    for k_clean, rule in kpi_rules.items():
        for c in df.columns:
            if k_clean in clean_col_name(c):
                active_kpis[c] = rule
                df[c] = clean_numeric_series(df[c])
                break

    return df, active_kpis, (cell_col, time_col), time_str_sample

df_4g_prep, active_kpis_4g, cols_4g, time_4g_sample = prepare_net_df(file_4g, KPI_THRESHOLDS_4G)
df_3g_prep, active_kpis_3g, cols_3g, time_3g_sample = prepare_net_df(file_3g, KPI_THRESHOLDS_3G)

display_time = time_4g_sample or time_3g_sample
if not display_time:
    display_time = datetime.now().strftime("%d/%m/%Y")

# 1. TIÊU ĐỀ 
st.title(f"📊 Kiểm Tra & Đánh Giá KPI Trạm Theo Tuần ({display_time})")

# ----------------- 2. BẢNG TRUNG BÌNH GỘP BỌC TRỌN VẸN -----------------
with st.expander(f"📊 XEM CHI TIẾT TRUNG BÌNH CỦA {len(all_stations_ui)} TRẠM (GỘP CHUNG 3G & 4G)", expanded=True):
    filter_choice = st.radio(
        "Bộ lọc kết quả trạm:", 
        ["Tất cả", "Chỉ các trạm ĐẠT", "Các trạm KHÔNG ĐẠT", "Chưa có dữ liệu"], 
        horizontal=True
    )
    
    mean_4g = df_4g_prep.groupby('MATCHED_ST')[list(active_kpis_4g.keys())].mean() if df_4g_prep is not None and not df_4g_prep.empty else pd.DataFrame()
    mean_3g = df_3g_prep.groupby('MATCHED_ST')[list(active_kpis_3g.keys())].mean() if df_3g_prep is not None and not df_3g_prep.empty else pd.DataFrame()

    table_header_html = """
    <div class='table-responsive-wrapper'>
    <table class='table-custom'>
    <thead>
        <tr>
            <th>MÃ TRẠM</th>
            <th>TÊN TRẠM</th>
            <th style='text-align:center;'>KQ TỔNG</th>
    """
    for rule in active_kpis_4g.values():
        table_header_html += f"<th style='text-align:right;'>{rule['label']}</th>"
    for rule in active_kpis_3g.values():
        table_header_html += f"<th style='text-align:right;'>{rule['label']}</th>"
    table_header_html += "</tr></thead><tbody>"

    rows_merged_html = []
    
    for st_code in all_stations_ui:
        st_name = dict_station.get(st_code, '')
        has_any_data = False
        station_failed = False
        cols_td = ""
        
        # Duyệt 4G
        for c, rule in active_kpis_4g.items():
            val = mean_4g.loc[st_code, c] if (not mean_4g.empty and st_code in mean_4g.index and c in mean_4g.columns) else None
            is_ok, formatted_val = evaluate_val(val, rule)
            if is_ok is None:
                cols_td += "<td style='text-align:right; color:#9e9e9e;'>-</td>"
            else:
                has_any_data = True
                if not is_ok:
                    station_failed = True
                    cols_td += f"<td style='text-align:right; color:#d32f2f; font-weight:bold;'>{formatted_val}</td>"
                else:
                    cols_td += f"<td style='text-align:right;'>{formatted_val}</td>"

        # Duyệt 3G
        for c, rule in active_kpis_3g.items():
            val = mean_3g.loc[st_code, c] if (not mean_3g.empty and st_code in mean_3g.index and c in mean_3g.columns) else None
            is_ok, formatted_val = evaluate_val(val, rule)
            if is_ok is None:
                cols_td += "<td style='text-align:right; color:#9e9e9e;'>-</td>"
            else:
                has_any_data = True
                if not is_ok:
                    station_failed = True
                    cols_td += f"<td style='text-align:right; color:#d32f2f; font-weight:bold;'>{formatted_val}</td>"
                else:
                    cols_td += f"<td style='text-align:right;'>{formatted_val}</td>"

        if not has_any_data:
            kq_type = "NODATA"
            badge = "<span class='badge-nodata'>Chưa có dữ liệu</span>"
        elif station_failed:
            kq_type = "FAIL"
            badge = "<span class='badge-fail'>FAIL</span>"
        else:
            kq_type = "PASS"
            badge = "<span class='badge-pass'>ĐẠT</span>"

        if filter_choice == "Chỉ các trạm ĐẠT" and kq_type != "PASS": continue
        if filter_choice == "Các trạm KHÔNG ĐẠT" and kq_type != "FAIL": continue
        if filter_choice == "Chưa có dữ liệu" and kq_type != "NODATA": continue

        rows_merged_html.append(f"<tr><td><b>{st_code}</b></td><td>{st_name}</td><td style='text-align:center;'>{badge}</td>{cols_td}</tr>")

    full_table_html = table_header_html + "".join(rows_merged_html) + "</tbody></table></div>"
    st.markdown(full_table_html, unsafe_allow_html=True)

# ----------------- 3. BỘ LỌC CHỌN TRẠM CỤ THỂ -----------------
selected_stations = st.multiselect(
    "🔍 Chọn Mã Trạm cần xem chi tiết Cell (để trống sẽ hiển thị tất cả các trạm có dữ liệu):",
    options=all_stations_ui,
    format_func=lambda x: f"{x} - {dict_station[x]}"
)
target_stations = selected_stations if selected_stations else all_stations_ui

tab4g, tab3g = st.tabs(["Chi tiết Cell 4G", "Chi tiết Cell 3G"])

def render_cell_details(df, active_kpis, cols_info, net_label):
    if df is None or df.empty:
        st.write(f"Chưa có dữ liệu {net_label}.")
        return

    cell_col, time_col = cols_info
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
        
        html_blocks.append(f"""
        <div class="header-station">
            <b style="font-size: 16px;">🔬 Chi Tiết Cell — {building_name} ({st_code})</b> 
            <span style="color: #666; font-size: 13px; margin-left: 10px;">• {cell_count} cells</span>
        </div>
        <div class='table-responsive-wrapper'>
        <table class='table-custom'><thead><tr>
            <th>THỜI GIAN</th><th>CELL</th><th style='text-align:center;'>KQ</th>
            {kpi_headers_html}
        </tr></thead><tbody>
        """)

        # DÒNG TRUNG BÌNH TOÀN TRẠM (NỀN ĐEN - ĐÃ FIX MÀU ĐỎ CHO CHỈ SỐ RỚT)
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
        html_blocks.append(f"<tr style='background-color: #1a1a1a;'><td style='border-bottom: 2px solid #444;'><span style='color:#ffffff;'>📅 <b>TRUNG BÌNH TRẠM</b></span></td><td style='border-bottom: 2px solid #444;'><span style='color:#ffffff;'>↳ Toàn Trạm</span></td><td style='text-align:center; border-bottom: 2px solid #444;'>{avg_badge}</td>{avg_cols_html}</tr>")

        # CÁC DÒNG CELL CON
        for _, row in group.iterrows():
            time_val = clean_time_string(row[time_col]) if time_col else ""
            cell_name = str(row[cell_col])
            cols_html = ""
            row_is_pass = True
            
            for col_name, rule in active_kpis.items():
                is_ok, formatted_val = evaluate_val(row.get(col_name), rule)
                if is_ok is False:
                    row_is_pass = False
                    cols_html += f"<td style='text-align:right;' class='kpi-fail'>{formatted_val}</td>"
                else:
                    cols_html += f"<td style='text-align:right;'>{formatted_val}</td>"

            status_badge = "<span class='badge-pass'>ĐẠT</span>" if row_is_pass else "<span class='badge-fail'>FAIL</span>"
            html_blocks.append(f"<tr><td>📅 {time_val}</td><td>↳ {cell_name}</td><td style='text-align:center;'>{status_badge}</td>{cols_html}</tr>")

        html_blocks.append("</tbody></table></div>")

    st.markdown("".join(html_blocks), unsafe_allow_html=True)

with tab4g:
    render_cell_details(df_4g_prep, active_kpis_4g, cols_4g, "4G")

with tab3g:
    render_cell_details(df_3g_prep, active_kpis_3g, cols_3g, "3G")