import json
import os
from datetime import timedelta

import joblib
import numpy as np
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import status, viewsets
from rest_framework.decorators import (api_view,  # Update baris ini
                                       permission_classes)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import (AllowAny,  # Tambahkan baris ini
                                        IsAuthenticated)
from rest_framework.response import Response

from .models import Ticket, UserProfile
from .serializers import TicketSerializer
from .utils.model_utils import SLAPredictor

AuthUser = get_user_model()
predictor = SLAPredictor()
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ENCODERS_PATH = os.path.join(APP_DIR, "utils", "label_encoders.pkl")
FEATURE_IMPORTANCE_PATH = os.path.join(APP_DIR, "utils", "feature_importances.json")

# Warna Cluster K=3 (digunakan di helper function)
cluster_colors = ['rgba(59, 130, 246, 0.8)', 'rgba(72, 187, 120, 0.8)', 'rgba(239, 68, 68, 0.8)'] 


# --- FUNGSI HELPER UNTUK QUERYSET ---
def get_filtered_queryset(request):
    """
    Fungsi helper terpusat untuk menerapkan filter umum
    dari query parameter ke Ticket queryset.
    """
    queryset = Ticket.objects.all()

    # Filter Prioritas
    priority_filter = request.query_params.get("priority", None)
    if priority_filter and priority_filter != "all":
        queryset = queryset.filter(priority=priority_filter)

    # Filter Pelanggaran SLA
    violation_filter = request.query_params.get("is_sla_violated", None)
    if violation_filter and violation_filter != "all":
        if violation_filter == "true":
            queryset = queryset.filter(is_sla_violated=True)
        elif violation_filter == "false":
            queryset = queryset.filter(is_sla_violated=False)

    return queryset


# --- FUNGSI HELPER BARU UNTUK CLUSTERING & DATA SAFETY ---
def safe_get_mean(summary, cluster_id, col_name, default=0.0):
    """
    Mengambil nilai rata-rata numerik dari summary, 
    mengubah string 'NaN' atau np.nan menjadi default (0.0).
    """
    raw_val = summary.get(str(cluster_id), {}).get('mean_numerical', {}).get(col_name)
    
    if isinstance(raw_val, (float, int)):
        return raw_val if not np.isnan(raw_val) else default
    
    if raw_val is None or raw_val == 'NaN':
        return default
        
    try:
        if isinstance(raw_val, np.generic):
            float_val = raw_val.item()
            return float_val if not np.isnan(float_val) else default
    except Exception:
        pass
        
    try:
        return float(raw_val)
    except (ValueError, TypeError):
        return default

def create_scatter_dataset(coords, labels, num_clusters, limit=2000):
    """
    Fungsi helper untuk memproses (sampling + formatting) koordinat 2D (PCA/MCA/UMAP)
    menjadi datasets yang siap untuk Chart.js.
    """
    if not coords or not labels or len(coords) != len(labels):
        return None
    
    total_points = len(coords)
    
    if total_points > limit:
        np.random.seed(42) # Untuk konsistensi sampling
        indices = np.random.choice(total_points, limit, replace=False)
    else:
        # PENTING: Menggunakan semua indeks jika sampling tidak diperlukan
        indices = np.arange(total_points) 
        
    datasets = []
    for cluster_id in range(num_clusters):
        points = [
            {"x": float(coords[i][0]), "y": float(coords[i][1])}
            for i in indices if int(labels[i]) == cluster_id
        ]
        datasets.append({
            "label": f"Cluster {cluster_id}",
            "data": points,
            "backgroundColor": cluster_colors[cluster_id % len(cluster_colors)],
            "pointRadius": 3,
        })
    return {"datasets": datasets}


# --- API VIEWS ---

