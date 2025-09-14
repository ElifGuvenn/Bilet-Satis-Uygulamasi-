from django.db import models
from django.contrib.auth.models import AbstractUser
import qrcode
from django.core.files.base import ContentFile
from io import BytesIO
from django.utils import timezone

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('C', 'Customer'),
        ('S', 'Seller'),
        ("A", "Admin"), )
    

    
    user_type = models.CharField(max_length=1, choices=USER_TYPE_CHOICES, default='C')
    followed_artists = models.ManyToManyField('Artist', blank=True, related_name='followers')  
    followed_actors = models.ManyToManyField('Actor', blank=True, related_name='actor_followers') 
    def __str__(self):
        return self.username

class Artist(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField()
    image = models.ImageField(upload_to='artists/', null=True, blank=True)
    def __str__(self):
        return self.name

class Actor(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField()
    image = models.ImageField(upload_to='actors/', null=True, blank=True)
    def __str__(self):
        return self.name

class Event(models.Model):
    CATEGORY_CHOICES = [
        ('concert', 'Concert'),
        ('cinema', 'Cinema'),
        ('theatre', 'Theatre'), ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    date = models.DateField()  
    time = models.TimeField()
    city = models.CharField(max_length=100, help_text="City")
         
    location = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='events/')
   
    price = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)
    price_a = models.DecimalField(max_digits=8, decimal_places=2, default=500)  
    price_b = models.DecimalField(max_digits=8, decimal_places=2, default=750)  
    price_c = models.DecimalField(max_digits=8, decimal_places=2, default=1000)

    seats_a =models.PositiveIntegerField(default=50)
    seats_b =models.PositiveIntegerField(default=50)
    seats_c =models.PositiveIntegerField(default=50)

    artist = models.ForeignKey(Artist, on_delete=models.SET_NULL, null=True, blank=True, related_name='events_by_artist', help_text="Select the artist associated with this event.")
    actor = models.ForeignKey(Actor, on_delete=models.SET_NULL, null=True, blank=True, related_name='events_by_actor', help_text="Select the actor associated with this event.")

    is_approved = models.BooleanField(default=False)
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='events')

    is_on_sale = models.BooleanField(default=False)
    sale_price_a = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_price_b = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_price_c = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_start_time = models.DateTimeField(null=True, blank=True)   

    

    def get_current_price(self, ticket_type):
        if self.is_on_sale:
            if ticket_type == 'A':
                return self.sale_price_a if self.sale_price_a is not None else self.price_a
            elif ticket_type == 'B':
                return self.sale_price_b if self.sale_price_b is not None else self.price_b
            elif ticket_type == 'C':
                return self.sale_price_c if self.sale_price_c is not None else self.price_c
        if ticket_type == 'A':
            return self.price_a
        elif ticket_type == 'B':
            return self.price_b
        elif ticket_type == 'C':
            return self.price_c
        return 0 




    def is_campaign_active(self):
        return self.is_on_sale

    def __str__(self):
        return self.title
    
class EventReview(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='event_reviews')
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='reviews')
    comment = models.TextField(blank=True, null=True)
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.rating}/5)"

class Ticket(models.Model):
    TICKET_TYPE_CHOICES = [
        ('A', 'A Type'),
        ('B', 'B Type'),
        ('C', 'C Type'),  ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    ticket_type = models.CharField(max_length=1, choices=TICKET_TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)
    qr_code = models.ImageField(upload_to='tickets/qrcodes/', null=True, blank=True)
    is_cancelled = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    purchase_time = models.DateTimeField(auto_now_add=True) 


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs) 
        if not self.qr_code:
            qr_data = (
                f"Ticket ID: {self.id}, " 
                f"Event: {self.event.title}, "
                f"Ticket Type: {self.ticket_type}, "
                f"User: {self.user.username}, "
                f"Date: {self.purchase_date.strftime('%Y-%m-%d %H:%M:%S')}"   )
            img = qrcode.make(qr_data)
            qr_image = BytesIO()
            img.save(qr_image, format='PNG') 
            qr_image.seek(0)
            self.qr_code.save(f"{self.id}_qr.png", ContentFile(qr_image.read()), save=False)
            super().save(update_fields=['qr_code'])
    def __str__(self):
        return f"{self.event.title} - {self.user.username} ({self.ticket_type} Ticket ID: {self.id})"
    
class Notification ( models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='notifications')
    message = models.TextField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    NOTIFICATION_TYPES = [
        ('new_event', 'New Event'),
        ('ticket_deal', 'Advantageous Ticket'),
        ('general', 'General'), ]
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    class Meta:
        ordering = ['-timestamp'] 
    def __str__(self):
        return f"Notification - {self.user.username}: {self.message[:50]}..."















