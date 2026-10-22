from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class RegistrationSerializer(serializers.ModelSerializer):
    # Accept the API field name and the existing frontend's alternative spelling.
    confirm_password = serializers.CharField(write_only=True, required=False)
    confirmed_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["email", "password", "confirm_password", "confirmed_password"]
        extra_kwargs = {"password": {"write_only": True}, "email": {"validators": []}}

    def validate_email(self, value):
        # Replace the default uniqueness message with a generic registration error.
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Registrierung nicht moeglich.")
        return value.lower()

    def validate(self, attrs):
        password = attrs.get("password")
        confirmation = get_password_confirmation(attrs)
        if password != confirmation:
            raise serializers.ValidationError("Passwoerter stimmen nicht ueberein.")
        validate_password(password)
        return attrs

    def create(self, validated_data):
        # Confirmation fields are not stored; set_password hashes the password.
        remove_password_confirmations(validated_data)
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwoerter stimmen nicht ueberein.")
        validate_password(attrs["new_password"], self.context.get("user"))
        return attrs


def get_password_confirmation(attrs):
    return attrs.pop("confirm_password", None) or attrs.pop("confirmed_password", None)


def remove_password_confirmations(data):
    data.pop("confirm_password", None)
    data.pop("confirmed_password", None)
