import streamlit as st
import pandas as pd
import zipfile
import os

def a_to_f(df):
    drop_columns = [
        "Sözleşme grubu", "Sayaç okuma birimi", "Muhatap", "Sözleşme", "Cihaz", "Ekipman", "Endeks",
        "Giriş numarası", "Kontrol rakamı", "Planlanan SO tarihi", "Sayaç okuma nedeni", "Çoklu tayin",
        "Pln.sayaç okuma tipi", "Sayaç okuma türü", "Sayaç okuma durumu", "Vrg.önc.basamaklar", "Ondalık basamaklar",
        "Hizmet siparişi", "Hizmet bildirimi", "SO belge dahili tn.", "Sprş.çkt.önc.alındı", "Bağımsız doğrulama",
        "Bağlı doğrulama", "Sayaç notu", "Geriye dönük thk.drm.", "Sayaç okuma etkin", "Gelişmiş sayaç okuma sistemi",
        "İletim durumu kodu", "Zaman damgası", "Kaynak sistem", "Aktarma tarihi", "Aktarım saati",
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
    df = df.sort_values(by=["Tesisat", "Sayaç okuma tarihi", "Okunan sayaç durumu", "Sayaç okuma zamanı"],
                        ascending=[True, True, False, True])
    return df.groupby(["Tesisat", "Sayaç okuma tarihi"], as_index=False).first()

def remain_last_two(df, date_column, muhatap_column):
    df[date_column] = pd.to_datetime(df[date_column], dayfirst=True)
    df = df.sort_values(by=["Tesisat", date_column], ascending=[True, False])
    df = df.groupby("Tesisat").apply(lambda x: x[x[muhatap_column].isin(x[muhatap_column].unique()[:2])])
    return df.reset_index(drop=True)

def run_p_analysis():
    st.write("🔄 P Analizi çalıştırılıyor...")
    try:
        # Dosya işlemleri
        zip_file_path = "tesisat_files.zip"
        output_folder = "./extracted_files"
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(output_folder)
        
        suspicious_tesisats = []
        for file_name in os.listdir(output_folder):
            if file_name.endswith(".csv"):
                file_path = os.path.join(output_folder, file_name)
                df = pd.read_csv(file_path, delimiter=';', encoding='utf-8')
                df['Okunan sayaç durumu'] = df['Okunan sayaç durumu'].astype(str).str.replace(',', '.').astype(float)
                
                for tesisat, group in df.groupby('Tesisat'):
                    p_values = group[group['Endeks türü'] == 'P']['Okunan sayaç durumu'].dropna().tolist()
                    if len(p_values) > 3 and sum(p_values[-3:]) / 3 < sum(p_values[:-3]) / len(p_values[:-3]):
                        suspicious_tesisats.append([tesisat])
        
        # Sonuçları CSV olarak kaydet
        suspicious_df = pd.DataFrame(suspicious_tesisats, columns=['Şüpheli Tesisat'])
        suspicious_df.to_csv("p_analizi_sonucu.csv", index=False, sep=';', encoding='utf-8')
        st.success("✅ P Analizi tamamlandı! Şüpheli tesisatlar kaydedildi.")
    except Exception as e:
        st.error(f"Hata oluştu: {e}")

def run_t_analysis():
    st.write("🔄 T1, T2, T3 Analizi çalıştırılıyor...")
    try:
        zip_file_path = "tesisat_files.zip"
        output_folder = "./extracted_files"
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(output_folder)
        
        suspicious_tesisats = []
        for file_name in os.listdir(output_folder):
            if file_name.endswith(".csv"):
                file_path = os.path.join(output_folder, file_name)
                df = pd.read_csv(file_path, delimiter=';', encoding='utf-8')
                df['Ortalama Tüketim'] = df['Ortalama Tüketim'].astype(str).str.replace(',', '.').astype(float)
                
                for tesisat, group in df.groupby("Tesisat"):
                    for t in ["T1", "T2", "T3"]:
                        t_values = group[group['Endeks Türü'] == t]['Ortalama Tüketim'].dropna().tolist()
                        if len(t_values) > 3 and sum(t_values[-3:]) / 3 < sum(t_values[:-3]) / len(t_values[:-3]):
                            suspicious_tesisats.append([tesisat, t])
        
        suspicious_df = pd.DataFrame(suspicious_tesisats, columns=['Şüpheli Tesisat', 'Endeks Türü'])
        suspicious_df.to_csv("t_analizi_sonucu.csv", index=False, sep=';', encoding='utf-8')
        st.success("✅ T Analizi tamamlandı! Şüpheli tesisatlar kaydedildi.")
    except Exception as e:
        st.error(f"Hata oluştu: {e}")

st.title("🔎 Tespit Arayüzü")

# Kullanıcı arayüzü kodu burada devam ediyor...

if st.button("🚀 Analizi Başlat"):
    if "P Analizi" in analysis_types:
        run_p_analysis()
    if any(t in analysis_types for t in ["T1 Analizi", "T2 Analizi", "T3 Analizi"]):
        run_t_analysis()

