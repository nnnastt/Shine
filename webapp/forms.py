from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from datetime import date, timedelta, timezone, datetime
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from webapp.models import UserInfo, PaymentCard, UserAddress

# Регистрация
class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "pattern": "^[А-Яа-яЁё\-]+$",
            "title": "Только русские буквы и дефисы",
            "minlength": "2"
        }),
        label='Имя',
        error_messages={
            'required': 'Введите имя',
            'min_length': 'Имя должно содержать не менее 2 символов',
            'invalid': 'Только русские буквы и дефисы'
        }
    )

    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "pattern": "^[А-Яа-яЁё\-]+$",
            "title": "Только русские буквы и дефисы",
            "minlength": "2"
        }),
        label='Фамилия',
        error_messages={
            'required': 'Введите фамилию',
            'min_length': 'Фамилия должна содержать не менее 2 символов',
            'invalid': 'Только русские буквы и дефисы'
        }
    )

    middle_name = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "False",
            "pattern": "^[А-Яа-яЁё\-]*$",
            "title": "Только русские буквы и дефисы (необязательно)"
        }),
        label='Отчество',
        required=False,
        error_messages={
            'invalid': 'Только русские буквы и дефисы'
        }
    )

    phone = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "pattern": "^\+7\(\d{3}\)-\d{3}-\d{2}-\d{2}$",
            "title": "Формат: +7(XXX)-XXX-XX-XX",
            "placeholder": "+7(XXX)-XXX-XX-XX"
        }),
        label='Телефон',
        error_messages={
            'required': 'Введите номер телефона',
            'invalid': 'Формат: +7(XXX)-XXX-XX-XX'
        }
    )

    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "required": "True",
            "max": (date.today() - timedelta(days=14 * 365)).strftime("%Y-%m-%d"),
            "min": "1900-01-01"
        }),
        label='Дата рождения',
        error_messages={
            'required': 'Введите дату рождения',
            'invalid': 'Введите корректную дату',
            'max_value': 'Вы должны быть старше 14 лет',
            'min_value': 'Дата не может быть раньше 1900 года'
        }
    )

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        today = date.today()

        if (today - birth_date) < timedelta(days=14 * 365):
            raise forms.ValidationError("Вы должны быть старше 14 лет")

        if birth_date > today:
            raise forms.ValidationError("Дата рождения не может быть в будущем")

        return birth_date

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "middle_name", "birth_date", "phone", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.error_messages = {
            'password_mismatch': "Пароли не совпадают",
        }

        self.fields["username"].widget.attrs.update({
            "class": "input-field",
            "type": "text",
            "pattern": "^[A-Za-zА-Яа-яЁё]+$",
            "minlength": "6",
            "title": "Не менее 6 символов"
        })
        self.fields["username"].label = "Логин"
        self.fields["username"].error_messages = {
            'required': 'Введите логин',
            'min_length': 'Логин должен содержать не менее 6 символов',
            'invalid': 'Только буквы (русские или латинские)'
        }

        self.fields["password1"].widget.attrs.update({
            "class": "input-field",
            "type": "password",
            "title": "Не менее 8 символов",
        })
        self.fields["password1"].label = "Пароль"
        self.fields["password1"].help_text = "Пароль должен содержать не менее 8 символов"
        self.fields["password1"].error_messages = {
            'required': 'Введите пароль',
            'min_length': 'Пароль должен содержать не менее 8 символов',
        }

        self.fields["password2"].widget.attrs.update({
            "class": "input-field",
            "type": "password",
            "title": "Не менее 8 символов",
        })
        self.fields["password2"].label = "Подтверждение пароля"
        self.fields["password2"].help_text = "Введите пароль ещё раз для подтверждения"
        self.fields["password2"].error_messages = {
            'required': 'Повторите пароль',
        }



