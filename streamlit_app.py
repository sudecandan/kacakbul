import streamlit as st
import pandas as pd
import zipfile
import os
import shutil
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.drawing.image import Image


# STREAMLIT BAŞLIĞI
st.title("⚡ KaçakBul")
st.write("EL31 ZIP Dosya Yolu:", os.path.abspath(el31_zip_path))
st.write("ZBLIR ZIP Dosya Yolu:", os.path.abspath(zblir_zip_path))


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
if el31_file:

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
if zblir_file:
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

    analysis_options = ["P Analizi", "T1 Analizi", "T2 Analizi", "T3 Analizi"]

    if "selected_analysis" not in st.session_state:
        st.session_state.selected_analysis = {opt: False for opt in analysis_options}

    for option in analysis_options:
        st.session_state.selected_analysis[option] = st.checkbox(option, st.session_state.selected_analysis[option])

    def toggle_all():
        all_selected = all(st.session_state.selected_analysis.values())
        for key in st.session_state.selected_analysis:
            st.session_state.selected_analysis[key] = not all_selected

    st.button("Tümünü Seç", on_click=toggle_all)

# 🔵 **Düşüş Parametreleri**
st.markdown("### 📉 Düşüş Parametreleri")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("#### 📉 **P Analizi İçin**")
    decrease_percentage_p = st.number_input("📉 P Yüzde Kaç Düşüş?", min_value=1, max_value=100, step=1, value=30)
    decrease_count_p = st.number_input("🔄 P Kaç Kez Düşüş?", min_value=1, max_value=10, step=1, value=3)

with col2:
    st.markdown("#### 📉 **T Analizi İçin**")
    decrease_percentage_t = st.number_input("📉 T Yüzde Kaç Düşüş?", min_value=1, max_value=100, step=1, value=50)
    decrease_count_t = st.number_input("🔄 T Kaç Kez Düşüş?", min_value=1, max_value=10, step=1, value=5)

# **Seçili analizleri belirleme**
selected_analysis = [key for key, value in st.session_state.selected_analysis.items() if value]

# **Analizi Başlat Butonu**
if st.button("🚀 Analizi Başlat"):

    combined_results = {}

    # **P Analizi Seçildiyse Çalıştır**
    if "P Analizi" in selected_analysis:
        def p_analizi(df, esik_orani, alt_esik_sayisi):
            df["Okunan sayaç durumu"] = df["Okunan sayaç durumu"].astype(str).str.replace(",", ".", regex=True)
            df["Okunan sayaç durumu"] = pd.to_numeric(df["Okunan sayaç durumu"], errors="coerce")
            df = df.dropna(subset=["Okunan sayaç durumu"])

            for tesisat, group in df.groupby("Tesisat"):
                p_values = group[group["Endeks türü"] == "P"]["Okunan sayaç durumu"].dropna().tolist()
                if not p_values:
                    continue

                p_values_nonzero = [val for val in p_values if val > 0]
                if len(p_values_nonzero) > 0:
                    p_avg = sum(p_values_nonzero) / len(p_values_nonzero)
                    esik_deger = p_avg * (1 - esik_orani / 100)

                    below_threshold_count = sum(1 for val in p_values_nonzero if val < esik_deger)

                    if below_threshold_count > alt_esik_sayisi:
                        if tesisat in combined_results:
                            combined_results[tesisat].append("P")
                        else:
                            combined_results[tesisat] = ["P"]

        p_analizi(df_el31, decrease_percentage_p, decrease_count_p)

    # **T Analizleri Seçildiyse Çalıştır**
    if any(t in selected_analysis for t in ["T1 Analizi", "T2 Analizi", "T3 Analizi"]):

        def calc_avg(df, endeks_turu, threshold_ratio):
            filtered_df = df[df["Endeks Türü"] == endeks_turu].copy()
            if filtered_df.empty:
                return None

            filtered_df["Ortalama Tüketim"] = pd.to_numeric(
                filtered_df["Ortalama Tüketim"].astype(str).str.replace(",", ".", regex=True), errors="coerce"
            )
            nonzero_values = filtered_df["Ortalama Tüketim"].dropna()
            nonzero_values = nonzero_values[nonzero_values > 0].tolist()

            if not nonzero_values:
                return None

            avg_value = sum(nonzero_values) / len(nonzero_values)
            threshold_value = avg_value * (1 - threshold_ratio / 100)

            return avg_value, threshold_value

        def analyze_tesisat_data(df, threshold_ratio, below_threshold_limit):
            for tesisat, group in df.groupby("Tesisat"):
                suspicious_endeks_types = []

                for endeks_turu in ["T1", "T2", "T3"]:
                    if endeks_turu + " Analizi" not in selected_analysis:
                        continue

                    result = calc_avg(group, endeks_turu, threshold_ratio)
                    if result is None:
                        continue

                    avg_value, threshold_value = result

                    below_threshold_count = sum(
                        1
                        for val in pd.to_numeric(
                            group[group["Endeks Türü"] == endeks_turu]["Ortalama Tüketim"]
                            .astype(str)
                            .str.replace(",", ".", regex=True), errors="coerce"
                        ).dropna()
                        if val > 0 and val < threshold_value
                    )

                    if below_threshold_count > below_threshold_limit:
                        if tesisat in combined_results:
                            combined_results[tesisat].append(endeks_turu)
                        else:
                            combined_results[tesisat] = [endeks_turu]

        analyze_tesisat_data(df_zblir, decrease_percentage_t, decrease_count_t)

    if combined_results:
        df_combined = pd.DataFrame(list(combined_results.items()), columns=["Şüpheli Tesisat", "Şüpheli Analiz Türleri"])
        df_combined["Şüpheli Analiz Türleri"] = df_combined["Şüpheli Analiz Türleri"].apply(lambda x: ", ".join(x))

        # **İndeksi 1’den başlat**
        df_combined.index += 1  

        # **Sonuçları Göster**
        st.success(f"✅ Analizler Tamamlandı! **Toplam {len(df_combined)} şüpheli tesisat bulundu.**")
        st.dataframe(df_combined)

        # **Tek bir CSV dosyası olarak indir**
        st.download_button(
            "📥 Analiz Sonuçlarını İndir",
            df_combined.to_csv(sep=";", index=True).encode("utf-8"),  # index=True ile yeni indeksleri de ekliyoruz
            "analiz_sonuclari.csv",
            "text/csv"
        )
    else:
        st.warning("⚠️ Seçilen analizler sonucunda şüpheli tesisat bulunamadı!")




