from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_internship_mail(subject, context, email):
    html_message = render_to_string('emails/internship_application_email_c.html', context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
        html_message=html_message
    )

def get_internship_application_mail_context(student_data, email):
    return(
        'Şirketinize Staj Başvurusu Alındı',
        {
            'title': 'Sirketinize Staj Başvurusu Alındı',
            'header_text': 'Sirketinize Staj Başvurusu Alındı',
            'name': f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}",
            'email': email,
            'site_url': 'https://site-url.com',
            'header_color': '#28a745',
            'button_color': '#28a745',
            'accent_color': '#28a745',
            'custom_message': f"<p>Ogrencimizin staj basvurusunu degerlendirmek icin web istemize gidiniz.</p>"
        }
    )

def get_internship_application_mail_context_for_student(student_data, email):
    return(
        'Staj Başvurunuz Alındı',
        {
            'title': 'Staj Başvurunuz Alındı',
            'header_text': 'Staj Başvurunuz Alındı',
            'name': f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}",
            'email': email,
            'site_url': 'https://site-url.com',
            'header_color': '#28a745',
            'button_color': '#28a745',
            'accent_color': '#28a745',
            'custom_message': f"<p>Staj basvurunuz alindi. Sonucunu bekleyiniz.</p>"
        }
    )

def get_internship_application_mail_context_for_student_rejected(student_data, email):
    return(
        'Staj Başvurunuz Reddedildi',
        {
            'title': 'Staj Başvurunuz Reddedildi',
            'header_text': 'Staj Başvurunuz Reddedildi',
            'name': f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}",
            'email': email,
            'site_url': 'https://site-url.com',
            'header_color': '#dc3545',
            'button_color': '#dc3545',
            'accent_color': '#dc3545',
            'custom_message': f"<p>Staj basvurunuz reddedildi. Sonucunu bekleyiniz.</p>"
        }
    )

def get_internship_application_mail_context_for_student_accepted(student_data, email):
    return(
        'Staj Başvurunuz Kabul Edildi',
        {
            'title': 'Staj Başvurunuz Kabul Edildi',
            'header_text': 'Staj Başvurunuz Kabul Edildi',
            'name': f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}",
            'email': email,
            'site_url': 'https://site-url.com',
            'header_color': '#28a745',
            'button_color': '#28a745',
            'accent_color': '#28a745',
            'custom_message': f"<p>Staj basvurunuz kabul edildi. Sonucunu bekleyiniz.</p>"
        }
    )