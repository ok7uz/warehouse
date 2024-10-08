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

    products_s = ProductSale.objects.filter(company=company).order_by("product_id").distinct("product_id").values_list('product', flat=True).distinct()
    products_o = ProductOrder.objects.filter(company=company).order_by("product_id").distinct("product_id").values_list('product', flat=True).distinct()
    products_st = ProductStock.objects.filter(company=company).order_by("product_id").distinct("product_id").values_list('product', flat=True).distinct()
    combined_product_ids = set(products_s) | set(products_o) | set(products_st)

    products = Product.objects.filter(id__in=combined_product_ids).order_by("id").distinct("id").values("id")

    

    shelf_stocks = Shelf.objects.filter(product__in=products, company=company).values('product').annotate(total_stock=Sum('stock'))
    sorting_stocks = SortingWarehouse.objects.filter(product__in=products, company=company)
    
    recommendations = Recommendations.objects.filter(company=company).delete()
    recommendations = []
    
    for sale in products:

        product = sale['id']
        
        barcode = Product.objects.get(id=int(product)).barcode
        product_w = Product.objects.filter(barcode=barcode,marketplace_type="wildberries")
        
        if product_w.exists():
            product = product_w.first()
        else:
            product = Product.objects.get(id=int(product))
        total_sale = ProductOrder.objects.filter(product=product,company=company, date__date__gte=date_from, date__date__lte=date_to).count()
        
        shelf_stock = shelf_stocks.filter(product=product,company=company).order_by("product")
        if shelf_stock.exists():
            shelf_stock = shelf_stock.first()
            shelf_stock = shelf_stock['total_stock']
        else:
            shelf_stock = 0
        sorting = sorting_stocks.filter(product=product).aggregate(total=Sum("unsorted"))["total"]
        in_production = InProduction.objects.filter(product=product,company=company)
        if in_production.exists():
            in_production = in_production.aggregate(total=Sum("manufacture"))["total"]
        else:
            in_production = 0
        
        if not sorting:
            sorting = 0
        
        summ = 0
        stock = ProductStock.objects.filter(company=company,product=product)
        
        if stock.exists():
            date = stock.latest("date").date
            stock = stock.filter(date=date).aggregate(total=Sum("quantity"))["total"]
        else:
            stock = 0

        avg_sale = total_sale/last_sale_days
        
        try:
            days_left = floor((shelf_stock + sorting + stock + in_production)/avg_sale)
        except:
            days_left = 0
        need_stock = int(round(avg_sale*next_sale_days))
        recommend = need_stock - (shelf_stock + sorting + stock + in_production)

        if recommend > 0 or stock + in_production + shelf_stock + sorting == 0:
            if stock + in_production + shelf_stock + sorting == 0:
                recommend = 30
            recommendations.append(Recommendations(company=company,product=product, quantity=recommend,days_left=days_left))
            
    build = Recommendations.objects.bulk_create(recommendations)
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
                stock = ProductStock.objects.filter(product=item,warehouse=stock_w,marketplace_type="wildberries",company=company)
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
            
            sorting = SortingWarehouse.objects.filter(product=item,company=company)
            if sorting.exists():
                sorting = sorting.aggregate(total=Sum("unsorted"))["total"]
            else:
                sorting = 0
            
            sale_per_day = sale/last_sale_days
            need_product = floor(sale_per_day*next_sale_days)
            all_quantity = sorting + stock + shelf
            try:
                days_left = floor(all_quantity/sale_per_day)
            except:
                days_left = 0
            difference = need_product - all_quantity

            if difference > 0:
                if Shipment.objects.filter(product__vendor_code=item.vendor_code) or RecomamandationSupplier.objects.filter(company=company,warehouse=w_item,product=item, marketplace_type="wildberries").exists():
                    continue
                recomamand_supplier, created = RecomamandationSupplier.objects.get_or_create(company=company,warehouse=w_item,product=item, marketplace_type="wildberries")
                
                if created:
                    recomamand_supplier.quantity = difference
                    recomamand_supplier.days_left = days_left
                    recomamand_supplier.save()
                else:
                    if recomamand_supplier.quantity - difference < 0:
                        difference = difference
                        days_d = days_left 
                        recomamand_supplier.quantity += difference
                        recomamand_supplier.days_left += days_d
                        recomamand_supplier.save()

        for w_item in warehouses_o:
            
            name = Warehouse.objects.get(id=w_item).name
            w_item = Warehouse.objects.get(id=w_item)
            sale = ProductSale.objects.filter(product=item, warehouse=w_item, date__range=(date_from,date_to),marketplace_type="ozon",company=company).count()
            shelf = Shelf.objects.filter(product=item)
            stock_w = WarehouseForStock.objects.filter(name=name)
            
            if stock_w.exists():
                stock_w = stock_w.first()
                stock = ProductStock.objects.filter(product=item,warehouse=stock_w,marketplace_type="ozon", company=company)
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
            
            sorting = SortingWarehouse.objects.filter(product=item,company=company)
            if sorting.exists():
                sorting = sorting.aggregate(total=Sum("unsorted"))["total"]
            else:
                sorting = 0
            
            sale_per_day = sale/last_sale_days
            need_product = floor(sale_per_day*next_sale_days)
            all_quantity = sorting + stock + shelf
            try:
                days_left = floor(all_quantity/sale_per_day)
            except:
                days_left = 0
            difference = need_product - all_quantity

            if difference > 0:
                if Shipment.objects.filter(product__vendor_code=item.vendor_code) or RecomamandationSupplier.objects.filter(company=company,warehouse=w_item,product=item, marketplace_type="ozon").exists():
                    continue
                try:
                    recomamand_supplier, created = RecomamandationSupplier.objects.get_or_create(company=company,warehouse=w_item,product=item, marketplace_type="ozon")
                except:
                    continue
                if created:
                    recomamand_supplier.quantity = difference
                    recomamand_supplier.days_left = days_left
                    recomamand_supplier.save()
                else:
                    if recomamand_supplier.quantity - difference < 0:
                        difference = difference
                        days_d = days_left 
                        recomamand_supplier.quantity += difference
                        recomamand_supplier.days_left += days_d
                        recomamand_supplier.save()

        for w_item in warehouses_y:
            
            name = Warehouse.objects.get(id=w_item).name
            w_item = Warehouse.objects.get(id=w_item)
            sale = ProductSale.objects.filter(product=item, warehouse=w_item, date__range=(date_from,date_to),marketplace_type="yandexmarket", company=company).count()
            shelf = Shelf.objects.filter(product=item)
            stock_w = WarehouseForStock.objects.filter(name=name)
            
            if stock_w.exists():
                stock_w = stock_w.first()
                stock = ProductStock.objects.filter(product=item,warehouse=stock_w,marketplace_type="yandexmarket",company=company)
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
            
            sorting = SortingWarehouse.objects.filter(product=item,company=company)
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
                if Shipment.objects.filter(product__vendor_code=item.vendor_code) or RecomamandationSupplier.objects.filter(company=company,warehouse=w_item,product=item, marketplace_type="yandexmarket").exists():
                    continue
                recomamand_supplier, created = RecomamandationSupplier.objects.get_or_create(company=company,warehouse=w_item,product=item, marketplace_type="yandexmarket")
                
                if created:
                    recomamand_supplier.quantity = difference
                    recomamand_supplier.days_left = days_left
                    recomamand_supplier.save()
                else:
                    if recomamand_supplier.quantity - difference < 0:
                        difference = difference
                        days_d = days_left 
                        recomamand_supplier.quantity += difference
                        recomamand_supplier.days_left += days_d
                        recomamand_supplier.save()

    return True

