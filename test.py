data = {
    "Яна_Мишка": {
      "2024-08-31": 0,
      "2024-09-01": 2,
      "2024-09-02": 0,
      "2024-09-03": 0,
      "2024-09-04": 0,
      "2024-09-05": 0,
      "2024-09-06": 0
    },
    "Юля_Мишка": {
      "2024-08-31": 56454654,
      "2024-09-01": 0,
      "2024-09-02": 0,
      "2024-09-03": 0,
      "2024-09-04": 0,
      "2024-09-05": 0,
      "2024-09-06": 0
    }
}

# Har bir mahsulot uchun barcha sanalardagi sotilgan dona sonlarini yig'indisini hisoblash
# va bu yig'indi bo'yicha mahsulotlarni saralash
sorted_data_by_total_sales = dict(sorted(data.items(), key=lambda item: sum(item[1].values()), reverse=True))

print(sorted_data_by_total_sales)
