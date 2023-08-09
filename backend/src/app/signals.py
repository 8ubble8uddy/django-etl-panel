from django.db.models.signals import post_save
from django.dispatch import receiver

from app.enums import ProcessStatus
from app.models import Process


@receiver(post_save, sender=Process)
def create_or_update_periodic_task(sender: Process, instance: Process, created: bool, **kwargs):
    """Функция-триггер для отправки задачи в Celery при создании процесса передачи данных.

    Args:
        sender: Отправитель сигнала
        instance: Экземпляр модели
        created: Указание на то, создана ли новая запись или редактируется старая
        kwargs: Необязательные именованные аргументы
    """
    if created:
        instance.setup_task()
    else:
        if instance.task is not None:
            instance.task.enabled = instance.status == ProcessStatus.active
            instance.task.save()
