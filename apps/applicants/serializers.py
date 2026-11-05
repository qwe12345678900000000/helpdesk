from rest_framework import serializers

from .models import Applicant


class ApplicantSerializer(serializers.ModelSerializer):
    tickets_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Applicant
        fields = ("id", "full_name", "department", "position", "room",
                  "phone", "email", "created_at", "tickets_count")
        read_only_fields = ("created_at",)
