from rest_framework import serializers
from .models import Claster, Company, WarehouseYandex, WarehouseOzon

class ClasterSerializer(serializers.ModelSerializer):
    claster_to = serializers.CharField()
    region_name = serializers.CharField()
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False)

    class Meta:
        model = Claster
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep.pop('company')
        return rep
    
class WarehouseSerializer(serializers.ModelSerializer):
    warehouse_id = serializers.IntegerField()
    claster_to = serializers.CharField()
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False)

    class Meta:
        model = WarehouseYandex
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep.pop('company')
        return rep
    
class WarehouseOzonSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField()
    claster_to = serializers.CharField()
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False)

    class Meta:
        model = WarehouseOzon
        fields = '__all__'

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep.pop('company')
        return rep
    