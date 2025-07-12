from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetCompleteView
from django.utils.decorators import method_decorator
from django.conf import settings
from django.http import JsonResponse
from django.core.mail import send_mail
from .models import SupportRequest
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_protect
from django.utils.timezone import make_aware
import logging
import json

from .forms import (
    AccountUpdateForm,
    CustomUserCreationForm,
    CustomLoginForm,
    CustomPasswordResetForm,
)

logger = logging.getLogger(__name__)
User = get_user_model()

@csrf_protect
def check_availability(request):
    logger.info(f"check_availability called: method={request.method}, headers={dict(request.headers)}")
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            logger.debug(f"Input: username={username}, email={email}")
            response = {
                'username_exists': User.objects.filter(username=username).exists() if username else False,
                'email_exists': User.objects.filter(email=email).exists() if email else False
            }
            logger.debug(f"Response: {response}")
            return JsonResponse(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return JsonResponse({'error': 'Server error'}, status=500)
    logger.warning(f"Invalid request: method={request.method}, is_ajax={request.headers.get('x-requested-with')}")
    return JsonResponse({'error': 'Invalid request method or not AJAX'}, status=400)

@csrf_protect
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_url = request.build_absolute_uri(
                reverse('activate', kwargs={'uidb64': uid, 'token': token})
            )
            mail_subject = 'Activate your Findus online shopping account'
            message = render_to_string('accounts/activation_email.html', {
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': user.phone_number,
                },
                'activation_url': activation_url,
            })
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.content_subtype = 'html'
            try:
                email.send()
                messages.success(
                    request,
                    "🎉 Activation link sent! Please check your inbox (or spam folder) for the activation email. "
                    "If you don't receive it within a few minutes, contact support at support@findus.com."
                )
                return redirect('login')
            except Exception as e:
                logger.error(f"Email sending failed for {user.email}: {e}")
                messages.error(
                    request,
                    '❌ Failed to send activation email. Please try again or contact support at support@findus.com.'
                )
                user.delete()
                return redirect('signup')
        else:
            errors = []
            for field, field_errors in form.errors.items():
                for error in field_errors:
                    errors.append(f"{form.fields[field].label}: {error}")
            messages.error(request, '⚠️ Please correct the following errors: ' + '; '.join(errors))
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

@csrf_protect
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if user.is_active:
            messages.warning(request, '⚠️ This account has already been activated.')
            return redirect('login')
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, '✅ Account activated! You can now log in.')
            return redirect('login')
        else:
            messages.error(request, '❌ Invalid or expired activation link.')
            return redirect('signup')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        logger.error(f"Activation error for uid {uidb64}: {e}")
        messages.error(request, '❌ Invalid or expired activation link.')
        return redirect('signup')


@csrf_protect
@never_cache
def login(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']

            user = None

            # If username_or_email looks like an email, try authenticate directly
            if '@' in username_or_email:
                user = authenticate(request, email=username_or_email, password=password)
            else:
                # Look up email by username
                try:
                    user_obj = User.objects.get(username=username_or_email)
                    user = authenticate(request, email=user_obj.email, password=password)
                except User.DoesNotExist:
                    user = None

            if user:
                if user.is_active:
                    auth_login(request, user)
                    messages.success(request, '✅ Logged in successfully!')
                    return redirect('home')
                else:
                    messages.warning(request, '⚠️ Your account is inactive.')
            else:
                messages.error(request, '❌ Invalid username/email or password.')
        else:
            messages.error(request, '⚠️ Please correct the form errors.')
    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


# ✅ Logout View
@csrf_protect
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, '✅ Logged out successfully.')
        return redirect('login')
    return redirect('login')


# ✅ My Account Page
@login_required
def my_account(request):
    user = request.user
    if request.method == 'POST':
        form = AccountUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Profile updated.')
            return redirect('my_account')
        else:
            messages.error(request, '⚠️ Please correct the errors.')
    else:
        form = AccountUpdateForm(instance=user)
    return render(request, 'accounts/account.html', {'form': form, 'user': user})


# ✅ Forgot Password (Password Reset Email)
@csrf_protect
def forgot_password(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )

                mail_subject = 'Password Reset Request for Findus'
                message = render_to_string('accounts/password_reset_email.html', {
                    'user': user,
                    'reset_url': reset_url,
                })
                email_message = EmailMessage(mail_subject, message, to=[email])
                email_message.content_subtype = 'html'
                email_message.send()
                messages.success(request, " ✅ Password reset link has been sent to your email! "
                                 " Please check your inbox and spam folder. The link will be valid for a limited time.")
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, "❌ We couldn't find any account with that email address."
                                "Please make sure you entered it correctly, or try another email you may have registered with.")
        else:
            messages.error(request, '⚠️ Please fix form errors.')
    else:
        form = CustomPasswordResetForm()
    return render(request, 'accounts/forgot_password.html', {'form': form})