@app.task
def update_priority(company_id):
    company = Company.objects.get(id=company_id)
    
    warehouse_product_counts = ProductSale.objects.filter(company=company).values('warehouse',"marketplace_type").annotate(product_count=Count('product', distinct=True)).order_by('warehouse')
    total_sale = sum(item['product_count'] for item in warehouse_product_counts)
    
    warehouse_product_totals = RecomamandationSupplier.objects.filter(company=company).values('warehouse',"marketplace_type").annotate(total_quantity=Sum('quantity'))
    total_shipments = sum(item['total_quantity'] for item in warehouse_product_totals)
    
    for item in warehouse_product_counts:
        product = item["product_count"]
        warehouse = item['warehouse']
        marketplace_type = item['marketplace_type']
        warehouse = Warehouse.objects.get(id=warehouse)
        shipments = warehouse_product_totals.filter(warehouse=warehouse,marketplace_type=marketplace_type)
        
        if shipments.exists():
            shipments = shipments.aggregate(total=Sum("total_quantity"))['total']
        else:
            shipments = 0
        
        share_sale = (product/total_sale)*100
        share_shipments = (shipments/total_shipments)*100
        shipping_priority = share_shipments/share_sale

        priority, created = PriorityShipments.objects.get_or_create(company=company,warehouse=warehouse, marketplace_type=marketplace_type)
        if created:
            priority.sales = product
            priority.shipments = shipments
            priority.sales_share = share_sale
            priority.shipments_share = share_shipments
            priority.shipping_priority = shipping_priority
            priority.save()
        else:
            if priority.sales - product < 0 or priority.shipments - shipments < 0:
                priority.sales = product
                priority.shipments = shipments
                priority.sales_share = share_sale
                priority.shipments_share = share_shipments
                priority.shipping_priority = shipping_priority
                priority.save()

    return True