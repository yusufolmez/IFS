from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_registration_mail(subject, context, email):
    html_message = render_to_string('emails/email.html', context)
    plain_message = strip_tags(html_message)
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
        html_message=html_message
    )

def get_student_mail_context(student_data, email, password):
    return (
        'Öğrenci Kaydı Başarılı',
        {
            'title': 'Öğrenci Kaydı Başarılı',
            'header_text': 'Öğrenci Kaydı Başarılı',
            'name': f"{student_data.get('first_name', '')} {student_data.get('last_name', '')}",
            'email': email,
            'password': password,
            'site_url': 'https://site-url.com',
            'header_color': '#0056b3',
            'button_color': '#0056b3',
            'accent_color': '#0056b3',
            'custom_message': '<p>Staj sistemine kaydolduğunuz için teşekkür ederiz. Staj başvurularınızı yapmaya başlayabilirsiniz.</p>'
        }
    )

def get_company_mail_context(company_data, email, password):
    return (
        'Şirket Kaydı Başarılı',
        {
            'title': 'Şirket Kaydı Başarılı',
            'header_text': 'Şirket Kaydı Başarılı',
            'name': company_data.get('contact_person', ''),
            'email': email,
            'password': password,
            'site_url': 'https://site-url.com',
            'header_color': '#28a745',
            'button_color': '#28a745',
            'accent_color': '#28a745',
            'custom_message': f"<p>Staj sistemine kaydolduğunuz için teşekkür ederiz. <strong>{company_data.get('company_name', '')}</strong> şirketinin staj başvurularını değerlendirmeye başlayabilirsiniz.</p>"
        }
    )

def get_admin_mail_context(email, password):
    return (
        'Admin Kaydı Başarılı',
        {
            'title': 'Admin Kaydı Başarılı',
            'header_text': 'Admin Kaydı Başarılı',
            'name': 'Admin',
            'email': email,
            'password': password,
            'site_url': 'https://site-url.com',
            'header_color': '#343a40',
            'button_color': '#343a40',
            'accent_color': '#343a40',
            'custom_message': '<p>Yönetici olarak sisteme kaydınız başarıyla tamamlandı.</p>'
        }
    ) 