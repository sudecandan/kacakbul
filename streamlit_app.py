import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO
import matplotlib.pyplot as plt
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# STREAMLIT BAŞLIĞI
st.title("⚡ KaçakBul")

# DOSYA YÜKLEME KISIMLARI
col1, col2, col3 = st.columns(3)

with col1:
    el31_file = st.file_uploader("📂 EL31 Dosyasını Yükleyin (.csv)", type=["csv"])
    
with col2:
    zblir_file = st.file_uploader("📂 ZBLIR_002 Dosyasını Yükleyin (.csv)", type=["csv"])

with col3:
    zdm240_file = st.file_uploader("📂 ZDM240 Dosyasını Yükleyin (.csv)", type=["csv"])

# YÜKLENEN DOSYALARIN ÖNİZLEMESİ    
col1, col2, col3 = st.columns(3)

if el31_file:
    with col1:
        df_el31 = pd.read_csv(el31_file, delimiter=";", encoding="utf-8")
        st.write("🔹 **EL31 Dosyası Önizleme**")
        st.dataframe(df_el31.head())
if zblir_file:
    with col2:
        df_zblir = pd.read_csv(zblir_file, delimiter=";", encoding="utf-8")
        st.write("🔹 **ZBLIR_002 Dosyası Önizleme**")
        st.dataframe(df_zblir.head())
if zdm240_file:
    with col3:
        df_zdm240 = pd.read_csv(zdm240_file, delimiter=";", encoding="utf-8")
        st.write("🔹 **ZDM240 Dosyası Önizleme**")
        st.dataframe(df_zdm240.head())


# **EL31 VERİLERİNİ DÜZENLEME**
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

# **ZBLIR_002 VERİLERİNİ DÜZENLEME**
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





#BURAYA KADAR OKEYYYYYYYYYY





# 📊 Kullanıcıdan analiz için giriş al
if el31_file and zblir_file and zdm240_file:
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



col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📉 **P Analizi**")
    decrease_percentage_p = st.number_input("P Yüzde Kaç Düşüş?", min_value=1, max_value=100, step=1, value=30)
    decrease_count_p = st.number_input("P Kaç Kez Düşüş?", min_value=1, max_value=10, step=1, value=3)

with col2:
    st.markdown("#### 📉 **T Analizi**")
    decrease_percentage_t = st.number_input("T Yüzde Kaç Düşüş?", min_value=1, max_value=100, step=1, value=50)
    decrease_count_t = st.number_input("T Kaç Kez Düşüş?", min_value=1, max_value=10, step=1, value=5)





# **Seçili analizleri belirleme**
selected_analysis = [key for key, value in st.session_state.selected_analysis.items() if value]









#BURAYA DÜZENLENMİŞ LİSTELER İÇİN OLUŞTURULAN GRAFİKLER İÇİN OLAN KODLAR GELECEK





#BURAYA KADAR DA OKEY















import streamlit as st
import pandas as pd
import os

# 📌 **Saklanacak dosya yolları**
FILE_PATHS = {
    "Sektör Listesi": "sector_list.csv",
    "Sektör Puan Listesi": "sector_score_list.csv",
    "Çarpan Listesi": "multiplier_list.csv",
    "Çarpan Puan Listesi": "multiplier_score_list.csv",
    "Boğaz Mahalle Listesi": "bogaz_neighborhood_list.csv",
    "Karadeniz Mahalle Listesi": "karadeniz_neighborhood_list.csv",
    "Marmara Mahalle Listesi 1": "marmara1_neighborhood_list.csv",
    "Marmara Mahalle Listesi 2": "marmara2_neighborhood_list.csv",
    "Mahalle Puan Listesi": "neighborhood_score_list.csv",
    "Şube Kablo Değişme Listesi": "cable_change_list.csv",
    "Şube Kablo Değişme Puan Listesi": "cable_change_score_list.csv",

}

WEIGHTS_FILE = "weights.csv"
UPLOADED_FILES_RECORD = "uploaded_files.csv"

