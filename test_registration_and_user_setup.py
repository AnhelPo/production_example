import pytest

from Extensions.Log import Log
from Tests.case_data import CaseData


def test_registration(manager):
    Log.trace("ПРИМЕНЕНИЕ ПРЕДУСЛОВИЙ")
    data = CaseData.main_registration_precondition(case_id=0)

    Log.trace("ОТКРЫТИЕ СТРАНИЦЫ РЕГИСТРАЦИИ СО СТРАНИЦЫ АВТОРИЗАЦИИ")
    manager.login_manager.open_login_page()
    manager.registration_manager.open_registration_from_login()

    Log.trace("РЕГИСТРАЦИЯ")
    manager.registration_manager.register(data)
    manager.validator.is_main_page()

    Log.trace("ПРОВЕРКА ПАРОЛЯ")
    manager.login_manager.logout() \
        .validator.is_login_page()
    manager.login_manager.sign_in(data.phone, data.password) \
        .go_on_site()
    manager.validator.is_main_page()

    Log.trace("УДАЛЕНИЕ АККАУНТА")
    manager.open_profile_page_from_upper_menu()
    manager.profile_manager.delete_account() \
        .validator.check_account_deleting(manager.login_manager, data.phone, data.password)

    Log.trace("НЕГАТИВНЫЕ ТЕСТЫ РЕГИСТРАЦИИ")
    manager.registration_manager.run_negative_tests(data)


def test_profile_setup(manager, prepare_and_fin):
    Log.trace("ИЗМЕНЕНИЕ ЛИЧНЫХ ДАННЫХ ПОЛЬЗОВАТЕЛЯ")
    manager.open_page_from_sidebar(page='personal_settings') \
        .profile_manager.set_user_info(prepare_and_fin)

    Log.trace("ИЗМЕНЕНИЕ НАСТРОЕК РАСШИРЕНИЯ")
    manager.open_page_from_sidebar(page='ext_settings') \
        .profile_manager.set_autocomplete_mode(prepare_and_fin.autocomplete)

    Log.trace("ИЗМЕНЕНИЕ НАСТРОЕК ОСАГО")
    manager.open_page_from_sidebar(page='osago_settings') \
        .profile_manager.set_osago_preferences(prepare_and_fin)

    Log.trace("ПРОВЕРКА ИЗМЕНЕНИЯ ЛИЧНЫХ ДАННЫХ И НАСТРОЕК ПОЛЬЗОВАТЕЛЯ")
    manager.login_manager.logout() \
        .validator.is_login_page()
    manager.login_manager.sign_in(prepare_and_fin.phone, prepare_and_fin.password).go_on_site()
    manager.validator.is_main_page()
    manager.open_page_from_sidebar(page='personal_settings') \
        .profile_manager.validator.check_user_info_changing(prepare_and_fin)
    manager.open_page_from_sidebar(page='ext_settings') \
        .profile_manager.validator.check_autocomplete_mode(prepare_and_fin.autocomplete)
    manager.open_page_from_sidebar(page='osago_settings') \
        .profile_manager.validator.check_user_preferences_changing(manager, prepare_and_fin)


@pytest.fixture
def prepare_and_fin(manager):
    Log.trace("ПРИМЕНЕНИЕ ПРЕДУСЛОВИЙ")
    data = CaseData.main_registration_precondition(case_id=1)

    Log.trace("ОТКРЫТИЕ СТРАНИЦЫ РЕГИСТРАЦИИ СО СТРАНИЦЫ АВТОРИЗАЦИИ")
    manager.login_manager.open_login_page()
    manager.registration_manager.open_registration_from_login()

    Log.trace("РЕГИСТРАЦИЯ")
    manager.registration_manager.register(data)
    manager.validator.is_main_page()

    yield data

    manager.open_profile_page_from_upper_menu()
    manager.profile_manager.delete_account() \
        .validator.check_account_deleting(manager.login_manager, data.phone, data.password)
