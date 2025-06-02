from django.contrib import admin
from django.utils.safestring import mark_safe
from webapp.models import UserInfo,UserAddress,PaymentCard,TypeProduct,ViewProduct,InfoProduct,ProductDetail,ProductWarning,Order,OrderItem,OrderConfirmation,Wishlist,WishlistItem,Cart,CartItem

admin.site.register(UserInfo)
admin.site.register(UserAddress)
admin.site.register(PaymentCard)
admin.site.register(ViewProduct)
admin.site.register(TypeProduct)
class TypeProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_preview')
    readonly_fields = ('image_preview',)
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 100px;" />')
        return "No image"
    image_preview.short_description = 'Preview'

admin.site.register(InfoProduct)
admin.site.register(ProductDetail)
admin.site.register(ProductWarning)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OrderConfirmation)
admin.site.register(Wishlist)
admin.site.register(WishlistItem)
admin.site.register(Cart)
admin.site.register(CartItem)










# Register your models here.
