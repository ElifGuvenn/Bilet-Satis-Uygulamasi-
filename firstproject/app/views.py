from django.shortcuts import render,get_object_or_404,redirect
from.forms import CustomUserCreationForm,AuthenticationForm ,EventReviewForm,EventForm,ArtistForm,ActorForm
from django.contrib.auth.models import auth
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import messages
from .models import Event,Ticket, EventReview,Artist,Actor,Notification,CustomUser
from django.urls import reverse
from PIL import Image
import datetime as dt    
from datetime import date
from datetime import time as dt_time 
from django.utils import timezone
from collections import Counter
import cv2,datetime,random ,numpy as np 
from django.db.models import Avg,Sum
from django.http import JsonResponse 
from decimal import Decimal
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors 

def index_view(request):
    if request.user.is_authenticated:
        return redirect('index')  
    return render(request, 'app/index.html')

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  
    else:
        form = CustomUserCreationForm()
    return render(request, 'app/register.html', {'RegistrationForm': form})

def login_view(request):
    if request.method == 'POST':
        LoginForm = AuthenticationForm(request, data=request.POST)
        if LoginForm.is_valid():
            user = LoginForm.get_user()
            login(request, user)
            if user.user_type == 'C':
                return redirect('dashboard') # Alıcı paneli
            elif user.user_type == 'S':
                return redirect('satici_dashboard') # Satıcı paneli
            elif user.user_type == 'A' : # Admin Paneli
                return redirect('custom_admin_dashboard')
            else:
                return redirect('login')  
        else:
            pass
    else:
        LoginForm = AuthenticationForm()
    return render(request, 'app/login.html', {'LoginForm': LoginForm})

def logout_view(request):
    auth.logout(request)
    return redirect('index')
   
@login_required(login_url='login')
def dashboard_view(request):
    return render(request, 'app/dashboard.html', {'user': request.user})

@login_required(login_url='login')
def satici_dashboard(request):
    events = Event.objects.filter(seller=request.user) 
    return render(request, 'app/satici_dashboard.html', {'events': events})

@login_required(login_url='login')
def event_list(request):
    now = timezone.now()
    clear_city = request.GET.get('clear_city')
    if clear_city:
        request.session['selected_city'] = None
    city_from_url = request.GET.get('city')
    if city_from_url:
        request.session['selected_city'] = city_from_url
        selected_city = city_from_url
    else:
        selected_city = request.session.get('selected_city')
    events_queryset = Event.objects.filter(is_approved=True).select_related('artist', 'actor')
    if selected_city:
        events_queryset = events_queryset.filter(city__icontains=selected_city)
    
    category = request.GET.get('category')
    location = request.GET.get('location')
    date_filter = request.GET.get('date')

    if category and category != "all":
        events_queryset = events_queryset.filter(category=category)
    if location:
        events_queryset = events_queryset.filter(location__icontains=location)
    if date_filter:
        events_queryset = events_queryset.filter(date=date_filter)
    future_events = []

    for event in events_queryset:
       event_datetime = timezone.make_aware(dt.datetime.combine(event.date, event.time or dt.time.min))
       if event_datetime >= now:
            future_events.append(event)
    random.shuffle(future_events)
    cities = Event.objects.filter(is_approved=True).values_list('city', flat=True).distinct()
    categories = Event.CATEGORY_CHOICES

    return render(request, 'app/event_list.html', {
     'events': future_events, 'categories': categories, 'cities': cities, 'selected_city': selected_city, })

def get_city_suggestions(request):
    query = request.GET.get('q', '')
    if query:
        cities = Event.objects.filter(is_approved=True,city__icontains=query).values_list('city', flat=True).distinct().order_by('city')
        return JsonResponse(list(cities), safe=False)
    return JsonResponse([], safe=False)

