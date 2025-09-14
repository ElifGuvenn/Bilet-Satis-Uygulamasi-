from django.urls import path
from .import views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index_view, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/',views.dashboard_view,name='dashboard'),
    path('satici_dashboard/', views.satici_dashboard, name='satici_dashboard'),
    path('etkinlikler/', views.event_list, name='event_list'),
    path('etkinlik/<int:event_id>/detay/', views.event_detail, name='event_detail'),
    path('bilet-al/<int:event_id>/', views.ticket_purchase, name='ticket_purchase'),
    path('biletlerim/',views.my_tickets, name='my_tickets'),
    path('biletlerim/iptal/<int:ticket_id>/', views.cancel_ticket, name='cancel_ticket'), 
    path('delete_ticket/<int:ticket_id>/', views.delete_ticket, name='delete_ticket'),
    path('following/', views.following, name='following'),
    path('follow-artist/<int:artist_id>/', views.follow_artist, name='follow_artist'),
    path('remove-artist/<int:artist_id>/', views.remove_artist, name='remove_artist'),
    path('follow-actor/<int:actor_id>/', views.follow_actor, name='follow_actor'),
    path('remove-actor/<int:actor_id>/', views.remove_actor, name='remove_actor'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('get-artist-suggestions/', views.get_artist_suggestions, name='get_artist_suggestions'),
    path('get-actor-suggestions/', views.get_actor_suggestions, name='get_actor_suggestions'),
    path('mark-all-notifications-as-read/', views.mark_all_notifications_as_read, name='mark_all_notifications_as_read'),
    path('mark-notification-as-read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('delete-notification/<int:notification_id>/', views.delete_notification, name='delete_notification'),
    path('add-event/', views.add_event, name='add_event'),
    path('sales-view/',views.sales_view,name='sales_view'),
    path('event-reviews/',views.event_reviews,name='event_reviews'),
    path('verify-ticket/', views.verify_ticket, name='verify_ticket'),
    path('get-location-suggestions/', views.get_location_suggestions, name='get_location_suggestions'),
    path('get-city-suggestions/', views.get_city_suggestions, name='get_city_suggestions'),
    path('satici/etkinliklerim/', views.event_management, name='event_management'),
    path('satici/etkinlik-kampanya/<int:event_id>/', views.set_event_on_sale, name='set_event_on_sale'),
    path('satici/kampanya-durdur/<int:event_id>/', views.stop_event_sale, name='stop_event_sale'),
    path('recommended-events/', views.recommended_events, name='recommended_events'),
    path('admin_panel/', views.custom_admin_dashboard, name='custom_admin_dashboard'),
    path('admin_panel/events/', views.manage_events, name='manage_events'),
    path('admin_panel/users/', views.manage_users, name='manage_users'),
    path('admin_panel/events/approve/<int:event_id>/', views.approve_event, name='approve_event'),
    path('admin_panel/events/reject/<int:event_id>/', views.reject_event, name='reject_event'),
    path('admin_panel/users/delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin_panel/manage-artists-and-actors/', views.manage_artists_and_actors, name='manage_artists_and_actors'),
    path('admin_panel/delete-artist/<int:artist_id>/', views.delete_artist, name='delete_artist'),
    path('admin_panel/delete-actor/<int:actor_id>/', views.delete_actor, name='delete_actor'),
    path('admin_panel/edit-artist/<int:artist_id>/', views.manage_artists_and_actors, name='edit_artist'),
    path('admin_panel/edit-actor/<int:actor_id>/', views.manage_artists_and_actors, name='edit_actor'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



