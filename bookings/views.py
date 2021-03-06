from datetime import datetime
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings

from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from physioactivities.settings import STRIPE_SECRET_KEY

from .models import Booking
from user.models import UserProfile
from services.models import Clinician, Service, ServiceDate, ServiceTime

import stripe
import json


@require_POST
def cache_bookings_data(request):
    try:
        pid = request.POST.get('client_secret').split('_secret')[0]
        stripe.api_key = STRIPE_SECRET_KEY
        bag = json.dumps(request.session.get('bag', {}))
        stripe.PaymentIntent.modify(pid, metadata={
            'bag': bag,
            'save_info': request.POST.get('save_info'),
            'username': request.user,
        })
        return HttpResponse(status=200)
    except Exception as e:
        messages.error(request, ('Sorry, your payment cannot be '
                                 'processed right now. Please try '
                                 'again later.'))
        return HttpResponse(content=e, status=400)


@login_required(login_url='/login?show_signup=true')
def bookings(request):
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    username = request.user.username
    user = UserProfile.objects.get(user__username=username)

    profile = {
        'name': user.fullname(),
        'email': user.user.email,
        'phone': user.phone
    }

    if request.method == 'POST':
        bag = request.session.get('bag', {})

        service = Service.objects.get(id=bag['service'])
        clinician = Clinician.objects.get(id=bag['clinician'])
        date = ServiceDate.objects.get(id=bag['date'])
        time = ServiceTime.objects.get(id=bag['time'])
        date_time = datetime.strptime(bag['datetime'][:-1], '%d/%m/%Y %H:%M')
        total = float(bag['total'])

        booking = Booking(service=service, clinician=clinician, date=date,
                          time=time, datetime=date_time, total=total, user=user)
        stripe_pid = request.POST.get('client_secret').split('_secret')[0]

        if stripe_pid is not None:
            booking.stripe_pid = stripe_pid
            booking.save()
            # Save the info to the user's profile if all is well
            request.session['save_info'] = 'save-info' in request.POST
            return redirect(reverse('bookings_success',
                                    args=[booking.booking_number]))
        else:
            messages.error(request, ('There was an error with your form. '
                                     'Please double check your information.'))

    if not stripe_public_key:
        messages.warning(request, ('Stripe public key is missing. '
                                   'Did you forget to set it in '
                                   'your environment?'))

    else:
        bag = request.session.get('bag', {})

        total = float(bag['total'])
        stripe_total = round(total * 100)
        stripe.api_key = STRIPE_SECRET_KEY
        intent = stripe.PaymentIntent.create(
            amount=stripe_total,
            currency=settings.STRIPE_CURRENCY,
        )

    template = 'bookings/bookings.html'

    context = {
        'bag': bag,
        'profile': profile,
        'stripe_public_key': stripe_public_key,
        'client_secret': intent.client_secret,
    }

    return render(request, template, context)


def bookings_success(request, booking_number):
    """
     Handle successful appointment
     """
    bag = request.session.get('bag', {})
    booking = get_object_or_404(Booking, booking_number=booking_number)
    if request.user.is_authenticated:
        profile = UserProfile.objects.get(user=request.user)
        # # Attach the user's profile to the booking
        # booking.user = UserProfile.objects.get(user=user)
        # booking.save()
        success_message = f'Appointment successfully processed! \
         Your appointment number is {booking_number}. A confirmation \
         email will be sent to {profile.user.email}.'
        messages.success(request, success_message)

        if 'bag' in request.session:
            del request.session['bag']

        if 'save_info' in request.session:
            del request.session['save_info']

        template = 'bookings/bookings_success.html'
        context = {
            'bag': bag,
            'profile': profile,
            'booking': booking,
        }

        return render(request, template, context)
