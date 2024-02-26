from django.db import models
from django.contrib.auth.models import User, Group

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    citi = models.CharField(max_length=36, blank=True)

    def save(self, *args, **kwargs):
        super(Profile, self).save(*args, **kwargs)

        # Проверяем, существует ли группа с нужным именем
        group_name = 'YourGroupName'  # Замените 'YourGroupName' на нужное имя группы
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            # Если группы не существует, создаем ее
            group = Group.objects.create(name=group_name)

        # Добавляем пользователя к созданной или существующей группе
        group.user_set.add(self.user)



