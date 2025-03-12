import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO

# STREAMLIT BAŞLIĞI
st.title("⚡ KaçakBul")

# Kullanıcıdan dosya yükleme için iki sütun
col1, col2 = st.columns(2)

with col1:
    el31_file = st.file_uploader("📂 EL31 Dosyasını Yükleyin (.csv)", type=["csv"])
    
with col2:
    zblir_file = st.file_uploader("📂 ZBLIR_002 Dosyasını Yükleyin (.csv)", type=["csv"])

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

# **EL31 VERİLERİNİ DÜZENLE BUTONU**
if el31_file and st.button("📌 EL31 Verilerini Düzenle"):

    def clean_el31(df):
        drop_columns = [
            "Sözleşme grubu", "Sayaç okuma birimi", "Muhatap", "Sözleşme", "Cihaz", "Ekipman", "Endeks",
            "Giriş numarası", "Kontrol rakamı", "Planlanan SO tarihi", "Sayaç okuma nedeni", "Çoklu tayin",
            "Pln.sayaç okuma tipi", "Sayaç okuma türü", "Sayaç okuma durumu", "Vrg.önc.basamaklar", "Ondalık basamaklar",
            "Hizmet siparişi", "Hizmet bildirimi", "SO belge dahili tn.", "Sprş.çkt.önc.alındı", "Bağımsız doğrulama",
            "Bağlı doğrulama", "Sayaç notu", "Geriye dönük thk.drm.", "Sayaç okuma etkin", "Gelişmiş sayaç okuma sistemi",
            "İletim durumu kodu", "Zaman damgası", "Kaynak sistem.1", "Aktarma tarihi", "Aktarım saati",
            "İletim durumu", "İletim durumu tanımı", "Kaynak sistem", "Doğal sayı", "Farklı sözleşme gr.",
            "Tahakkuk edilecek sayaç durumu", "Katalog 1", "Kod grubu 1", "Kod 1", "Açıklama 1", "Bildirim 1",
            "Katalog 2", "Kod grubu 2", "Kod 2", "Açıklama 2", "Bildirim 2", "Katalog 3", "Kod grubu 3",
            "Kod 3", "Açıklama 3", "Bildirim 3", "Deneme Sayısı", "Okuma Zamanı", "Manually-read"
        ]
        return df.drop(columns=drop_columns, errors='ignore')

    def only_p_lines(df):
        return df[df["Endeks türü"] == "P"]

    def filter_max_reading(df):
        df["Okunan sayaç durumu"] = df["Okunan sayaç durumu"].astype(str).str.replace(",", ".").astype(float)
        df = df.sort_values(by=["Tesisat", "Sayaç okuma tarihi", "Okunan sayaç durumu"], ascending=[True, True, False])
        return df.groupby(["Tesisat", "Sayaç okuma tarihi"], as_index=False).first()

    # **EL31 Verilerini Temizleme**
    df_el31_cleaned = clean_el31(df_el31)
    df_el31_cleaned = only_p_lines(df_el31_cleaned)
    df_el31_filtered = filter_max_reading(df_el31_cleaned)

    # **ZIP dosyasına kaydetme**
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for tesisat, group in df_el31_filtered.groupby("Tesisat"):
            unique_muhatap = group["Muhatap adı"].unique()

            if len(unique_muhatap) == 1:
                file_name = f"{tesisat}.csv"
                csv_data = group.to_csv(sep=";", index=False).encode("utf-8")
                zipf.writestr(file_name, csv_data)

            elif len(unique_muhatap) == 2:
                latest_muhatap = unique_muhatap[0]
                file_name_A = f"{tesisat}-A.csv"
                csv_data_A = group[group["Muhatap adı"] == latest_muhatap].to_csv(sep=";", index=False).encode("utf-8")
                zipf.writestr(file_name_A, csv_data_A)

                file_name_AB = f"{tesisat}-AB.csv"
                csv_data_AB = group.to_csv(sep=";", index=False).encode("utf-8")
                zipf.writestr(file_name_AB, csv_data_AB)

    zip_buffer.seek(0)

    st.success("✅ EL31 Verileri Düzenlendi!")
    st.download_button("📥 Düzenlenmiş EL31 Dosyalarını ZIP Olarak İndir", zip_buffer, "el31_duzenlenmis.zip", "application/zip")




