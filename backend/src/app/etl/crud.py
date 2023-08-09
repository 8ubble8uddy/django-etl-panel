import abc
from typing import Any, Dict, Iterator, Optional, Type

import pandas as pd
import sqlalchemy
from elasticsearch import Elasticsearch
from elasticsearch import exceptions as es_exc
from elasticsearch.helpers import bulk
from elasticsearch.helpers import errors as es_errors
from elasticsearch_dsl import Search, query
from sqlalchemy import exc as sql_exc

from app.etl import errors as etl_errors


class CRUD(abc.ABC):
    """Абстрактный ETL-сервис для выполнения CRUD-операций."""

    engines: Optional[Dict] = None

    def __init__(self, db_type: str):
        """При инициализации ожидает получить тип базы данных.

        Args:
            db_type: Тип базы данных
        """
        self.db_type = db_type

    @classmethod
    def get_subclasses(cls) -> Iterator[Type]:
        """Вспомогательный метод для получения все наследников данного класса.

        Yields:
            Iterator[type]:  Наследники класса
        """
        for subclass in cls.__subclasses__():
            yield from subclass.get_subclasses()
            yield subclass

    @classmethod
    def get_engine(cls, db_type: str) -> 'CRUD':
        """Получение движка базы данных для реализации CRUD сервиса.

        Args:
            db_type: Тип БД

        Returns:
            CRUD: Объект CRUD сервиса
        """
        if cls.engines is None:
            cls.engines = {}
            for engine_cls in cls.get_subclasses():
                engine = engine_cls()
                cls.engines[engine.db_type] = engine
        return cls.engines[db_type]

    @abc.abstractmethod
    def create(self, df: pd.DataFrame, uri: str, resource: str) -> int:
        """Вставка данных.

        Args:
            df: Датафрейм
            uri: Имя хоста БД
            resource: Название ресурса, куда вставляем данные
        """

    @abc.abstractmethod
    def read(self, uri: str, resource: str) -> pd.DataFrame:
        """Чтение данных.

        Args:
            uri: Имя хоста БД
            resource: Название ресурса, от куда извлекаем данные
        """

    @abc.abstractmethod
    def update(self, df: pd.DataFrame, uri: str, resource: str):
        """Обновление данных.

        Args:
            df: Датафрейм
            uri: Имя хоста БД
            resource: Название ресурса, где изменяем данные
        """

    @abc.abstractmethod
    def delete(self, df: pd.DataFrame, uri: str, resource: str):
        """Удаление данных.

        Args:
            df: Датафрейм
            uri: Имя хоста БД
            resource: Название ресурса, от куда удаляем данные
        """


class ElasticEngine(CRUD):
    """ETL-сервис для выполнения CRUD-операций в Elasticsearch."""

    def __init__(self):
        """При инициализации отправляем родительскому классу тип базы данных для регистрации."""
        super().__init__('elasticsearch')

    def create(self, df: pd.DataFrame, uri: str, resource: str) -> int:
        """Вставка данных в индекс.

        Args:
            df: Датафрейм
            uri: Имя хоста
            resource: Название индекса

        Raises:
            LoadTableError: Ошибка индекса
            LoadConnectionError: Ошибка подключения

        Returns:
            int: Количество вставленных документов
        """
        def doc_generator(df: pd.DataFrame, index: str):
            for idx, document in df.iterrows():
                yield {
                    '_index': index,
                    '_id': idx,
                    '_source': document.to_dict(),
                }
        try:
            with Elasticsearch(uri) as elastic:
                result = bulk(elastic, doc_generator(df, resource), refresh=True)[0]
        except es_errors.BulkIndexError as exc:
            raise etl_errors.LoadTableError(str(exc.errors[0]))
        except es_exc.ConnectionError as exc:
            raise etl_errors.LoadConnectionError(exc.error)
        return result

    def read(self, uri: str, resource: str) -> pd.DataFrame:
        """Чтение данных из индекса.

        Args:
            uri: Имя хоста
            resource: Название индекса

        Raises:
            ExtractTableError: Ошибка индекса
            ExtractConnectionError: Ошибка подключения

        Returns:
            pd.DataFrame: Датафрейм индекса
        """
        try:
            with Elasticsearch(uri) as elastic:
                cursor = Search(using=elastic, index=resource)
                df = pd.DataFrame(doc.to_dict() for doc in cursor.scan())
        except es_exc.NotFoundError as exc:
            raise etl_errors.ExtractTableError(exc.error)
        except es_exc.ConnectionError as exc:
            raise etl_errors.ExtractConnectionError(exc.error)
        return df

    def update(self, df: pd.DataFrame, uri: str, resource: str) -> int:
        """Обновление данных в индексе.

        Args:
            df: Датафрейм
            uri: Имя хоста
            resource: Название индекса

        Returns:
            int: Количество обновленных документов
        """
        return self.create(df, uri, resource)

    def delete(self, df: pd.DataFrame, uri: str, resource: str):
        """Удаление данных в индексе.

        Args:
            df: Датафрейм
            uri: Имя хоста
            resource: Название индекса

        Raises:
            LoadTableError: Ошибка индекса
            LoadConnectionError: Ошибка подключения

        Returns:
            int: Количество удалённых документов
        """
        try:
            with Elasticsearch(uri) as elastic:
                ids = [index for index, _ in df.iterrows()]
                docs = Search(using=elastic, index=resource).filter(query.Terms(_id=ids))
                result = docs.delete()['deleted']
        except es_exc.NotFoundError as exc:
            raise etl_errors.LoadTableError(exc.error)
        except es_exc.ConnectionError as exc:
            raise etl_errors.LoadConnectionError(exc.error)
        return result


