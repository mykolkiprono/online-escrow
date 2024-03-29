from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import *
from .models import *
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from decouple import config
from django.contrib.auth import authenticate, login, logout

from .mpesa.core import MpesaClient
from .mpesa.utils import mpesa_access_token
from .forms import *


import smtplib
import ssl
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from email.mime.image import MIMEImage


cl = MpesaClient()
stk_push_callback_url = 'https://api.darajambili.com/express-payment'
# stk_push_callback_url =appartment_name','appartment_number','usage' 'https://api.darajambili.com/express-payment'
b2c_callback_url = 'https://api.darajambili.com/b2c/result'

def send_email( subject, body, emails=[]):
    port = settings.EMAIL_PORT
    smtp_server = settings.EMAIL_HOST
    sender_email = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD
    receiver_email = emails
    # subject = 'Website registration'
    # body = 'Activate your account.'
    message = 'Subject: {}\n\n{}'.format(subject, body)
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
    return 1

def oauth_success(request):
	r = cl.access_token()
	return JsonResponse(r, safe=False)

def stk_push_success(request):
	amount = 1
	account_reference = 'ABC001'
	transaction_desc = 'STK Push Description'
	callback_url = stk_push_callback_url
	r = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
	return JsonResponse(r.response_description, safe=False)

def is_trader(user):
    return user.groups.filter(name='trader').exists()

def is_intermediary(user):
    return user.groups.filter(name='administrator').exists()

def signin(request):  
    loginForm=LoginForm()
    if request.method == "POST":
        username = request.POST['username']
        password =  request.POST['password']
        user = authenticate(
    		    request, 
    		    username=username, 
    		    password=password
        )
        if user:
            login(request, user)
            if is_trader(user):
                return redirect(customer_view)
            elif is_intermediary(user):
                return redirect(intermediary_view)                 
   
    return render(request, "auth/signin.html", {"loginForm":loginForm})

def signup(request):
    userForm=UserForm()
    traderForm=TraderForm()
    mydict={'userForm':userForm,'traderForm':TraderForm}
    if request.method=='POST':
        userForm=UserForm(request.POST)
        traderForm=TraderForm(request.POST,request.FILES)
        if userForm.is_valid() and traderForm.is_valid():
            user=userForm.save()
            raw_password = userForm.cleaned_data['password']
            user.set_password(user.password)
            # user.save()
            
            trader=traderForm.save(commit=False)
            trader.user=user
            trader.collateral_amount = 0.00
            trader.save()
            user.save()
            # login(request, user)            
            my_trader_group = Group.objects.get_or_create(name='trader')
            my_trader_group[0].user_set.add(user)
            login(request, user)     
            
            return redirect(customer_view)
    return render(request, "auth/signup.html", {'userForm':userForm,'traderForm':traderForm})

from django.apps import apps

def landing_view(request):
    models = apps.get_models()
    for m in models:
        print(m.__name__)
    return render(request, "landing/SoftLand/index.html", {})

def search_info(request):
    info = request.session['exists']
    del request.session['exists']
    return info

from django.db.models import Sum

