from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from decimal import Decimal


#Профиль
class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    avatar = models.ImageField(upload_to='avatar', blank=True, default=None, verbose_name='Фото профиля')
    first_name = models.CharField(max_length=100, blank=True, verbose_name='Имя')
    last_name = models.CharField(max_length=100, blank=True, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Профиль {self.user.username}'

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()


# Адреса пользователя
class UserAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_line1 = models.CharField(max_length=255, verbose_name='Улица, дом, квартира')
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name='Дополнительная информация')
    city = models.CharField(max_length=100, verbose_name='Город')
    postal_code = models.CharField(max_length=20, verbose_name='Почтовый индекс')
    country = models.CharField(max_length=100, verbose_name='Страна', default='Россия')
    is_default = models.BooleanField(default=False, verbose_name='Основной адрес')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Адрес пользователя'
        verbose_name_plural = 'Адреса пользователей'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f'{self.address_line1}, {self.city}, {self.postal_code}'

    def clean(self):
        if self.is_default and UserAddress.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).exists():
            raise ValidationError('У пользователя может быть только один адрес ')

    def save(self, *args, **kwargs):
        if self.is_default:
            UserAddress.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_default and self.user.addresses.count() > 1:
            # Назначаем другой адрес основным перед удалением
            new_default = self.user.addresses.exclude(pk=self.pk).first()
            new_default.is_default = True
            new_default.save()
        super().delete(*args, **kwargs)

# Платежные карты
class PaymentCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards', verbose_name='Пользователь',
                             null=False)
    card_holder = models.CharField(max_length=100, verbose_name='Владелец карты')
    card_number = models.CharField(max_length=16, verbose_name='Номер карты')
    expiry_month = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)],
                                               verbose_name='Месяц окончания')
    expiry_year = models.PositiveIntegerField(verbose_name='Год окончания')
    cvv = models.CharField(max_length=4, verbose_name='CVV код')
    is_default = models.BooleanField(default=False, verbose_name='Основная карта')
    created_at = models.DateTimeField(auto_now_add=True)
    CARD_TYPES = (
        ('visa', 'Visa'),
        ('mastercard', 'MasterCard'),
        ('mir', 'Мир'),
        ('other', 'Другая'),
    )
    card_type = models.CharField(max_length=20, choices=CARD_TYPES, default='visa', verbose_name='Тип карты')

    class Meta:
        verbose_name = 'Платежная карта'
        verbose_name_plural = 'Платежные карты'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f'{self.get_card_type_display()} {self.masked_number} ({self.card_holder})'

    @property
    def masked_number(self):
        return f'**** **** **** {self.card_number[-4:]}'

    @property
    def masked_cvv(self):
        return '***'

    @property
    def expiry_date(self):
        return f"{self.expiry_month:02d}/{self.expiry_year}"

    def clean(self):
        if self.expiry_month is None or self.expiry_year is None:
            raise ValidationError('Необходимо указать месяц и год окончания действия карты')

        current_year = timezone.now().year
        current_month = timezone.now().month

        if self.expiry_year < current_year or (self.expiry_year == current_year and self.expiry_month < current_month):
            raise ValidationError('Срок действия карты истек')

        if self.is_default:
            existing_default = PaymentCard.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).first()

            if existing_default:
                raise ValidationError('У пользователя может быть только одна карта по умолчанию')

    def save(self, *args, **kwargs):
        if self.card_number:
            self.card_number = self.card_number.replace(' ', '')

        if not self.pk and not PaymentCard.objects.filter(user=self.user).exists():
            self.is_default = True

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_default and self.user.cards.count() > 1:
            new_default = self.user.cards.exclude(pk=self.pk).first()
            new_default.is_default = True
            new_default.save()
        super().delete(*args, **kwargs)

# Категории + Новинки
class TypeProduct(models.Model):
    image = models.ImageField(upload_to='type')
    name = models.CharField(max_length=200, verbose_name="Наименование категории")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок сортировки")

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_list_by_category', args=[self.pk])

# Сортировка
class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True, quantity__gt=0)

    def sort_by_price(self):
        return self.order_by('price')

    def sort_by_new(self):
        return self.order_by('-created_at')

    def sort_by_popularity(self):
        return self.order_by('-views')

