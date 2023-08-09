class ExtractError(Exception):
    """Ошибка при извлечении данных."""


class ExtractConnectionError(ExtractError):
    """Ошибка подключения с источником данных."""

    def __init__(self, detail: str):
        """При инициализации исключения ожидает получить описание ошибки соединения при извлечении.

        Args:
            detail: Детали ошибки
        """
        self.message = 'Нет подключения к отправителю данных!\nПричина: {detail}'.format(detail=detail)
        super().__init__(self.message)


class ExtractTableError(ExtractError):
    """Ошибка таблицы источника данных."""

    def __init__(self, detail: str):
        """При инициализации исключения ожидает получить описание ошибки таблицы при извлечении.

        Args:
            detail: Детали ошибки
        """
        self.message = 'Данные не были извлечены!\nПричина: {detail}'.format(detail=detail)
        super().__init__(self.message)


class TransformError(Exception):
    """Ошибка при преобразовании данных."""

    def __init__(self, errors: list, index: str):
        """При инициализации исключения ожидает получить данные об ошибке и номер строки, где была ошибка.

        Args:
            errors: Данные об ошибке
            index: Номер строки
        """
        self.message = 'Ошибка валидации:\n- колонка: {column}\n- сообщение: {message}\n- строка: {index}\n'.format(
            column=errors[0]['loc'][0],
            message=errors[0]['msg'],
            index=index,
        )
        super().__init__(self.message)


class LoadError(Exception):
    """Ошибка при загрузке данных."""


class LoadConnectionError(LoadError):
    """Ошибка подключения с получателем данных."""

    def __init__(self, detail: str):
        """При инициализации исключения ожидает получить описание ошибки соединения при загрузке.

        Args:
            detail: Детали ошибки
        """
        self.message = 'Нет подключения к получателю данных!\nПричина: {detail}'.format(detail=detail)
        super().__init__(self.message)


class LoadTableError(LoadError):
    """Ошибка таблицы получателя данных."""

    def __init__(self, detail: str):
        """При инициализации исключения ожидает получить описание ошибки таблицы при загрузке.

        Args:
            detail: Детали ошибки
        """
        self.message = 'Данные не были загружены!\nПричина: {detail}'.format(detail=detail)
        super().__init__(self.message)