def get_location_suggestions(request):


    query = request.GET.get('loc', '')
    selected_city = request.GET.get('city')
    locations = []
    if query and selected_city:
        locations_query = Event.objects.filter(is_approved=True, city=selected_city, location__icontains=query)
        valid_locations = set()
        for loc_event in locations_query:
            valid_locations.add(loc_event.location)
        locations = sorted(list(valid_locations))
    return JsonResponse(locations, safe=False)


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    reviews = event.reviews.all()
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    prices = {'A': event.get_current_price('A'), 'B': event.get_current_price('B'),'C': event.get_current_price('C'),}
    user_reviews = reviews.filter(user=request.user)
    review_form = EventReviewForm()

    if request.method == 'POST':
        if 'review_submit' in request.POST:
            review_form = EventReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.user = request.user
                review.event = event
                review.save()
                return redirect('event_detail', event_id=event.id)
        elif 'review_edit' in request.POST:
            review_id_to_edit = request.POST.get('review_id')
            if review_id_to_edit:
                try:
                    review_to_edit = EventReview.objects.get(id=review_id_to_edit, user=request.user, event=event)
                    edit_form = EventReviewForm(request.POST, instance=review_to_edit)
                    if edit_form.is_valid():
                        edit_form.save()
                        return redirect('event_detail', event_id=event.id)
                except EventReview.DoesNotExist:
                    pass
        elif 'review_delete' in request.POST:
            review_id_to_delete = request.POST.get('review_id')
            if review_id_to_delete:
                try:
                    review_to_delete = EventReview.objects.get(id=review_id_to_delete, user=request.user, event=event)
                    review_to_delete.delete()
                    return redirect('event_detail', event_id=event.id)
                except EventReview.DoesNotExist:
                    pass 
        elif 'ticket_purchase_submit' in request.POST:
            ticket_type = request.POST.get('ticket_type')
            return redirect(f"{reverse('ticket_purchase', args=[event.id])}?ticket_type={ticket_type}")
        
    context = {'event': event,'reviews': reviews,'average_rating': average_rating,'review_form': review_form,
        'user_reviews': user_reviews,  'selected_ticket_type': request.POST.get('ticket_type', 'A'),
        'prices': prices,}
    return render(request, 'app/event_detail.html', context)


def luhn_check(card_number):
    digits = [int(d) for d in card_number]
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def expiry_valid(expiry):
    try:
        if not expiry or "/" not in expiry:
            return False
        parts = [part.strip() for part in expiry.split('/')]
        if len(parts) != 2:
            return False
        month_str, year_str = parts
        if not (month_str.isdigit() and year_str.isdigit() and len(year_str) == 2):
            return False
        month = int(month_str)
        year = int(year_str) + 2000
        today = date.today()
        if not (1 <= month <= 12):
            return False
        if year < today.year:
            return False
        if year == today.year and month < today.month:
            return False
        return True
    except (ValueError, IndexError):
        return False

