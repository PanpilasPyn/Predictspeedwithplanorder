
import streamlit as st
import pandas as pd
import joblib
import io

st.set_page_config(page_title="Production Plan & Predict Speed", layout="wide")
st.title("🚀 Production Planning with Predict Speed Model + Due Date")

@st.cache_resource
def load_model():
    model = joblib.load("rf_model_latest.pkl")
    feature_columns = joblib.load("feature_columns_latest.pkl")
    return model, feature_columns

model, feature_columns = load_model()

def encode_input(df_input, columns):
    dropdown_cols = [
        "Can Size", "Drink Type", "Coil type", "OV type",
        "Design type", "Customer", "IC type"
    ]
    for col in dropdown_cols:
        if col in df_input.columns:
            df_input[col] = df_input[col].astype(str)
    df_encoded = pd.get_dummies(df_input)
    for col in columns:
        if col not in df_encoded:
            df_encoded[col] = 0
    return df_encoded[columns]

uploaded_file = st.file_uploader("📤 อัปโหลดไฟล์ Excel สำหรับวางแผนผลิต", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.write("ตัวอย่างข้อมูลที่อัปโหลด", df.head())

    try:
        df_encoded = encode_input(df, feature_columns)
        df["Predicted Good Speed run"] = model.predict(df_encoded)
        df["Predict hour"] = df["Good Qty (Can)"] / df["Predicted Good Speed run"]

        size_col = "Can Size" if "Can Size" in df.columns else None
        ov_col = "OV type" if "OV type" in df.columns else None
        coil_col = "Coil type" if "Coil type" in df.columns else None
        due_col = "duedate" if "duedate" in df.columns else None

        # ถ้า duedate ไม่ใช่ datetime ให้แปลง
        if due_col and not pd.api.types.is_datetime64_any_dtype(df[due_col]):
            df[due_col] = pd.to_datetime(df[due_col])

        sort_cols = [col for col in [due_col, size_col, ov_col, coil_col, 'Predict hour'] if col is not None]
        if sort_cols:
            plan_df = df.sort_values(sort_cols).reset_index(drop=True)
        else:
            plan_df = df.copy()
        plan_df['Sequence'] = plan_df.index + 1

        st.success("🎯 ผลลัพธ์แผนการผลิตเรียงตาม duedate > Can Size > OV type > Coil type")
        st.dataframe(plan_df)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            plan_df.to_excel(writer, index=False)
        st.download_button(
            label="📥 ดาวน์โหลดไฟล์แผนการผลิต (Excel)",
            data=output.getvalue(),
            file_name="production_plan_with_predict_speed.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")

    st.markdown("---")
    st.info(
        "นำไฟล์โมเดล .pkl และ feature columns .pkl ไว้ในโฟลเดอร์เดียวกับไฟล์นี้\n"
        "Format ของไฟล์ input ควรมี duedate, Can Size, OV type, Coil type, Good Qty (Can) และ features ที่โมเดลต้องการ"
    )