# Все продукты
class ViewProduct(models.Model):
    TYPE_CHOICES = [
        ('all', 'Показать все'),
        ('gold', 'Золото'),
        ('silver', 'Серебро'),
    ]

    type_material = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Вид материала", default='all')
    category = models.ForeignKey(TypeProduct, related_name='view_products', on_delete=models.CASCADE,
                                 verbose_name='Категория', null=True, blank=True)
    product = models.ImageField(upload_to='productimage', verbose_name="Изображение товара")
    product2 = models.ImageField(upload_to='productimageswiper', verbose_name="Изображение товара2", null=True,
                                 blank=True)
    name_product = models.CharField(max_length=200, verbose_name="Название")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Количество")
    is_active = models.BooleanField(default=True, verbose_name="Активен", db_index=True)
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Старая цена')
    discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name='Скидка (%)')
    final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                      verbose_name='Цена со скидкой')
    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Все товары'
        verbose_name_plural = 'Все товары'
        indexes = [models.Index(fields=['is_active']), ]

    def __str__(self):
        return self.name_product

    def get_absolute_url(self):
        return reverse('product_view', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        self.is_active = self.quantity > 0
        if self.discount:
            factor = Decimal(self.discount) / Decimal(100)
            self.final_price = round(self.price * (1 - factor), 2)
        else:
            self.final_price = self.price
        super().save(*args, **kwargs)

    @property
    def discounted_price(self):
        if self.discount:
            return round(self.price * (1 - self.discount / 100), 2)
        return self.price

    @property
    def price_with_currency(self):
        if self.discount:
            return f"<span class='old-price'>{self.price} ₽</span> <span class='discounted-price'>{self.final_price} ₽</span>"
        return f"{self.price} ₽"

# Информация о продукте
class InfoProduct(models.Model):
    view_product = models.OneToOneField(ViewProduct, related_name='detailed_info', on_delete=models.CASCADE,
                                        verbose_name='Товар')
    info = models.TextField(verbose_name="Описание")

    class Meta:
        verbose_name = 'Информация о товаре'
        verbose_name_plural = 'Информация о товаре'

    def __str__(self):
        return self.view_product.name_product

    def get_absolute_url(self):
        return reverse('product_view', kwargs={'pk': self.view_product.pk})

# Состав и характеристики
class ProductDetail(models.Model):
    product = models.ForeignKey(InfoProduct, related_name='details', on_delete=models.CASCADE)
    title = models.CharField(default="Состав и характеристики", max_length=100)
    content = models.TextField(default="Содержание")

    class Meta:
        verbose_name = 'Детальная информация'
        verbose_name_plural = 'Детальная информация'

    def __str__(self):
        return f"{self.title} для {self.product.view_product.name_product}"

# Предупреждения
class ProductWarning(models.Model):
    product = models.ForeignKey(InfoProduct, related_name='warnings', on_delete=models.CASCADE)
    title = models.CharField(default="Предупреждение", max_length=100)
    content = models.TextField(default="Текст предупреждения")

    class Meta:
        verbose_name = 'Предупреждение'
        verbose_name_plural = 'Предупреждения'

    def __str__(self):
        return f"{self.title} для {self.product.view_product.name_product}"

#Заказы
class Order(models.Model):
    ORDER_STATUS = (
        ('pending', 'В обработке'),
        ('processing', 'В процессе'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
        ('returned', 'Возвращен'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    order_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата заказа')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending', verbose_name='Статус заказа')
    shipping_address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True,
                                         related_name='shipping_orders')
    billing_address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True,
                                        related_name='billing_orders')
    payment_card = models.ForeignKey(PaymentCard, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True, verbose_name='Дата доставки')
    delivery_time = models.CharField(max_length=50, blank=True, null=True, verbose_name='Время доставки')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма товаров')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=450, verbose_name='Стоимость доставки')
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Скидка')
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Итоговая сумма')
    email = models.EmailField(verbose_name='Email для заказа')
    phone = models.CharField(max_length=20, verbose_name='Телефон для заказа')
    notes = models.TextField(blank=True, verbose_name='Примечания к заказу')
    tracking_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='Трек-номер')
    cancellation_reason = models.TextField(blank=True, null=True, verbose_name='Причина отмены')

    class Meta:
        ordering = ['-order_date']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ #{self.order_number}'

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all()) + self.shipping_cost - self.discount

    @property
    def status_color(self):
        colors = {
            'pending': 'secondary',
            'processing': 'info',
            'shipped': 'warning',
            'delivered': 'success',
            'cancelled': 'danger',
        }
        return colors.get(self.status, 'secondary')

    def get_available_statuses(self):
        """Возвращает доступные статусы для текущего состояния заказа"""
        if self.status == 'pending':
            return [('processing', 'В процессе'), ('cancelled', 'Отменен')]
        elif self.status == 'processing':
            return [('shipped', 'Отправлен'), ('cancelled', 'Отменен')]
        elif self.status == 'shipped':
            return [('delivered', 'Доставлен'), ('cancelled', 'Отменен')]
        elif self.status == 'cancelled':
            return []
        return []

    @property
    def can_be_cancelled(self):
        """Можно ли отменить заказ"""
        return self.status in ['pending', 'processing', 'shipped']

    @property
    def status_css_class(self):
        return f"shine-status-{self.status}"

