import parse
from django import forms
from django.core.validators import EMPTY_VALUES

from app.enums import DatabaseType
from app.models import Database


class DatabaseForm(forms.ModelForm):
    """Форма модели базы данных для показа определенных настроек подключения соответственно её типу."""

    host = forms.CharField(max_length=255, required=False)
    port = forms.CharField(max_length=255, required=False)
    file_path = forms.CharField(max_length=255, required=False)
    dbname = forms.CharField(max_length=255, required=False)
    user = forms.CharField(max_length=255, required=False)
    password = forms.CharField(max_length=255, required=False)
    schema = forms.CharField(max_length=255, required=False)

    URI_TEMPLATES = {
        'sqlite': 'sqlite:///file:{file_path}?mode=rw&uri=true',
        'postgresql': 'postgresql://{user}:{password}@{host}:{port}/{dbname}?options=-c%20search_path={schema}',
        'elasticsearch': '{host}:{port}',
    }

    def __init__(self, *args, **kwargs):
        """При инициализации формы в случае наличии БД, парсит URI и заполняет поля с параметрами.

        Args:
            args: Необязательные позиционные аргументы
            kwargs: Необязательные именованные аргументы
        """
        if instance := kwargs.get('instance'):
            kwargs['initial'] = self.parse_uri(instance.uri, instance.type)
        super().__init__(*args, **kwargs)

    def clean(self) -> dict:
        """Определние обязательных полей исходя из типа базы данных.

        Returns:
            dict: Данные после валидации
        """
        if db_type := self.cleaned_data.get('type'):
            required_fields = parse.compile(self.URI_TEMPLATES[db_type]).named_fields
            for field, value in self.cleaned_data.items():
                if field in required_fields and value in EMPTY_VALUES:
                    self._errors[field] = self.error_class(['Обязательное поле'])
        return super().clean()

    def parse_uri(self, uri: str, db_type: DatabaseType) -> dict:
        """Парсинг URI базы данных для получения параметров подключения.

        Args:
            uri: URI-адрес БД
            db_type: Тип БД

        Returns:
            dict: Параметры подключения
        """
        parsed = parse.parse(self.URI_TEMPLATES[db_type], uri)
        return parsed.named

    def save(self, commit: bool = True) -> Database:
        """Составляет URI из параметров подключения базы данных по шаблону исходя из её типа.

        Args:
            commit: Создавать ли объект

        Returns:
            Database: База данных
        """
        db_type = self.cleaned_data.pop('type')
        self.instance.uri = self.URI_TEMPLATES[db_type].format(**self.cleaned_data)
        return super().save(commit=commit)

    class Meta:
        """Метаданные формы."""

        model = Database
        exclude = ('uri',)
        widgets = {
            'type': forms.Select(
                attrs={
                    '--hideshow-fields': 'host, port, file_path, dbname, user, password, schema, uri',
                    '--show-on-sqlite': 'file_path',
                    '--show-on-postgresql': 'host, port, dbname, user, password, schema',
                    '--show-on-elasticsearch': 'host, port',
                },
            ),
        }

    class Media:
        """Настройки для динамической формы."""

        js = ('https://cdn.jsdelivr.net/gh/scientifichackers/django-hideshow@0.0.1/hideshow.js',)


class ProcessForm(forms.ModelForm):
    """Форма модели процесса для показа поля выбора интервала времени при отметке синхронизации."""

    class Meta:
        """Метаданные формы."""

        widgets = {
            'sync': forms.CheckboxInput(
                attrs={
                    '--hideshow-fields': 'time_interval',
                    '--show-on-checked': 'time_interval',
                },
            ),
        }

    class Media:
        """Настройки для динамической формы."""

        js = ('https://cdn.jsdelivr.net/gh/scientifichackers/django-hideshow@0.0.1/hideshow.js',)