@api_view(["POST"])
def send_otp(request):
    # ... (kode send_otp tidak berubah) ...
    email = request.data.get("email")
    if not email:
        return Response({"error": "Email diperlukan"}, status=400)

    otp = get_random_string(6, allowed_chars="0123456789")
    expiry = timezone.now() + timedelta(minutes=10)

    user, created = AuthUser.objects.get_or_create(email=email, defaults={"username": email})
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.otp_code = otp
    profile.otp_expiry = expiry
    profile.save()

    send_mail(
        "OTP Reset Password SLA Predictor",
        f"Kod OTP Anda: {otp} (kadaluarsa 10 menit)",
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

    return Response({"message": "OTP dikirim ke email Anda"})


@api_view(["POST"])
def verify_otp(request):
    # ... (kode verify_otp tidak berubah) ...
    email = request.data.get("email")
    otp = request.data.get("otp")
    password = request.data.get("new_password")

    if not all([email, otp, password]):
        return Response({"error": "Email, OTP, dan password baru diperlukan"}, status=400)

    try:
        user = AuthUser.objects.get(email=email)
        profile = UserProfile.objects.get(user=user)
        if profile.otp_expiry < timezone.now() or profile.otp_code != otp:
            return Response({"error": "OTP salah atau kadaluarsa"}, status=400)

        user.set_password(password)
        user.save()
        profile.email_verified = True
        profile.otp_code = ""
        profile.save()

        return Response({"message": "Password berhasil direset! Silakan login."})
    except AuthUser.DoesNotExist:
        return Response({"error": "Email tidak terdaftar"}, status=400)


@api_view(["GET"])
def get_feature_importance(request):
    # ... (kode get_feature_importance tidak berubah) ...
    try:
        with open(FEATURE_IMPORTANCE_PATH, "r") as f:
            importance_data = json.load(f)
            if isinstance(importance_data, list):
                return Response(importance_data[:10])
            return Response(importance_data)
    except FileNotFoundError:
        return Response({"error": f"File {os.path.basename(FEATURE_IMPORTANCE_PATH)} tidak ditemukan."}, status=500)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
def get_clusters(request):
    """
    API utama untuk data clustering K-Prototypes.
    Memproses UMAP/t-SNE (Hybrid), PCA (Numerik), dan MCA (Kategorikal) Scatter.
    """
    json_path = os.path.join(settings.BASE_DIR, "tickets", "static", "clustering", "cluster_results.json")

    sample_data = {
        "num_clusters": 0, "summary_per_cluster": {}, "visual_coords_2d": [], 
        "pca_coords": [], "mca_coords": [], "cluster_labels": [], 
        "numerical_columns_summary": [], "categorical_columns_summary": [],
        "final_silhouette_score": None, "best_gamma": None,
    }

    # Load data
    try:
        data = sample_data
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                data_raw = json.load(f)
            
            def convert_nan(obj):
                if isinstance(obj, dict):
                    return {k: convert_nan(v) for k, v in obj.items()}
                return np.nan if obj == 'NaN' else obj 
            
            data = convert_nan(data_raw)
            print("Cluster JSON loaded and converted successfully.")
        else:
            print("Using sample data (cluster_results.json not found).")
    except Exception as e:
        print(f"Load error: {e}")
        data = sample_data

    # --- Ekstraksi & Variabel ---
    charts = {}
    num_clusters = data.get("num_clusters", 0)
    cluster_labels = data.get("cluster_labels", [])
    summary = data.get("summary_per_cluster", {})
    numerical_cols = data.get("numerical_columns_summary", []) or []
    categorical_cols = data.get("categorical_columns_summary", []) or []

    # Ambil koordinat mentah dari JSON
    visual_coords_2d = data.get("visual_coords_2d", []) or data.get("pca_coords", [])
    pca_coords = data.get("pca_coords", []) 
    mca_coords = data.get("mca_coords", []) 

    # Ekstraksi performa model
    charts["model_performance"] = {
        "silhouette_score": round(data.get("final_silhouette_score", 0) if isinstance(data.get("final_silhouette_score"), (float, int)) else 0, 4),
        "best_gamma": round(data.get("best_gamma", 0) if isinstance(data.get("best_gamma"), (float, int)) else 0, 4),
    }

    # 1. Scatter Chart Data (UMAP/t-SNE - Hybrid)
    charts["visual_scatter"] = create_scatter_dataset(visual_coords_2d, cluster_labels, num_clusters)

    # 2. PCA Scatter (Numerik Saja)
    charts["pca_scatter"] = create_scatter_dataset(pca_coords, cluster_labels, num_clusters)

    # 3. MCA Scatter (Kategorikal Saja)
    charts["mca_scatter"] = create_scatter_dataset(mca_coords, cluster_labels, num_clusters)
    
    # 4. Mean Bar Chart Data (Top 5 Numerik)
    bar_chart_num_datasets = []
    if summary and numerical_cols and num_clusters > 0:
        top_num_cols = numerical_cols[:5]
        for index, num_col in enumerate(top_num_cols):
            dataset = {
                "label": num_col,
                "data": [safe_get_mean(summary, i, num_col) for i in range(num_clusters)],
                "backgroundColor": f"hsl({int(index * 50)}, 60%, 60%)",
            }
            bar_chart_num_datasets.append(dataset)
    charts["mean_bar_numerical"] = {"labels": [f"Cluster {i}" for i in range(num_clusters)], "datasets": bar_chart_num_datasets}

    # 5. Cluster Size Pie Chart Data
    pie_charts_data = {}
    if summary and num_clusters > 0:
        pie_labels = []
        cluster_sizes = []
        for i in range(num_clusters):
            cluster_summary = summary.get(str(i), {})
            mode_value = cluster_summary.get("mode_categorical", {}).get("Item") or cluster_summary.get("mode_categorical", {}).get("Category", "Unknown")
            pie_labels.append(f"Cluster {i} ({mode_value})")
            cluster_sizes.append(cluster_summary.get("size", 0))

        background_colors = [f"hsl({int(i * (360 / max(1, num_clusters)))}, 70%, 50%)" for i in range(num_clusters)]

        pie_charts_data = {
            "labels": pie_labels,
            "datasets": [{"data": cluster_sizes, "backgroundColor": background_colors}],
        }
    charts["cluster_size_pie"] = pie_charts_data

    # 6. Data Bar Chart SLA Compliance Rate
    sla_data = []
    if num_clusters > 0:
        for i in range(num_clusters):
            rate = safe_get_mean(summary, i, 'Application SLA Compliance Rate') * 100 
            sla_data.append(round(rate, 4))
    charts['sla_compliance_bar'] = {
        'labels': [f'Cluster {i}' for i in range(num_clusters)],
        'datasets': [{'label': 'SLA Compliance Rate Rata-rata (%)', 'data': sla_data, 'backgroundColor': cluster_colors}]
    }
    
    # 7. Data Bar Chart Average Resolution Time (menit)
    res_data_min = []
    if num_clusters > 0:
        for i in range(num_clusters):
            res_days = safe_get_mean(summary, i, 'Resolution Duration')
            res_min = res_days * 24 * 60
            res_data_min.append(round(res_min, 0))
    charts['resolution_time_bar'] = {
        'labels': [f'Cluster {i}' for i in range(num_clusters)],
        'datasets': [{'label': 'Average Resolution Time (menit)', 'data': res_data_min, 'backgroundColor': cluster_colors}]
    }

    # 8. Data Centroid Scatter (Days to Due vs Resolution Time)
    centroid_scatter_datasets = []
    if num_clusters > 0:
        for i in range(num_clusters):
            x_val = safe_get_mean(summary, i, 'Days to Due')
            y_val_days = safe_get_mean(summary, i, 'Resolution Duration')
            y_coord_hours = y_val_days * 24 
            centroid_scatter_datasets.append({'label': f'Cluster {i}', 'data': [{'x': round(x_val, 4), 'y': round(y_coord_hours, 4)}],
                'backgroundColor': cluster_colors[i % len(cluster_colors)], 'pointRadius': 10})
    charts['centroid_scatter'] = {'datasets': centroid_scatter_datasets}


    # Sertakan ringkasan lengkap agar frontend dapat menampilkan kartu detail per cluster
    charts["summary_per_cluster"] = summary
    charts["categorical_columns"] = categorical_cols
    charts["numerical_columns"] = numerical_cols

    # Kembalikan 'charts' yang sudah terisi penuh
    return Response(charts)


@api_view(["GET"])
def get_violation_by_category(request):
    # ... (kode get_violation_by_category tidak berubah) ...
    queryset = get_filtered_queryset(request)

    category_stats = (
        queryset.values("category")
        .annotate(total_tickets=Count("number"), violated_tickets=Count("number", filter=Q(is_sla_violated=True)))
        .order_by("-total_tickets")
    )

    results = []
    for stat in category_stats:
        total = stat["total_tickets"]
        violated = stat["violated_tickets"]
        violation_rate = (violated / total * 100) if total > 0 else 0
        results.append({"category": stat["category"], "violation_rate": round(violation_rate, 2), "total_tickets": total})

    return Response(results[:10])


@api_view(["GET"])
def get_monthly_trend(request):
    # ... (kode get_monthly_trend tidak berubah) ...
    queryset = get_filtered_queryset(request)

    monthly_data = (
        queryset.annotate(month=TruncMonth("open_date"))
        .values("month")
        .annotate(total_tickets=Count("number"), violated_tickets=Count("number", filter=Q(is_sla_violated=True)))
        .order_by("month")
    )

    results = [
        {"month": data["month"].strftime("%Y-%m"), "total_tickets": data["total_tickets"], "violated_tickets": data["violated_tickets"]}
        for data in monthly_data
    ]
    return Response(results)


@api_view(["POST"])
def predict_sla(request):
    # ... (kode predict_sla tidak berubah) ...
    input_data = request.data
    try:
        result = predictor.predict(input_data)
        if result.get("status") == "error":
            return Response({"error": result.get("message", "Prediksi gagal")}, status=400)

        from .models import PredictionLog

        user = request.user if request.user.is_authenticated else None
        ip_address = request.META.get("REMOTE_ADDR")

        PredictionLog.objects.create(user=user, input_data=input_data, prediction_result=result, ip_address=ip_address)
        return Response(result)
    except Exception as e:
        print(f"Predict error detail: {type(e).__name__}: {e}")
        return Response({"error": f"Internal Server Error: {str(e)}"}, status=500)


@api_view(["GET"])
@permission_classes([AllowAny]) # Biar aman kalau diakses sebelum login full, tapi sebaiknya IsAuthenticated
def get_unique_values(request):
    """
    Mengambil daftar unik Category dan Item langsung dari Database.
    Jauh lebih akurat daripada mengambil dari file .pkl.
    """
    try:
        # 1. Ambil Category unik yang ada di DB, urut abjad
        categories_qs = Ticket.objects.values_list('category', flat=True).distinct().order_by('category')
        
        # 2. Ambil Item unik yang ada di DB, urut abjad
        items_qs = Ticket.objects.values_list('item', flat=True).distinct().order_by('item')

        # 3. Format untuk React-Select { value: '...', label: '...' }
        categories = [
            {"value": cat, "label": cat.replace("-", " ").title()} 
            for cat in categories_qs if cat
        ]
        
        items = [
            {"value": item, "label": item.title()} 
            for item in items_qs if item
        ]

        return Response({
            "categories": categories,
            "items": items,
            "sub_categories": [] # Kosongkan jika tidak dipakai
        })

    except Exception as e:
        print(f"Error fetching unique values: {e}")
        return Response({"error": str(e)}, status=500)


class TicketPagination(PageNumberPagination):
    # ... (kode TicketPagination tidak berubah) ...
    page_size = 7
    page_size_query_param = "page_size"
    max_page_size = 100


class TicketViewSet(viewsets.ReadOnlyModelViewSet):
    # ... (kode TicketViewSet tidak berubah) ...
    queryset = Ticket.objects.all().order_by("-open_date")
    serializer_class = TicketSerializer
    pagination_class = TicketPagination
    lookup_field = "number"

    def get_queryset(self):
        base_queryset = super().get_queryset()
        queryset = base_queryset

        # Search by ID
        search_query = self.request.query_params.get("search", None)
        if search_query:
            queryset = queryset.filter(Q(number__icontains=search_query))

        # Filter by priority
        priority_filter = self.request.query_params.get("priority", None)
        if priority_filter and priority_filter != "all":
            queryset = queryset.filter(priority=priority_filter)

        # Filter by category
        category_filter = self.request.query_params.get("category", None)
        if category_filter and category_filter != "all":
            queryset = queryset.filter(category=category_filter)

        # Filter Pelanggaran SLA
        violation_filter = self.request.query_params.get("is_sla_violated", None)
        if violation_filter and violation_filter != "all":
            if violation_filter == "true":
                queryset = queryset.filter(is_sla_violated=True)
            elif violation_filter == "false":
                queryset = queryset.filter(is_sla_violated=False)

        # Sort by open_date
        sort_order = self.request.query_params.get("sort", "-open_date")
        if sort_order in ["open_date", "-open_date"]:
            queryset = queryset.order_by(sort_order)
        else:
            queryset = queryset.order_by("-open_date")

        print(f"Queryset count after filters: {queryset.count()}")
        return queryset


@api_view(["GET"])
def get_stats(request):
    # ... (kode get_stats tidak berubah) ...
    queryset = get_filtered_queryset(request)

    total = queryset.aggregate(total=Count("number"))["total"]
    violations = queryset.filter(is_sla_violated=True).aggregate(count=Count("number"))["count"]
    compliance = total - violations
    rate = (compliance / total * 100) if total > 0 else 0

    low_priority = queryset.filter(priority="4 - Low").aggregate(count=Count("number"))["count"]
    medium_priority = queryset.filter(priority="3 - Medium").aggregate(count=Count("number"))["count"]
    high_priority = queryset.filter(priority="2 - High").aggregate(count=Count("number"))["count"]
    critical_priority = queryset.filter(priority="1 - Critical").aggregate(count=Count("number"))["count"]
    avg_duration = queryset.aggregate(avg=Avg("resolution_duration"))["avg"] or 0
    avg_compliance = queryset.aggregate(avg=Avg("application_sla_compliance_rate"))["avg"] or 0

    data = {
        "total_tickets": total,
        "violation_count": violations,
        "compliance_count": compliance,
        "compliance_rate": round(rate, 1),
        "low_priority_count": low_priority,
        "medium_priority_count": medium_priority,
        "high_priority_count": high_priority,
        "critical_priority_count": critical_priority,
        "avg_resolution_duration": round(avg_duration, 2),
        "avg_compliance_rate": round(avg_compliance * 100, 1),
    }
    return Response(data)