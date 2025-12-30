import csv
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from tickets.models import Ticket


class Command(BaseCommand):
    help = 'Import tickets from CSV'

    def handle(self, *args, **options):
        # ... (kode path file Anda sudah benar) ...
        csv_path = os.path.join('tickets', 'management', 'commands', 'processed_tickets.csv')
        
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f"File tidak ditemukan: {csv_path}"))
            return
        
        self.stdout.write(f"File ditemukan: {csv_path}")
        
        # ----- BARU: Buat mapping untuk prioritas -----
        priority_mapping = {
            'Low': '4 - Low',
            'Medium': '3 - Medium',
            '2 - High': '2 - High',  # Amankan nilai yang sudah benar
            'Critical': '1 - Critical',
            # Tambahkan nilai lain jika ada, misal:
            # '1 - Critical': '1 - Critical' 
        }
        # ---------------------------------------------
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            imported_count = 0
            
            # Hapus data lama sebelum impor baru (WAJIB!)
            self.stdout.write("Menghapus data tiket lama...")
            Ticket.objects.all().delete()
            self.stdout.write("Data lama dihapus.")

            for row in reader:
                try:
                    open_date_naive = datetime.strptime(row['Open Date'], '%Y-%m-%d %H:%M:%S') 
                    due_date_naive = datetime.strptime(row['Due Date'], '%Y-%m-%d %H:%M:%S')
                    closed_date_naive = None
                    if row['Closed Date']:
                        closed_date_naive = datetime.strptime(row['Closed Date'], '%Y-%m-%d %H:%M:%S')
                    
                    # ----- PERUBAHAN DI SINI -----
                    # Ambil nilai prioritas dari CSV
                    raw_priority = row['Priority']
                    # Map ke nilai yang konsisten
                    # .get() akan menggunakan nilai default (raw_priority itu sendiri) jika tidak ada di map
                    # Tapi kita ingin memastikan HANYA nilai yang ter-map yang masuk
                    mapped_priority = priority_mapping.get(raw_priority)

                    # Jika mapping tidak ditemukan, lewati baris ini atau beri peringatan
                    if not mapped_priority:
                         self.stdout.write(self.style.WARNING(f"Skipping row {row.get('Number')}: Prioritas '{raw_priority}' tidak dikenal."))
                         continue
                    # -----------------------------

                    Ticket.objects.create(
                        number=row['Number'],             
                        
                        priority=mapped_priority,  # <-- Gunakan nilai yang sudah di-map
                        
                        category=row['Category'],
                        open_date=timezone.make_aware(open_date_naive),
                        closed_date=timezone.make_aware(closed_date_naive) if closed_date_naive else None,
                        due_date=timezone.make_aware(due_date_naive),
                        time_left_incl_on_hold=float(row['Time Left Incl. On Hold']),
                        item=row['Item'],          
                        is_sla_violated=bool(int(row['Is SLA Violated'])),
                        is_open_date_off=True if row['Is Open Date Off'] == 'Hari Libur' else False,
                        is_due_date_off=True if row['Is Due Date Off'] == 'Hari Libur' else False,
                        days_to_due=int(row['Days to Due']),
                        open_month=int(row['Open Month']),
                        application_creation_day_of_week=row['Application Creation Day of Week'],
                        application_creation_hour=int(row['Application Creation Hour']),
                        application_sla_deadline_day_of_week=row['Application SLA Deadline Day of Week'],
                        application_sla_deadline_hour=int(row['Application SLA Deadline Hour']),
                        resolution_duration=float(row['Resolution Duration']),
                        total_tickets_resolved_wc=float(row['Total Tickets Resolved (Wc)']),
                        sla_threshold=float(row['SLA Threshold']),
                        average_resolution_time_ac=float(row['Average Resolution Time (Ac)']),
                        sla_to_average_resolution_ratio_rc=float(row['SLA to Average Resolution Ratio (Rc)']),
                        application_sla_compliance_rate=float(row['Application SLA Compliance Rate']),
                    )
                    imported_count += 1
                except ValueError as e:
                    self.stdout.write(self.style.WARNING(f"Error parsing row {row.get('Number', 'unknown')}: {e}"))
                    continue
            
            self.stdout.write(self.style.SUCCESS(f'Import selesai! {imported_count} rows imported.'))