class SQLEngine(CRUD):
    """ETL-сервис для выполнения CRUD-операций в SQL базах данных."""

    def __init__(self):
        """При инициализации отправляем родительскому классу тип движка баз данных."""
        super().__init__('sql')

    def create(self, df: pd.DataFrame, uri: str, resource: str):
        """Вставка данных в таблицу.

        Args:
            df: Датафрейм
            uri: Имя хоста
            resource: Название индекса

        Raises:
            LoadTableError: Ошибка таблицы
            LoadConnectionError: Ошибка подключения

        Returns:
            int: Количество вставленных строк
        """
        try:
            with sqlalchemy.create_engine(uri).connect() as sql_conn:
                df.to_sql(resource, sql_conn, if_exists='append', index=False)
                result = df[df.columns[0]].count()
        except (sql_exc.OperationalError, sql_exc.ProgrammingError, sql_exc.IntegrityError) as exc:
            if exc.statement:
                raise etl_errors.LoadTableError(detail=str(exc.orig))
            else:
                raise etl_errors.LoadConnectionError(detail=str(exc.orig))
        return result

    def read(self, uri: str, resource: str) -> pd.DataFrame:
        """Чтение данных из таблицы.

        Args:
            uri: Имя хоста
            resource: Название таблицы

        Raises:
            ExtractTableError: Ошибка таблицы
            ExtractConnectionError: Ошибка подключения

        Returns:
            pd.DataFrame: Датафрейм таблицы
        """
        try:
            with sqlalchemy.create_engine(uri).connect() as sql_conn:
                df = pd.read_sql(resource, sql_conn)
        except (sql_exc.OperationalError, sql_exc.ProgrammingError) as exc:
            if exc.statement == resource:
                raise etl_errors.ExtractTableError(detail=str(exc.orig))
            else:
                raise etl_errors.ExtractConnectionError(detail=str(exc.orig))
        return df

    def update(self, df: pd.DataFrame, uri: str, resource: str) -> Any:
        """Обновление данных в таблице.

        Args:
            df: Датафрейм
            uri: Имя хоста
            resource: Название таблицы

        Returns:
            Any: На данный момент не реализовано
        """
        return NotImplemented

    def delete(self, df: pd.DataFrame, uri: str, resource: str) -> Any:
        """Удаление данных в таблице.

        Args:
            df: Датафрейм
            uri: Имя хоста
            resource: Название таблицы

        Returns:
            Any: На данный момент не реализовано
        """
        return NotImplemented


class SQLiteEngine(SQLEngine):
    """ETL-сервис для выполнения CRUD-операций в SQLite базах данных."""

    def __init__(self):
        """При инициализации отправляем прародительскому классу (CRUD) тип базы данных для регистрации."""
        super(SQLEngine, self).__init__('sqlite')


class PostgresEngine(SQLEngine):
    """ETL-сервис для выполнения CRUD-операций в PostgreSQL базах данных."""

    def __init__(self):
        """При инициализации отправляем прародительскому классу (CRUD) тип базы данных для регистрации."""
        super(SQLEngine, self).__init__('postgresql')
