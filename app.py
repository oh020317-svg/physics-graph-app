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

font_ok = setup_font()

st.set_page_config(page_title="물리실험 그래프 도구", layout="centered")
st.title("📊 일반물리학실험 그래프 생성 도구")

uploaded = st.file_uploader("엑셀 또는 CSV 파일을 업로드하세요", type=["xlsx", "xls", "csv"])

if uploaded:
    try:
        if uploaded.name.endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"파일 읽기 오류: {e}")
        st.stop()

    # 숫자형 컬럼만 추출
    numeric_cols = []
    for col in df.columns:
        converted = pd.to_numeric(df[col], errors='coerce')
        if converted.notna().sum() > 0:
            df[col] = converted
            numeric_cols.append(col)

    if len(numeric_cols) < 2:
        st.error("숫자 데이터가 있는 컬럼이 2개 이상 필요해요.")
        st.stop()

    st.success(f"파일 로드 완료! ({df.shape[0]}행 × {df.shape[1]}열)")
    st.write("데이터 미리보기:", df[numeric_cols].head())

    st.markdown("---")

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

    title = st.text_input("그래프 제목", value="그래프")
    trendline = st.checkbox("선형 추세선 표시", value=True)

    COLORS = ['steelblue', 'tomato', 'seagreen', 'darkorange', 'mediumpurple']
    TREND_COLORS = ['#1a5276', '#922b21', '#1e8449', '#9c5a00', '#5b2c8d']

    if st.button("그래프 그리기"):
        if not y_cols:
            st.warning("y축 컬럼을 하나 이상 선택해주세요.")
            st.stop()

        x = pd.to_numeric(df[x_col], errors='coerce').dropna().values
        fig, ax = plt.subplots(figsize=(8, 5))

        for i, y_col in enumerate(y_cols):
            y_raw = pd.to_numeric(df[y_col], errors='coerce')
            mask = y_raw.notna()
            xi = x[:mask.sum()] if len(x) >= mask.sum() else x
            yi = y_raw.dropna().values[:len(xi)]
            min_len = min(len(xi), len(yi))
            xi, yi = xi[:min_len], yi[:min_len]

            color = COLORS[i % len(COLORS)]
            ax.scatter(xi, yi, color=color, s=40, zorder=3, label=f'{y_col} 측정값')

            if trendline and len(xi) >= 2:
                coeffs = np.polyfit(xi, yi, 1)
                slope, intercept = coeffs
                x_line = np.linspace(xi.min(), xi.max(), 200)
                y_line = slope * x_line + intercept
                ax.plot(x_line, y_line, color=TREND_COLORS[i % len(TREND_COLORS)],
                        linewidth=1.5, linestyle='--',
                        label='_nolegend_')

        if trendline:
            st.markdown("### 📐 선형 회귀 결과")
            result_cols = st.columns(len(y_cols))
            for i, y_col in enumerate(y_cols):
                y_raw = pd.to_numeric(df[y_col], errors='coerce').dropna().values
                xi = x[:len(y_raw)]
                min_len = min(len(xi), len(y_raw))
                xi, yi = xi[:min_len], y_raw[:min_len]
                if len(xi) >= 2:
                    coeffs = np.polyfit(xi, yi, 1)
                    slope, intercept = coeffs
                    y_pred = slope * xi + intercept
                    ss_res = np.sum((yi - y_pred)**2)
                    ss_tot = np.sum((yi - np.mean(yi))**2)
                    r2 = 1 - ss_res / ss_tot if ss_tot != 0 else 0
                    with result_cols[i]:
                        st.markdown(f"**{y_col}**")
                        st.metric("기울기", f"{slope:.5f}")
                        st.metric("절편", f"{intercept:.5f}")
                        st.metric("R²", f"{r2:.5f}")

        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.set_title(title, fontsize=13)
        ax.legend(fontsize=9)
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()

        st.pyplot(fig)

        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        st.download_button("PNG 다운로드", data=buf, file_name="graph.png", mime="image/png")
