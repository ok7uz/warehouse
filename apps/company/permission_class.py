from rest_framework import permissions

class IsSuperUser(permissions.BasePermission):
    """ Faqat superuserlarga ruxsat beradi. """
    def has_permission(self, request, view):
        return request.user.is_superuser or request.user.groups.filter(name="Супер пользователь").exists()

class IsProductionManager(permissions.BasePermission):
    """ 'Начальник производства' guruhiga kiruvchi foydalanuvchilarga ruxsat beradi. """
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Начальник производства').exists()

class IsManager(permissions.BasePermission):
    """ 'Менеджер' guruhiga kiruvchi foydalanuvchilarga ruxsat beradi, magazinlar qo'shish va API kalitlarini o'zgartirishdan tashqari. """
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Менеджер').exists() and not request.user.is_superuser

class IsWarehouseWorker(permissions.BasePermission):
    """ 'Кладовщик' guruhiga kiruvchi foydalanuvchilarga faqat ombor bilan bog'liq vazifalarga ruxsat beradi. """
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Кладовщик').exists() and not request.user.is_superuser

class IsMachineOperator(permissions.BasePermission):
    """ 'Оператор станка' guruhiga kiruvchi foydalanuvchilarga ishlab chiqarish va inventarizatsiya bilan bog'liq vazifalarga ruxsat beradi. """
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Оператор станка').exists() and not request.user.is_superuser
