from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    has_vendor_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "phone",
            "role", "is_email_verified", "has_vendor_profile",
        ]
        read_only_fields = ["id", "role", "is_email_verified", "has_vendor_profile"]

    def get_has_vendor_profile(self, obj):
        return hasattr(obj, "vendor_profile")


class RegisterSerializer(serializers.ModelSerializer):
    """Customer registration."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "password", "password2"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password2"):
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data, role=User.Roles.CUSTOMER)
        user.set_password(password)
        user.save()
        return user


class VendorRegisterSerializer(serializers.Serializer):
    """Vendor registration that also creates the shop (pending verification)."""

    # account
    email = serializers.EmailField()
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)
    # shop
    shop_name = serializers.CharField(max_length=150)
    market = serializers.IntegerField()
    primary_category = serializers.IntegerField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_market(self, value):
        from markets.models import Market

        if not Market.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Selected market does not exist.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password2"):
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        from vendors.models import Vendor

        user = User(
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            phone=validated_data.get("phone", ""),
            role=User.Roles.VENDOR,
        )
        user.set_password(validated_data["password"])
        user.save()
        vendor = Vendor.objects.create(
            user=user,
            shop_name=validated_data["shop_name"],
            market_id=validated_data["market"],
            primary_category_id=validated_data.get("primary_category"),
            phone=validated_data.get("phone", ""),
            description=validated_data.get("description", ""),
            is_verified=False,
        )
        self.context["vendor"] = vendor
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField(validators=[validate_password])


class EmailVerifySerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
