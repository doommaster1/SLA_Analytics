import os
from datetime import datetime

import joblib
import numpy as np
import pandas as pd  # Kita butuh pandas untuk holiday

# Coba impor holidays, jika gagal, beri peringatan
try:
    from holidays import Indonesia
except ImportError:
    print("WARNING: 'holidays' library not installed. 'Is Holiday' feature will be 0.")
    Indonesia = None

class SLAPredictor:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, 'rf_sla_model.pkl')
        encoders_path = os.path.join(script_dir, 'label_encoders.pkl')
        scaler_path = os.path.join(script_dir, 'minmax_scaler.pkl')
        features_path = os.path.join(script_dir, 'feature_names.pkl')
        threshold_path = os.path.join(script_dir, 'best_threshold.pkl')
        
        # Inisialisasi kalender libur
        if Indonesia:
            # Ambil tahun sekarang dan tahun depan untuk kalender libur
            current_year = datetime.now().year
            self.holidays_id = Indonesia(years=[current_year, current_year + 1])
            self.holiday_dates = set(self.holidays_id.keys())
        else:
            self.holiday_dates = set()

        # Validasi file
        missing_files = []
        for path, name in [
            (model_path, 'rf_sla_model.pkl'), 
            (encoders_path, 'label_encoders.pkl'), 
            (scaler_path, 'minmax_scaler.pkl'), 
            (features_path, 'feature_names.pkl')
        ]:
            if not os.path.exists(path):
                missing_files.append(name)
        
        if missing_files:
            raise FileNotFoundError(f"File hilang di {script_dir}: {', '.join(missing_files)}. Pastikan Anda sudah melatih ulang model dan menyalin file .pkl yang baru.")
        
        self.model = joblib.load(model_path)
        self.encoders = joblib.load(encoders_path) # Dict encoders
        self.scaler = joblib.load(scaler_path)
        self.feature_names = joblib.load(features_path)
        self.threshold = joblib.load(threshold_path)
        
        # Cari tahu kolom mana yang di-scale saat training
        # Ini jauh lebih aman daripada hardcode indeks
        try:
            # Cek scaler punya atribut features_names_in_ (dari scikit-learn >= 0.24)
            self.scaled_feature_names = self.scaler.feature_names_in_
            print(f"Scaler dilatih pada fitur: {self.scaled_feature_names}")
        except AttributeError:
            # Fallback jika versi scikit-learn lama (mengambil dari notebook Anda)
            self.scaled_feature_names = ['Days to Due'] # Sesuaikan jika Anda mengubah scaling di notebook
            print(f"Scaler fallback, asumsi fitur: {self.scaled_feature_names}")
            
        print("Model (versi baru) berhasil dimuat!")
        print(f"Model ini mengharapkan {len(self.feature_names)} fitur:")
        print(self.feature_names)


    def _is_off(self, dt):
        """ Cek apakah tanggal adalah weekend (Sabtu=5, Minggu=6) atau hari libur """
        is_weekend = dt.weekday() >= 5
        is_holiday = dt.date() in self.holiday_dates
        return 1 if (is_weekend or is_holiday) else 0

    def preprocess_input(self, input_data):
        print("\n" + "="*30)
        print("=== 1. PREPROCESS_INPUT DIMULAI ===")
        print(f"Input Data Mentah: {input_data}")

        # 1. Konversi Tanggal
        try:
            open_dt = datetime.fromisoformat(input_data['open_date'])
            due_dt = datetime.fromisoformat(input_data['due_date'])
            print(f"Tanggal dikonversi: Open={open_dt}, Due={due_dt}")
        except Exception as e:
            print(f"!!! ERROR TANGGAL: {e}")
            raise e

        # 2. Buat DataFrame
        processed_df = pd.DataFrame(columns=self.feature_names)
        
        # 3. Hitung Fitur Turunan
        days_to_due_val = (due_dt - open_dt).days
        processed_df.loc[0, 'Days to Due'] = days_to_due_val
        print(f"Days to Due: {days_to_due_val}")
        
        open_month_val = open_dt.month
        processed_df.loc[0, 'Open Month'] = open_month_val
        print(f"Open Month: {open_month_val}")
        
        # ... (tambahkan print untuk fitur turunan lainnya: Hour, Day of Week, Is Off) ...
        processed_df.loc[0, 'Application Creation Hour'] = open_dt.hour
        print(f"Creation Hour: {open_dt.hour}")
        processed_df.loc[0, 'Is Open Date Off'] = self._is_off(open_dt)
        print(f"Is Open Off: {self._is_off(open_dt)}")


        # 4. Handle Fitur Kategorikal
        print("\n--- Encoding Dimulai ---")
        for col_name_map in [
            ('Priority', 'priority'), 
            ('Category', 'category'),
            ('Item', 'item'),
            ('Sub Category', 'sub_category')
        ]:
            notebook_col, react_col = col_name_map
            if notebook_col in self.encoders:
                le = self.encoders[notebook_col]
                input_val = input_data.get(react_col, 'nan').lower().strip()
                
                if input_val in le.classes_:
                    encoded_val = le.transform([input_val])[0]
                    print(f"Encode {notebook_col}: '{input_val}' -> {encoded_val}")
                else:
                    print(f"!!! '{input_val}' (untuk {notebook_col}) TIDAK DITEMUKAN di encoder.")
                    if 'unknown' in le.classes_:
                         encoded_val = le.transform(['unknown'])[0]
                         print(f"    -> Fallback ke 'unknown': {encoded_val}")
                    else:
                         encoded_val = -1
                         print(f"    -> Fallback ke -1")
                
                processed_df.loc[0, notebook_col] = encoded_val
        print("--- Encoding Selesai ---")

        # 5. Fillna
        processed_df = processed_df.fillna(0)
        
        # 6. Scaling
        if self.scaled_feature_names:
            cols_to_scale = [col for col in self.scaled_feature_names if col in processed_df.columns]
            if cols_to_scale:
                print(f"\nScaling kolom: {cols_to_scale}")
                # Ambil nilai sebelum di-scale
                before_scale = processed_df[cols_to_scale].values
                processed_df[cols_to_scale] = self.scaler.transform(processed_df[cols_to_scale])
                # Ambil nilai sesudah di-scale
                after_scale = processed_df[cols_to_scale].values
                print(f"Nilai '{cols_to_scale[0]}' SEBELUM scale: {before_scale[0][0]}")
                print(f"Nilai '{cols_to_scale[0]}' SETELAH scale: {after_scale[0][0]}")

        # 7. Kembalikan array
        final_array = processed_df[self.feature_names].values
        print(f"\nBentuk Array Final: {final_array.shape}")
        print("=== PREPROCESS_INPUT SELESAI ===\n")
        return final_array
  

    def predict(self, input_data):
        try:
            # 1. Preprocessing input
            X = self.preprocess_input(input_data)

            print("\n" + "=" * 30)
            print("=== 2. PREDICT DIMULAI ===")
            print(f"Data array yang akan diprediksi:\n{X}")

            # 2. Dapatkan probabilitas dari model
            proba_all = self.model.predict_proba(X)[0]
            print(f"Probabilitas Mentah (Semua Kelas): {proba_all}")
            print(f"Kelas Model: {self.model.classes_}")

            # 3. Cari probabilitas untuk kelas '1' (Melanggar)
            violated_idx = np.where(self.model.classes_ == 1)[0][0]
            pred_proba = proba_all[violated_idx]
            print(f"Probabilitas Melanggar (Kelas 1): {pred_proba:.6f}")

            # 4. Terapkan threshold
            print(f"Threshold yang Digunakan: {self.threshold}")
            model_prediction = 1 if pred_proba >= self.threshold else 0
            print(f"Hasil Prediksi Model (sebelum hardcode): {model_prediction}")
            model_confidence = pred_proba * 100

            # 5. Logika hardcode '1 - critical'
            input_priority_raw = input_data.get('priority', '').strip().lower()
            if input_priority_raw == '1 - critical':
                final_prediction = 1
                final_confidence = 100.0
                final_text = 'Ya (Aturan Bisnis)'
            else:
                final_prediction = model_prediction
                final_confidence = model_confidence
                final_text = 'Ya' if final_prediction else 'Tidak'

            print(f"Prediksi Final (setelah hardcode): {final_prediction}")
            print("=== PREDICT SELESAI ===")

            # --- START PERBAIKAN UNTUK FRONTEND REACT ---
            # Frontend React mengharapkan key/data yang berbeda.

            # A. Ambil/Hitung ulang data untuk UI (Days to Due & Open Hour)
            try:
                open_dt = datetime.fromisoformat(input_data['open_date'])
                due_dt = datetime.fromisoformat(input_data['due_date'])
                ui_days_to_due = (due_dt - open_dt).days
                ui_open_hour = open_dt.hour
            except Exception:
                ui_days_to_due = -1
                ui_open_hour = -1

            # B. Siapkan risk factors & recommendations
            ui_risk_factors = []
            ui_recommendations = ""

            if final_prediction == 1:
                # Jika diprediksi Melanggar
                ui_risk_factors.append(f"Probabilitas pelanggaran: {final_confidence:.2f}%")
                if ui_days_to_due <= 3:
                    ui_risk_factors.append("Waktu pengerjaan (Days to Due) singkat")
                if input_priority_raw == '1 - critical':
                    ui_risk_factors.append("Aturan Bisnis: Tiket Critical")
                ui_recommendations = (
                    "Rekomendasikan eskalasi ke tim terkait atau pantau tiket ini secara proaktif."
                )
            else:
                # Jika diprediksi Aman
                ui_risk_factors.append(f"Risiko pelanggaran rendah ({final_confidence:.2f}%)")
                if ui_days_to_due > 10:
                    ui_risk_factors.append("Waktu pengerjaan (Days to Due) panjang")
                ui_recommendations = "Tiket dapat diproses sesuai alur kerja standar."

            # C. Buat dictionary return yang sesuai dengan kebutuhan React
            return {
                'status': 'sukses',
                'sla_violated': bool(final_prediction),
                'confidence': final_confidence,
                'violation_text': final_text,              # Ganti 'text_result' -> 'violation_text'
                'days_to_due': ui_days_to_due,
                'open_hour': ui_open_hour,
                'risk_factors': ui_risk_factors,
                'recommended_actions': ui_recommendations
            }
            # --- AKHIR PERBAIKAN ---

        except Exception as e:
            print(f"!!! ERROR SAAT PREDIKSI: {e}")
            return {'status': 'error', 'message': str(e)}

    

        


    