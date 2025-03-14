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
    st.download_button("📥 Düzenlenmiş ZBLIR_002 Dosyalarını ZIP Olarak İndir", zip_buffer, "zblir_duzenlenmis.zip", "application/zip")







#BURAYA KADAR OKEYYYYYYYYYY



# 📊 Kullanıcıdan analiz için giriş al
col1, col2 = st.columns([1, 1])  

# 🟢 **Analiz Seçenekleri**
with col1:
    st.markdown("#### 📊 Hangi Analiz Yapılacak?")

    # Seçeneklerin listesi
    analysis_options = ["P Analizi", "T1 Analizi", "T2 Analizi", "T3 Analizi"]

    # Session state içinde checkbox durumlarını sakla
    if "selected_analysis" not in st.session_state:
        st.session_state.selected_analysis = {opt: False for opt in analysis_options}

    # Checkboxları oluştur
    for option in analysis_options:
        st.session_state.selected_analysis[option] = st.checkbox(option, st.session_state.selected_analysis[option])

    # Tümünü Seç butonu
    def toggle_all():
        all_selected = all(st.session_state.selected_analysis.values())
        for key in st.session_state.selected_analysis:
            st.session_state.selected_analysis[key] = not all_selected  # Tersine çevir

    st.button("Tümünü Seç", on_click=toggle_all)

# 🔵 **Düşüş Parametreleri**
with col2:
    st.markdown("#### 📉 Düşüş Parametreleri")
    decrease_percentage = st.number_input("📉 Yüzde Kaç Düşüş?", min_value=1, max_value=100, step=1, value=30)
    decrease_count = st.number_input("🔄 Kaç Kez Düşüş?", min_value=1, max_value=10, step=1, value=3)

# **Seçili analizleri belirleme**
selected_analysis = [key for key, value in st.session_state.selected_analysis.items() if value]










#BURAYA KADAR DA OKEYYYY GİBİ