# ✅ Password Reset Confirm View (check if same password is used)
@method_decorator(csrf_protect, name='dispatch')
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        user = self.user  # ✅ Use the user object provided by Django

        new_password = form.cleaned_data['new_password1']

        if user.check_password(new_password):
            messages.error(self.request, "⚠️ You've already used this password. Please choose a different one.")
            return redirect(self.request.path)  # Reload the page

        response = super().form_valid(form)

        messages.success(
            self.request,
            "✅ Your password has been reset successfully. You can now log in with your new password."
        )
        return response


@login_required
def about_us(request):
    """
    View to render the About Us page.
    Requires user to be logged in.
    """
    return render(request, 'accounts/About_us.html')


@login_required
@csrf_protect
def contact_us(request):
    user = request.user
    full_name = user.get_full_name() or user.username
    email = user.email
    mobile = user.phone_number  # ✅ fetch directly from model

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        mobile_from_form = request.POST.get('mobile', '').strip()

        full_message = (
            f"From: {full_name} <{email}>\n"
            f"Mobile: {mobile_from_form}\n\n"
            f"Subject: {subject}\n\n"
            f"Message:\n{message}"
        )

        try:
            send_mail(
                subject=subject,
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            return JsonResponse({'success': True, 'message': 'Message sent successfully!'})
        except Exception as e:
            logger.error(f"Failed to send contact email: {e}")
            return JsonResponse({'success': False, 'message': f'Failed to send message: {e}'})

    # For GET request – render form with pre-filled data
    context = {
        'full_name': full_name,
        'email': email,
        'mobile': mobile,
    }
    return render(request, 'accounts/contact_us.html', context)


# Optional fallback if non-AJAX fallback POST
@login_required
@csrf_protect
def submit_contact(request):
    if request.method == 'POST':
        user = request.user
        name = user.get_full_name() or user.username
        email = user.email
        mobile = user.phone_number  # ✅ pulled from user model
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        content = (
            f"New Contact Message:\n\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Mobile: {mobile}\n"
            f"Subject: {subject}\n\n"
            f"Message:\n{message}"
        )
        mail_subject = f"Contact Form Submission from {name}"
        to_email = settings.DEFAULT_FROM_EMAIL

        try:
            email_message = EmailMessage(mail_subject, content, to=[to_email])
            email_message.send()
            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f"Contact email failed: {e}")
            return JsonResponse({'success': False, 'error': 'Failed to send email.'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})

AUTO_REPLIES = [
    "Hi! 👋 Thanks for reaching out. We’ve received your message.",
    "We're looking into your concern and will get back shortly.",
    "Please allow us a few minutes while we check the details.",
    "Your issue is being reviewed by our support expert.",
    "Thanks for your patience. We value your time!",
    "This might take a few more minutes. Stay with us.",
    "Almost done! Preparing the solution for you.",
    "Here’s what you can try in the meantime: restart the app.",
    "If this doesn’t help, we’ll escalate it to our technical team.",
    "Done! We hope this resolves your issue. Let us know if you need anything else!",
]

@login_required
def customer_support(request):
    user = request.user

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if subject and message:
            support_request = SupportRequest.objects.create(user=user, subject=subject, message=message)
            # Optionally trigger Celery task here to send auto replies
            
            return JsonResponse({'success': True, 'message': 'Message sent!'})
        else:
            return JsonResponse({'success': False, 'message': 'Subject and message are required.'})

    support_requests = SupportRequest.objects.filter(user=user).order_by('created_at')
    context = {
        'user': user,
        'full_name': user.get_full_name() or user.username,
        'support_requests': support_requests,
    }
    return render(request, 'accounts/CustomerSupport.html', context)


@login_required
@csrf_protect
def check_support_updates(request):
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        last_check = request.POST.get("last_check")
        if not last_check:
            return JsonResponse({"new_messages": []})

        try:
            last_dt = make_aware(parse_datetime(last_check))
        except Exception:
            return JsonResponse({"new_messages": []})

        new_responses = SupportRequest.objects.filter(
            user=request.user,
            response__isnull=False,
            updated_at__gt=last_dt
        ).order_by("updated_at")

        new_messages = [
            {
                "subject": req.subject,
                "response": req.response,
                "timestamp": req.updated_at.strftime("%b %d, %Y %I:%M %p")
            }
            for req in new_responses
        ]

        return JsonResponse({"new_messages": new_messages})

    return JsonResponse({"error": "Invalid request"}, status=400)




@login_required
def fetch_new_replies(request):
    if request.is_ajax():
        last_id = request.GET.get('last_id')
        try:
            last_id = int(last_id)
        except (TypeError, ValueError):
            last_id = 0

        new_replies_qs = SupportRequest.objects.filter(
            user=request.user,
            response__isnull=False,
            id__gt=last_id
        ).order_by('id')

        new_replies = []
        for req in new_replies_qs:
            new_replies.append({
                'id': req.id,
                'response': req.response,
                'subject': req.subject,
                'created_at': req.created_at.strftime('%b %d, %Y %I:%M %p'),
            })

        return JsonResponse({'new_replies': new_replies})
    return JsonResponse({'error': 'Invalid request'}, status=400)