import os
import re
import mistune


markdown = mistune.Markdown()


def get_container_start_time(
    file_path='./docs_build/index.html',
    pattern=r'^build\sdate\s.*\:\s([0-9\:\s\-]*)'  # noqa
):
    """ Получите время запуска контейнера с помощью регулярного выражения.
    Использует шаблон `pattern` из файла `file_path`.
    Используется в `main_page.py ` для отображения при запуске контейнера docker.

    Аргументы:
        file_path (str): путь к файлу, который содержит необходимую информацию с временной меткой
        pattern (str): шаблон регулярного выражения, который определяет формат
        искомой строки с меткой времени

    В конце `docs_build/index.html "мы можем найти время, когда это будет сделано
    файлы были созданы. И мы можем использовать это время как время запуска контейнера docker

    Возвращать:
        str - строковое представление значения временной метки
    """
    build_date = ''

    if not os.path.exists(file_path):
        return ''

    with open(file_path) as f:
        # выполните итерацию по строкам файла от конца к началу
        for line in reversed(f.readlines()):
            result = re.match(pattern, line, flags=re.IGNORECASE)
            if result:
                build_date = result.group(0)
                break

    return build_date


def get_changelog_preview(changelog_path, version_amount):
    """Возвращает последние изменения из журнала изменений.
    Аргументы:
        changelog_path (str): путь операционной системы к файлу журнала изменений
        version_amount (int): сколько элементов (версий) должен включать предварительный просмотр

    `version_amount` - это количество элементов из файла журнала изменений, таких как:
        # ?.?.? - <номер версии>
        <Описание изменений, которые были внесены для одной задачи>

    Возвращать:
        str - html-строка, сгенерированная из markdown
    """
    changelog_lines = []
    if not os.path.exists(changelog_path):
        return ''

    with open(changelog_path) as f:
        for line in f:
            if re.match(r'^###\s(\d+)\.(\d+)\.(\d+)$', line):  # noqa
                version_amount -= 1

            if version_amount <= 0:
                break

            changelog_lines.append(line)

    if not changelog_lines:
        return ''

    # исключить первую и вторую строки (заголовок журнала изменений и пустую строку)
    changelog_preview = '\n'.join(changelog_lines[2:])

    # создайте html из markdown
    changelog_preview = markdown(changelog_preview)

    return changelog_preview


def get_changelog_html(changelog_name):
    """ Преобразуйте текст журнала изменений в html. """
    changelog_path = f'docs/changelog_{changelog_name}/changelog.md'
    if not os.path.exists(changelog_path):
        return ''

    with open(changelog_path) as file:
        changelog = file.read()

    return markdown(changelog)
