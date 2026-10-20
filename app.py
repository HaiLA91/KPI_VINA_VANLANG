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
       CẤU HÌNH FREEZE CỘT & THU GỌN VỪA KHÍT NỘI DUNG
       ========================================================== */
    /* Class ép cột thu gọn vừa khít với chữ bên trong */
    .col-fit { width: 1% !important; white-space: nowrap !important; padding-left: 10px !important; padding-right: 10px !important; }

    .f-hist-tram { position: sticky !important; left: 0 !important; min-width: 190px; max-width: 190px; white-space: normal !important; word-wrap: break-word; border-right: 2px solid #1976d2 !important; z-index: 4; }
    th.f-hist-tram { z-index: 15 !important; background-color: #1e293b !important; top: 0 !important; }
    td.f-hist-tram { background-color: #1e1e1e !important; color: #eee !important; }

    .f-col1 { position: sticky !important; left: 0 !important; min-width: 95px; max-width: 95px; white-space: normal !important; word-wrap: break-word; z-index: 4; }
    .f-col2 { position: sticky !important; left: 95px !important; min-width: 150px; max-width: 150px; white-space: normal !important; word-wrap: break-word; border-right: 2px solid #1976d2 !important; z-index: 4; }
    th.f-col1, th.f-col2 { z-index: 15 !important; background-color: #1e293b !important; top: 0 !important; } 
    td.f-col1, td.f-col2 { background-color: #1e1e1e !important; color: #eee !important; }

    /* Cột CELL ôm sát vừa khít độ dài tên Cell, không bị dư khoảng trống */
    .f-cell-sticky { position: sticky !important; left: 0 !important; width: 1% !important; white-space: nowrap !important; padding: 7px 10px !important; border-right: 2px solid #1976d2 !important; z-index: 4; }
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

        .f-cell-sticky { font-size: 11px !important; padding: 5