# **ZBLIR_002 VERİLERİNİ DÜZENLE BUTONU**
if zblir_file and st.button("📌 ZBLIR_002 Verilerini Düzenle"):
    def filter_latest_two_contacts(df):
        """Her tesisat için en güncel iki muhatabı seçer."""
        df["Son Okuma Tarihi"] = pd.to_datetime(df["Son Okuma Tarihi"], dayfirst=True)
        df = df.sort_values(by=["Tesisat", "Son Okuma Tarihi"], ascending=[True, False])
        df = df.groupby("Tesisat").apply(lambda x: x[x["Muhatap Adı"].isin(x["Muhatap Adı"].unique()[:2])])
        return df.reset_index(drop=True)

    df_zblir_cleaned = filter_latest_two_contacts(df_zblir)

    # **ZIP DOSYASI OLUŞTURMA**
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for tesisat, group in df_zblir_cleaned.groupby("Tesisat"):
            unique_muhatap = group["Muhatap Adı"].unique()

            if len(unique_muhatap) == 1:
                file_name = f"{tesisat}.csv"
                csv_data = group.to_csv(sep=";", index=False).encode("utf-8")
                zipf.writestr(file_name, csv_data)

            elif len(unique_muhatap) == 2:
                latest_muhatap = unique_muhatap[0]

                file_name_A = f"{tesisat}-A.csv"
                csv_data_A = group[group["Muhatap Adı"] == latest_muhatap].to_csv(sep=";", index=False).encode("utf-8")
                zipf.writestr(file_name_A, csv_data_A)

                file_name_AB = f"{tesisat}-AB.csv"
                csv_data_AB = group.to_csv(sep=";", index=False).encode("utf-8")
                zipf.writestr(file_name_AB, csv_data_AB)

    zip_buffer.seek(0)

    st.success("✅ ZBLIR_002 Verileri Düzenlendi!")
    st.download_button("📥 Düzenlenmiş ZBLIR_002 Dosyalarını ZIP Olarak İndir", zip_buffer, "zblir_edited.zip", "application/zip")







#BURAYA KADAR OKEYYYYYYYYYY



import streamlit as st

# 📊 Kullanıcıdan analiz için giriş al

col1, col2 = st.columns([1, 1])  # Sol tarafı genişlettik

# 🟢 **Analiz Seçenekleri**
with col1:
    st.markdown("#### 📊 Hangi Analiz Yapılacak?")
    
    # Seçeneklerin listesi
    analysis_options = ["P Analizi", "T1 Analizi", "T2 Analizi", "T3 Analizi"]

    # Kutucuklar için boş bir sözlük
    selected_options = {}

    # Her analiz için bir checkbox ekleyelim
    for option in analysis_options:
        selected_options[option] = st.checkbox(option)

    # Tümünü Seç butonu
    if st.button("Tümünü Seç"):
        for key in selected_options:
            selected_options[key] = True  # Hepsini seçili yapar

# 🔵 **Düşüş Parametreleri**
with col2:
    st.markdown("#### 📉 Düşüş Parametreleri")
    decrease_percentage = st.number_input("📉 Yüzde Kaç Düşüş?", min_value=1, max_value=100, step=1, value=10)
    decrease_count = st.number_input("🔄 Kaç Kez Düşüş?", min_value=1, max_value=10, step=1, value=2)

# **Seçili analizleri belirleme**
selected_analysis = [key for key, value in selected_options.items() if value]

















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



