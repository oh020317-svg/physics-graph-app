import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from io import BytesIO
import os
import urllib.request

def setup_font():
    font_path = "/tmp/NanumGothic.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
        try:
            urllib.request.urlretrieve(url, font_path)
        except:
            return False
    fm.fontManager.addfont(font_path)
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
    plt.rcParams['axes.unicode_minus'] = False
    return True

setup_font()

st.set_page_config(page_title="물리실험 데이터 시각화 도구", layout="centered")
st.title("📊 물리실험 데이터 시각화 도구")

uploaded = st.file_uploader("엑셀 또는 CSV 파일을 업로드하세요", type=["xlsx", "xls", "csv"])

if uploaded:
    try:
        if uploaded.name.endswith(".csv"):
            df = pd.read_csv(uploaded)
            sheet_name = None
        else:
            xl = pd.ExcelFile(uploaded)
            sheet_names = xl.sheet_names
            sheet_name = st.selectbox("시트 선택", sheet_names)
            df = pd.read_excel(uploaded, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"파일 읽기 오류: {e}")
        st.stop()

    numeric_cols = []
    for col in df.columns:
        converted = pd.to_numeric(df[col], errors='coerce')
        if converted.notna().sum() > 0:
            df[col] = converted
            numeric_cols.append(col)

    if len(numeric_cols) < 2:
        st.error("숫자 데이터가 있는 컬럼이 2개 이상 필요해요.")
        st.stop()

    st.success(f"'{sheet_name}' 시트 로드 완료! ({df.shape[0]}행 × {df.shape[1]}열)")
    st.write("데이터 미리보기:", df[numeric_cols].head())

    st.markdown("---")

    graph_type = st.selectbox("그래프 종류 선택", [
        "산점도 + 선형 추세선",
        "산점도 + 2차 곡선 피팅",
        "꺾은선 그래프",
        "막대 그래프"
    ])

    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("x축 컬럼", numeric_cols, index=0)
        x_label = st.text_input("x축 레이블", value=numeric_cols[0])
    with col2:
        y_cols = st.multiselect(
            "y축 컬럼 (여러 개 선택 가능)",
            [c for c in numeric_cols if c != x_col],
            default=[numeric_cols[1]] if len(numeric_cols) > 1 else []
        )
        y_label = st.text_input("y축 레이블", value=", ".join(y_cols) if y_cols else "")

    title = st.text_input("그래프 제목", value=f"{sheet_name} 그래프" if sheet_name else "그래프")

    COLORS = ['steelblue', 'tomato', 'seagreen', 'darkorange', 'mediumpurple']
    TREND_COLORS = ['#1a5276', '#922b21', '#1e8449', '#9c5a00', '#5b2c8d']

    if st.button("그래프 그리기"):
        if not y_cols:
            st.warning("y축 컬럼을 하나 이상 선택해주세요.")
            st.stop()

        x = pd.to_numeric(df[x_col], errors='coerce').dropna().values
        fig, ax = plt.subplots(figsize=(8, 5))

        for i, y_col in enumerate(y_cols):
            y_raw = pd.to_numeric(df[y_col], errors='coerce').dropna().values
            min_len = min(len(x), len(y_raw))
            xi, yi = x[:min_len], y_raw[:min_len]
            color = COLORS[i % len(COLORS)]
            trend_color = TREND_COLORS[i % len(TREND_COLORS)]

            if graph_type == "산점도 + 선형 추세선":
                ax.scatter(xi, yi, color=color, s=40, zorder=3, label=f'{y_col}')
                if len(xi) >= 2:
                    coeffs = np.polyfit(xi, yi, 1)
                    x_line = np.linspace(xi.min(), xi.max(), 200)
                    ax.plot(x_line, np.polyval(coeffs, x_line),
                            color=trend_color, linewidth=1.5, linestyle='--', label='_nolegend_')

            elif graph_type == "산점도 + 2차 곡선 피팅":
                ax.scatter(xi, yi, color=color, s=40, zorder=3, label=f'{y_col}')
                if len(xi) >= 3:
                    coeffs = np.polyfit(xi, yi, 2)
                    x_line = np.linspace(xi.min(), xi.max(), 200)
                    ax.plot(x_line, np.polyval(coeffs, x_line),
                            color=trend_color, linewidth=1.5, linestyle='--', label='_nolegend_')

            elif graph_type == "꺾은선 그래프":
                ax.plot(xi, yi, color=color, linewidth=1.8, marker='o',
                        markersize=5, label=f'{y_col}')

            elif graph_type == "막대 그래프":
                width = (xi.max() - xi.min()) / len(xi) * 0.7 / len(y_cols)
                offset = (i - len(y_cols) / 2 + 0.5) * width
                ax.bar(xi + offset, yi, width=width, color=color, alpha=0.8, label=f'{y_col}')

        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.set_title(title, fontsize=13)
        ax.legend(fontsize=9)
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()

        st.pyplot(fig)

        if graph_type in ["산점도 + 선형 추세선", "산점도 + 2차 곡선 피팅"]:
            st.markdown("### 📐 회귀 결과")
            result_cols = st.columns(len(y_cols))
            for i, y_col in enumerate(y_cols):
                y_raw = pd.to_numeric(df[y_col], errors='coerce').dropna().values
                min_len = min(len(x), len(y_raw))
                xi, yi = x[:min_len], y_raw[:min_len]
                with result_cols[i]:
                    st.markdown(f"**{y_col}**")
                    if graph_type == "산점도 + 선형 추세선" and len(xi) >= 2:
                        coeffs = np.polyfit(xi, yi, 1)
                        y_pred = np.polyval(coeffs, xi)
                        r2 = 1 - np.sum((yi - y_pred)**2) / np.sum((yi - np.mean(yi))**2)
                        st.metric("기울기", f"{coeffs[0]:.5f}")
                        st.metric("절편", f"{coeffs[1]:.5f}")
                        st.metric("R²", f"{r2:.5f}")
                    elif graph_type == "산점도 + 2차 곡선 피팅" and len(xi) >= 3:
                        coeffs = np.polyfit(xi, yi, 2)
                        y_pred = np.polyval(coeffs, xi)
                        r2 = 1 - np.sum((yi - y_pred)**2) / np.sum((yi - np.mean(yi))**2)
                        st.metric("a (x²)", f"{coeffs[0]:.5f}")
                        st.metric("b (x)", f"{coeffs[1]:.5f}")
                        st.metric("c (상수)", f"{coeffs[2]:.5f}")
                        st.metric("R²", f"{r2:.5f}")

        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        st.download_button("PNG 다운로드", data=buf, file_name="graph.png", mime="image/png")
