from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.utils.html import format_html
from django_celery_beat import models as celery_models

from app.forms import DatabaseForm, ProcessForm
from app.models import Column, Database, Model, Process, Relationship


class RelationshipInline(admin.StackedInline):
    """Класс для вставки связей между таблицами в админку процессов."""

    model = Relationship
    autocomplete_fields = ('process',)


class ColumnInline(admin.TabularInline):
    """Класс для вставки колонок таблицы в админку модели."""

    model = Column
    autocomplete_fields = ('model',)


@admin.register(Database)
class DatabaseAdmin(admin.ModelAdmin):
    """Классс админки баз данных."""

    form = DatabaseForm
    list_filter = ('type',)
    list_display = ('type', 'dsn')
    search_fields = ('slug',)

    @admin.display
    def dsn(self, obj: Database) -> str:
        """Вывод настроек подключения к базам данных.

        Args:
            obj: База данных

        Returns:
            str: DSN (Data Source Name) БД
        """
        params = self.form().parse_uri(obj.uri, obj.type)
        return format_html('<br>'.join(f'{key}={value}' for key, value in params.items()))


@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    """Класс админки моделей."""

    inlines = (ColumnInline,)
    search_fields = ('title',)
    list_display = ('title', 'columns')

    @admin.display
    def columns(self, obj: Model) -> str:
        """Вывод колонок модели.

        Args:
            obj: Модель

        Returns:
            str: Колонки модели
        """
        return format_html('<br>'.join(str(col) for col in obj.columns.all()))


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    """Класс админки процессов."""

    form = ProcessForm
    inlines = (RelationshipInline,)
    search_fields = ('slug', 'source', 'target')
    list_filter = ('source', 'target')
    list_display = ('slug', 'from_', 'to', 'active')
    exclude = ('task',)

    @admin.display(description='from')
    def from_(self, obj: Process) -> str:
        """Вывод отправителя данных ETL-процесса.

        Args:
            obj: Процесс

        Returns:
            str: Отправитель данных
        """
        return '{slug}: {from_table}'.format(slug=obj.source.slug, from_table=obj.from_table)

    @admin.display
    def to(self, obj: Process):
        """Вывод получателя данных ETL-процесса.

        Args:
            obj: Процесс

        Returns:
            str: Получатель данных
        """
        return '{slug}: {to_table}'.format(slug=obj.target.slug, to_table=obj.to_table)

    @admin.display(boolean=True)
    def active(self, obj: Process) -> bool:
        """Вывод состояния ETL-процесса.

        Args:
            obj: Процесс

        Returns:
            bool: Состояние процесса
        """
        return obj.task.enabled


admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.unregister(celery_models.PeriodicTask)
admin.site.unregister(celery_models.IntervalSchedule)
admin.site.unregister(celery_models.ClockedSchedule)
admin.site.unregister(celery_models.CrontabSchedule)
admin.site.unregister(celery_models.SolarSchedule)