# Профиль
class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Имя',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "pattern": "^[А-Яа-яЁё\-]+$",
            "title": "Только русские буквы и дефисы",
            "minlength": "2"
        }),
        error_messages={
            'required': 'Поле "Имя" обязательно для заполнения',
            'min_length': 'Имя должно содержать минимум 2 символа',
            'invalid': 'Имя может содержать только русские буквы и дефис'
        }
    )

    last_name = forms.CharField(
        label='Фамилия',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "pattern": "^[А-Яа-яЁё\-]+$",
            "title": "Только русские буквы и дефисы",
            "minlength": "2"
        }),
        error_messages={
            'required': 'Поле "Фамилия" обязательно для заполнения',
            'min_length': 'Фамилия должна содержать минимум 2 символа',
            'invalid': 'Фамилия может содержать только русские буквы и дефис'
        }
    )

    middle_name = forms.CharField(
        label='Отчество',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "pattern": "^[А-Яа-яЁё\-]*$",
            "title": "Только русские буквы и дефисы (необязательно)"
        }),
        required=False,
        error_messages={
            'invalid': 'Отчество может содержать только русские буквы и дефис'
        }
    )

    phone = forms.CharField(
        label='Телефон',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "+7(XXX)-XXX-XX-XX"
        }),
        error_messages={
            'required': 'Поле "Телефон" обязательно для заполнения',
            'invalid': 'Введите телефон в формате +7(XXX)-XXX-XX-XX'
        }
    )

    birth_date = forms.DateField(
        label='Дата рождения',
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "max": (date.today() - timedelta(days=14 * 365)).strftime("%Y-%m-%d"),
            "min": "1900-01-01"
        }),
        error_messages={
            'required': 'Поле "Дата рождения" обязательно для заполнения',
            'invalid': 'Введите корректную дату рождения'
        }
    )

    class Meta:
        model = UserInfo
        fields = ['first_name', 'last_name', 'middle_name', 'phone', 'birth_date', 'avatar']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'phone': forms.TextInput(attrs={'placeholder': '+7(XXX)-XXX-XX-XX'}),
        }

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        today = date.today()

        if birth_date > today:
            raise ValidationError('Дата рождения не может быть в будущем')

        if birth_date > today - timedelta(days=14 * 365):
            raise ValidationError('Вы должны быть старше 14 лет')

        return birth_date

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        cleaned_phone = ''.join(c for c in phone if c.isdigit() or c == '+')

        if not cleaned_phone.startswith('7') and not cleaned_phone.startswith('+7'):
            raise ValidationError('Телефон должен начинаться с +7 или 7')

        if len(cleaned_phone) != 11:
            raise ValidationError('Телефон должен содержать 12 цифр')

        return f"+7({cleaned_phone[1:4]})-{cleaned_phone[4:7]}-{cleaned_phone[7:9]}-{cleaned_phone[9:11]}"

# Адрес информация
class AddressForm(forms.ModelForm):
    address_line1 = forms.CharField(
        label='Улица, дом, квартира',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "minlength": "5"
        }),
        error_messages={
            'required': 'Поле "Адрес" обязательно для заполнения',
            'min_length': 'Адрес должен содержать минимум 5 символов'
        }
    )

    city = forms.CharField(
        label='Город',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "pattern": "^[А-Яа-яЁё\s\-]+$",
            "title": "Только русские буквы, пробелы и дефисы"
        }),
        error_messages={
            'required': 'Поле "Город" обязательно для заполнения',
            'invalid': 'Название города может содержать только русские буквы, пробелы и дефисы'
        }
    )

    postal_code = forms.CharField(
        label='Почтовый индекс',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "pattern": "^[0-9]{6}$",
            "title": "6 цифр"
        }),
        error_messages={
            'required': 'Поле "Почтовый индекс" обязательно для заполнения',
            'invalid': 'Почтовый индекс должен состоять из 6 цифр'
        }
    )
    country = forms.CharField(
        label='Страна',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Россия"
        }),
        error_messages={
            'required': 'Поле "Страна" обязательно для заполнения'
        }
    )

    class Meta:
        model = UserAddress
        fields = ['address_line1', 'address_line2', 'city', 'postal_code', 'country', 'is_default']
        widgets = {
            'address_line2': forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Дополнительная информация"
            }),
            'is_default': forms.CheckboxInput(attrs={
                "class": "form-check-input"
            })
        }

    def clean_postal_code(self):
        postal_code = self.cleaned_data['postal_code']
        if not postal_code.isdigit() or len(postal_code) != 6:
            raise ValidationError('Почтовый индекс должен состоять из 6 цифр')
        return postal_code

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        is_default = cleaned_data.get('is_default')

        if is_default and self.request:
            UserAddress.objects.filter(user=self.request.user, is_default=True).update(is_default=False)

        return cleaned_data

