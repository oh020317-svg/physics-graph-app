import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import subprocess
import os

# 한글 폰트 설치 (코랩 환경)
def install_korean_font():
    try:
        subprocess.run(['apt-get', 'install', '-y', 'fonts-nanum'], capture_output=True)
        fm.fontManager.__init__()
    except:
        pass

install_korean_font()

st.set_page_config(page_title="물리실험 그래프 도구", layout="centered")
st.title("📊 일반물리학실험 그래프 생성 도구")

uploaded = st.file_uploader("엑셀 또는 CSV 파일을 업로드하세요", type=["xlsx", "xls", "csv"])

if uploaded:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)

    st.success(f"파일 로드 완료! ({df.shape[0]}행 × {df.shape[1]}열)")
    st.write("데이터 미리보기:", df.head())

    cols = list(df.columns)

    col1, col2 = st.columns(2)
    with col1:
        x_col = st.selectbox("x축 컬럼", cols, index=0)
        x_label = st.text_input("x축 레이블", value=cols[0])
    with col2:
        y_col = st.selectbox("y축 컬럼", cols, index=min(1, len(cols)-1))
        y_label = st.text_input("y축 레이블", value=cols[min(1, len(cols)-1)])

    title = st.text_input("그래프 제목", value=f"{y_col} - {x_col} 그래프")
    trendline = st.checkbox("선형 추세선 표시", value=True)

    if st.button("그래프 그리기"):
        x = df[x_col].dropna().values.astype(float)
        y = df[y_col].dropna().values.astype(float)

        try:
            plt.rcParams['font.family'] = 'NanumGothic'
        except:
            pass
        plt.rcParams['axes.unicode_minus'] = False

        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(x, y, color='steelblue', s=40, zorder=3, label='측정값')

        if trendline:
            coeffs = np.polyfit(x, y, 1)
            slope, intercept = coeffs
            x_line = np.linspace(x.min(), x.max(), 200)
            y_line = slope * x_line + intercept
            ax.plot(x_line, y_line, color='tomato', linewidth=1.5,
                    label=f'추세선: y = {slope:.4f}x + {intercept:.4f}')

            y_pred = slope * x + intercept
            ss_res = np.sum((y - y_pred)**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            r2 = 1 - ss_res / ss_tot

            st.markdown("### 📐 선형 회귀 결과")
            c1, c2, c3 = st.columns(3)
            c1.metric("기울기", f"{slope:.5f}")
            c2.metric("절편", f"{intercept:.5f}")
            c3.metric("R²", f"{r2:.5f}")

        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.set_title(title, fontsize=13)
        ax.legend(fontsize=10)
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()

        st.pyplot(fig)

        from io import BytesIO
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        buf.seek(0)
        st.download_button("PNG 다운로드", data=buf, file_name="graph.png", mime="image/png")
