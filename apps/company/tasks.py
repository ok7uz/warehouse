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

    products = ProductSale.objects.filter(company=company).order_by("product_id").distinct("product_id").values("product_id")
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
            
            shelf_stock = shelf_stocks.filter(product=product).order_by("product")
            if shelf_stock.exists():
                shelf_stock = shelf_stock.first()
                shelf_stock = shelf_stock['total_stock']
            else:
                shelf_stock = 0
            sorting = sorting_stocks.filter(product=product).aggregate(total=Sum("unsorted"))["total"]
            if not sorting:
                sorting = 0
            try:
                stock = stocks.filter(product=product, warehouse__in=warehouses).values('warehouse').annotate(latest_date=Max('date'))
                summ = 0
                for item in stock:
                    count = stocks.filter(warehouse=item["warehouse"],date=item["latest_date"])
                    if count.exists():
                        summ += count.first().quantity
                stock = summ
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

@app.task
def update_recomendation_supplier(company):
    settings = CompanySettings.objects.get(company=company)
    last_sale_days = settings.last_sale_days
    next_sale_days = settings.next_sale_days
    date_to = datetime.now()
    date_from = date_to - timedelta(days=last_sale_days)
    company = Company.objects.get(id=company)

    products = ProductSale.objects.filter(company=company).order_by("product_id").distinct("product_id").values_list("product_id",flat=True)
    
    for item in products:
        warehouses_w = ProductSale.objects.filter(product=item, marketplace_type="wildberries").values_list("warehouse", flat=True)
        warehouses_o = ProductSale.objects.filter(product=item, marketplace_type="ozon").values_list("warehouse", flat=True)
        warehouses_y = ProductSale.objects.filter(product=item, marketplace_type="yandexmarket").values_list("warehouse", flat=True)
        item = Product.objects.get(id=item)
        for w_item in warehouses_w:
            
            name = Warehouse.objects.get(id=w_item).name
            w_item = Warehouse.objects.get(id=w_item)
            sale = ProductSale.objects.filter(product=item, warehouse=w_item, date__range=(date_from,date_to),marketplace_type="wildberries").count()
            shelf = Shelf.objects.filter(product=item)
            stock_w = WarehouseForStock.objects.filter(name=name)
            
            if stock_w.exists():
                stock_w = stock_w.first()
                stock = ProductStock.objects.filter(product=item,warehouse=stock_w,marketplace_type="wildberries")
                if stock.exists():
                    stock = stock.latest("date").quantity
                else:
                    stock = 0
            else:
                stock = 0

            if shelf.exists():
                shelf = shelf.aggregate(total=Sum("stock"))["total"]
            else:
                shelf = 0
            
            sorting = SortingWarehouse.objects.filter(product=item)
            if sorting.exists():
                sorting = sorting.aggregate(total=Sum("unsorted"))["total"]
            else:
                sorting = 0
            
            sale_per_day = sale/last_sale_days
            need_product = floor(sale_per_day*next_sale_days)
            all_quantity = sorting + stock + shelf
            days_left = floor(all_quantity/sale_per_day)
            difference = need_product - all_quantity

            if difference > 0:
                recomamand_supplier, created = RecomamandationSupplier.objects.get_or_create(company=company,warehouse=w_item,product=item, marketplace_type="wildberries")
                
                if created:
                    recomamand_supplier.quantity = difference
                    recomamand_supplier.days_left = days_left
                else:
                    if recomamand_supplier.quantity - difference < 0:
                        difference = difference - recomamand_supplier.quantity
                        days_d = days_left - recomamand_supplier.days_left
                        recomamand_supplier.quantity += difference
                        recomamand_supplier.days_left += days_d
                        recomamand_supplier.save()

        for w_item in warehouses_o:
            
            name = Warehouse.objects.get(id=w_item).name
            w_item = Warehouse.objects.get(id=w_item)
            sale = ProductSale.objects.filter(product=item, warehouse=w_item, date__range=(date_from,date_to),marketplace_type="ozon").count()
            shelf = Shelf.objects.filter(product=item)
            stock_w = WarehouseForStock.objects.filter(name=name)
            
            if stock_w.exists():
                stock_w = stock_w.first()
                stock = ProductStock.objects.filter(product=item,warehouse=stock_w,marketplace_type="ozon")
                if stock.exists():
                    stock = stock.latest("date").quantity
                else:
                    stock = 0
            else:
                stock = 0

            if shelf.exists():
                shelf = shelf.aggregate(total=Sum("stock"))["total"]
            else:
                shelf = 0
            
            sorting = SortingWarehouse.objects.filter(product=item)
            if sorting.exists():
                sorting = sorting.aggregate(total=Sum("unsorted"))["total"]
            else:
                sorting = 0
            
            sale_per_day = sale/last_sale_days
            need_product = floor(sale_per_day*next_sale_days)
            all_quantity = sorting + stock + shelf
            days_left = floor(all_quantity/sale_per_day)
            difference = need_product - all_quantity

            if difference > 0:
                recomamand_supplier, created = RecomamandationSupplier.objects.get_or_create(company=company,warehouse=w_item,product=item, marketplace_type="ozon")
                
                if created:
                    recomamand_supplier.quantity = difference
                    recomamand_supplier.days_left = days_left
                else:
                    if recomamand_supplier.quantity - difference < 0:
                        difference = difference - recomamand_supplier.quantity
                        days_d = days_left - recomamand_supplier.days_left
                        recomamand_supplier.quantity += difference
                        recomamand_supplier.days_left += days_d
                        recomamand_supplier.save()

        for w_item in warehouses_y:
            
            name = Warehouse.objects.get(id=w_item).name
            w_item = Warehouse.objects.get(id=w_item)
            sale = ProductSale.objects.filter(product=item, warehouse=w_item, date__range=(date_from,date_to),marketplace_type="yandexmarket").count()
            shelf = Shelf.objects.filter(product=item)
            stock_w = WarehouseForStock.objects.filter(name=name)
            
            if stock_w.exists():
                stock_w = stock_w.first()
                stock = ProductStock.objects.filter(product=item,warehouse=stock_w,marketplace_type="yandexmarket")
                if stock.exists():
                    stock = stock.latest("date").quantity
                else:
                    stock = 0
            else:
                stock = 0

            if shelf.exists():
                shelf = shelf.aggregate(total=Sum("stock"))["total"]
            else:
                shelf = 0
            
            sorting = SortingWarehouse.objects.filter(product=item)
            if sorting.exists():
                sorting = sorting.aggregate(total=Sum("unsorted"))["total"]
            else:
                sorting = 0
            
            sale_per_day = sale/last_sale_days
            need_product = floor(sale_per_day*next_sale_days)
            try:
                all_quantity = sorting + stock + shelf
            except:
                all_quantity = 0
            try:
                days_left = floor(all_quantity/sale_per_day)
            except:
                days_left = 0
            difference = need_product - all_quantity

            if difference > 0:
                recomamand_supplier, created = RecomamandationSupplier.objects.get_or_create(company=company,warehouse=w_item,product=item, marketplace_type="yandexmarket")
                
                if created:
                    recomamand_supplier.quantity = difference
                    recomamand_supplier.days_left = days_left
                else:
                    if recomamand_supplier.quantity - difference < 0:
                        difference = difference - recomamand_supplier.quantity
                        days_d = days_left - recomamand_supplier.days_left
                        recomamand_supplier.quantity += difference
                        recomamand_supplier.days_left += days_d
                        recomamand_supplier.save()

    return True

            
    