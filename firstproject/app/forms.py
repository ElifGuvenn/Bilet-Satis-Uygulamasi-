from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from .models import CustomUser
from .models import Event,EventReview,Artist,Actor

class CustomUserCreationForm(UserCreationForm):
    USER_TYPE_CHOICES = [  ('C', 'Customer'), ('S', 'Seller'), ("A", "Admin"),]
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        label="User Type",
        widget=forms.Select(attrs={'class': 'form-select'}))
    class Meta:
        model = CustomUser 
        fields = ['username', 'email', 'password1', 'password2', 'user_type']

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'User name' })
        self.fields['password'].widget.attrs.update({ 'class': 'form-control', 'placeholder': 'Password' })
        
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'time','city','location', 'category', 
            'price_a', 'price_b', 'price_c', 'seats_a', 'seats_b', 'seats_c', 
            'artist', 'actor', 'image']
        widgets = { 'description': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
                   'date': forms.DateInput(attrs={'type': 'date'}),
                   'time': forms.TimeInput(attrs={'type': 'time'}),
                   'city': forms.TextInput(attrs={'placeholder': 'city'}) }
        
    image = forms.ImageField(required=False)
    artist = forms.ModelChoiceField(  queryset=Artist.objects.all(), required=False, empty_label="Choose Artist" )
    actor = forms.ModelChoiceField( queryset=Actor.objects.all(),  required=False,empty_label="Choose Actor " )
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        artist = cleaned_data.get('artist')
        actor = cleaned_data.get('actor')
        city = cleaned_data.get('city')

        if not time:
         raise forms.ValidationError("Fill in the event time field.")
        if not city:
            raise forms.ValidationError("Fill in the city information field")
        
        
        if date and time:
            event_datetime = timezone.make_aware(timezone.datetime.combine(date, time))
            if event_datetime < timezone.now():
                raise forms.ValidationError("You cannot add an event with a past date or time.")
            

        if not artist and not actor:
            raise forms.ValidationError("You must select either an artist or an actor for the event.")
        if artist and actor:
            raise forms.ValidationError("You can only select one: either an artist or an actor, but not both.")
        return cleaned_data

class EventReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[
            (5, '★★★★★'),
            (4, '★★★★☆'),
            (3, '★★★☆☆'),
            (2, '★★☆☆☆'),
            (1, '★☆☆☆☆'), ],
            widget=forms.RadioSelect,
        label="Your Score" )
    class Meta:
        model = EventReview
        fields = ['rating','comment'] 
        widgets = {  'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your comment here...'}), }
        labels = { 'comment': 'Your Comment', }

class ArtistForm(forms.ModelForm):
    class Meta:
        model = Artist
        fields = ['name', 'bio', 'image']
        labels = {'name': 'Name','bio': 'Bio','image': 'İmage', }

class ActorForm(forms.ModelForm):
    class Meta:
        model = Actor
        fields = ['name', 'bio', 'image']
        labels = {'name': 'Name','bio': 'Bio','image': 'İmage',}



   