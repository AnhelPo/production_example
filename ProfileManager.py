from selenium.common.exceptions import TimeoutException
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from DataModels.InsuranceData import InsuranceData
from Enums.Service.LogLevel import LogLevel
from Enums.Service.PopupType import PopupType
from Extensions.DatePickerEx import DatePickerEx
from Extensions.Log import Log
from Extensions.WebDriverEx import ElementEx, Waiting, Tabs
from Extensions.WindowsEx import WindowsEx
from Helpers.DropDownHelper import DropDownHelper
from Helpers.Generators import AgentNewData
from Helpers.TextInputHelper import TextInputHelper
from PageObjects.main_page import MainPageLocators
from PageObjects.profile_extension_page import ExtensionPageLocators
from PageObjects.profile_osago_settings_page import OsagoSettingsPageLocators
from PageObjects.profile_personal_page import PersonalPageLocators
from TestManagers.RegistrationManager import RegistrationManager
from TestManagers.Validators.Profile import Profile


class ProfileManager:
    """Менеджер для управления профилем и настройками пользователя"""

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
        self.inpHelp = TextInputHelper(self.browser)
        "Помощник для текстовых полей ввода"
        self.dropdownHp = DropDownHelper(self.browser)
        "Помощник для выпадающих списков"
        self.reg_manager = RegistrationManager(self.browser)
        "Менеджер регистрации"
        self.profile_page_loc = PersonalPageLocators
        "Локаторы вкладки 'Личные данные' страницы профиля"
        self.insurance_page_loc = OsagoSettingsPageLocators
        "Локаторы вкладки 'Настройки' страницы профиля"
        self.validator = Profile(self.browser)
        "Валидатор для профиля пользователя"

    # region Общее
    def go_to_tab(self, locator):
        """Переход на указаную вкладку на странице профиля"""
        Log.trace("Открытие вкладки", LogLevel.MANAGER)
        self.elementEx.find_and_click(locator)

    # endregion Общее

    # region Личные данные
    @staticmethod
    def __precondition(agent_data):
        """Дозаполнение модели данных для изменения профиля пользователя"""
        Log.trace("Дозаполнение модели данных пользователя", LogLevel.MANAGER)
        AgentNewData.generate(agent_data)

    @retry(retry=retry_if_exception_type(TimeoutException), reraise=True, stop=stop_after_attempt(2))
    def __set_personal_info(self, agent_data):
        """Изменение имени, населенного пункта и типа АЗ пользователя"""
        Log.trace("Изменение имени, населенного пункта и типа АЗ пользователя", LogLevel.MANAGER)
        self.inpHelp.fill(self.profile_page_loc.LAST_NAME, agent_data.new_last_name) \
            .fill(self.profile_page_loc.FIRST_NAME, agent_data.new_first_name) \
            .fill(self.profile_page_loc.MIDDLE_NAME, agent_data.middle_name) \
            .fill_autocomplete_input(self.profile_page_loc.CITY, agent_data.new_city)
        self.elementEx.find_and_click(self.profile_page_loc.USER_INFO_SAVE_BTN)
        self.windowsEx.close_popup(PopupType.SUCCESS)

    @retry(retry=retry_if_exception_type(TimeoutException), reraise=True, stop=stop_after_attempt(2))
    def __set_phone(self, agent_data):
        """Изменение телефона пользователя"""
        Log.trace("Изменение телефона пользователя", LogLevel.MANAGER)
        self.inpHelp.fill(self.profile_page_loc.PHONE, agent_data.new_phone)
        self.elementEx.find_and_click(self.profile_page_loc.PHONE_SAVE_BTN)
        self.wait.element_present(self.profile_page_loc.PHONE_CODE_INPUT)
        self.reg_manager.get_code(agent_data)
        self.inpHelp.fill(self.profile_page_loc.PHONE_CODE_INPUT, agent_data.sms_code)
        self.elementEx.find_and_click(self.profile_page_loc.PHONE_CONFIRM_BTN)
        self.windowsEx.close_popup(PopupType.SUCCESS)
        agent_data.phone = agent_data.new_phone

    @retry(retry=retry_if_exception_type(TimeoutException), reraise=True, stop=stop_after_attempt(2))
    def __set_email(self, agent_data):
        """Изменение адреса электронной почты пользователя"""
        Log.trace("Изменение адреса электронной почты пользователя", LogLevel.MANAGER)
        self.elementEx.find_and_click(self.profile_page_loc.EMAIL_CHANGE_BTN)
        self.wait.element_present(self.profile_page_loc.EMAIL_INPUT)
        self.inpHelp.fill(self.profile_page_loc.EMAIL_INPUT, agent_data.new_email)
        self.elementEx.find_and_click(self.profile_page_loc.EMAIL_SAVE_BTN)
        self.windowsEx.close_popup(PopupType.SUCCESS)

    @retry(retry=retry_if_exception_type(TimeoutException), reraise=True, stop=stop_after_attempt(2))
    def __set_password(self, agent_data):
        """Изменение пароля пользователя"""
        Log.trace("Изменение пароля пользователя", LogLevel.MANAGER)
        self.inpHelp.fill(self.profile_page_loc.PASSWORD_CURRENT, agent_data.password) \
            .fill(self.profile_page_loc.PASSWORD_NEW, agent_data.new_pass) \
            .fill(self.profile_page_loc.PASSWORD_NEW_CONFIRM, agent_data.new_pass)
        self.elementEx.find_and_click(self.profile_page_loc.PASSWORD_CHANGE_BTN)
        self.windowsEx.close_popup(PopupType.SUCCESS)
        agent_data.password = agent_data.new_pass

    def set_user_info(self, agent_data):
        """
        Изменение личных данных пользователя

        :param agent_data: модель данных агента
        :type agent_data: AgentData
        :return: ProfileManager
        :rtype: ProfileManager
        """
        self.__precondition(agent_data)
        self.__set_personal_info(agent_data)
        self.__set_phone(agent_data)
        self.__set_email(agent_data)
        self.__set_password(agent_data)
        return self

    def delete_account(self):
        """Удаление аккаунта"""
        Log.trace("Удаление аккаунта", LogLevel.MANAGER)
        self.wait.element_present(self.profile_page_loc.DELETE_BTN)
        self.elementEx.find_and_click(self.profile_page_loc.DELETE_BTN)
        self.inpHelp.fill(self.profile_page_loc.CONFIRM_DELETE_INPUT, "Удалить")
        self.elementEx.find_and_click(self.profile_page_loc.CONFIRM_DELETE_BTN)
        self.wait.title_change("Регистрация")
        return self

    # endregion Личные данные

    # region Настройки расширения
    def set_autocomplete_mode(self, mode):
        """Выбор типа АЗ в настройках расширения"""
        locator = ExtensionPageLocators.get_locator_for_mode(mode)
        self.elementEx.find_and_click(locator)

    # endregion Настройки расширения

    # region Настройки ОСАГО
    def search(self, alias):
        """Поиск СК или агрегатора на странице настроек"""
        self.inpHelp.fill(self.insurance_page_loc.SEARCH, alias)
        self.wait.element_present(self.insurance_page_loc.SEARCH_RESULT)
        return self

    def __activate(self, alias):
        """Подключение СК или агрегатора"""
        self.search(alias)
        self.wait.element_present(self.insurance_page_loc.ACTIVATE)
        self.elementEx.find_and_click(self.insurance_page_loc.ACTIVATE)
        self.wait.element_present(self.insurance_page_loc.DEACTIVATE)
        return self

    def __deactivate(self, alias):
        """Отключение СК или агрегатора"""
        self.search(alias)
        self.wait.element_present(self.insurance_page_loc.DEACTIVATE)
        self.elementEx.find_and_click(self.insurance_page_loc.DEACTIVATE)
        self.wait.element_present(self.insurance_page_loc.ACTIVATE)
        return self

    def __set_kv(self, object_data):
        """Задание КВ для СК или агрегатора"""
        if object_data.kv:
            self.inpHelp.fill(self.insurance_page_loc.KV, object_data.kv)
        return self

    def __set_as_default(self, object_data):
        """Задание СК или агрегатора по умолчанию"""
        if object_data.default:
            self.elementEx.find_and_click(self.insurance_page_loc.DEFAULT)
        return self

    def __select_in_modal(self, value):
        """Выбор пункта в выпадающем меню"""
        self.wait.element_present(MainPageLocators.MODAL_DROPDOWN)
        self.dropdownHp.select(
            MainPageLocators.MODAL_DROPDOWN, value, strict=True)
        self.wait.element_not_present(MainPageLocators.DROPDOWN_OPTION)

    def __set_autocomplete_preferences(self, insurance_data: InsuranceData):
        """Задание настроек автозаполнения для СК"""
        if insurance_data.policy_type or insurance_data.manager:
            self.elementEx.find_and_click(self.insurance_page_loc.AUTOCOMPLETE)
            if insurance_data.manager:
                self.inpHelp.fill(MainPageLocators.MODAL_INPUT, insurance_data.manager)
            if insurance_data.policy_type:
                self.__select_in_modal(insurance_data.policy_type)
            self.elementEx.find_and_click(MainPageLocators.MODAL_SAVE_BTN)
            self.windowsEx.close_popup(PopupType.SUCCESS)
        return self

    def __save_settings(self):
        """Сохранение настроек для всех СК и агрегаторов"""
        self.elementEx.find_and_click(self.insurance_page_loc.GENERAL_SAVE_BTN)
        self.windowsEx.close_popup(PopupType.SUCCESS)

    def set_osago_preferences(self, agent_data):
        """
        Настройка параметров СК и агрегаторов пользователя

        :param agent_data: модель данных агента
        :type agent_data: AgentData
        :return: ProfileManager
        :rtype: ProfileManager
        """
        Log.trace("Изменение настроек СК и агрегаторов", LogLevel.MANAGER)
        for group in (agent_data.insurances, agent_data.aggregators):
            if group == agent_data.aggregators:
                self.elementEx.find_and_click(self.insurance_page_loc.AGGREGATORS_TAB)
                self.wait.element_present(OsagoSettingsPageLocators.AGGREGATORS_TAB_ACTIVE)
            for obj_data in group:
                self.search(obj_data.name) \
                    .__set_kv(obj_data) \
                    .__set_as_default(obj_data)
                if hasattr(obj_data, "policy_type"):
                    self.__set_autocomplete_preferences(obj_data)

            if group == agent_data.insurances:
                Log.trace("Отключение выбранной ранее СК", LogLevel.MANAGER)
                self.__deactivate(agent_data.insurance_disable)
                # удаляем СК из модели для корректной валидации изменения настроек
                insurance_index = agent_data.insurances_names.index(agent_data.insurance_disable)
                del agent_data.insurances[insurance_index]
                del agent_data.insurances_names[insurance_index]

                Log.trace("Подключение не выбранной ранее СК", LogLevel.MANAGER)
                self.__activate(agent_data.insurance_enable)
                self.__save_settings()

            elif group == agent_data.aggregators:
                Log.trace("Отключение выбранного ранее агрегатора", LogLevel.MANAGER)
                self.__deactivate(agent_data.aggregator_disable)
                # удаляем агрегатор из модели для корректной валидации изменения настроек
                aggregator_index = agent_data.aggregators_names.index(agent_data.aggregator_disable)
                del agent_data.aggregators[aggregator_index]
                del agent_data.aggregators_names[aggregator_index]

                Log.trace("Подключение не выбранного ранее агрегатора", LogLevel.MANAGER)
                self.__activate(agent_data.aggregator_enable)
                self.__save_settings()

        return self

    # endregion Настройки ОСАГО
