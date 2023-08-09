from django.db import models


class DataType(models.TextChoices):
    """Вспомогательная модель для выбора типа данных."""

    str = 'str'
    int = 'int'
    float = 'float'
    date = 'date'
    datetime = 'datetime'
    UUID = 'UUID'


class DatabaseType(models.TextChoices):
    """Вспомогательная модель для выбора типа базы данных."""

    sqlite = 'sqlite'
    postgresql = 'postgresql'
    elasticsearch = 'elasticsearch'


class TimeInterval(models.TextChoices):
    """Вспомогательная модель для выбора интервала времени."""

    one_min = '1 min'
    five_mins = '5 mins'
    one_hour = '1 hour'


class ProcessStatus(models.TextChoices):
    """Вспомогательная модель для выбора статуса процесса."""

    active = 'active'
    disabled = 'disabled'