# **Analizi Başlat Butonu**
if st.button("🚀 Analizi Başlat"):

    combined_results = {}

    # **P Analizi Seçildiyse Çalıştır**
    if "P Analizi" in selected_analysis:
        def p_analizi(df, esik_orani, alt_esik_sayisi):
            suspicious = []

            # **Veri temizleme işlemi**
            df["Okunan sayaç durumu"] = df["Okunan sayaç durumu"].astype(str).str.replace(",", ".", regex=True)

            # **Sadece sayısal değerleri al ve hatalı olanları temizle**
            df["Okunan sayaç durumu"] = pd.to_numeric(df["Okunan sayaç durumu"], errors="coerce")
            
            # **NaN olan satırları temizle**
            df = df.dropna(subset=["Okunan sayaç durumu"])

            for tesisat, group in df.groupby("Tesisat"):
                p_values = group[group["Endeks türü"] == "P"]["Okunan sayaç durumu"].dropna().tolist()

                if not p_values:
                    continue  # Eğer "P" değeri yoksa atla

                # **Ortalama P değeri hesapla**
                p_values_nonzero = [val for val in p_values if val > 0]
                if len(p_values_nonzero) > 0:
                    p_avg = sum(p_values_nonzero) / len(p_values_nonzero)
                    esik_deger = p_avg * (1 - esik_orani / 100)  # Kullanıcının belirlediği düşüş yüzdesine göre eşik belirle

                    # **Eşik altında kalan değerlerin sayısını hesapla**
                    below_threshold_count = sum(1 for val in p_values_nonzero if val < esik_deger)

                    # **Son 3 değer ortalamadan büyükse şüpheli listeye ekleme**
                    last_three_values = p_values_nonzero[-3:] if len(p_values_nonzero) >= 3 else []
                    if all(val > p_avg for val in last_three_values):
                        continue  # Eğer son 3 değer ortalamadan büyükse, tesisat şüpheli olarak eklenmez

                    # **Şüpheli tesisatı ekle**
                    if below_threshold_count > alt_esik_sayisi:
                        combined_results[tesisat] = ["P Analizi"]

    # **T1, T2 veya T3 Analizlerinden En Az Biri Seçildiyse Çalıştır**
    if any(t in selected_analysis for t in ["T1 Analizi", "T2 Analizi", "T3 Analizi"]):

        def calc_avg(df, endeks_turu, threshold_ratio):
            """Her endeks türü için ortalama tüketimi ve eşik değerini hesaplar."""
            filtered_df = df[df["Endeks Türü"] == endeks_turu].copy()

            if filtered_df.empty:
                return None  # Eğer bu endeks türü yoksa işlem yapma

            # "Ortalama Tüketim" sütununu temizle ve sayısal formata çevir
            filtered_df["Ortalama Tüketim"] = pd.to_numeric(
                filtered_df["Ortalama Tüketim"]
                .astype(str)
                .str.replace(",", ".", regex=True)
                .str.extract(r'(\d+\.\d+|\d+)')[0], 
                errors="coerce"
            )

            # NaN ve sıfır olmayan tüketim değerlerini filtrele
            nonzero_values = filtered_df["Ortalama Tüketim"].dropna()
            nonzero_values = nonzero_values[nonzero_values > 0].tolist()

            if not nonzero_values:
                return None  # Eğer sıfır olmayan veri yoksa işlem yapma

            avg_value = sum(nonzero_values) / len(nonzero_values)  # Ortalama hesapla
            threshold_value = avg_value * (1 - threshold_ratio / 100)  # Kullanıcıdan alınan yüzdelik değere göre eşik hesapla

            return avg_value, threshold_value

        def analyze_tesisat_data(df, threshold_ratio, below_threshold_limit):
            """T1, T2, T3 analizlerini yaparak şüpheli tesisatları belirler."""
            for tesisat, group in df.groupby("Tesisat"):
                suspicious_endeks_types = []

                for endeks_turu in ["T1", "T2", "T3"]:
                    if endeks_turu + " Analizi" not in selected_analysis:  # Kullanıcının seçtiği analizleri kontrol et
                        continue

                    result = calc_avg(group, endeks_turu, threshold_ratio)

                    if result is None:
                        continue  # Eğer bu endeks türü için veri yoksa atla

                    avg_value, threshold_value = result

                    # Eşik değerinin altına düşen tüketim sayısını hesapla
                    below_threshold_count = sum(
                        1
                        for val in pd.to_numeric(
                            group[group["Endeks Türü"] == endeks_turu]["Ortalama Tüketim"]
                            .astype(str)
                            .str.replace(",", ".", regex=True)
                            .str.extract(r'(\d+\.\d+|\d+)')[0], 
                            errors="coerce"
                        ).dropna()
                        if val > 0 and val < threshold_value
                    )

                    # Eğer belirlenen eşik altı sayısından fazla düşük değer varsa şüpheli olarak ekle
                    if below_threshold_count > below_threshold_limit:
                        if tesisat in combined_results:
                            combined_results[tesisat].append(endeks_turu)
                        else:
                            combined_results[tesisat] = [endeks_turu]

    # **Sonuçları Tek Bir DataFrame'de Birleştirme**
    if combined_results:
        df_combined = pd.DataFrame(list(combined_results.items()), columns=["Şüpheli Tesisat", "Şüpheli Analiz Türleri"])
        df_combined["Şüpheli Analiz Türleri"] = df_combined["Şüpheli Analiz Türleri"].apply(lambda x: ", ".join(x))

        # **Sonuçları Göster**
        st.success("✅ Analizler Tamamlandı!")
        st.dataframe(df_combined)

        # **Tek bir CSV dosyası olarak indir**
        st.download_button(
            "📥 Analiz Sonuçlarını İndir",
            df_combined.to_csv(sep=";", index=False).encode("utf-8"),
            "analiz_sonuclari.csv",
            "text/csv"
        )
    else:
        st.warning("⚠️ Seçilen analizler sonucunda şüpheli tesisat bulunamadı!")