def customer_view(request):
    user = request.user
    trader = Trader.objects.get(user=user)
    # we need transactions that i am awaiting delivery of, other traders are awaiting delivery of

    reviews = Review.objects.filter(seller=trader)
    buyer = trader.sent_transactions.all() # transactions where i am the buyer i need to confirm delivery or ancel the trade
    
    # awaiting_delivery_pending = trader.sent_transactions.all().filter(status="Accepted")
    # seller = trader.received_transactions.all() # where i am the seller now in the ones that am selling i need to deliver the product before the trade is cancelled
    # sending_delivery_pending = trader.sent_transactions.all().filter(status="Accepted")
     # awaiting_delivery_pending = trader.sent_transactions.all().filter(status="Accepted")
    awaiting_delivery_pending = trader.sent_transactions.all().filter(sender=trader)
    awaiting_delivery_pending = awaiting_delivery_pending.filter(status="Accepted")

    seller = trader.received_transactions.all() # where i am the seller now in the ones that am selling i need to deliver the product before the trade is cancelled
    sending_delivery_pending = trader.sent_transactions.all().filter(receiver=trader)
    sending_delivery_pending = sending_delivery_pending.filter(status="Accepted")
    transactions = Transaction.objects.filter(sender=trader) | \
                   Transaction.objects.filter(receiver=trader)

    pending = transactions.filter(status="Pending")
    success = transactions.filter(status="Accepted")
    # awaiting_delivery = transactions.filter(status="Accepted")
    rejected = transactions.filter(status="Rejected")
    complaints = Complaint.objects.filter(transaction__in=transactions)
    exists = ""
    total_ratings = Review.objects.filter(seller=trader).aggregate(total_stars=Sum('stars'))

    if 'username' in request.session:
        del request.session['username']

    if 'exists' in request.session:
        exists = request.session["exists"]
        del request.session['exists']

    return render(request, "main/Impact/index.html", {"sending_delivery_pending":sending_delivery_pending, "awaiting_delivery_pending":awaiting_delivery_pending, "user":user, "trader":trader,"transactions":transactions,"pending":pending, "success":success, "rejected":rejected,"exists":exists,"complaints":complaints,"total_ratings":total_ratings})

def confirm_delivery(request, pk):
    user = request.user
    trader = Trader.objects.get(user=user)

    trade = Transaction.objects.get(pk=pk)
    trade.status = "Delivered"
    trade.save()


    # mpesa payment for the full amount
    phone_number = trade.receiver.phone_number
    amount = int(trade.amount)
    account_reference = 'Payment to Online Escrow'
    transaction_desc = 'STK Push Description'
    callback_url = stk_push_callback_url
    # r = cl.stk_push(phone_number,amount, account_reference, transaction_desc, callback_url) 

    reviews = Review.objects.filter(seller=trader)
    buyer = trader.sent_transactions.all() # transactions where i am the buyer i need to confirm delivery or ancel the trade
    
    # awaiting_delivery_pending = trader.sent_transactions.all().filter(status="Accepted")
    awaiting_delivery_pending = trader.sent_transactions.all().filter(sender=trader)
    awaiting_delivery_pending = awaiting_delivery_pending.filter(status="Accepted")

    seller = trader.received_transactions.all() # where i am the seller now in the ones that am selling i need to deliver the product before the trade is cancelled
    sending_delivery_pending = trader.sent_transactions.all().filter(receiver=trader)
    sending_delivery_pending = sending_delivery_pending.filter(status="Accepted")

    transactions = Transaction.objects.filter(sender=trader) | \
                   Transaction.objects.filter(receiver=trader)

    pending = transactions.filter(status="Pending")
    success = transactions.filter(status="Accepted")
    # awaiting_delivery = transactions.filter(status="Accepted")
    rejected = transactions.filter(status="Rejected")
    complaints = Complaint.objects.filter(transaction__in=transactions)
    exists = ""
    total_ratings = Review.objects.filter(seller=trader).aggregate(total_stars=Sum('stars'))

    if 'username' in request.session:
        del request.session['username']

    if 'exists' in request.session:
        exists = request.session["exists"]
        del request.session['exists']
    return redirect(customer_view)

from django.http import Http404
from django.urls import reverse
from django.contrib import messages

def search(request):
    buyer_user = request.user
    buyer = Trader.objects.get(user=buyer_user) # the person who wants to start a new transaction
    exists = ""
    review_status = None
    m_rating =  None
    m_review = None
    total_ratings = 0
    transactions = ""
    if ('rating' and 'review') in request.session:
        m_rating =  request.session['rating']
        m_review = request.session['review']
        del request.session['review']
        del request.session['rating']  
    if 'username' in request.session:
        username = request.session['username']
        seller_user = User.objects.get(username=username)    
        seller = Trader.objects.get(user=seller_user) # the person who has the product to be sold
        reviews = Review.objects.filter(seller=seller)
        total_ratings = Review.objects.filter(seller=seller).aggregate(total_stars=Sum('stars'))
        transactions = Transaction.objects.filter(sender=seller, receiver=buyer) \
        | Transaction.objects.filter(sender=buyer, receiver=seller)
        
    if (request.POST):
        data = request.POST.dict()
        username = str(data.get("name"))
        
        try:
            seller_user = User.objects.get(username=username)    
            seller = Trader.objects.get(user=seller_user) 
            reviews = Review.objects.filter(seller=seller)
            request.session["username"] = username
        except User.DoesNotExist:
            exists = "Trader with that username does not exist"
            request.session['exists'] = exists
            return redirect(customer_view)
        except Trader.DoesNotExist:
            exists = "Trader with that username does not exist"
            request.session['exists'] = exists
            return redirect(customer_view)  

    return render(request, "main/search.html", {"seller_user":seller_user, "buyer_user":buyer_user,"seller":seller,"reviews":reviews, "exists":exists,"transactions":transactions,"review_status":review_status, "m_rating":m_rating, "m_review":m_review,"total_ratings":total_ratings})

