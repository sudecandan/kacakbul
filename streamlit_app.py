import streamlit as st
import pandas as pd
import zipfile
import os

# Streamlit başlığı
st.title("⚡ KaçakBul")

# Kullanıcıdan dosya yükleme için iki sütun
col1, col2 = st.columns(2)

with col1:
    el31_file = st.file_uploader("📂 EL31 Dosyanızı Yükleyin (.csv)", type=["csv"])
    
with col2:
    zblir_file = st.file_uploader("📂 ZBLIR_002 Dosyanızı Yükleyin (.csv)", type=["csv"])

# Kullanıcı dosyaları yüklediyse önizleme göster
if el31_file and zblir_file:
    st.subheader("📊 Yüklenen Dosya Önizlemesi")
    
    col1, col2 = st.columns(2)

    with col1:
        df_el31 = pd.read_csv(el31_file, delimiter=";", encoding="utf-8")
        st.write("🔹 **EL31 Dosyası Önizleme**")
        st.dataframe(df_el31.head())

    with col2:
        df_zblir = pd.read_csv(zblir_file, delimiter=";", encoding="utf-8")
        st.write("🔹 **ZBLIR_002 Dosyası Önizleme**")
        st.dataframe(df_zblir.head())

# **EL31 Verilerini Düzenle** Butonu
if el31_file and st.button("📌 EL31 Verilerini Düzenle"):
    def clean_el31(df):
        drop_columns = ["Sözleşme grubu", "Sayaç okuma birimi", "Muhatap", "Sözleşme", "Cihaz", "Ekipman", "Endeks",
                        "Giriş numarası", "Kontrol rakamı", "Planlanan SO tarihi", "Sayaç okuma nedeni", "Çoklu tayin"]
        df = df.drop(columns=drop_columns, errors='ignore')
        df = df[df["Endeks türü"] == "P"]
        df["Okunan sayaç durumu"] = df["Okunan sayaç durumu"].astype(str).str.replace(",", ".").astype(float)
        df = df.sort_values(by=["Tesisat", "Sayaç okuma tarihi", "Okunan sayaç durumu"], ascending=[True, True, False])
        df = df.groupby(["Tesisat", "Sayaç okuma tarihi"], as_index=False).first()
        return df

    df_el31_cleaned = clean_el31(df_el31)
    st.success("✅ EL31 Verileri Düzenlendi!")

    st.download_button("📥 Düzenlenmiş EL31 Dosyasını İndir", df_el31_cleaned.to_csv(sep=";", index=False).encode("utf-8"), "el31_edited.csv", "text/csv")

# **ZBLIR_002 Verilerini Düzenle** Butonu
if zblir_file and st.button("📌 ZBLIR_002 Verilerini Düzenle"):
    def clean_zblir(df):
        df["Son Okuma Tarihi"] = pd.to_datetime(df["Son Okuma Tarihi"], dayfirst=True)
        df = df.sort_values(by=["Tesisat", "Son Okuma Tarihi"], ascending=[True, False])
        df = df.groupby("Tesisat").apply(lambda x: x[x["Muhatap Adı"].isin(x["Muhatap Adı"].unique()[:2])])
        df = df.reset_index(drop=True)
        return df

    df_zblir_cleaned = clean_zblir(df_zblir)
    st.success("✅ ZBLIR_002 Verileri Düzenlendi!")

    st.download_button("📥 Düzenlenmiş ZBLIR_002 Dosyasını İndir", df_zblir_cleaned.to_csv(sep=";", index=False).encode("utf-8"), "zblir_edited.csv", "text/csv")

# Kullanıcıdan analiz için giriş al
st.subheader("📊 Analiz Parametreleri")

col1, col2 = st.columns(2)
with col1:
    decrease_percentage = st.number_input("📉 Yüzde Kaç Düşüş (%)", min_value=1, max_value=100, step=1)
with col2:
    decrease_count = st.number_input("🔄 Kaç Kez Düşüş", min_value=1, max_value=10, step=1)

# Analiz seçenekleri
st.subheader("📌 Hangi Analizleri Yapmak İstersiniz?")
options = ["P", "T1", "T2", "T3"]
selected_analysis = st.multiselect("Seçim Yapın:", options)
select_all = st.checkbox("✅ Tümünü Seç")

if select_all:
    selected_analysis = options

# **Analizi Başlat Butonu**
if st.button("🚀 Analizi Başlat"):
    if "P" in selected_analysis:
        # **P Analizi**
        def p_analizi(df, esik_orani, alt_esik_sayisi):
            suspicious = []
            df["Okunan sayaç durumu"] = df["Okunan sayaç durumu"].astype(str).str.replace(",", ".").astype(float)
            for tesisat, group in df.groupby("Tesisat"):
                p_values = group[group["Endeks türü"] == "P"]["Okunan sayaç durumu"].dropna().tolist()
                if not p_values:
                    continue
                avg_p = sum(p_values) / len(p_values)
                threshold = avg_p * (1 - esik_orani / 100)
                below_threshold_count = sum(1 for val in p_values if val < threshold)
                if below_threshold_count > alt_esik_sayisi:
                    suspicious.append([tesisat])
            return pd.DataFrame(suspicious, columns=["Şüpheli Tesisat"])

        df_suspicious_p = p_analizi(df_el31, decrease_percentage, decrease_count)
        st.success("✅ P Analizi Tamamlandı!")
        st.dataframe(df_suspicious_p)
        st.download_button("📥 P Analizi Sonuçlarını İndir", df_suspicious_p.to_csv(sep=";", index=False).encode("utf-8"), "p_analizi.csv", "text/csv")

    if any(t in selected_analysis for t in ["T1", "T2", "T3"]):
        # **T Analizi**
        def t_analizi(df, threshold_ratio, below_threshold_limit):
            suspicious = []
            for tesisat, group in df.groupby("Tesisat"):
                for endeks in ["T1", "T2", "T3"]:
                    values = group[group["Endeks Türü"] == endeks]["Ortalama Tüketim"].dropna().tolist()
                    if not values:
                        continue
                    avg_value = sum(values) / len(values)
                    threshold = avg_value * (1 - threshold_ratio / 100)
                    below_threshold_count = sum(1 for val in values if val < threshold)
                    if below_threshold_count > below_threshold_limit:
                        suspicious.append([tesisat, endeks])
            return pd.DataFrame(suspicious, columns=["Şüpheli Tesisat", "Endeks Türü"])

        df_suspicious_t = t_analizi(df_zblir, decrease_percentage, decrease_count)
        st.success("✅ T Analizi Tamamlandı!")
        st.dataframe(df_suspicious_t)
        st.download_button("📥 T Analizi Sonuçlarını İndir", df_suspicious_t.to_csv(sep=";", index=False).encode("utf-8"), "t_analizi.csv", "text/csv")