@login_required
def ticket_purchase(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    ticket_type = request.GET.get('ticket_type', 'A')
    price = event.get_current_price(ticket_type)
    price_map = {'A': 'price_a', 'B': 'price_b', 'C': 'price_c'}
    stock_map = {'A': 'seats_a', 'B': 'seats_b', 'C': 'seats_c'}
    price = getattr(event, price_map.get(ticket_type))
    stock = getattr(event, stock_map.get(ticket_type))
    error = None

    if request.method == "POST":
        quantity = int(request.POST.get('quantity', 0))
        total_price = price * quantity
        if quantity > stock:
            error = "Not enough tickets!"

        else:
            card_number = request.POST.get('card_number', '').replace(" ", "").replace("-", "")
            expiry = request.POST.get('expiry', '')
            cvv = request.POST.get('cvv', '')
            if not (card_number.isdigit() and luhn_check(card_number) and len(card_number)==16):
                error = "Invalid card number!"
            elif not expiry_valid(expiry):
                error = "Invalid expiry date!"
            elif not (cvv.isdigit() and len(cvv) == 3):
                error = "Invalid CVV!"
            else:
                for _ in range(quantity):
                    Ticket.objects.create(
                        user=request.user,event=event,
                        ticket_type=ticket_type, quantity=1,
                        total_price=price)
                setattr(event, stock_map.get(ticket_type), stock - quantity)
                event.save()
                return redirect('my_tickets')
    return render(request, 'app/ticket_purchase.html', {'event': event,'ticket_type': ticket_type, 'stock': stock,'price': price,'error': error})

@login_required
def my_tickets(request):
    now = timezone.now()
    tickets = Ticket.objects.filter(user=request.user).select_related('event').order_by('-purchase_time')
    active_tickets = []
    past_tickets = []
    for ticket in tickets:
        event_datetime = timezone.make_aware(dt.datetime.combine(ticket.event.date, ticket.event.time or dt_time.min))
        if event_datetime >= now:
            active_tickets.append(ticket)
        else:
            past_tickets.append(ticket)

    active_tickets.sort(key=lambda t: (t.event.date, t.event.time))
    past_tickets.sort(key=lambda t: (t.event.date, t.event.time), reverse=True)
    return render(request, 'app/my_tickets.html', {'active_tickets': active_tickets, 'past_tickets': past_tickets, })

@login_required
def cancel_ticket(request, ticket_id): 
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    event = ticket.event
    now = timezone.now()
    event_datetime = timezone.make_aware(dt.datetime.combine(event.date, event.time or dt_time.min))
    if event_datetime < now:
        return redirect('my_tickets')
    stock_map = {'A': 'seats_a', 'B': 'seats_b', 'C': 'seats_c'}
    current_stock = getattr(event, stock_map.get(ticket.ticket_type))
    setattr(event, stock_map.get(ticket.ticket_type), current_stock + ticket.quantity)
    event.save()
    ticket.delete()
    messages.success(request, "Ticket canceled successfully.")
    return redirect('my_tickets')

@login_required
def delete_ticket(request, ticket_id): 
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    now = timezone.now()
    event = ticket.event
    event_datetime = timezone.make_aware(dt.datetime.combine(event.date, event.time or dt_time.min))
    if event_datetime >= now:
        return redirect('my_tickets')
    ticket.delete()
    messages.success(request, "Ticket deleted successfully.")
    return redirect('my_tickets')

@login_required(login_url='login')
def following(request):
    user = request.user
    all_artists = Artist.objects.all()
    all_actors = Actor.objects.all()
    # Kullanıcının takip ettiği sanatçılar ve oyuncular
    followed_artists = user.followed_artists.all()
    followed_actors = user.followed_actors.all()
    return render(request, 'app/following.html', { 'user': user,
        'all_artists': all_artists, 'all_actors': all_actors,            
        'followed_artists': followed_artists,  'followed_actors': followed_actors,  })

@login_required
def follow_artist(request, artist_id):
    artist = get_object_or_404(Artist, id=artist_id)
    request.user.followed_artists.add(artist)
    return redirect('following')

def get_artist_suggestions(request):
    query = request.GET.get('q', '')
    user = request.user
    followed_artists = user.followed_artists.all()
    if query:
     artists = Artist.objects.filter( name__icontains=query).exclude(pk__in=followed_artists.values_list('pk', flat=True)).values('id', 'name')
     return JsonResponse(list(artists), safe=False)
    return JsonResponse([], safe=False)

@login_required
def remove_artist(request, artist_id):
    artist = get_object_or_404(Artist, id=artist_id)
    request.user.followed_artists.remove(artist)
    return redirect('following')

@login_required
def follow_actor(request, actor_id):
    actor = get_object_or_404(Actor, id=actor_id)
    request.user.followed_actors.add(actor)
    return redirect('following')

def get_actor_suggestions(request):
    query = request.GET.get('q', '')
    user = request.user
    followed_actors = user.followed_actors.all()
    if query:
        actors = Actor.objects.filter(name__icontains=query).exclude( pk__in=followed_actors.values_list('pk', flat=True)).values('id', 'name')
        return JsonResponse(list(actors), safe=False)
    return JsonResponse([], safe=False)

@login_required
def remove_actor(request, actor_id):
    actor = get_object_or_404(Actor, id=actor_id)
    request.user.followed_actors.remove(actor)
    return redirect('following')

@login_required(login_url='login')
def notifications_view(request):
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-timestamp')
    if request.method == "POST":
        notification_ids = request.POST.getlist('notification_ids')
        notifications_to_delete = Notification.objects.filter(id__in=notification_ids, user=user)
        notifications_to_delete.delete()
        return redirect('notifications')
    return render(request, 'app/notifications.html', {'notifications': notifications})

@login_required
def mark_all_notifications_as_read(request):
    if request.method == "POST":
        user = request.user
        Notification.objects.filter(user=user, is_read=False).update(is_read=True)
    return redirect('notifications')

@login_required
def mark_notification_as_read(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
    return redirect('notifications')

@login_required
def delete_notification(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.delete()
    return redirect('notifications')

@login_required(login_url='login')
def add_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.seller = request.user  
            event.save()
            messages.success(request, "Your event has been added successfully.!")
            return redirect('satici_dashboard')
    else:
        form = EventForm()
    return render(request, 'app/add_event.html', {'form': form})

@login_required(login_url='login')
def sales_view(request):
    selected_city = request.GET.get('city')
    base_events_query = Event.objects.filter(seller=request.user, is_approved=True)
    available_cities = base_events_query.values_list('city', flat=True).distinct().order_by('city')

    if selected_city:
        events = base_events_query.filter(city=selected_city).annotate(
        tickets_sold=Sum('ticket__quantity'), revenue=Sum('ticket__total_price')).order_by('-date', '-time')
    else:
        events = base_events_query.annotate(tickets_sold=Sum('ticket__quantity'), revenue=Sum('ticket__total_price'))
    total_revenue = events.aggregate(total=Sum('revenue'))['total'] or 0
    total_tickets_sold = events.aggregate(total=Sum('tickets_sold'))['total'] or 0
    return render(request, 'app/sales_view.html', {
        'events': events,'total_revenue': total_revenue, 'total_tickets_sold': total_tickets_sold,
        'available_cities': available_cities,'selected_city': selected_city, })

@login_required(login_url='login')
def event_reviews(request):
    selected_city = request.GET.get('city')
    date_filter = request.GET.get('date_filter', 'all')
    now = timezone.now()
    seller_events_query = Event.objects.filter(seller=request.user, is_approved=True)
    if date_filter in ['past', 'future']:
        events = []
        for event in seller_events_query:
            event_datetime = dt.datetime.combine(event.date, event.time or dt_time.min)
            event_datetime = timezone.make_aware(event_datetime) 
            if (date_filter == 'past' and event_datetime < now) or (date_filter == 'future' and event_datetime > now):
                events.append(event.id)
        seller_events_query = seller_events_query.filter(id__in=events)

    if selected_city:
        seller_events_query = seller_events_query.filter(city=selected_city)
    seller_events = seller_events_query.order_by('-date', '-time')
    event_reviews_grouped = []

    for event in seller_events:
        reviews = EventReview.objects.filter(event=event).order_by('-created_at').select_related('user')
        average_rating = reviews.aggregate(avg=Avg('rating'))['avg']
        event_reviews_grouped.append({"event": event, "reviews": reviews, "average_rating": average_rating})
    available_cities = (Event.objects.filter(seller=request.user, is_approved=True).values_list('city', flat=True).distinct().order_by('city'))
    context = { "event_reviews_grouped": event_reviews_grouped, "selected_city": selected_city,"date_filter": date_filter,"available_cities": available_cities,}
    return render(request, "app/event_reviews.html", context)

@login_required(login_url='login')
def verify_ticket(request):
    error = None
    ticket = None
    if request.method == 'POST' and 'qr_code' in request.FILES:
        try:
            qr_image = request.FILES['qr_code']
            img = Image.open(qr_image)
            img_np = np.array(img)
            if img_np.dtype == np.bool_:
                img_np = img_np.astype(np.uint8) * 255
            if len(img_np.shape) == 3:
                img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            else:
                img_cv = img_np
            detector = cv2.QRCodeDetector()
            value, _, _ = detector.detectAndDecode(img_cv)
            if not value:
                error = "An invalid or unreadable QR code."
            else:
                qr_data = value
                parts = {}
                for p in qr_data.split(', '):
                    if ': ' in p:
                        key, val = p.split(': ', 1)
                        parts[key.strip()] = val.strip()

                ticket_id = parts.get('Ticket ID')
                user_username = parts.get('User')
                event_title = parts.get('Event')

                if ticket_id and user_username and event_title:
                    now = timezone.now()
                    try:
                        ticket = Ticket.objects.get(
                            id=ticket_id,
                            user__username=user_username,
                            event__title=event_title,
                            is_cancelled=False,
                            is_used=False,)
                        event_datetime = datetime.combine(ticket.event.date, ticket.event.time or dt_time.min)
                        if event_datetime <= now:
                            error = "This ticket is for an event that has already passed or is currently ongoing."
                            ticket = None 
                        else:
                            ticket.is_used = True
                            ticket.save()
                    except Ticket.DoesNotExist:
                        error = "An invalid, canceled, or already used ticket, or ticket not found."
                    except ValueError:
                        error = "Invalid Ticket ID format in QR code."
                else:
                    error = "QR code data is in an invalid format."
        except Exception as e:
            error = f"An error occurred during QR code processing: {e}"
    return render(request, 'app/verify_ticket.html', {'error': error, 'ticket': ticket})

@login_required(login_url='login')
def event_management(request):
    now = timezone.now()
    selected_city = request.GET.get('city') 
    all_seller_events_qs = Event.objects.filter( seller=request.user,is_approved=True ).order_by('-date', '-time') 
    filtered_events = []
    all_cities_for_filter = set() 

    for event in all_seller_events_qs:
        event_datetime = dt.datetime.combine(event.date, event.time or dt_time.min)
        event_datetime = timezone.make_aware(event_datetime) 
        if event_datetime > now:
            if selected_city:
                if event.city == selected_city:
                    filtered_events.append(event)
            else:
                filtered_events.append(event)
            all_cities_for_filter.add(event.city) 

    seller_events = sorted( filtered_events, key=lambda event: (event.date, event.time or dt_time.min), reverse=True )
    available_cities = sorted(list(all_cities_for_filter))
    context = { 'seller_events': seller_events, 'selected_city': selected_city,  'available_cities': available_cities, }
    return render(request, 'app/event_management.html', context)

@login_required(login_url='login')
def set_event_on_sale(request, event_id):
    event = get_object_or_404(Event, id=event_id, seller=request.user)

    def get_initial_data(source):
        return {
            'sale_price_a': source.get('sale_price_a'),
            'sale_price_b': source.get('sale_price_b'),
            'sale_price_c': source.get('sale_price_c'),  }
    
    def render_form(initial_data=None, error_message=None):
        if error_message:
            messages.error(request, error_message)
        return render(request, 'app/set_on_sale_form.html', {
            'event': event, 'initial_data': initial_data or {}, })

    if request.method == 'POST':
        initial_data = get_initial_data(request.POST)
        if not all(value and str(value).strip() for value in initial_data.values()): 
            messages.error(request, 'All price fields must be filled.')
            return render_form(initial_data)
        try:
            sale_prices = {
                'a': Decimal(initial_data['sale_price_a']), 
                'b': Decimal(initial_data['sale_price_b']),
                'c': Decimal(initial_data['sale_price_c']),  }
        except (ValueError, TypeError):
            return render_form(initial_data, 'Invalid price format.')
        
        price_map = { 'a': event.price_a, 'b': event.price_b, 'c': event.price_c,}

        for k, sale_price in sale_prices.items():
            if price_map[k] is not None and sale_price >= price_map[k]: #orijinal fiyatından düşük değer gir.
                return render_form(initial_data, 'Campaign prices must be lower than original prices.')
        
        event.sale_price_a = sale_prices['a']
        event.sale_price_b = sale_prices['b']
        event.sale_price_c = sale_prices['c']
        event.is_on_sale = True
        event.sale_start_time = timezone.now()
        event.save()
        messages.success(request, 'Event sale prices updated successfully!')
        return redirect('event_management')
    
    initial_data = get_initial_data({
        'sale_price_a': event.sale_price_a if event.is_on_sale and event.sale_price_a is not None else '',
        'sale_price_b': event.sale_price_b if event.is_on_sale and event.sale_price_b is not None else '',
        'sale_price_c': event.sale_price_c if event.is_on_sale and event.sale_price_c is not None else '',  })
    return render_form(initial_data)

@login_required
def stop_event_sale(request, event_id):
    event = get_object_or_404(Event, id=event_id, seller=request.user)
    if request.method == 'POST': 
        event.is_on_sale = False
        event.sale_price_a = None
        event.sale_price_b = None
        event.sale_price_c = None
        event.sale_start_time = None 
        event.save()
        return redirect('event_management')
    else:
     return redirect('event_management')
    
@login_required
def recommended_events(request):
    user = request.user
    now = timezone.now()
    user_tickets = Ticket.objects.filter(user=user, is_cancelled=False).select_related("event")
    if not user_tickets.exists():
        return render(request, "app/recommended_events.html", {"recommended": []})

    purchased_event_ids = {t.event.id for t in user_tickets}
    user_cities = [t.event.city for t in user_tickets if t.event.city]
    city_counts = Counter(user_cities)
    most_frequent_city = city_counts.most_common(1)[0][0] if city_counts else None
    user_categories = [t.event.category for t in user_tickets if t.event.category]
    category_counts = Counter(user_categories)
    most_frequent_category = category_counts.most_common(1)[0][0] if category_counts else None
    followed_artists = set(user.followed_artists.all())
    followed_actors = set(user.followed_actors.all())
    events_to_recommend = Event.objects.filter(city__in=city_counts.keys(),category__in=category_counts.keys(),is_approved=True).exclude(id__in=purchased_event_ids)
    
    if not events_to_recommend.exists():
        return render(request, "app/recommended_events.html", {"recommended": []})
    
    event_scores = {e.id: {"event": e, "score": 0} for e in events_to_recommend}

    users = CustomUser.objects.filter(ticket__isnull=False).distinct()
    if len(users) > 1:
        user_map = {u.id: i for i, u in enumerate(users)}
        user_features = [[u.ticket_set.count(), sum(float(t.total_price) for t in u.ticket_set.all())] for u in users]
        scaler = StandardScaler()
        user_features_scaled = scaler.fit_transform(user_features)
        knn = NearestNeighbors(metric="cosine", algorithm="brute")
        knn.fit(user_features_scaled)
        user_idx = user_map.get(user.id)
        if user_idx is not None:
            distances, indices = knn.kneighbors([user_features_scaled[user_idx]], n_neighbors=min(5, len(users) - 1) + 1)
            similar_user_indices = indices.flatten()[1:]
            similar_distances = distances.flatten()[1:]

            for i, dist in zip(similar_user_indices, similar_distances):
                neighbor = users[int(i)]
                weight = 1 - dist
                neighbor_tickets = neighbor.ticket_set.filter(is_cancelled=False, event__in=events_to_recommend)
                for t in neighbor_tickets:
                    event_scores[t.event.id]["score"] += weight


    final_scores = []
    for data in event_scores.values():
        e = data["event"]
        city_score = 1.0 if e.city == most_frequent_city else 0.5 if e.city in city_counts else 0.0
        category_score = 1.0 if e.category == most_frequent_category else 0.5 if e.category in category_counts else 0.0
        follow_score = 0.0
        if e.artist in followed_artists or e.actor in followed_actors:
            follow_score = 1.0
        neighbor_score = data["score"]
        total_score = (city_score * 0.40 +  category_score * 0.30 +  follow_score * 0.20 + neighbor_score * 0.10  )
        final_scores.append((e, total_score))
    recommended_events_list = [e for e, _ in sorted(final_scores, key=lambda x: x[1], reverse=True)]
    return render(request, "app/recommended_events.html", {"recommended": recommended_events_list})

def is_admin(user):
    return user.is_authenticated and user.user_type == 'A'

@user_passes_test(is_admin)
def custom_admin_dashboard(request):
    return render(request, 'app/custom_admin_dashboard.html')

@user_passes_test(is_admin)
def manage_events(request):
    events_to_approve = Event.objects.filter(is_approved=False)
    context = { 'events_to_approve': events_to_approve}
    return render(request, 'app/manage_events.html', context)

@user_passes_test(is_admin)
def manage_users(request):
    users = CustomUser.objects.all()
    context = {'users': users }
    return render(request, 'app/manage_users.html', context)

@user_passes_test(is_admin)
def approve_event(request, event_id):
    if request.method == 'POST':
        event = get_object_or_404(Event, id=event_id)
        event.is_approved = True
        event.save()
        messages.success(request, f'"{event.title}" event named successfully confirmed.')
    return redirect('manage_events')

@user_passes_test(is_admin)
def reject_event(request, event_id):
    if request.method == 'POST':
        event = get_object_or_404(Event, id=event_id)
        event.is_approved = False
        event.save()
        messages.warning(request, f'"{event.title}"event named was rejected.')
    return redirect('manage_events')

@user_passes_test(is_admin)
def delete_user(request, user_id):
    if request.method == 'POST':
        user_to_delete = get_object_or_404(CustomUser, id=user_id)
        username = user_to_delete.username
        user_to_delete.delete()
        messages.success(request, f'User "{username}" successfully deleted.')
    return redirect('manage_users')

@user_passes_test(is_admin)
def manage_artists_and_actors(request, artist_id=None, actor_id=None):
    artist_to_edit = None
    actor_to_edit = None
    artist_form = ArtistForm()

    if request.method == 'POST' and 'add_artist' in request.POST:
        artist_form = ArtistForm(request.POST, request.FILES)
        if artist_form.is_valid():
            artist_form.save() 
            messages.success(request, 'Artist added successfully.')
            return redirect(f"{reverse('manage_artists_and_actors')}?tab=artists")
    actor_form = ActorForm()

    if request.method == 'POST' and 'add_actor' in request.POST:
        actor_form = ActorForm(request.POST, request.FILES)
        if actor_form.is_valid():
            actor_form.save() 
            messages.success(request, 'Actor added successfully.')
            return redirect(f"{reverse('manage_artists_and_actors')}?tab=actors")
    
    if artist_id:
        artist_to_edit = get_object_or_404(Artist, id=artist_id)
        artist_form = ArtistForm(request.POST or None, request.FILES or None, instance=artist_to_edit)
        if request.method == 'POST' and artist_form.is_valid():
            artist_form.save() 
            messages.success(request, f'Artist "{artist_to_edit.name}" updated successfully.')
            return redirect(f"{reverse('manage_artists_and_actors')}?tab=artists")

    if actor_id:
        actor_to_edit = get_object_or_404(Actor, id=actor_id)
        actor_form = ActorForm(request.POST or None, request.FILES or None, instance=actor_to_edit)
        if request.method == 'POST' and actor_form.is_valid():
            actor_form.save() 
            messages.success(request, f'Actor "{actor_to_edit.name}" updated successfully.')
            return redirect(f"{reverse('manage_artists_and_actors')}?tab=actors")
    artists = Artist.objects.all().order_by('name')
    actors = Actor.objects.all().order_by('name')
    context = {'artists': artists,'actors': actors,'artist_form': artist_form,'actor_form': actor_form,'artist_to_edit': artist_to_edit,'actor_to_edit': actor_to_edit,}
    return render(request, 'app/manage_artists_and_actors.html', context)
    
@user_passes_test(is_admin)
def delete_artist(request, artist_id):
    if request.method == 'POST':
        artist = get_object_or_404(Artist, id=artist_id)
        artist_name = artist.name
        artist.delete()
        messages.success(request, f'Artist "{artist_name}" deleted successfully.')
    return redirect(f"{reverse('manage_artists_and_actors')}?tab=artists")

@user_passes_test(is_admin)
def delete_actor(request, actor_id):
    if request.method == 'POST':
        actor = get_object_or_404(Actor, id=actor_id)
        actor_name = actor.name
        actor.delete()
        messages.success(request, f'Actor "{actor_name}" deleted successfully.')
    return redirect(f"{reverse('manage_artists_and_actors')}?tab=actors")