# Информация о картах
class PaymentCardForm(forms.ModelForm):
    card_holder = forms.CharField(
        label='Имя владельца',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "pattern": "^[A-Za-zА-Яа-яЁё\s\-]+$",
            "title": "Только буквы и пробелы"
        }),
        error_messages={
            'required': 'Поле "Имя владельца" обязательно для заполнения',
            'invalid': 'Имя может содержать только буквы и пробелы'
        }
    )

    card_number = forms.CharField(
        label='Номер карты',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "placeholder": "XXXX XXXX XXXX XXXX",
        }),
        error_messages={
            'required': 'Поле "Номер карты" обязательно для заполнения',
        }
    )

    expiry_month = forms.IntegerField(
        label='Месяц окончания',
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "required": "True",
            "min": "1",
            "max": "12",
            "placeholder": "MM"
        }),
        error_messages={
            'required': 'Поле "Месяц" обязательно для заполнения',
            'min_value': 'Месяц должен быть от 1 до 12',
            'max_value': 'Месяц должен быть от 1 до 12'
        }
    )

    expiry_year = forms.IntegerField(
        label='Год окончания',
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "required": "True",
            "min": datetime.now().year,
            "max": datetime.now().year + 20,
            "placeholder": "YYYY"
        }),
        error_messages={
            'required': 'Поле "Год" обязательно для заполнения',
            'min_value': 'Год не может быть меньше текущего',
            'max_value': 'Год не может быть больше текущего + 20 лет'
        }
    )

    cvv = forms.CharField(
        label='CVV',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "pattern": "^[0-9]{3,4}$",
            "placeholder": "XXX",
            "maxlength": "4",
            "title": "3 или 4 цифры"
        }),
        error_messages={
            'required': 'Поле "CVV" обязательно для заполнения',
            'invalid': 'CVV должен состоять из 3 или 4 цифр'
        }
    )

    class Meta:
        model = PaymentCard
        fields = ['card_holder', 'card_number', 'expiry_month', 'expiry_year', 'cvv', 'card_type', 'is_default']
        widgets = {
            'card_type': forms.Select(attrs={
                "class": "form-control"
            }),
            'is_default': forms.CheckboxInput(attrs={
                "class": "form-check-input"
            })
        }

    def clean_card_number(self):
        card_number = self.cleaned_data['card_number'].replace(' ', '')
        if len(card_number) != 16 or not card_number.isdigit():
            raise ValidationError('Введите 16 цифр номера карты')
        return card_number[-4:]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def cleaner(self):
        cleaned_data = super().clean()
        is_default = cleaned_data.get('is_default')

        if is_default and self.request:
            PaymentCard.objects.filter(user=self.request.user, is_default=True).update(is_default=False)

        return cleaned_data

    def clean(self):
        cleaned_data = super().clean()
        expiry_month = cleaned_data.get('expiry_month')
        expiry_year = cleaned_data.get('expiry_year')

        if expiry_month is None or expiry_year is None:
            raise ValidationError('Необходимо указать месяц и год окончания действия карты')

        current_year = datetime.now().year
        current_month = datetime.now().month

        if expiry_year < current_year or (expiry_year == current_year and expiry_month < current_month):
            raise ValidationError('Срок действия карты истек')

        return cleaned_data


# Загрузка аватарки
class AvatarUpdateForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = ['avatar']

# Система корзины
class CheckoutForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if hasattr(self.user, 'profile') and self.user.profile.phone:
            self.fields['phone'].initial = self.user.profile.phone

    phone = forms.CharField(
        label='Телефон',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "placeholder": "+7(XXX)-XXX-XX-XX"
        })
    )

    address = forms.CharField(
        label='Адрес',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "placeholder": "Улица, дом, квартира"
        })
    )

    city = forms.CharField(
        label='Город',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "placeholder": "Москва"
        })
    )

    postal_code = forms.CharField(
        label='Почтовый индекс',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "placeholder": "123456"
        })
    )

    card_name = forms.CharField(
        label='Имя на карте',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "placeholder": "IVAN IVANOV"
        })
    )

    card_number = forms.CharField(
        label='Номер карты',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "placeholder": "XXXX XXXX XXXX XXXX"
        })
    )

    card_expiry = forms.CharField(
        label='Срок действия (MM/YY)',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "placeholder": "MM/YY"
        })
    )

    card_cvv = forms.CharField(
        label='CVV',
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "placeholder": "XXX"
        })
    )

    delivery_date = forms.DateField(
        label='Дата доставки',
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "required": "True"
        })
    )

    delivery_time = forms.ChoiceField(
        label='Время доставки',
        choices=[
            ('09:00-12:00', '09:00-12:00'),
            ('12:00-15:00', '12:00-15:00'),
            ('15:00-18:00', '15:00-18:00'),
            ('18:00-21:00', '18:00-21:00')
        ],
        widget=forms.Select(attrs={
            "class": "form-control",
            "required": "True"
        })
    )

    def clean_delivery_date(self):
        delivery_date = self.cleaned_data['delivery_date']
        min_date = timezone.now().date() + timedelta(days=3)
        max_date = timezone.now().date() + timedelta(days=30)

        if delivery_date < min_date:
            raise ValidationError('Дата доставки должна быть не ранее чем через 3 дня')
        if delivery_date > max_date:
            raise ValidationError('Дата доставки должна быть не позднее чем через 30 дней')
        return delivery_date

    def clean_card_expiry(self):
        expiry = self.cleaned_data['card_expiry']
        try:
            month, year = map(int, expiry.split('/'))
            if month < 1 or month > 12:
                raise ValidationError('Неверный месяц')
            if year < timezone.now().year % 100 or year > (timezone.now().year % 100) + 10:
                raise ValidationError('Неверный год')
        except (ValueError, IndexError):
            raise ValidationError('Неверный формат. Используйте MM/YY')
        return expiry

