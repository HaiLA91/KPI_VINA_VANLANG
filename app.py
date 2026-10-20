import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Đánh giá KPI Trạm 3G/4G", layout="wide")

# 1. NHÚNG CSS TỐI ƯU CHO CẢ PC VÀ MOBILE
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    html, body, .stApp { max-width: 100vw !important; overflow-x: hidden !important; }

    /* Tiêu đề chính gọn gàng hơn */
    .main-title { font-size: 22px; font-weight: bold; margin-bottom: 12px; color: #fff; line-height: 1.3; }

    .kpi-fail { color: #ff5252; font-weight: bold; }
    .kpi-pass { color: #2e7d32; }
    .badge-pass { background-color: #e8f5e9; color: #2e7d32; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .badge-fail { background-color: #ffebee; color: #c62828; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    .badge-nodata { background-color: #f5f5f5; color: #757575; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
    
    .table-responsive-wrapper {
        width: 100%; max-width: 100vw; max-height: 72vh; 
        overflow-x: auto; overflow-y: auto; 
        border: 1px solid #444; border-radius: 6px;
        margin-top: 8px; margin-bottom: 15px;
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
    .table-custom td { padding: 7px 10px; border-bottom: 1px solid #333; white-space: nowrap; }
    
    /* Đảm bảo thead luôn nổi lên trên tbody khi cuộn dọc */
    .table-custom thead { position: sticky; top: 0; z-index: 10; }
    .combined-table thead tr:first-child th { top: 0; z-index: 10; height: 40px; font-size: 13px; font-weight: bold; }
    .combined-table thead tr:nth-child(2) th { top: 40px; z-index: 9; }
    .detail-table thead tr:first-child th { top: 0; z-index: 10; }

    .th-group-4g { background-color: #0288d1 !important; color: #ffffff !important; text-align: center !important; border-right: 3px solid #ffeb3b !important; }
    .th-group-3g { background-color: #e65100 !important; color: #ffffff !important; text-align: center !important; }

    /* ==========================================================
       CẤU HÌNH FREEZE CỘT TRÊN MÁY TÍNH (PC)
       ========================================================== */
    .f-hist-tram { position: sticky !important; left: 0 !important; min-width: 190px; max-width: 190px; white-space: normal !important; word-wrap: break-word; border-right: 2px solid #1976d2 !important; z-index: 4; }
    th.f-hist-tram { z-index: 15 !important; background-color: #1e293b !important; top: 0 !important; }
    td.f-hist-tram { background-color: #1e1e1e !important; color: #eee !important; }

    .f-col1 { position: sticky !important; left: 0 !important; min-width: 95px; max-width: 95px; white-space: normal !important; word-wrap: break-word; z-index: 4; }
    .f-col2 { position: sticky !important; left: 95px !important; min-width: 150px; max-width: 150px; white-space: normal !important; word-wrap: break-word; border-right: 2px solid #1976d2 !important; z-index: 4; }
    th.f-col1, th.f-col2 { z-index: 15 !important; background-color: #1e293b !important; top: 0 !important; } 
    td.f-col1, td.f-col2 { background-color: #1e1e1e !important; color: #eee !important; }

    .f-cell-sticky { position: sticky !important; left: 0 !important; min-width: 175px; max-width: 175px; white-space: normal !important; word-wrap: break-word; border-right: 2px solid #1976d2 !important; z-index: 4; }
    th.f-cell-sticky { z-index: 15 !important; background-color: #1e293b !important; top: 0 !important; }
    td.f-cell-sticky { background-color: #1e1e1e !important; color: #eee !important; }

    .header-station { background-color: #1e293b; padding: 10px 14px; border-left: 4px solid #1976d2; border-radius: 4px; margin: 12px 0 4px 0; color: #fff; }
    .kpi-target { font-size: 10px; color: #ffeb3b; display: block; margin-top: 2px; }

    /* ==========================================================
       TỐI ƯU HÓA RIÊNG CHO ĐIỆN THOẠI (MÀN HÌNH <= 768px)
       ========================================================== */
    @media screen and (max-width: 768px) {
        /* Giữ padding-top 3.5rem để không bị thanh Header/Fork của Streamlit che mất phần tử đầu tiên */
        .block-container { 
            padding-left: 0.5rem !important; 
            padding-right: 0.5rem !important; 
            padding-top: 3.5rem !important; 
        }
        .main-title { font-size: 16px !important; margin-bottom: 10px !important; }
        
        .table-custom { font-size: 11.5px !important; }
        .table-custom th, .table-custom td { padding: 5px 6px !important; }
        .combined-table thead tr:first-child th { height: 32px; font-size: 11.5px; }
        .combined-table thead tr:nth-child(2) th { top: 32px; }

        .f-hist-tram { min-width: 125px !important; max-width: 125px !important; font-size: 11px !important; }

        .f-col1 { min-width: 85px !important; max-width: 85px !important; border-right: 2px solid #1976d2 !important; }
        .f-col2 { position: static !important; min-width: 120px !important; max-width: 140px !important; border-right: 1px solid #333 !important; }
        th.f-col2 { z-index: 9 !important; }

        .f-cell-sticky { min-width: 130px !important; max-width: 130px !important; font-size: 11px !important; }
        
        .header-station { padding: 8px 10px; font-size: 13px; }
    }
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
def load_excel_data_with_mtime(file_path, file_mtime, header_keywords=None, sheet_name=0): 
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    if header_keywords:
        cols_str = [str(c).upper().replace(' ', '') for c in df.columns]
        if not any(any(kw in c for kw in header_keywords) for c in cols_str):
            for i in range(min(15, len(df))):
                row_vals = [str(x).upper().replace(' ', '') for x in df.iloc[i].values]
                if any(any(kw in v for kw in header_keywords) for v in row_vals):
                    df.columns = df.iloc[i]
                    df = df.iloc[i+1:].reset_index(drop=True)
                    break
    return df

@st.cache_data
def parse_mapping_file(df_map):
    df_map = df_map.ffill()
    mapping = {}
    region_mapping = {}
    
    ma_cols = [c for c in df_map.columns if 'MÃ' in str(c).upper() or 'MA TR' in str(c).upper() or 'MÃ TR' in str(c).upper()]
    ten_cols = [c for c in df_map.columns if 'TÊN' in str(c).upper() or 'TEN TR' in str(c).upper() or 'TÊN TR' in str(c).upper()]
    
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
file_tonghop = tim_file_excel("TONGHOP")

if not (file_mapping and file_3g and file_4g):
    st.markdown("<div class='main-title'>📊 Kiểm Tra & Đánh Giá KPI VINAPHONE Tuần</div>", unsafe_allow_html=True)
    st.error("⚠️ Chưa tìm đủ file '3G', '4G', 'TRAM'.")
    st.stop()

# ----------------- ĐỌC DỮ LIỆU TỪ EXCEL -----------------
try:
    mtime_map = os.path.getmtime(file_mapping) if os.path.exists(file_mapping) else 0
    df_map_raw = load_excel_data_with_mtime(file_mapping, mtime_map, header_keywords=['MÃTR', 'MATR', 'MÃ', 'STT'], sheet_name=0)
    dict_station, dict_region = parse_mapping_file(df_map_raw)
    
    df_history_raw = pd.DataFrame()
    if file_tonghop:
        mtime_th = os.path.getmtime(file_tonghop) if os.path.exists(file_tonghop) else 0
        try:
            df_history_raw = load_excel_data_with_mtime(file_tonghop, mtime_th, header_keywords=['TÊNTRẠM', 'TÊN TRẠM', 'STT'], sheet_name=0)
        except Exception as e:
            st.warning(f"Lỗi đọc file Tổng hợp: {e}")
            
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
    df = load_excel_data_with_mtime(file_data, mtime, header_keywords=['CELL', 'ENODEB', 'CI'], sheet_name=0)
    
    cell_col = next((c for c in df.columns if 'CELL NAME' in str(c).upper() or 'TÊN CELL' in str(c).upper() or str(c).upper() == 'CELL'), None)
    if not cell_col: cell_col = next((c for c in df.columns if 'CELL' in str(c).upper()), None)
    
    time_col = next((c for c in df.columns if 'THỜI' in str(c).upper() or 'TIME' in str(c).upper()), None)
    
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

# ----------------- TÍNH TOÁN TRUNG BÌNH & KẾT QUẢ TỔNG -----------------
mean_4g = df_4g_prep.groupby('MATCHED_ST')[list(active_kpis_4g.keys())].mean() if df_4g_prep is not None and not df_4g_prep.empty else pd.DataFrame()
mean_3g = df_3g_prep.groupby('MATCHED_ST')[list(active_kpis_3g.keys())].mean() if df_3g_prep is not None and not df_3g_prep.empty else pd.DataFrame()

station_results_by_name = {}

for st_code in all_stations_ui:
    has_any_data = False
    station_failed = False
    st_name = str(dict_station.get(st_code, '')).strip().upper()
    
    for c, rule in active_kpis_4g.items():
        val = mean_4g.loc[st_code, c] if (not mean_4g.empty and st_code in mean_4g.index and c in mean_4g.columns) else None
        is_ok, _ = evaluate_val(val, rule)
        if is_ok is not None:
            has_any_data = True
            if not is_ok: station_failed = True

    for c, rule in active_kpis_3g.items():
        val = mean_3g.loc[st_code, c] if (not mean_3g.empty and st_code in mean_3g.index and c in mean_3g.columns) else None
        is_ok, _ = evaluate_val(val, rule)
        if is_ok is not None:
            has_any_data = True
            if not is_ok: station_failed = True

    if not has_any_data: kq_type = "NODATA"
    elif station_failed: kq_type = "Fail"
    else: kq_type = "Pass"
    
    station_results_by_name[st_name] = kq_type


# =====================================================================================
# 1. ĐƯA TIÊU ĐỀ CHÍNH LÊN ĐẦU TIÊN
# =====================================================================================
st.markdown(f"<div class='main-title'>📊 Đánh Giá KPI VINAPHONE Tuần ({display_time})</div>", unsafe_allow_html=True)

# =====================================================================================
# 2. BẢNG LỊCH SỬ CÁC TUẦN (NẰM NGAY DƯỚI TIÊU ĐỀ, KHÔNG BỊ CHE KHUẤT)
# =====================================================================================
if not df_history_raw.empty:
    with st.expander("📊 LỊCH SỬ ĐÁNH GIÁ CÁC TUẦN TRƯỚC", expanded=False):
        ten_tram_col = next((c for c in df_history_raw.columns if 'TÊN' in str(c).upper()), None)
        khu_vuc_col = next((c for c in df_history_raw.columns if 'KHU' in str(c).upper()), None)
        
        if ten_tram_col:
            df_hist = df_history_raw.dropna(subset=[ten_tram_col]).copy()
            week_cols = [c for c in df_hist.columns if 'TUẦN' in str(c).upper()]
            df_hist[week_cols] = df_hist[week_cols].astype(object)
            last_filled_week = None
            first_empty_week = None
            
            for wc in week_cols:
                col_vals = df_hist[wc].astype(str).str.strip().str.upper()
                if col_vals.isin(['PASS', 'FAIL']).any():
                    last_filled_week = wc
                else:
                    first_empty_week = wc
                    break
            
            is_duplicate = False
            if last_filled_week and first_empty_week:
                differences = 0
                valid_comparisons = 0
                for idx, row in df_hist.iterrows():
                    tram_name = str(row[ten_tram_col]).strip().upper()
                    if tram_name in station_results_by_name and station_results_by_name[tram_name] != "NODATA":
                        current_val = station_results_by_name[tram_name].upper()
                        prev_val = str(row[last_filled_week]).strip().upper()
                        
                        if prev_val in ['PASS', 'FAIL']:
                            valid_comparisons += 1
                            if current_val != prev_val:
                                differences += 1
                
                if valid_comparisons > 0 and differences == 0:
                    is_duplicate = True

            tuan_can_dien = None
            if is_duplicate:
                st.info(f"💡 Dữ liệu tính toán hoàn toàn giống với **{last_filled_week}**. Hệ thống tự động bỏ qua ghi đè.")
            elif first_empty_week:
                tuan_can_dien = first_empty_week
                # Ép kiểu cột trống sang object để cho phép ghi chữ "Pass"/"Fail" mà không bị lỗi TypeError
                df_hist[tuan_can_dien] = df_hist[tuan_can_dien].astype(object)
                for idx, row in df_hist.iterrows():
                    tram_name = str(row[ten_tram_col]).strip().upper()
                    if tram_name in station_results_by_name and station_results_by_name[tram_name] != "NODATA":
                        df_hist.at[idx, tuan_can_dien] = station_results_by_name[tram_name]
            else:
                st.warning("⚠️ File Tổng hợp đã được điền kín các tuần. Không còn cột trống để ánh xạ!")

            hist_header_html = """
            <div class='table-responsive-wrapper'>
            <table class='table-custom detail-table'>
            <thead>
                <tr>
                    <th class='f-hist-tram'>TÊN TRẠM</th>
                    <th>KHU VỰC</th>
            """
            for wc in week_cols:
                if wc == tuan_can_dien: 
                    hist_header_html += f"<th style='text-align:center; color:#ffeb3b;'>{wc} (Mới)</th>"
                else: 
                    hist_header_html += f"<th style='text-align:center;'>{wc}</th>"
            hist_header_html += "</tr></thead><tbody>"
            
            hist_rows_html = []
            for _, row in df_hist.iterrows():
                tram_name = str(row[ten_tram_col]).strip()
                khu_vuc = str(row[khu_vuc_col]).strip() if khu_vuc_col else ""
                
                td_html = ""
                for wc in week_cols:
                    val = str(row[wc]).strip().upper()
                    if val == 'PASS':
                        td_html += "<td style='text-align:center;'><span class='badge-pass'>PASS</span></td>"
                    elif val == 'FAIL':
                        td_html += "<td style='text-align:center;'><span class='badge-fail'>FAIL</span></td>"
                    else:
                        display_val = row[wc] if pd.notna(row[wc]) else '-'
                        td_html += f"<td style='text-align:center; color:#9e9e9e;'>{display_val}</td>"
                
                hist_rows_html.append(f"<tr><td class='f-hist-tram'><b>{tram_name}</b></td><td>{khu_vuc}</td>{td_html}</tr>")
                
            full_hist_html = hist_header_html + "".join(hist_rows_html) + "</tbody></table></div>"
            st.markdown(full_hist_html, unsafe_allow_html=True)

            if tuan_can_dien:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_hist.to_excel(writer, index=False, sheet_name='TongHop')
                excel_data = output.getvalue()
                st.download_button(
                    label=f"📥 Tải xuống file Tổng Hợp đã tự động điền {tuan_can_dien}", 
                    data=excel_data, 
                    file_name="Tonghop_DaCapNhat.xlsx", 
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

elif file_tonghop is None:
    st.info("💡 Không tìm thấy file 'Tonghop.xlsx' trong thư mục để hiển thị lịch sử.")


# =====================================================================================
# 3. BẢNG TRUNG BÌNH GỘP
# =====================================================================================
with st.expander(f"📊 XEM CHI TIẾT TRUNG BÌNH CỦA {len(all_stations_ui)} TRẠM", expanded=False):
    col_filter1, col_filter2, col_filter3 = st.columns([1, 1, 1.5])
    
    with col_filter1:
        filter_choice = st.radio("Bộ lọc kết quả:", ["Tất cả", "Chỉ các trạm ĐẠT", "Các trạm KHÔNG ĐẠT"], horizontal=True)
        
    with col_filter2:
        avail_regions = sorted(list(set(r for r in dict_region.values() if r and r.upper() != 'NAN')))
        if not avail_regions: avail_regions = ["HCM", "VTU", "BDG"]
        region_choice = st.radio("Lọc Khu vực:", ["Tất cả"] + avail_regions, horizontal=True)
        
    with col_filter3:
        search_avg_stations = st.multiselect("🔍 Lọc nhanh theo Mã Trạm:", options=all_stations_ui, format_func=lambda x: f"{x} - {dict_station[x]}")

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
                    cols_td += f"<td style='text-align:right; color:#ff5252; font-weight:bold;'>{formatted_val}</td>"
                else: cols_td += f"<td style='text-align:right;'>{formatted_val}</td>"

        for c, rule in active_kpis_3g.items():
            val = mean_3g.loc[st_code, c] if (not mean_3g.empty and st_code in mean_3g.index and c in mean_3g.columns) else None
            is_ok, formatted_val = evaluate_val(val, rule)
            if is_ok is None: cols_td += "<td style='text-align:right; color:#9e9e9e;'>-</td>"
            else:
                has_any_data = True
                if not is_ok:
                    station_failed = True
                    cols_td += f"<td style='text-align:right; color:#ff5252; font-weight:bold;'>{formatted_val}</td>"
                else: cols_td += f"<td style='text-align:right;'>{formatted_val}</td>"

        if not has_any_data: badge, kq_type = "<span class='badge-nodata'>Chưa có DL</span>", "NODATA"
        elif station_failed: badge, kq_type = "<span class='badge-fail'>FAIL</span>", "FAIL"
        else: badge, kq_type = "<span class='badge-pass'>ĐẠT</span>", "PASS"

        if filter_choice == "Chỉ các trạm ĐẠT" and kq_type != "PASS": continue
        if filter_choice == "Các trạm KHÔNG ĐẠT" and kq_type != "FAIL": continue

        rows_merged_html.append(f"<tr><td class='f-col1'><b>{st_code}</b></td><td class='f-col2'>{st_name}</td><td style='text-align:center;'>{badge}</td>{cols_td}</tr>")

    full_table_html = table_header_html + "".join(rows_merged_html) + "</tbody></table></div>"
    st.markdown(full_table_html, unsafe_allow_html=True)


# =====================================================================================
# 4. BẢNG CHI TIẾT CELL
# =====================================================================================
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
        
        if net_label == '4G': 
            th_id = "<th class='f-cell-sticky'>CELL</th><th style='text-align:center;'>KQ</th><th>ENODEB ID</th><th>CELL ID</th>"
        else: 
            th_id = "<th class='f-cell-sticky'>CELL</th><th style='text-align:center;'>KQ</th><th>CI</th>"
        
        html_blocks.append(f"""
        <div class="header-station">
            <b>🔬 Chi Tiết Cell — {building_name} ({st_code})</b> 
            <span style="color: #94a3b8; font-size: 12px; margin-left: 8px;">• {cell_count} cells</span>
        </div>
        <div class='table-responsive-wrapper'>
        <table class='table-custom detail-table'><thead><tr>
            {th_id}
            {kpi_headers_html}
        </tr></thead><tbody>
        """)

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
            html_blocks.append(f"<tr style='background-color: #1a1a1a;'><td class='f-cell-sticky' style='background-color: #1a1a1a !important; border-bottom: 2px solid #444;'><span style='color:#ffeb3b;'><b>TB TRẠM</b></span></td><td style='text-align:center; border-bottom: 2px solid #444;'>{avg_badge}</td><td colspan='2' style='color:#9e9e9e; text-align:center; border-bottom: 2px solid #444;'>Toàn trạm</td>{avg_cols_html}</tr>")
        else:
            html_blocks.append(f"<tr style='background-color: #1a1a1a;'><td class='f-cell-sticky' style='background-color: #1a1a1a !important; border-bottom: 2px solid #444;'><span style='color:#ffeb3b;'><b>TB TRẠM</b></span></td><td style='text-align:center; border-bottom: 2px solid #444;'>{avg_badge}</td><td style='color:#9e9e9e; text-align:center; border-bottom: 2px solid #444;'>Toàn trạm</td>{avg_cols_html}</tr>")

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
            
            if net_label == '4G':
                val_en = str(row[col_enodeb]).replace('.0', '') if col_enodeb and not pd.isna(row[col_enodeb]) else "-"
                val_cid = str(row[col_cellid]).replace('.0', '') if col_cellid and not pd.isna(row[col_cellid]) else "-"
                if val_en == 'nan': val_en = "-"
                if val_cid == 'nan': val_cid = "-"
                html_blocks.append(f"<tr><td class='f-cell-sticky'>{cell_name}</td><td style='text-align:center;'>{status_badge}</td><td style='color:#aaa;'>{val_en}</td><td style='color:#aaa;'>{val_cid}</td>{cols_html}</tr>")
            else:
                val_ci = str(row[col_ci]).replace('.0', '') if col_ci and not pd.isna(row[col_ci]) else "-"
                if val_ci == 'nan': val_ci = "-"
                html_blocks.append(f"<tr><td class='f-cell-sticky'>{cell_name}</td><td style='text-align:center;'>{status_badge}</td><td style='color:#aaa;'>{val_ci}</td>{cols_html}</tr>")

        html_blocks.append("</tbody></table></div>")

    st.markdown("".join(html_blocks), unsafe_allow_html=True)

with tab4g:
    render_cell_details(df_4g_prep, active_kpis_4g, cols_4g, "4G")

with tab3g:
    render_cell_details(df_3g_prep, active_kpis_3g, cols_3g, "3G")