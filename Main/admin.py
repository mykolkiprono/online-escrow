from django.contrib import admin
from .models import *

class AccessTokenAdmin(admin.ModelAdmin):
    tokens = AccessToken.objects.all().count()
    list_display=['token','created_at']

admin.site.register(AccessToken,AccessTokenAdmin)

class TraderAdmin(admin.ModelAdmin):
    traders = Trader.objects.all().count()
    list_display=["first_name",
                    "last_name",
                    "phone_number",
                    "collateral_amount",
                    "county",
                    "sub_county"]

admin.site.register(Trader,TraderAdmin)


class TransactionAdmin(admin.ModelAdmin):
    customers = Transaction.objects.all().count()
    list_display=['sender','receiver','amount','time','product','description','status']

admin.site.register(Transaction,TransactionAdmin)

class Seller_CommitmentAdmin(admin.ModelAdmin):
    customers = Seller_Commitment.objects.all().count()
    list_display=['amount','transaction']

admin.site.register(Seller_Commitment,Seller_CommitmentAdmin)

class Recieved_confirmationAdmin(admin.ModelAdmin):
    customers = Recieved_confirmation.objects.all().count()
    list_display=['transaction','confirmation']

admin.site.register(Recieved_confirmation,Recieved_confirmationAdmin)

class ComplaintAdmin(admin.ModelAdmin):
    customers = Complaint.objects.all().count()
    list_display=['transaction','issue']

admin.site.register(Complaint,ComplaintAdmin)

class VerdictAdmin(admin.ModelAdmin):
    customers = Verdict.objects.all().count()
    list_display=['complaint']

admin.site.register(Verdict,VerdictAdmin)

class IntermediaryAdmin(admin.ModelAdmin):
    customers = Intermediary.objects.all().count()
    list_display=['user','phone_number']

admin.site.register(Intermediary,IntermediaryAdmin)

class ReviewAdmin(admin.ModelAdmin):
    customers = Review.objects.all().count()
    list_display=['seller','comment','stars']

admin.site.register(Review,ReviewAdmin)

class PenaltyAdmin(admin.ModelAdmin):
    customers = Penalty.objects.all().count()
    list_display=['trader','amount']

admin.site.register(Penalty,PenaltyAdmin)