DEFAULT_WEIGHTS = {
    "Sektör Puanı Ağırlığı": 0.30,
    "Çarpan Puanı Ağırlığı": 0.20,
    "Mahalle Puanı Ağırlığı": 0.30,
    "Şube Kablo Puanı Ağırlığı": 0.20
}

def save_weights(weights):
    df = pd.DataFrame([weights])
    df.to_csv(WEIGHTS_FILE, index=False)

def load_weights():
    if os.path.exists(WEIGHTS_FILE):
        df = pd.read_csv(WEIGHTS_FILE)
        return df.iloc[0].to_dict()
    return DEFAULT_WEIGHTS

def save_uploaded_files(files):
    df = pd.DataFrame(list(files.items()), columns=["Dosya Adı", "Dosya Yolu"])
    df.to_csv(UPLOADED_FILES_RECORD, index=False)

def load_uploaded_files():
    if os.path.exists(UPLOADED_FILES_RECORD):
        df = pd.read_csv(UPLOADED_FILES_RECORD)
        return dict(zip(df["Dosya Adı"], df["Dosya Yolu"]))
    return {key: None for key in FILE_PATHS.keys()}

# 📌 **Varsayılan Listeleri ve Ağırlık Dosyasını Oluştur**
for file in FILE_PATHS.values():
    if not os.path.exists(file):
        pd.DataFrame(columns=["Değer"]).to_csv(file, index=False, sep=";")

if not os.path.exists(WEIGHTS_FILE):
    save_weights(DEFAULT_WEIGHTS)

if not os.path.exists(UPLOADED_FILES_RECORD):
    save_uploaded_files({key: None for key in FILE_PATHS.keys()})

# 📌 **Session State Güncelleme**
if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = load_uploaded_files()
if "weights" not in st.session_state:
    st.session_state["weights"] = load_weights()

# --- ADMIN PANELİ GİRİŞİ ---
def admin_login():
    """Admin giriş ekranı."""
    st.sidebar.subheader("🔐 Admin Girişi")
    
    username = st.sidebar.text_input("Kullanıcı Adı", key="admin_username_input")
    password = st.sidebar.text_input("Şifre", type="password", key="admin_password_input")

    if st.sidebar.button("Giriş Yap"):
        if username == "admin" and password == "password123":  
            st.session_state["admin_authenticated"] = True
            st.sidebar.success("✅ Başarıyla giriş yapıldı!")
        else:
            st.sidebar.error("🚫 Hatalı kullanıcı adı veya şifre!")

    # 📌 **Admin Çıkış Butonu**
    if st.sidebar.button("🚪 Çıkış Yap"):
        st.session_state["admin_authenticated"] = False
        st.sidebar.success("✅ Başarıyla çıkış yapıldı!")
        st.rerun()

admin_login()

# 🟠 **Admin Paneli Açıldıysa Listeler Yönetilebilir**
if st.session_state["admin_authenticated"]:
    st.sidebar.subheader("📂 **Listeleri Güncelle**")

    for list_name, file_path in FILE_PATHS.items():
        # Önceden yüklenmiş dosya varsa göster
        if st.session_state["uploaded_files"].get(list_name):
            st.sidebar.markdown(f"📂 **Son Yüklenen Dosya:** `{st.session_state['uploaded_files'][list_name]}`")

        uploaded_file = st.sidebar.file_uploader(f"📌 {list_name} Dosya Yükleyin", type=["csv"], key=list_name)
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8", delimiter=";", low_memory=False)
                df.to_csv(file_path, index=False, sep=";")

                st.session_state["uploaded_files"][list_name] = file_path  
                save_uploaded_files(st.session_state["uploaded_files"])  

                st.sidebar.success(f"✅ {list_name} güncellendi ve kaydedildi!")
            except Exception as e:
                st.sidebar.error(f"⚠️ Hata: Dosya yüklenemedi! {str(e)}")

