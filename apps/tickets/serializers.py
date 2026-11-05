from rest_framework import serializers

from apps.accounts.models import User

from .models import Ticket, TicketComment


class TicketSerializer(serializers.ModelSerializer):
    code = serializers.CharField(read_only=True)
    applicant_name = serializers.StringRelatedField(source="applicant", read_only=True)
    category_name = serializers.StringRelatedField(source="category", read_only=True)
    executor_name = serializers.StringRelatedField(source="executor", read_only=True)
    created_by_name = serializers.StringRelatedField(source="created_by", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Ticket
        fields = ("id", "code", "subject", "description",
                  "applicant", "applicant_name", "category", "category_name",
                  "priority", "priority_display", "channel", "channel_display",
                  "status", "status_display", "executor", "executor_name",
                  "created_by_name", "resolution", "deadline", "is_overdue",
                  "created_at", "updated_at", "resolved_at", "closed_at")
        read_only_fields = ("status", "deadline", "resolved_at", "closed_at",
                            "created_at", "updated_at")

    def validate_executor(self, value):
        if value and value.role != User.Role.EXECUTOR:
            raise serializers.ValidationError("Исполнителем может быть только сотрудник с ролью «Исполнитель».")
        return value

    def validate_category(self, value):
        if not value.is_active:
            raise serializers.ValidationError("Категория неактивна.")
        return value


class TicketStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Ticket.Status.choices)
    comment = serializers.CharField(required=False, allow_blank=True, default="")
    resolution = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        ticket = self.context["ticket"]
        new_status = attrs["status"]
        if not ticket.can_change_to(new_status):
            raise serializers.ValidationError({
                "status": f"Недопустимый переход: «{ticket.get_status_display()}» → "
                          f"«{Ticket.status_label(new_status)}»"
            })
        if new_status == Ticket.Status.RESOLVED and not (attrs.get("resolution") or ticket.resolution):
            raise serializers.ValidationError({"resolution": "Для статуса «Решено» опишите решение."})
        return attrs


class TicketAssignSerializer(serializers.Serializer):
    executor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.EXECUTOR, is_active=True)
    )


class TicketCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.StringRelatedField(source="author", read_only=True)
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)

    class Meta:
        model = TicketComment
        fields = ("id", "kind", "kind_display", "text", "old_status", "new_status",
                  "author_name", "created_at")
        read_only_fields = ("kind", "old_status", "new_status", "created_at")
