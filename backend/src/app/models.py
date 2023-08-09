import json

from django.db import models
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from app.enums import DatabaseType, DataType, ProcessStatus, TimeInterval


class Database(models.Model):
    """Модель базы данных."""

    slug = models.SlugField(unique=True)
    type = models.CharField(choices=DatabaseType.choices, max_length=50)
    uri = models.CharField(max_length=255)

    def __str__(self) -> str:
        """Строковое представление базы данных в виде уникальной человекочитаемый строки.

        Returns:
            str: Строка-идентификатор
        """
        return self.slug


class Model(models.Model):
    """Модель для схемы данных."""

    title = models.CharField(unique=True, max_length=255)

    def __str__(self) -> str:
        """Строковое представление схемы данных в виде её заголовка.

        Returns:
            str: Уникальное название схемы
        """
        return self.title


class Column(models.Model):
    """Модель для колонок схемы данных."""

    name = models.CharField(max_length=255)
    type = models.CharField(choices=DataType.choices, max_length=50)
    default = models.CharField(blank=True, null=True, max_length=255)
    alias = models.CharField(blank=True, null=True, max_length=255)
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='columns')

    def __str__(self) -> str:
        """Строковое представление колонки в виде её метаданных.

        Returns:
            str: Метаданные колонки
        """
        prefix = ''
        if default_value := self.default:
            prefix += ' DEFAULT {value}'.format(value=default_value)
        return '{name}: {type}'.format(name=self.alias or self.name, type=self.type.upper()) + prefix


class Process(models.Model):
    """Модель для процесса передачи данных."""

    slug = models.SlugField(unique=True)
    source = models.ForeignKey(Database, on_delete=models.CASCADE, related_name='targets')
    target = models.ForeignKey(Database, on_delete=models.CASCADE, related_name='sources')
    status = models.CharField(choices=ProcessStatus.choices, default=ProcessStatus.active, max_length=50)
    from_table = models.CharField(max_length=255)
    to_table = models.CharField(max_length=255)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    index_col = models.CharField(max_length=255, default='id')
    sync = models.BooleanField(default=False)
    time_interval = models.CharField(choices=TimeInterval.choices, default=TimeInterval.one_min, max_length=50)
    task = models.OneToOneField(PeriodicTask, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        """Метаданные модели."""

        verbose_name_plural = 'Processes'

    def __str__(self) -> str:
        """Строковое представление процесса передачи данных в виде уникальной человекочитаемый строки.

        Returns:
            str: Строка-идентификатор
        """
        return self.slug

    def delete(self, *args, **kwargs) -> tuple:
        """Удаление задачи вместе с процессом.

        Args:
            args: Необязательные позиционые аргументы
            kwargs: Необязательные именнованные аргументы

        Returns:
            tuple: Метаданные
        """
        if self.task is not None:
            self.task.delete()
        return super().delete(*args, **kwargs)

    def setup_task(self):
        """Создание задачи в Celery."""
        self.task = PeriodicTask.objects.create(
            name=self.slug,
            task='sync_data' if self.sync else 'transfer_data',
            interval=self.interval_schedule,
            args=json.dumps([self.id]),
            start_time=timezone.now(),
            one_off=True if not self.sync else False,
        )
        self.save()

    @property
    def interval_schedule(self) -> IntervalSchedule:
        """Свойство для получения интервала времени.

        Returns:
            IntervalSchedule: Объект реализующий интервал времени
        """
        if self.time_interval == TimeInterval.one_min:
            return IntervalSchedule.objects.get_or_create(every=1, period='minutes')[0]
        if self.time_interval == TimeInterval.five_mins:
            return IntervalSchedule.objects.get_or_create(every=5, period='minutes')[0]
        if self.time_interval == TimeInterval.one_hour:
            return IntervalSchedule.objects.get_or_create(every=1, period='hours')[0]


class Relationship(models.Model):
    """Модель для связей таблиц базы данных."""

    related_name = models.CharField(max_length=50)
    table = models.CharField(max_length=50)
    through_table = models.CharField(max_length=50)
    suffix = models.CharField(max_length=50, default='_id')
    flat = models.BooleanField(default=False)
    condition = models.CharField(max_length=255, blank=True, null=True)
    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name='relationships')
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='relationships')
