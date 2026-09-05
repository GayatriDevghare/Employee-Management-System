from rest_framework import serializers
from .models import Employee

class EmployeeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employee
        fields = "__all__"

    def validate_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Minimum 3 characters required.")
        return value

    def validate_age(self, value):
        if value < 18:
            raise serializers.ValidationError("Age must be at least 18.")
        return value

    def validate_email(self, value):

        if Employee.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")

        return value