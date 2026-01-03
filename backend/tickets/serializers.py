from datetime import datetime

from django.utils import timezone
from rest_framework import serializers

from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    # Format date untuk readable di frontend
    open_date = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    closed_date = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    due_date = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    sla_violated_text = serializers.SerializerMethodField()  # 'Ya'/'Tidak' untuk frontend
    resolution_duration_formatted = serializers.SerializerMethodField()  # e.g., '2.725 hari'
    compliance_rate_percent = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = '__all__'  # Semua fields dari model (sesuai CSV)
    
    def get_sla_violated_text(self, obj):
        return 'Ya' if obj.is_sla_violated else 'Tidak'

    def get_resolution_duration_formatted(self, obj):
        return f"{obj.resolution_duration:.2f} hari"

    def get_compliance_rate_percent(self, obj):
        return f"{obj.application_sla_compliance_rate * 100:.1f}%"
