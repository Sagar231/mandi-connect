from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin_role)


class IsVendorRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_vendor)


class IsCustomerRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_customer)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level: only the owning user may write."""

    owner_field = "user"

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, self.owner_field, None)
        return owner == request.user


class IsVendorOwnerOrReadOnly(permissions.BasePermission):
    """Object-level: only the vendor that owns the listing may write."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_admin_role:
            return True
        vendor = getattr(getattr(request.user, "vendor_profile", None), "pk", None)
        return obj.vendor_id == vendor