#BURAYA KADAR DA OKEY


# **ZIP Dosyalarını Grafiklemek için Buton**
if st.button("📊 Grafikleri Oluştur ve İndir"):

    st.subheader("📊 Grafikleme İşlemi Başlatıldı")

    # **Dosyaların var olup olmadığını kontrol et**
    el31_zip_path = "el31_duzenlenmis.zip"
    zblir_zip_path = "zblir_duzenlenmis.zip"

    if not os.path.exists(el31_zip_path) or not os.path.exists(zblir_zip_path):
        st.error("⚠️ EL31 veya ZBLIR düzenlenmiş ZIP dosyaları bulunamadı!")
        st.stop()

    # **Geçici Klasörler Oluştur**
    temp_folder_el31 = "temp_el31_xlsx"
    temp_folder_zblir = "temp_zblir_xlsx"
    output_folder = "output_xlsx_with_charts"

    os.makedirs(temp_folder_el31, exist_ok=True)
    os.makedirs(temp_folder_zblir, exist_ok=True)
    os.makedirs(output_folder, exist_ok=True)

    # **ZIP Dosyalarını Aç ve İçindeki Dosyaları Çıkart**
    with zipfile.ZipFile(el31_zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_folder_el31)

    with zipfile.ZipFile(zblir_zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_folder_zblir)

    # **Tüm Çıkartılan CSV Dosyalarını İşle**
    for folder in [temp_folder_el31, temp_folder_zblir]:
        for file_name in os.listdir(folder):
            if file_name.endswith('.csv'):
                file_path = os.path.join(folder, file_name)

                try:
                    # **CSV Dosyasını Oku**
                    df = pd.read_csv(file_path, delimiter=";", encoding="utf-8")

                    # **Gerekli Sütunları Kontrol Et**
                    required_columns = ['İlk Okuma Tarihi', 'Son Okuma Tarihi', 'Ortalama Tüketim', 'Muhatap Adı', 'Endeks Türü']
                    if not all(col in df.columns for col in required_columns):
                        st.warning(f"⚠️ {file_name} dosyasında eksik sütunlar var, atlanıyor.")
                        continue

                    # **Tarihleri Düzenle**
                    df['İlk Okuma Tarihi'] = pd.to_datetime(df['İlk Okuma Tarihi'], errors='coerce')
                    df['Son Okuma Tarihi'] = pd.to_datetime(df['Son Okuma Tarihi'], errors='coerce')
                    df = df.sort_values(by='İlk Okuma Tarihi')

                    # **X Ekseni için Tarihleri Birleştir**
                    df['Tarih'] = df['İlk Okuma Tarihi'].combine_first(df['Son Okuma Tarihi'])
                    df['Ortalama Tüketim'] = pd.to_numeric(df['Ortalama Tüketim'], errors='coerce')

                    # **Excel Dosyası Hazırla**
                    excel_filename = os.path.splitext(file_name)[0] + ".xlsx"
                    excel_path = os.path.join(output_folder, excel_filename)
                    df.to_excel(excel_path, index=False)

                    # **Excel Dosyasını Aç**
                    wb = load_workbook(excel_path)
                    ws = wb.active

                    # **Endeks Türlerine Göre Grafikler**
                    unique_endeks_types = df['Endeks Türü'].dropna().unique()

                    for endeks in unique_endeks_types:
                        df_filtered = df[df['Endeks Türü'] == endeks]

                        if df_filtered.empty:
                            continue

                        y_values = df_filtered['Ortalama Tüketim']
                        x_values = df_filtered['Tarih']

                        # **Eğer boş satırlar varsa uyarı ver ve devam et**
                        if x_values.isnull().all() or y_values.isnull().all():
                            st.warning(f"⚠️ {file_name} içindeki {endeks} endeksi için geçerli veri bulunamadı, atlanıyor.")
                            continue

                        avg_consumption = np.nanmean(y_values)

                        # **Muhatap Değişimlerini Belirle**
                        muhatap_degisimleri = df_filtered[df_filtered['Muhatap Adı'] != df_filtered['Muhatap Adı'].shift()]

                        # **Grafik Oluştur**
                        plt.figure(figsize=(10, 5))
                        plt.plot(x_values, y_values, marker='o', linestyle='-', color='b', label="Ortalama Tüketim")
                        plt.axhline(y=avg_consumption, color='r', linestyle='--', label="Ortalama Tüketim Ortalaması")

                        for _, row in muhatap_degisimleri.iterrows():
                            plt.axvline(x=row['Tarih'], color='g', linestyle=':', label="Muhatap Değişimi")

                        plt.text(x_values.iloc[-1], avg_consumption, f"Ortalama: {avg_consumption:.2f}",
                                 verticalalignment='bottom', horizontalalignment='right', color='r', fontsize=10, fontweight='bold')

                        plt.xlabel("Tarih")
                        plt.ylabel("Ortalama Tüketim")
                        plt.title(f"{file_name} - {endeks} Endeks Türü")
                        plt.xticks(rotation=45)
                        plt.legend()
                        plt.grid()

                        # **Grafiği Hafızaya Kaydet**
                        img_stream = BytesIO()
                        plt.savefig(img_stream, format='png')
                        plt.close()

                        # **Grafiği Excel'e Ekle**
                        img = Image(img_stream)
                        img.anchor = f"J{10 * (list(unique_endeks_types).index(endeks) + 1)}"
                        ws.add_image(img)

                    # **Yeni Dosyayı Kaydet**
                    wb.save(excel_path)

                except Exception as e:
                    st.error(f"⚠️ {file_name} dosyasında hata oluştu: {str(e)}")

    # **Grafikli Dosyaları ZIP'e Kaydet**
    output_zip_buffer = BytesIO()
    with zipfile.ZipFile(output_zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_name in os.listdir(output_folder):
            file_path = os.path.join(output_folder, file_name)
            zipf.write(file_path, arcname=file_name)

    output_zip_buffer.seek(0)

    # **Sonuçları Göster ve İndirme Butonu**
    st.success("✅ Grafikler oluşturuldu ve Excel dosyalarına eklendi!")
    st.download_button(
        "📥 Grafikli Dosyaları ZIP Olarak İndir",
        output_zip_buffer,
        "grafikli_dosyalar.zip",
        "application/zip"
    )

    # **Geçici Klasörleri Temizle**
    shutil.rmtree(temp_folder_el31)
    shutil.rmtree(temp_folder_zblir)
    shutil.rmtree(output_folder)



