from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Event, Notification

@receiver(pre_save, sender=Event)
def store_old_is_on_sale(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_event = Event.objects.get(pk=instance.pk)
            instance._old_is_on_sale = old_event.is_on_sale
            instance._old_is_approved = old_event.is_approved
        except Event.DoesNotExist:
            instance._old_is_on_sale = False
            instance._old_is_approved = False
    else:
        instance._old_is_on_sale = False
        instance._old_is_approved = False

@receiver(post_save, sender=Event)
def send_event_notifications(sender, instance, created, **kwargs):
    if not instance.is_approved:
        return
    if (created and instance.is_approved) or (
        not created and not getattr(instance, "_old_is_approved", False) and instance.is_approved):
        followers = []
        message = ""

        if instance.artist:
            followers = instance.artist.followers.all()
            message = f"The artist you follow '{instance.artist.name}' has a new event: '{instance.title}'. Tickets are on sale!"
        elif instance.actor:
            followers = instance.actor.actor_followers.all()
            message = f"The actor you follow '{instance.actor.name}' has a new event: '{instance.title}'. Tickets are on sale!"

        if followers:
            for user in followers:
                Notification.objects.create(user=user, message=message,event=instance,notification_type='new_event'  )


    if not created and not getattr(instance, "_old_is_on_sale", False) and instance.is_on_sale:
        followers = []
        message = ""

        if instance.artist:
            followers = instance.artist.followers.all()
            message = f"The artist you follow '{instance.artist.name}' during the discounted ticket period: '{instance.title}'! Hurry up."
        elif instance.actor:
            followers = instance.actor.actor_followers.all()
            message = f"The actor you follow '{instance.actor.name}' during the discounted ticket period: '{instance.title}'! Hurry up."

        if followers:
            for user in followers:
                Notification.objects.create(user=user, message=message,event=instance,notification_type='ticket_deal')

