from django.db import models
from django.contrib.auth.models import User

class AccessToken(models.Model):
	token = models.CharField(max_length=30)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		get_latest_by = 'created_at'

	def __str__(self):
		return self.token

class Trader(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    phone_number  = models.CharField(max_length=10)
    collateral_amount = models.DecimalField(max_digits=10, decimal_places=2)
    county = models.CharField(max_length=50)
    sub_county = models.CharField(max_length=50)

    def __str__(self):       
        return f"{self.last_name}, {self.first_name}"

class Transaction(models.Model):
    """
     add a field to show when the seller has accepted to go ahead with the sale
    """
    sender = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver = models.ForeignKey(Trader, on_delete=models.CASCADE, related_name='received_transactions')
    time = models.DateTimeField(auto_now=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    product = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    status = models.TextField(choices=(('Accepted', 'Accepted'), ('Pending', 'Pending'),('Rejected', 'Rejected'),('Delivered', 'Delivered')))
    security_key = models.CharField(max_length=10,default="0000000000")

    def __str__(self):
        return f"buying: {self.product}, from: {self.receiver}"

class Seller_Commitment(models.Model):
    """ m-pesa payment to confirm you want to procede to do the exchange """
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)

class Recieved_confirmation(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    confirmation = models.BinaryField()

class Complaint(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    issue =  models.CharField(max_length=100)
    status = models.TextField(choices=(('Pending', 'Pending'), ('Resolved', 'Resolved')),default="Pending")

class Verdict(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE)
    # response = models.BinaryField()
    comment = models.CharField(max_length=50, default="none")
    action = models.TextField(choices=(('Reject', 'Reject'), ('Proceed', 'Proceed')),default="Proceed")

class Intermediary(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=10)
    def __str__(self):       
        return f"{self.user.username}"       

class Review(models.Model):
    seller = models.ForeignKey(Trader, on_delete=models.CASCADE)
    comment = models.CharField(max_length=50)
    stars = models.DecimalField(max_digits=5, decimal_places=0)

class Penalty(models.Model):
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2)

