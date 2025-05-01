from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Adds sample iPhone products to the database'

    def handle(self, *args, **options):
        products = [
            {
                'title': 'iPhone 15 Pro Max 256GB',
                'description': 'Новый iPhone 15 Pro Max с процессором A17 Pro, камерой 48MP и дисплеем 6.7"',
                'price': '129990',
                'phone_model': 'iPhone 15 Pro Max',
                'color': 'Титановый',
                'storage': '256GB',
                'condition': 'A',
                'body_condition': 'A',
                'screen_condition': 'A',
                'battery_health': 100,
                'turbo': True,
                'комплектация': ['Телефон', 'Кабель USB-C', 'Документация', 'Сим-инструмент'],
                'screen_size': 6.7
            },
            {
                'title': 'iPhone 15 Pro 128GB',
                'description': 'iPhone 15 Pro с процессором A17 Pro, камерой 48MP и дисплеем 6.1"',
                'price': '99990',
                'phone_model': 'iPhone 15 Pro',
                'color': 'Черный',
                'storage': '128GB',
                'condition': 'A',
                'body_condition': 'A',
                'screen_condition': 'A',
                'battery_health': 100,
                'turbo': True,
                'комплектация': ['Телефон', 'Кабель USB-C', 'Документация', 'Сим-инструмент'],
                'screen_size': 6.1
            },
            {
                'title': 'iPhone 14 Pro Max 512GB',
                'description': 'iPhone 14 Pro Max с процессором A16, камерой 48MP и дисплеем 6.7"',
                'price': '109990',
                'phone_model': 'iPhone 14 Pro Max',
                'color': 'Фиолетовый',
                'storage': '512GB',
                'condition': 'A',
                'body_condition': 'A',
                'screen_condition': 'A',
                'battery_health': 98,
                'turbo': True,
                'комплектация': ['Телефон', 'Кабель Lightning', 'Документация', 'Сим-инструмент'],
                'screen_size': 6.7
            },
            {
                'title': 'iPhone 14 Pro 256GB',
                'description': 'iPhone 14 Pro с процессором A16, камерой 48MP и дисплеем 6.1"',
                'price': '89990',
                'phone_model': 'iPhone 14 Pro',
                'color': 'Золотой',
                'storage': '256GB',
                'condition': 'A',
                'body_condition': 'A',
                'screen_condition': 'A',
                'battery_health': 97,
                'turbo': True,
                'комплектация': ['Телефон', 'Кабель Lightning', 'Документация', 'Сим-инструмент'],
                'screen_size': 6.1
            },
            {
                'title': 'iPhone 13 Pro Max 1TB',
                'description': 'iPhone 13 Pro Max с процессором A15, камерой 12MP и дисплеем 6.7"',
                'price': '99990',
                'phone_model': 'iPhone 13 Pro Max',
                'color': 'Графитовый',
                'storage': '1TB',
                'condition': 'B',
                'body_condition': 'B',
                'screen_condition': 'A',
                'battery_health': 92,
                'turbo': True,
                'комплектация': ['Телефон', 'Кабель Lightning', 'Документация', 'Сим-инструмент'],
                'screen_size': 6.7
            },
            {
                'title': 'iPhone 13 Pro 128GB',
                'description': 'iPhone 13 Pro с процессором A15, камерой 12MP и дисплеем 6.1"',
                'price': '79990',
                'phone_model': 'iPhone 13 Pro',
                'color': 'Серебристый',
                'storage': '128GB',
                'condition': 'B',
                'body_condition': 'B',
                'screen_condition': 'A',
                'battery_health': 91,
                'turbo': True,
                'комплектация': ['Телефон', 'Кабель Lightning', 'Документация', 'Сим-инструмент'],
                'screen_size': 6.1
            },
            {
                'title': 'iPhone 12 Pro Max 256GB',
                'description': 'iPhone 12 Pro Max с процессором A14, камерой 12MP и дисплеем 6.7"',
                'price': '69990',
                'phone_model': 'iPhone 12 Pro Max',
                'color': 'Тихоокеанский синий',
                'storage': '256GB',
                'condition': 'B',
                'body_condition': 'B',
                'screen_condition': 'B',
                'battery_health': 88,
                'turbo': True,
                'комплектация': ['Телефон', 'Кабель Lightning', 'Документация', 'Сим-инструмент'],
                'screen_size': 6.7
            },
            {
                'title': 'iPhone 12 Pro 128GB',
                'description': 'iPhone 12 Pro с процессором A14, камерой 12MP и дисплеем 6.1"',
                'price': '59990',
                'phone_model': 'iPhone 12 Pro',
                'color': 'Графитовый',
                'storage': '128GB',
                'condition': 'B',
                'body_condition': 'B',
                'screen_condition': 'B',
                'battery_health': 87,
                'turbo': True,
                'комплектация': ['Телефон', 'Кабель Lightning', 'Документация', 'Сим-инструмент'],
                'screen_size': 6.1
            },
            {
                'title': 'iPhone 11 Pro Max 64GB',
                'description': 'iPhone 11 Pro Max с процессором A13, камерой 12MP и дисплеем 6.5"',
                'price': '49990',
                'phone_model': 'iPhone 11 Pro Max',
                'color': 'Серебристый',
                'storage': '64GB',
                'condition': 'C',
                'body_condition': 'C',
                'screen_condition': 'B',
                'battery_health': 82,
                'turbo': False,
                'комплектация': ['Телефон', 'Кабель Lightning', 'Документация', 'Сим-инструмент'],
                'screen_size': 6.5
            },
            {
                'title': 'iPhone 11 Pro 256GB',
                'description': 'iPhone 11 Pro с процессором A13, камерой 12MP и дисплеем 5.8"',
                'price': '44990',
                'phone_model': 'iPhone 11 Pro',
                'color': 'Зеленый',
                'storage': '256GB',
                'condition': 'C',
                'body_condition': 'C',
                'screen_condition': 'B',
                'battery_health': 80,
                'turbo': False,
                'комплектация': ['Телефон', 'Кабель Lightning', 'Документация', 'Сим-инструмент'],
                'screen_size': 5.8
            }
        ]

        for product_data in products:
            product = Product.objects.create(**product_data)
            self.stdout.write(self.style.SUCCESS(f'Successfully created product: {product.title}'))

        self.stdout.write(self.style.SUCCESS('Successfully added all sample products')) 