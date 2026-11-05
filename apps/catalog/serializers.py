from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    default_executor_name = serializers.StringRelatedField(source="default_executor", read_only=True)
    tickets_count = serializers.IntegerField(read_only=True)
    open_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "description", "default_executor",
                  "default_executor_name", "is_active", "tickets_count", "open_count")

    def validate_default_executor(self, value):
        if value and value.role != "executor":
            raise serializers.ValidationError("Ответственным может быть только исполнитель.")
        return value