# 📌 **Admin giriş yaptıysa ağırlıkları girebilir**
if st.session_state["admin_authenticated"]:
    st.sidebar.subheader("📊 **Ağırlık Katsayılarını Girin**")

    sektor_weight = st.sidebar.number_input("Sektör Puanı Ağırlığı", min_value=0.0, max_value=1.0, step=0.01, value=st.session_state["weights"]["Sektör Puanı Ağırlığı"])
    carpan_weight = st.sidebar.number_input("Çarpan Puanı Ağırlığı", min_value=0.0, max_value=1.0, step=0.01, value=st.session_state["weights"]["Çarpan Puanı Ağırlığı"])
    mahalle_weight = st.sidebar.number_input("Mahalle Puanı Ağırlığı", min_value=0.0, max_value=1.0, step=0.01, value=st.session_state["weights"]["Mahalle Puanı Ağırlığı"])
    sube_kablo_weight = st.sidebar.number_input("Şube Kablo Puanı Ağırlığı", min_value=0.0, max_value=1.0, step=0.01, value=st.session_state["weights"]["Şube Kablo Puanı Ağırlığı"])

    # 📌 **Ağırlıkları Kaydet Butonu**
    if st.sidebar.button("✅ Değişiklikleri Kaydet"):
        new_weights = {
            "Sektör Puanı Ağırlığı": sektor_weight,
            "Çarpan Puanı Ağırlığı": carpan_weight,
            "Mahalle Puanı Ağırlığı": mahalle_weight,
            "Şube Kablo Puanı Ağırlığı": sube_kablo_weight
        }
        save_weights(new_weights)  
        st.session_state["weights"] = new_weights  
        st.sidebar.success("📌 Ağırlık katsayıları başarıyla güncellendi!")

































#BURAYA KADAR OKEYDİR.




# 📌 **Session State ile Analiz Sonuçlarını Kaydet**
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "selected_tesisat" not in st.session_state:
    st.session_state.selected_tesisat = None  # Kullanıcının seçtiği tesisat numarası






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


        # 📌 **Analiz Sonuçlarını Session State'e Kaydet**
        st.session_state.analysis_results = df_combined 

        # **Tek bir CSV dosyası olarak indir**
        st.download_button(
            "📥 Analiz Sonuçlarını İndir",
            df_combined.to_csv(sep=";", index=True).encode("utf-8"),  # index=True ile yeni indeksleri de ekliyoruz
            "analiz_sonuclari.csv",
            "text/csv"
        )
    else:
        st.warning("⚠️ Seçilen analizler sonucunda şüpheli tesisat bulunamadı!")



# 📌 **Eğer analiz sonuçları varsa, sabit olarak ekranda göster**
if st.session_state.analysis_results is not None:
    st.success(f"✅ Analizler Tamamlandı! **Toplam {len(st.session_state.analysis_results)} şüpheli tesisat bulundu.**")
    st.dataframe(st.session_state.analysis_results)































col1 = st.columns(1)[0]  # Tek sütun kullan

with col1:
    seasonal_analysis_enabled = st.checkbox("### **Mevsimsel Dönem Analizi**", key="seasonal_analysis")

if seasonal_analysis_enabled:
    decrease_percentage_q = st.number_input("Q Yüzde Kaç Düşüş?", min_value=1, max_value=100, step=1, value=30)





#BURAYA Q ANALİZİ GELECEK!!!!!!!










# 📌 **Tesisatları Öncelik Sırasına Göre Sırala Butonu**
st.header("⚡ Tesisat Öncelik Sıralaması")