from .models import *

def send_complaint(request, pk):
    """ 
    for traders to send issue concerning their trade:
        icluding fake products
        dissatisfactory produccts,
        delay in approval after delivery 

    """
    user = request.user
    transaction = Transaction.objects.get(pk=pk)
    msg = None
    if request.POST:
        data = request.POST.dict()
        complaint = str(data.get("complaint"))
        Complaint.objects.create(transaction=transaction, issue=complaint)
        msg = "complaint sent succesfully"
        return render(request, "main/send_complaint.html", {"transaction":transaction,"msg":msg})  
    msg = None
         

    return render(request, "main/send_complaint.html", {"transaction":transaction,"msg":msg})

def send_review(request):
    buyer_user = request.user
    buyer = Trader.objects.get(user=buyer_user)    
    if request.session['username']:
        username = request.session['username']
    seller_user = User.objects.get(username=username)    
    seller = Trader.objects.get(user=seller_user) 
    exists = ""
    if (request.POST):
        data = request.POST.dict()
        review = data.get("review")
        rating = data.get("rating")
        Review.objects.create(seller=seller, comment=review, stars=rating)
        request.session['rating'] = rating
        request.session['review']  = review
    return redirect(search)

def intermediary_view(request):
    """
      recieve complaits,
      cancel pending transactions,
    """
    complaints = Complaint.objects.all().filter(status="Pending")
    return render(request, "main/intermediary.html", {"complaints":complaints})

def complaints_view(request):
    return render(request, "main/complaints.html", {})

def respond_complaint(request, pk):
    complaint = Complaint.objects.get(pk=pk)
    msg=None
    if (request.POST):
        data = request.POST.dict()
        verdict = str(data.get("verdict"))
        action = str(data.get("action"))
        if action=="accept":
            # mpesa
            complaint = Complaint.objects.get(pk=pk)
            subject = 'Request For reversal'
            body = 'Your Request For reversal is being processed and you will recieve your payment'
            email = [complaint.transaction.sender.user.email]
            send_email(subject=subject, body=body, emails=email)
            Verdict.objects.create(complaint=complaint, comment=verdict,action=action)
            complaint.status="Resolved"
            complaint.save()
            phone_number = complaint.transaction.sender.phone_number
            amount = complaint.transaction.amount
            
            # r = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url)
            msg = "Response sent succesfully."
        else:
            complaint = Complaint.objects.get(pk=pk)
            subject = 'Request For reversal'
            body = 'Your Request For reversal has been rejected . '+str(verdict)
            email = [complaint.transaction.sender.user.email]
            send_email(subject=subject, body=body, emails=email)
            Verdict.objects.create(complaint=complaint, comment=verdict,action=action)
            complaint.status="Resolved"
            complaint.save()
            msg = "Response sent succesfully."

    return render(request, "main/respond_complaints.html", {"complaint":complaint,"msg":msg})

def accept_refund(request, pk):
    if (request.POST):
        
        # complaint.transaction
        complaint.transaction.sender.user.email
        complaint.transaction.status = "Rejected"
        complaint.transaction.status.save()
    return redirect(respond_complaint, complaint.id)

def reject_refund(request, pk):
    complaint = Complaint.objects.get(pk=pk)
    return render(request, "", {})

from django.utils import timezone
import json
import random

