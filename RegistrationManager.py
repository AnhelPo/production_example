import json
from copy import deepcopy
from pathlib import Path

import pytest
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type

# Импорты внутри проекта
from Enums.Service.LogLevel import LogLevel
from Enums.Service.WaitingTime import WaitingTime
from Extensions.DatePickerEx import DatePickerEx
from Extensions.Log import Log
from Extensions.WebDriverEx import ElementEx, Waiting, Tabs
from Extensions.WindowsEx import WindowsEx
from Helpers.DropDownHelper import DropDownHelper
from Helpers.Generators import CityName
from Helpers.Locator import LocatorHelper as locHp
from Helpers.TextInputHelper import TextInputHelper
from PageObjects.login_page import LoginPageLocators
from PageObjects.registration_page import RegistrationPage, RegistrationPageLocators
from TestManagers.DB.AutoTestDBManager import AutoTestDBManager
from TestManagers.Validators.Registration import Registration

path = Path(__file__).parents[1].joinpath('config.json')
with path.open() as f:
    config = json.load(f)


class RegistrationManager:
    """Менеджер регистрации"""

    def __init__(self, browser):
        self.browser = browser
        self.wait = Waiting(self.browser)
        "Класс-расширение для работы с ожиданиями"
        self.elementEx = ElementEx(self.browser)
        "Класс-расширение для элементов страницы"
        self.tabs = Tabs(self.browser)
        "Класс-расширение для работы со вкладками"
        self.datePickerEx = DatePickerEx(self.browser)
        "Класс-расширение для выбора даты из календаря"
        self.windowsEx = WindowsEx(self.browser)
        "Класс-расширение для работы с окнами"
        self.ATDBManager = AutoTestDBManager()
        "AutoTest DB Manager"
        self.inpHelp = TextInputHelper(self.browser)
        "Помощник для текстовых полей ввода"
        self.dropdownHp = DropDownHelper(self.browser)
        "Помощник для выпадающих списков"
        self.reg_page = RegistrationPage(self.browser)
        "Страница регистрации"
        self.reg_page_loc = RegistrationPageLocators
        "Локаторы страницы регистрации"
        self.validator = Registration(self.browser)
        "Валидатор для страницы регистрации"

    # region Открытие страницы регистрации
    def open_registration_page(self):
        """Открытие страницы регистрации"""
        Log.trace("Открытие страницы регистрации", LogLevel.MANAGER)
        self.reg_page.open()
        self.wait.element_present(RegistrationPageLocators.LAST_NAME, WaitingTime.LONG)
        self.validator.is_registration_page()
        return self

    def open_registration_from_login(self):
        """Открытие страницы регистрации со страницы авторизации"""
        Log.trace("Открытие страницы регистрации со страницы авторизации", LogLevel.MANAGER)
        self.elementEx.find_and_click(LoginPageLocators.REGISTER_LINK)
        self.wait.element_present(RegistrationPageLocators.LAST_NAME, WaitingTime.LONG)
        self.validator.is_registration_page()
        return self

    # endregion Открытие страницы регистрации

    # region Заполнение и валидация заполнения формы
    def __fill_city_name(self, agent_data):
        """
        Заполнение названия города по случайно выбранной начальной букве

        :param agent_data: модель данных страхового агента
        :type agent_data: AgentData
        :return: None
        :rtype: None
        """
        first_letter = CityName.generate()
        while agent_data.city is None:
            try:
                agent_data.city = self.inpHelp.select_autocomplete(
                    self.reg_page_loc.CITY, first_letter, ('г ',))
                break
            # В проекте собственная система обработки ошибок для перезапуска тестов в определенных обстоятельствах;
            # базовый Exception выбрасывается вручную после обработки и логирования основного исключения
            except Exception:
                first_letter = CityName.generate()
        else:
            try:
                self.inpHelp.fill_autocomplete_input(self.reg_page_loc.CITY, agent_data.city,
                                                     strict=False)
            # При выборе значения не из списка (для негативного теста регистрации)
            except Exception:
                self.inpHelp.fill(self.reg_page_loc.CITY, agent_data.city)

    def __fill_registration_data(self, agent_data):
        """
        Заполнение и валидация заполнения формы регистрации

        :param agent_data: модель данных страхового агента
        :type agent_data: AgentData
        :return: RegistrationManager
        :rtype: RegistrationManager
        """
        self.inpHelp \
            .fill(self.reg_page_loc.LAST_NAME, agent_data.last_name) \
            .fill(self.reg_page_loc.FIRST_NAME, agent_data.first_name)
        self.__fill_city_name(agent_data)
        self.inpHelp \
            .fill(self.reg_page_loc.PHONE, agent_data.phone) \
            .fill(self.reg_page_loc.EMAIL, agent_data.email)

        if agent_data.insurances_names:
            self.dropdownHp.select_multiple(
                locHp.make_locator_from_template(self.reg_page_loc.MULTISELECT_TOGGLE,
                                                 self.reg_page_loc.INSURANCE_ROOT),
                locHp.make_locator_from_template(self.reg_page_loc.MULTISELECT_OPTIONS,
                                                 self.reg_page_loc.INSURANCE_ROOT),
                agent_data.insurances_names)

        if agent_data.aggregators_names:
            self.dropdownHp.select_multiple(
                locHp.make_locator_from_template(self.reg_page_loc.MULTISELECT_TOGGLE,
                                                 self.reg_page_loc.AGGREGATOR_ROOT),
                locHp.make_locator_from_template(self.reg_page_loc.MULTISELECT_OPTIONS,
                                                 self.reg_page_loc.AGGREGATOR_ROOT),
                agent_data.aggregators_names)

        self.dropdownHp.select(self.reg_page_loc.SOURCE, agent_data.source_of_info)

        self.validator.check_registration_data(agent_data)

        return self

    # endregion Заполнение и валидация заполнения формы

    # region Регистрация
    def __send_to_register(self):
        """
        Отправка запроса на регистрацию

        :return: RegistrationManager
        :rtype: RegistrationManager
        """
        Log.trace("Отправка запроса на регистрацию", LogLevel.FUNCT)
        self.elementEx.find_and_click(self.reg_page_loc.CONTINUE)
        return self

    def __fill_and_send(self, agent_data):
        """
        Заполнение формы и отправка запроса на регистрацию

        :param agent_data: AgentData
        :type agent_data: AgentData
        :return: RegistrationManager
        :rtype: RegistrationManager
        """
        self.__fill_registration_data(agent_data) \
            .__send_to_register()
        return self

    @retry(retry=retry_if_exception_type(AssertionError), wait=wait_fixed(0.5),
           reraise=True, stop=stop_after_attempt(3))
    def get_code(self, agent_data):
        """
        Получение СМС-кода из БД для регистрации или изменения логина

        :param agent_data: AgentData
        :type agent_data: AgentData
        :return: None
        :rtype: None
        """
        Log.trace("Получение СМС-кода", LogLevel.FUNCT)
        info_from_db = self.ATDBManager.get_registration_code()
        if agent_data.new_phone:
            phone = agent_data.new_phone
        else:
            phone = agent_data.phone
        assert info_from_db['phone'] == phone, \
            "СМС-код не был получен." \
            f"\nТелефон {phone}"
        agent_data.sms_code = info_from_db['code']

    @retry(retry=retry_if_exception_type(AssertionError), wait=wait_fixed(0.5),
           reraise=True, stop=stop_after_attempt(3))
    def __get_password(self, agent_data):
        """
        Получение пароля для входа в личный кабинет

        :param agent_data: AgentData
        :type agent_data: AgentData
        :return: None
        :rtype: None
        """
        Log.trace("Получение пароля", LogLevel.FUNCT)
        info_from_db = self.ATDBManager.get_password()
        assert info_from_db['phone'] == agent_data.phone, \
            "Пароль для учетной записи не был получен." \
            f"\nТелефон {agent_data.phone}"
        agent_data.password = info_from_db['message'].split('пароль: ')[1]

    def __confirm_registration(self, agent_data):
        """
        Подтверждение регистрации

        :param agent_data: AgentData
        :type agent_data: AgentData
        :return: None
        :rtype: None
        """
        Log.trace("Подтверждение регистрации", LogLevel.MANAGER)
        self.get_code(agent_data)
        self.wait.element_present(self.reg_page_loc.CODE_INPUT)
        self.inpHelp.fill(self.reg_page_loc.CODE_INPUT, agent_data.sms_code)
        self.elementEx.find_and_click(self.reg_page_loc.SUBMIT_CODE)
        self.__get_password(agent_data)

    def register(self, agent_data):
        """
        Регистрация

        :param agent_data: модель данных страхового агента
        :type agent_data: AgentData
        :return: RegistrationManager
        :rtype: RegistrationManager
        """
        Log.trace("Заполнение формы и отправка запроса на регистрацию", LogLevel.MANAGER)
        self.wait.element_present(self.reg_page_loc.LAST_NAME, WaitingTime.LONG)
        self.__fill_and_send(agent_data) \
            .__confirm_registration(agent_data)
        # Ожидание перехода на главную страницу
        self.wait.title_change('СекретарЪ', strict=True)
        self.windowsEx.skip_learning()

        return self

    # endregion Регистрация

    # region Негативные тесты
    def __clear_required_attributes(self, data, attributes):
        """
        Замена атрибутов модели пустыми значениями

        :param data: AgentData
        :type data: AgentData
        :param attributes: атрибуты, которые нужно очистить
        :type attributes: tuple
        :return: RegistrationManager
        :rtype: RegistrationManager
        """
        for attribute_name in attributes:
            attribute = getattr(data, attribute_name)
            if type(attribute) == list:
                setattr(data, attribute_name, [])
            else:
                setattr(data, attribute_name, '')
        return self

    def __fill_with_single_insurance(self, agent_data):
        """
        Заполнение формы регистрации с одной СК

        :param agent_data: AgentData
        :type agent_data: AgentData
        :return: RegistrationManager
        :rtype: RegistrationManager
        """
        Log.trace("Заполнение формы с одной СК", LogLevel.MANAGER)
        data = deepcopy(agent_data)
        data.insurances = data.insurances[:1]
        data.insurances_names = data.insurances_names[:1]
        self.__fill_and_send(data) \
            .validator.check_few_insurance_error()
        return self

    def __fill_without_required_fields(self, agent_data):
        """
        Заполнение формы регистрации с пустыми обязательными полями

        :param agent_data: AgentData
        :type agent_data: AgentData
        :return: RegistrationManager
        :rtype: RegistrationManager
        """
        for attribute in agent_data.required:
            Log.trace(f"Заполнение формы с пустым обязательным полем: {attribute}",
                      LogLevel.MANAGER)
            self.tabs.refresh_page()
            data = deepcopy(agent_data)
            self.__clear_required_attributes(data, (attribute,)) \
                .__fill_and_send(data) \
                .validator.check_broken_field_error(attribute)
        Log.trace(f"Заполнение формы со всеми пустыми полями",
                  LogLevel.MANAGER)
        self.tabs.refresh_page()
        self.__send_to_register() \
            .validator.check_broken_field_error()
        return self

    def __fill_with_broken_city(self, agent_data):
        """
        Заполнение формы регистрации с населенным пунктом не из списка

        :param agent_data: AgentData
        :type agent_data: AgentData
        :return: RegistrationManager
        :rtype: RegistrationManager
        """
        Log.trace("Заполнение формы с населенным пунктом не из списка", LogLevel.MANAGER)
        self.tabs.refresh_page()
        data = deepcopy(agent_data)
        data.city = "Новый населенный пункт"
        self.__fill_and_send(data) \
            .validator.check_broken_field_error('city')
        return self

    def __fill_with_broken_phone(self, agent_data):
        """
        Заполнение формы регистрации с некорректным телефоном

        :param agent_data: AgentData
        :type agent_data: AgentData
        :return: RegistrationManager
        :rtype: RegistrationManager
        """
        Log.trace("Заполнение формы с некорректным телефоном", LogLevel.MANAGER)
        self.tabs.refresh_page()
        data = deepcopy(agent_data)
        data.phone = data.phone[:-2]
        self.__fill_and_send(data) \
            .validator.check_broken_field_error('phone')
        return self

    def __fill_with_broken_email(self, agent_data):
        """
        Заполнение формы регистрации с некорректным адресом

        :param agent_data: AgentData
        :type agent_data: AgentData
        :return: RegistrationManager
        :rtype: RegistrationManager
        """
        Log.trace("Заполнение формы с некорректным адресом", LogLevel.MANAGER)
        self.tabs.refresh_page()
        data = deepcopy(agent_data)
        # При заполнении полей в обычном порядке всплывающая подсказка рядом с полем адреса
        # блокирует дальнейшее заполнение, поэтому порядок изменен
        self.__clear_required_attributes(data, ('email',))
        self.__fill_registration_data(data)
        self.inpHelp.fill(self.reg_page_loc.EMAIL, 'broken@@email')
        self.__send_to_register() \
            .validator.check_broken_field_error('email')
        return self

    def __fill_with_registered_user_data(self, agent_data):
        """
        Заполнение формы регистрации данными зарегистрированного пользователя

        :param agent_data: AgentData
        :type agent_data: AgentData
        :return: RegistrationManager
        :rtype: RegistrationManager
        """
        for attr_name, attr_value in zip(
                ('phone', 'email'),
                (config['base_config']['site_params'][pytest.envir]['login'],
                 config['base_config']['site_params'][pytest.envir]['email'])):
            Log.trace("Заполнение формы данными зарегистрированного пользователя: "
                      f"{attr_name}", LogLevel.MANAGER)
            self.tabs.refresh_page()
            data = deepcopy(agent_data)
            setattr(data, attr_name, attr_value)
            self.__fill_and_send(data) \
                .validator.check_registered_error()
        return self

    def run_negative_tests(self, agent_data):
        self.open_registration_page() \
            .__fill_with_single_insurance(agent_data) \
            .__fill_without_required_fields(agent_data) \
            .__fill_with_broken_city(agent_data) \
            .__fill_with_broken_phone(agent_data) \
            .__fill_with_broken_email(agent_data) \
            .__fill_with_registered_user_data(agent_data)

    # endregion Негативные тесты