# Элементы заказа
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(ViewProduct, on_delete=models.PROTECT, verbose_name='Товар')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    discount = models.PositiveIntegerField(default=0, verbose_name='Скидка (%)')
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена со скидкой')

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f'{self.product.name_product} x{self.quantity}'

    def total_price(self):
        return self.price * self.quantity


# Подтверждение заказа
class OrderConfirmation(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='confirmation')
    confirmation_number = models.CharField(max_length=50, unique=True)
    confirmed_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_content = models.TextField(blank=True, verbose_name='Содержание письма')

    class Meta:
        verbose_name = 'Подтверждение заказа'
        verbose_name_plural = 'Подтверждения заказов'

    def __str__(self):
        return f'Подтверждение #{self.confirmation_number}'



#Избранное
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist', verbose_name='Пользователь')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def __str__(self):
        return f'Избранное пользователя {self.user.username}'


#Избранное элемент
class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items',
                                 verbose_name='Список избранного')
    product = models.ForeignKey(ViewProduct, on_delete=models.CASCADE, verbose_name='Товар')

    class Meta:
        unique_together = ('wishlist', 'product')
        verbose_name = 'Элемент избранного'
        verbose_name_plural = 'Элементы избранного'

    def __str__(self):
        return f'{self.product.name_product} в избранном у {self.wishlist.user.username}'

#Корзина
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart', verbose_name='Пользователь')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f'Корзина пользователя {self.user.username}'

    @property
    def total_items(self):
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def total_price(self):
        total = 0
        for item in self.items.all():
            if item.product.discount:
                total += item.product.final_price * item.quantity
            else:
                total += item.product.price * item.quantity
        return total

    def add_item(self, product, quantity=1):
        cart_item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        return cart_item

    def remove_item(self, product):
        try:
            cart_item = CartItem.objects.get(cart=self, product=product)
            cart_item.delete()
            return True
        except CartItem.DoesNotExist:
            return False

    def update_item_quantity(self, product, quantity):
        try:
            cart_item = CartItem.objects.get(cart=self, product=product)
            if quantity <= 0:
                cart_item.delete()
            else:
                cart_item.quantity = quantity
                cart_item.save()
            return True
        except CartItem.DoesNotExist:
            return False

    def check_availability(self):
        """Проверяет доступность всех товаров в корзине"""
        for item in self.items.all():
            if item.product.quantity < item.quantity:
                return False, item
        return True, None

    def create_order(self, user, address, payment_method=None):
        """Создает заказ из корзины"""
        order = Order.objects.create(
            user=user,
            email=user.email,
            phone=user.profile.phone,
            shipping_address=address,
            billing_address=address,
            payment_card=payment_method,
            subtotal=self.total_price,
            total=self.total_price,
        )

        for item in self.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                discounted_price=item.product.final_price if item.product.discount else item.product.price
            )
            # Уменьшаем количество товара на складе
            item.product.quantity -= item.quantity
            item.product.save()

        self.items.all().delete()  # Очищаем корзину
        return order

# Элементы корзины
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name='Корзина')
    product = models.ForeignKey(ViewProduct, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')
        verbose_name = 'Элемент корзины'
        verbose_name_plural = 'Элементы корзины'
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.product.name_product} ({self.quantity}) в корзине {self.cart.user.username}'

    @property
    def total_price(self):
        if self.product.discount:
            return self.product.final_price * self.quantity
        return self.product.price * self.quantity

    def save(self, *args, **kwargs):
        if self.quantity > self.product.quantity:
            raise ValidationError("Недостаточно товара на складе")
        super().save(*args, **kwargs)