if st.button("📊 **Tesisatları Sırala**"):

    # **P ve T analizleri sonucunda bulunan şüpheli tesisatlar**
    if st.session_state.analysis_results is None or st.session_state.analysis_results.empty:
        st.warning("⚠️ Henüz analiz yapılmadı veya şüpheli tesisat bulunamadı!")
    else:
        supheli_tesisatlar = st.session_state.analysis_results["Şüpheli Tesisat"].tolist()

        # 📌 **Gerekli CSV Dosyalarını Yükle**
        sektor_list = pd.read_csv(st.session_state["uploaded_files"]["Sektör Listesi"], dtype=str, delimiter=';')
        carpan_list = pd.read_csv(st.session_state["uploaded_files"]["Çarpan Listesi"], dtype=str, delimiter=';')
        mahalle1_list = pd.read_csv(st.session_state["uploaded_files"]["Marmara Mahalle Listesi 1"], dtype=str, delimiter=';')
        mahalle2_list = pd.read_csv(st.session_state["uploaded_files"]["Marmara Mahalle Listesi 2"], dtype=str, delimiter=';')
        bogaz_list = pd.read_csv(st.session_state["uploaded_files"]["Boğaz Mahalle Listesi"], dtype=str, delimiter=';')
        karadeniz_list = pd.read_csv(st.session_state["uploaded_files"]["Karadeniz Mahalle Listesi"], dtype=str, delimiter=';')
        sube_kablo_list = pd.read_csv(st.session_state["uploaded_files"]["Şube Kablo Değişme Listesi"], dtype=str, delimiter=';')
        mahalle_puan_list = pd.read_csv(st.session_state["uploaded_files"]["Mahalle Puan Listesi"], dtype=str, delimiter=';')

        # 📌 **Ağırlık Değerlerini Al**
        sektor_weight = st.session_state["weights"]["Sektör Puanı Ağırlığı"]
        carpan_weight = st.session_state["weights"]["Çarpan Puanı Ağırlığı"]
        mahalle_weight = st.session_state["weights"]["Mahalle Puanı Ağırlığı"]
        sube_kablo_weight = st.session_state["weights"]["Şube Kablo Puanı Ağırlığı"]

    

        
        # 📌 **Verileri Sözlüklere Dönüştürme**
        sektor_dict = dict(zip(sektor_list['Tesisat'], sektor_list['Nace Kodu']))
        carpan_dict = dict(zip(carpan_list['Tesisat'], carpan_list['Tahakkuk faktörü']))
        sube_kablo_dict = dict(zip(sube_kablo_list['Tesisat'], sube_kablo_list['Kablo']))

        # 📌 **Mahalle Eşleşmesi**
        mahalle_tesisat_dict = {}
        for df, mahalle_adi in zip([mahalle1_list, mahalle2_list, bogaz_list, karadeniz_list],
                                   ["Marmara 1", "Marmara 2", "Boğaz", "Karadeniz"]):
            for _, row in df.iterrows():
                mahalle_tesisat_dict[row['Tesisat']] = row['Mahalle']

        # 📌 **Mahalle Puanları**
        mahalle_puan_dict = dict(zip(mahalle_puan_list['Mahalle'], mahalle_puan_list['Puan']))

        # 📌 **Şüpheli Tesisatları Puanlama**
        results = []
        for tesisat in supheli_tesisatlar:
            nace_kodu = sektor_dict.get(tesisat, None)
            tahakkuk_faktoru = carpan_dict.get(tesisat, None)
            kablo = sube_kablo_dict.get(tesisat, None)
            mahalle_adi = mahalle_tesisat_dict.get(tesisat, None)

            mahalle_puan = float(mahalle_puan_dict.get(mahalle_adi, "0").replace(',', '.')) if mahalle_adi else 0
            sektor_puan = float(sektor_dict.get(nace_kodu, "0").replace(',', '.')) if nace_kodu else 0
            carpan_puan = float(carpan_dict.get(tahakkuk_faktoru, "0").replace(',', '.')) if tahakkuk_faktoru else 0
            sube_kablo_puan = float(sube_kablo_dict.get(kablo, "0").replace(',', '.')) if kablo else 0

            toplam_puan = (
                (sektor_puan * sektor_weight) +
                (carpan_puan * carpan_weight) +
                (mahalle_puan * mahalle_weight) +
                (sube_kablo_puan * sube_kablo_weight)
            )

            results.append([tesisat, toplam_puan])

        # 📌 **Sonuçları Sırala ve Göster**
        df_sorted = pd.DataFrame(results, columns=['Tesisat', 'Puan']).sort_values(by="Puan", ascending=False)
        
        st.success(f"✅ Şüpheli tesisatlar başarıyla sıralandı! Toplam {len(df_sorted)} tesisat listelendi.")
        st.dataframe(df_sorted)

        # 📌 **İndirme Butonu**
        st.download_button("📥 Sıralanmış Şüpheli Tesisatları İndir",
                           df_sorted.to_csv(sep=";", index=False).encode("utf-8"),
                           "supheli_tesisatlar_sirali.csv",
                           "text/csv")
