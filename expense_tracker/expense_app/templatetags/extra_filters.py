from django import template

# Регистрация библиотеки шаблонов для создания пользовательских фильтров
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)