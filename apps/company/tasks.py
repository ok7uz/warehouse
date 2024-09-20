from config.celery import app
from apps.product.models import *
from apps.company.models import CompanySettings
from datetime import datetime, timedelta
from django.db.models import Count, OuterRef, Max, Subquery, Sum
from django.db import transaction
from math import ceil, floor

@app.task
def update_recomendations(company):
    settings = CompanySettings.objects.get(company=company)
    last_sale_days = settings.last_sale_days
    next_sale_days = settings.next_sale_days
    date_to = datetime.now()
    date_from = date_to - timedelta(days=last_sale_days)
    company = Company.objects.get(id=company)

    products = ProductStock.objects.filter(company=company).order_by("product_id").distinct("product_id").values("product_id")
    sales = ProductSale.objects.filter(company=company, product__in=products,date__range=(date_from,date_to)).values("product").annotate(total_sales=Count("id"))

    stocks = ProductStock.objects.filter(
        product_id__in=products, company=company)

    shelf_stocks = Shelf.objects.filter(product__in=products, company=company).values('product').annotate(total_stock=Sum('stock'))
    sorting_stocks = SortingWarehouse.objects.filter(product__in=products, company=company)
    
    with transaction.atomic():
        for sale in sales:
            
            product = sale['product']
            total_sale = sale['total_sales']
            product = Product.objects.get(id=int(product))
            warehouses = ProductStock.objects.filter(product=product).values_list("warehouse")
            
            shelf_stock = shelf_stocks.filter(product=product).order_by("product").first()
            if shelf_stock:
                shelf_stock = shelf_stock['stock']
            else:
                shelf_stock = 0
            sorting = sorting_stocks.filter(product=product).aggregate(total=Sum("unsorted"))["total"]
            if not sorting:
                sorting = 0
            try:
                stock = stocks.filter(product=product, warehouse__in=warehouses).latest("date").quantity
            except:
                stock = 0
            
            avg_sale = total_sale/last_sale_days
            days_left = floor((shelf_stock + sorting + stock)/avg_sale)
            need_stock = int(round(avg_sale*next_sale_days))
            recommend = need_stock - (shelf_stock + sorting + stock)
            
            if recommend > 0:
                
                recommendations, created = Recommendations.objects.get_or_create(company=company,product=product)
                if created:
                    recommendations.quantity = recommend
                    recommendations.days_left = days_left
                    recommendations.save()
                else:
                    difference = recommend - recommendations.quantity
                    if difference > 0 :
                        recommendations.quantity = recommend
                        recommendations.days_left = days_left
                        recommendations.save()

        return True
