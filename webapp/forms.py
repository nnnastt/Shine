from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from datetime import date, timedelta
from django.core.exceptions import ValidationError

from webapp.models import UserInfo, PaymentCard, UserAddress


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "pattern": "^[А-Яа-яЁё\-]+$",
            "title": "Только русские буквы и дефисы",
            "minlength": "2"
        }),
        label='Имя'
    )

    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "pattern": "^[А-Яа-яЁё\-]+$",
            "title": "Только русские буквы и дефисы",
            "minlength": "2"
        }),
        label='Фамилия'
    )

    middle_name = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "False",
            "pattern": "^[А-Яа-яЁё\-]*$",
            "title": "Только русские буквы и дефисы (необязательно)"
        }),
        label='Отчество',
        required=False
    )

    phone = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "required": "True",
            "pattern": "^\+7\(\d{3}\)-\d{3}-\d{2}-\d{2}$",
            "title": "Формат: +7(XXX)-XXX-XX-XX",
            "placeholder": "+7(XXX)-XXX-XX-XX"
        }),
        label='Телефон'
    )
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
            "required": "True",
            "max": (date.today() - timedelta(days=14 * 365)).strftime("%Y-%m-%d"),
            "min": "1900-01-01"
        }),
        label='Дата рождения'
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
        self.fields["username"].widget.attrs.update({
            "class": "input-field",
            "type": "text",
            "pattern": "^[A-Za-zА-Яа-яЁё]+$",
            "minlength": "6",
            "title": "Не менее 6 символов"
        })
        self.fields["username"].label = "Логин"

        self.fields["password1"].widget.attrs.update({
            "class": "input-field",
            "type": "password",
        })
        self.fields["password1"].label = "Пароль"

        self.fields["password2"].widget.attrs.update({
            "class": "input-field",
            "type": "password",
            "title": "Не менее 8 символов",
        })
        self.fields["password2"].label = "Подтверждение пароля"


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = ['first_name', 'last_name', 'middle_name', 'phone', 'birth_date', 'avatar']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'phone': forms.TextInput(attrs={'placeholder': '+7(XXX)-XXX-XX-XX'}),
        }

class AddressForm(forms.ModelForm):
    class Meta:
        model = UserAddress
        fields = ['address_line1', 'address_line2', 'city', 'postal_code', 'country', 'is_default']
        widgets = {
            'address_line1': forms.TextInput(attrs={'placeholder': 'Улица, дом, квартира'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Дополнительная информация'}),
            'postal_code': forms.TextInput(attrs={'placeholder': 'Почтовый индекс'}),
        }


class PaymentCardForm(forms.ModelForm):
    class Meta:
        model = PaymentCard
        fields = ['card_holder', 'card_number', 'expiry_month', 'expiry_year', 'cvv', 'card_type', 'is_default']
        widgets = {
            'card_number': forms.TextInput(attrs={'placeholder': 'XXXX XXXX XXXX XXXX'}),
            'expiry_month': forms.NumberInput(attrs={'placeholder': 'MM', 'min': 1, 'max': 12}),
            'expiry_year': forms.NumberInput(attrs={'placeholder': 'YYYY', 'min': date.today().year}),
            'cvv': forms.TextInput(attrs={'placeholder': 'XXX', 'maxlength': 4}),
        }

class AvatarUpdateForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = ['avatar']