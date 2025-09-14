from django.contrib import admin,messages
from django.utils import timezone
from .models import Event
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import UserChangeForm
from .models import Artist, Actor
import datetime

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = UserChangeForm
    model = CustomUser
    list_display = ['username', 'email', 'user_type', 'is_staff']
    
admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'title', 'description', 
                ('date', 'time'),
                'city', 'location', 'category', 
                ('price_a', 'price_b', 'price_c'), 
                ('seats_a', 'seats_b', 'seats_c'), 
                'artist', 'actor', 'image',
                'seller', 'is_approved',  ),}),)
    
    list_display = ('title', 'city', 'category', 'date', 'time', 'seller', 'is_approved')
    list_filter = ['is_approved', 'seller', 'city']
    search_fields = ['title', 'description', 'city']
    actions = ['approve_events', 'reject_events']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        original_clean = form.clean

        def new_clean(self):
            cleaned_data = original_clean(self)

            event_date = cleaned_data.get('date')
            event_time = cleaned_data.get('time')
            
            if event_date and event_time:
                event_datetime = timezone.make_aware(datetime.datetime.combine(event_date, event_time) )
                now = timezone.now()
                if event_datetime < now:
                    self.add_error(None, "Past events cannot be added.")


            if not event_time:
                self.add_error('time', "Fill in the event time field.")
                return cleaned_data

            artist = cleaned_data.get('artist')
            actor = cleaned_data.get('actor')

            if artist and actor:
                self.add_error(None, "You can only select either an artist or an actor, not both.")

            if not artist and not actor:
                self.add_error(None, "You must select either an artist or an actor.")

            return cleaned_data
        form.clean = new_clean
        return form

    def save_model(self, request, obj, form, change):
        now = timezone.now()
        event_datetime = timezone.make_aware(
            datetime.datetime.combine(obj.date, obj.time) )
        if event_datetime < now and obj.is_approved:
            obj.is_approved = False
        super().save_model(request, obj, form, change)

    def approve_events(self, request, queryset):
        now = timezone.now()
        past_events = queryset.filter(date__lt=now.date()) | queryset.filter(
            date=now.date(), 
            time__lt=now.time() )

        if past_events.exists():
            self.message_user(
                request,  "Some events could not be approved because their dates or times have passed.",
                level=messages.ERROR )
            queryset = queryset.exclude(id__in=past_events.values_list('id', flat=True))

        if queryset.exists():
            queryset.update(is_approved=True)
            self.message_user(request, "Selected event(s) approved.")
    approve_events.short_description = "Approve Events"

    def reject_events(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, "Selected event(s) rejected.")
    reject_events.short_description = "Reject Events"
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "seller":
            kwargs["queryset"] = CustomUser.objects.filter(user_type='S')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'bio', 'image')  
    search_fields = ('name',)  
    list_filter = ('name',)  
    ordering = ('name',)  

@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('name', 'bio', 'image')  
    search_fields = ('name',)  
    list_filter = ('name',)  
    ordering = ('name',)