def payment(request,pk):     
    user = request.user
    sender=Trader.objects.get(user=user)
    reciever = Trader.objects.get(pk=pk)      
    customer_message = None 
    if (request.POST):
            data = request.POST.dict()
            phone_number = str(data.get("phone"))
            product = str(data.get("product"))
            description = str(data.get("description"))
            amount = int(data.get("amount"))
            if len(phone_number)<10:
                msg="invalid phone number"
                return render(request, "client-home/argon/payment.html", {"user":user,"bill":bill,"msg":msg,"test":test})    

            account_reference = 'Online Escrow Shopping'
            transaction_desc = 'STK Push Description'
            callback_url = stk_push_callback_url
            mpesa_access_token()
            r = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url) 
            customer_message = r.customer_message
            # security_key = str(''.join([str(random.randint(0, 9)) for _ in range(10)]))
             
            t=Transaction.objects.create(sender=sender,receiver=reciever,time=timezone.now(),status='Pending',\
             amount=amount, product=product,description=description,security_key=str(''.join([str(random.randint(0, 9)) for _ in range(10)])))          
            subject = "Payment For Peer To Peer Exchange" 
            body = "confirmed you have paid " +str(amount)+" to "+str(reciever.user.username)+" for trade proposal of "+str(t.product)+" transaction code is "+str(t.security_key)
            body1 = "confirmed your online escrow account has recieved payment of " +str(amount)+" from "+str(sender.user.username)+" for "+str(t.product)+" use security code "+str(t.security_key)+" during verification"
            email = [reciever.user.email]
            send_email(subject=subject, body=body,emails=email)
            send_email(subject=subject, body=body1,emails=str(reciever.user.email))

            redirect(payment, pk)
        
    return render(request, "main/payment.html", {"user":user,"customer_message":customer_message,"reciever":reciever})

def commitment_fee(request,pk):
    """
        paid by the seller to assert his/her commitment to making a trade 
    """
    customer_message = None
    transaction = Transaction.objects.get(pk=pk)
    trader = transaction.receiver
    security_error = ""
    if (request.POST):
        # payment here
        data = request.POST.dict()
        phone_number = str(data.get("phone"))
        # amount = str(data.get("amount"))
        amount = 500
        security_code = str(data.get("security_code"))
        print(transaction.security_key, transaction.security_key,"pppppppppppppppppppppppppppppppppppppppppp")
        if str(security_code) == str(transaction.security_key):
            account_reference = 'Online Shopping Escrow'
            transaction_desc = 'STK Push Description'
            # transaction_desc = 'Pay '
            callback_url = stk_push_callback_url
            r = cl.stk_push(phone_number, amount, account_reference, transaction_desc, callback_url) 
            # customer_message = r.customer_message
            customer_message = "Succesfully Accepted"
            subject = "Confirmation Commitment For Peer To Peer Exchange" 
            body = "Confirmed You have payed kshs " + str(amount) + " as commitment fee to "+str(trader.user)+" , it will be refunded after your trade is finalised"
            # body = f"""
                       
            #             <p>{customer_message}</p>
            #             <p>You have paid <strong>kshs {amount}</strong> commitment to be refunded after your trade is finalized.</p>
            #             <p>Thank you!</p>
            #             </body>
            #             </html>
            #         """
            email = [trader.user.email]
            send_email(subject=subject, body=body,emails=email) 
            transaction.status = 'Accepted'
            transaction.save()
        else:
            security_error = "the security code doesn't match."
        
    # payment    
    return render(request, "main/accept.html", {"transaction":transaction,"customer_message":customer_message,"trader":trader,"security_error":security_error})

def reject_tansaction(request,pk):
    """
        if the reciever rejects a proposal 
        refund the money automatically
     """
    transaction = Transaction.objects.get(pk=pk)
    transaction.status = 'Rejected'
    transaction.save()
    subject = "Transaction status."
    body = "Your proposed transaction  of "+str(transaction)+"  has been rejected."
    email = [transaction.sender.user.email]
    send_email(subject=subject, body=body,emails=email) 

    return redirect(customer_view)

def logout_view(request):
    user = request.user
    message = 'bye '+str(user.username)
    messages.add_message(request, messages.INFO,message)
    username = user.username
    logout(request)
    return redirect(landing_view)

