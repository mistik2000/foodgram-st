from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
import base64
import uuid
import os
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message='Имя пользователя может содержать только буквы, цифры и символы @/./+/-/_',
        )],
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Адрес электронной почты'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        upload_to='users/avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        swappable = 'AUTH_USER_MODEL'

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(upload_to='users/avatars/', null=True, blank=True)

    def __str__(self):
        return self.user.username

    def set_avatar_from_base64(self, base64_image):
        if not base64_image:
            raise ValidationError('Изображение не предоставлено')

        try:
           
            if ';base64,' not in base64_image:
                raise ValidationError('Неверный формат base64 строки')

            format, imgstr = base64_image.split(';base64,')
            
           
            ext = format.split('/')[-1].lower()
            if ext not in ['jpeg', 'jpg', 'png', 'gif']:
                raise ValidationError(f'Неподдерживаемый формат изображения: {ext}')

        
            try:
                image_data = base64.b64decode(imgstr)
            except Exception as e:
                raise ValidationError('Ошибка декодирования base64 строки')

            
            if self.avatar:
                if os.path.isfile(self.avatar.path):
                    os.remove(self.avatar.path)

           
            filename = f"{uuid.uuid4()}.{ext}"
            data = ContentFile(image_data)
            self.avatar.save(filename, data, save=True)
            
            return self.avatar.url

        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(f'Ошибка при сохранении аватара: {str(e)}')

class Subscription(models.Model):
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    author = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='subscribers'
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'author']

    def __str__(self):
        return f'{self.user.username} -> {self.author.username}'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)
    instance.profile.save()
