from config.celery import app
from apps.product.models import *
from apps.company.models import CompanySettings
from datetime import datetime, timedelta
from django.db.models import Count, Sum
from celery_once import QueueOnce
from math import ceil, floor

@app.task(bind=True, acks_late=True, retry=False,base=QueueOnce, once={'graceful': True})
def update_recomendations(self,company):
    
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

    products = Product.objects.filter(id__in=combined_product_ids).order_by("vendor_code").distinct("vendor_code").values("vendor_code")

    shelf_stocks = Shelf.objects.filter(product__vendor_code__in=products, company=company).values('product__vendor_code').annotate(total_stock=Sum('stock'))
    sorting_stocks = SortingWarehouse.objects.filter(product__vendor_code__in=products, company=company)
    
    recommendations = Recommendations.objects.filter(company=company).delete()
    recommendations = []
    
    for sale in products:

        product = sale['vendor_code']
        
        product = Product.objects.filter(vendor_code=product)
        product_w = product.filter(marketplace_type="wildberries")
        if product_w.exists():
            product = product_w.first()
        else:
            product = product.first()
        total_sale = ProductOrder.objects.filter(product__vendor_code=product.vendor_code,company=company, date__date__gte=date_from, date__date__lte=date_to).count()
        
        shelf_stock = shelf_stocks.filter(product__vendor_code=product.vendor_code,company=company).order_by("product")
        if shelf_stock.exists():
            shelf_stock = shelf_stock.first()
            shelf_stock = shelf_stock['total_stock']
        else:
            shelf_stock = 0
        sorting = sorting_stocks.filter(product__vendor_code=product.vendor_code).aggregate(total=Sum("unsorted"))["total"]
        in_production = InProduction.objects.filter(product__vendor_code=product.vendor_code,company=company)
        
        if in_production.exists():
            in_production = in_production.aggregate(total=Sum("manufacture"))["total"]
        else:
            in_production = 0
        
        if not sorting:
            sorting = 0
        
        summ = 0
        stock = ProductStock.objects.filter(company=company,product__vendor_code=product.vendor_code)
        
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

@app.task(bind=True, acks_late=True, retry=False, base=QueueOnce, once={'graceful': True})
def update_recomendation_supplier(self,company):
    
    settings = CompanySettings.objects.get(company=company)
    last_sale_days = settings.last_sale_days
    next_sale_days = settings.next_sale_days
    date_to = datetime.now()
    date_from = date_to - timedelta(days=last_sale_days)
    company = Company.objects.get(id=company)

    products = ProductOrder.objects.filter(company=company).order_by("product__vendor_code").distinct("product__vendor_code").values_list("product_id",flat=True)
    
    for item in products:
        
        item = Product.objects.get(id=item)
        
        warehouses_w = ProductOrder.objects.filter(product__vendor_code=item.vendor_code, marketplace_type="wildberries")
        if warehouses_w.exists():
            warehouses_w = warehouses_w.filter(date__date__gte=date_from,date__date__lte=date_to).values_list("warehouse", flat=True)
        else:
            warehouses_w = []

        warehouses_o = ProductOrder.objects.filter(product__vendor_code=item.vendor_code, marketplace_type="ozon")
        if warehouses_o.exists():
            warehouses_o = warehouses_o.filter(date__date__gte=date_from,date__date__lte=date_to).values_list("warehouse", flat=True)
            
        else:
            warehouses_o = []
        
        warehouses_y = ProductOrder.objects.filter(product__vendor_code=item.vendor_code, marketplace_type="yandexmarket")
        if warehouses_y.exists():
            warehouses_y = warehouses_y.filter(date__date__gte=date_from,date__date__lte=date_to).values_list("warehouse", flat=True)

        else:
            warehouses_y = []
        
        for w_item in warehouses_w:
            
            w_item = Warehouse.objects.get(id=w_item)
            oblast_okrug_name = w_item.oblast_okrug_name
            sale = ProductOrder.objects.filter(product__vendor_code=item.vendor_code, warehouse__oblast_okrug_name=oblast_okrug_name, date__range=(date_from,date_to),marketplace_type="wildberries",company=company).count()
            shelf = Shelf.objects.filter(product__vendor_code=item.vendor_code)
            names = Warehouse.objects.filter(oblast_okrug_name=oblast_okrug_name).values("name")
            stock_w = WarehouseForStock.objects.filter(name__in=names)
            stock = 0
            for item_w in stock_w:
                P_S = ProductStock.objects.filter(product__vendor_code=item.vendor_code, date__range=(date_from,date_to), warehouse=item_w, marketplace_type="wildberries", company=company)
                if P_S.exists():
                    P_S = P_S.latest("date")
                    stock += P_S.quantity

            if shelf.exists():
                shelf = shelf.aggregate(total=Sum("stock"))["total"]
            else:
                shelf = 0
            
            sorting = SortingWarehouse.objects.filter(product__vendor_code=item,company=company)
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
            
            w_item = Warehouse.objects.get(id=w_item)
            oblast_okrug_name = w_item.oblast_okrug_name
            sale = ProductOrder.objects.filter(product__vendor_code=item.vendor_code, warehouse__oblast_okrug_name=oblast_okrug_name, date__range=(date_from,date_to),marketplace_type="ozon",company=company).count()
            
            shelf = Shelf.objects.filter(product__vendor_code=item.vendor_code)
            names = Warehouse.objects.filter(oblast_okrug_name=oblast_okrug_name).values("name")
            stock_w = WarehouseForStock.objects.filter(name__in=names)
            stock = 0
            
            for item_w in stock_w:
                P_S = ProductStock.objects.filter(product__vendor_code=item.vendor_code, date__gte=date_from,date__lte=date_to, warehouse=item_w, marketplace_type="ozon", company=company)
                if P_S.exists():
                    P_S = P_S.latest("date")
                    stock += P_S.quantity

            if shelf.exists():
                shelf = shelf.aggregate(total=Sum("stock"))["total"]
            else:
                shelf = 0
            
            sorting = SortingWarehouse.objects.filter(product__vendor_code=item,company=company)
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
            
            w_item = Warehouse.objects.get(id=w_item)
            oblast_okrug_name = w_item.oblast_okrug_name
            sale = ProductOrder.objects.filter(product__vendor_code=item.vendor_code, warehouse__oblast_okrug_name=oblast_okrug_name, date__range=(date_from,date_to),marketplace_type="yandexmarket",company=company).count()
            shelf = Shelf.objects.filter(product__vendor_code=item.vendor_code)
            names = Warehouse.objects.filter(oblast_okrug_name=oblast_okrug_name).values("name")
            stock_w = WarehouseForStock.objects.filter(name__in=names)
            stock = 0
            
            for item_w in stock_w:
                P_S = ProductStock.objects.filter(product__vendor_code=item.vendor_code, date__range=(date_from,date_to) ,warehouse=item_w, marketplace_type="yandexmarket", company=company)
                if P_S.exists():
                    P_S = P_S.latest("date")
                    stock += P_S.quantity

            if shelf.exists():
                shelf = shelf.aggregate(total=Sum("stock"))["total"]
            else:
                shelf = 0
            
            sorting = SortingWarehouse.objects.filter(product__vendor_code=item.vendor_code,company=company)
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

@app.task(bind=True, acks_late=True, retry=False, base=QueueOnce, once={'graceful': True})
def update_priority(self,company_id):
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
        try:
            share_shipments = (shipments/total_shipments)*100
        except:
            share_shipments = 0
        try:
            shipping_priority = share_shipments/share_sale
        except:
            shipping_priority = 0

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