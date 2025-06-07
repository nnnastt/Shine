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


# Платежные карты (значительно улучшено)
class PaymentCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
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
        current_year = timezone.now().year
        current_month = timezone.now().month
        if self.expiry_year < current_year or (self.expiry_year == current_year and self.expiry_month < current_month):
            raise ValidationError('Срок действия карты истек')
        if self.is_default and PaymentCard.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).exists():
            raise ValidationError('У пользователя может быть только одна карта по умолчанию')

    def save(self, *args, **kwargs):
        if self.is_default:
            PaymentCard.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


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
    view_product = models.ForeignKey(ViewProduct, related_name='detailed_info', on_delete=models.CASCADE,
                                     verbose_name='Товар')
    info = models.TextField(verbose_name="Описание")

    class Meta:
        verbose_name = 'Информация о товаре'
        verbose_name_plural = 'Информация о товаре'

    def __str__(self):
        return self.view_product.name_product

    def get_absolute_url(self):
        return reverse('product_view', kwargs={'pk': self.view_product.pk})


# Детали
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

    PAYMENT_STATUS = (
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачен'),
        ('failed', 'Ошибка оплаты'),
        ('refunded', 'Возврат средств'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    order_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата заказа')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending', verbose_name='Статус заказа')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending',
                                      verbose_name='Статус оплаты')
    shipping_address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True,
                                         related_name='shipping_orders')
    billing_address = models.ForeignKey(UserAddress, on_delete=models.SET_NULL, null=True,
                                        related_name='billing_orders')
    payment_card = models.ForeignKey(PaymentCard, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True, verbose_name='Дата доставки')
    delivery_time = models.CharField(max_length=50, blank=True, null=True, verbose_name='Время доставки')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма товаров')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Стоимость доставки')
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Скидка')
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Итоговая сумма')
    email = models.EmailField(verbose_name='Email для заказа')
    phone = models.CharField(max_length=20, verbose_name='Телефон для заказа')
    notes = models.TextField(blank=True, verbose_name='Примечания к заказу')
    tracking_number = models.CharField(max_length=100, blank=True, null=True, verbose_name='Трек-номер')

    class Meta:
        ordering = ['-order_date']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ #{self.order_number}'


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




