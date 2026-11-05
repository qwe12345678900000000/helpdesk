"""python manage.py seed_demo [--clear] — заполнение базы демонстрационными данными."""
from datetime import timedelta

from django.contrib.auth.models import Group, Permission
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.applicants.models import Applicant
from apps.catalog.models import Category
from apps.tickets.models import Ticket, TicketComment

PASSWORD = "Demo12345!"
R = User.Role

GROUP_PERMS = {
    "Диспетчеры": {"tickets.ticket": ("view", "add", "change"),
                   "tickets.ticketcomment": ("view", "add"),
                   "applicants.applicant": ("view", "add", "change"),
                   "catalog.category": ("view",), "accounts.user": ("view",)},
    "Исполнители": {"tickets.ticket": ("view", "change"),
                    "tickets.ticketcomment": ("view", "add"),
                    "applicants.applicant": ("view",), "catalog.category": ("view",)},
    "Руководители": {"tickets.ticket": ("view",), "tickets.ticketcomment": ("view",),
                     "applicants.applicant": ("view",), "catalog.category": ("view",),
                     "accounts.user": ("view",)},
}

USERS = [
    ("dispatcher", "Смирнова Ольга Викторовна", R.DISPATCHER, "Диспетчер службы поддержки", "Диспетчеры"),
    ("ivanov", "Иванов Сергей Петрович", R.EXECUTOR, "Системный администратор", "Исполнители"),
    ("petrov", "Петров Алексей Игоревич", R.EXECUTOR, "Инженер технической поддержки", "Исполнители"),
    ("sidorova", "Сидорова Мария Андреевна", R.EXECUTOR, "Специалист по ПО", "Исполнители"),
    ("head", "Кузнецов Дмитрий Николаевич", R.HEAD, "Руководитель IT-отдела", "Руководители"),
]

CATEGORIES = [
    ("Оборудование", "Компьютеры, мониторы, проекторы, периферия", "petrov"),
    ("Учётные записи и доступ", "Пароли, доступ к системам и папкам", "ivanov"),
    ("Программное обеспечение", "Установка, обновление и ошибки ПО", "sidorova"),
    ("Сеть и интернет", "Wi-Fi, проводная сеть, почта", "ivanov"),
    ("Печать и МФУ", "Принтеры, сканеры, картриджи", "petrov"),
    ("Прочее", "Обращения без определённой категории", None),
]

APPLICANTS = [
    ("Андреева Елена Викторовна", "Бухгалтерия", "Главный бухгалтер", "104"),
    ("Белов Николай Сергеевич", "Учебная часть", "Заведующий учебной частью", "210"),
    ("Волкова Ирина Олеговна", "Приёмная комиссия", "Секретарь", "101"),
    ("Григорьев Антон Павлович", "Кафедра информатики", "Преподаватель", "305"),
    ("Данилова Светлана Ивановна", "Библиотека", "Библиотекарь", "120"),
    ("Егоров Максим Андреевич", "Отдел кадров", "Специалист по кадрам", "108"),
    ("Жукова Татьяна Николаевна", "Кафедра экономики", "Преподаватель", "312"),
    ("Зайцев Роман Викторович", "Хозяйственный отдел", "Завхоз", "015"),
]

# тема, описание, заявитель, категория, приоритет, канал, итоговый статус, дней назад, часов до решения
TICKETS = [
    ("Не включается компьютер", "После выходных ПК не реагирует на кнопку питания", 0, "Оборудование", "high", "phone", "closed", 9, 3),
    ("Сброс пароля к почте", "Забыла пароль от корпоративной почты", 2, "Учётные записи и доступ", "medium", "portal", "closed", 8, 1),
    ("Установить пакет офисных программ", "Нужен редактор таблиц на ПК в аудитории 305", 3, "Программное обеспечение", "low", "email", "resolved", 7, 20),
    ("Нет Wi-Fi в библиотеке", "Ноутбуки читателей не видят сеть", 4, "Сеть и интернет", "high", "visit", "resolved", 6, 12),
    ("Замятие бумаги в МФУ", "МФУ в бухгалтерии постоянно зажёвывает бумагу", 0, "Печать и МФУ", "medium", "phone", "closed", 6, 5),
    ("Доступ к папке «Кадры»", "Нужен доступ к сетевой папке отдела кадров", 5, "Учётные записи и доступ", "medium", "portal", "resolved", 5, 30),
    ("Не работает проектор", "Проектор в ауд. 210 не выводит изображение", 1, "Оборудование", "critical", "phone", "in_progress", 1, None),
    ("Ошибка при запуске 1С", "При запуске появляется ошибка лицензии", 0, "Программное обеспечение", "high", "email", "in_progress", 2, None),
    ("Медленный интернет", "Страницы открываются очень долго", 6, "Сеть и интернет", "low", "portal", "waiting", 2, None),
    ("Заменить картридж", "Принтер печатает бледно", 4, "Печать и МФУ", "low", "portal", "in_progress", 1, None),
    ("Новый сотрудник — учётная запись", "Создать учётную запись для нового преподавателя", 5, "Учётные записи и доступ", "medium", "email", "in_progress", 0, None),
    ("Шумит системный блок", "Сильный шум вентилятора в каб. 015", 7, "Оборудование", "low", "visit", "in_progress", 0, None),
    ("Подключить второй монитор", "Нужен второй монитор для приёмной комиссии", 2, "Прочее", "medium", "portal", "new", 0, None),
    ("Не открывается электронный журнал", "Сайт журнала выдаёт ошибку 502", 6, "Программное обеспечение", "critical", "phone", "in_progress", 0, None),
]


class Command(BaseCommand):
    help = "Заполняет базу демонстрационными данными (роли, сотрудники, справочники, обращения)"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true",
                            help="Удалить обращения, заявителей и категории перед заполнением")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            TicketComment.objects.all().delete()
            Ticket.objects.all().delete()
            Applicant.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write("Старые данные удалены.")

        groups = self.create_groups()
        users = self.create_users(groups)
        categories = self.create_categories(users)
        applicants = self.create_applicants()
        count = self.create_tickets(users, categories, applicants)

        try:
            cache.clear()
        except Exception:
            pass
        self.stdout.write(self.style.SUCCESS(
            f"Готово: сотрудников {len(users)}, категорий {len(categories)}, "
            f"заявителей {len(applicants)}, обращений {count}. Пароль демо-пользователей: {PASSWORD}"
        ))

    def create_groups(self):
        groups = {}
        for name, spec in GROUP_PERMS.items():
            group, _ = Group.objects.get_or_create(name=name)
            perms = []
            for label, actions in spec.items():
                app_label, model = label.split(".")
                for act in actions:
                    perms.append(Permission.objects.get(content_type__app_label=app_label,
                                                        content_type__model=model,
                                                        codename=f"{act}_{model}"))
            group.permissions.set(perms)
            groups[name] = group
        return groups

    def create_users(self, groups):
        users = {}
        for username, fio, role, position, group in USERS:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(PASSWORD)
            user.full_name, user.role, user.position = fio, role, position
            user.email = f"{username}@college.local"
            user.is_staff = True
            user.save()
            user.groups.set([groups[group]])
            users[username] = user
        return users

    def create_categories(self, users):
        result = {}
        for name, descr, executor in CATEGORIES:
            cat, _ = Category.objects.update_or_create(
                name=name, defaults={"description": descr,
                                     "default_executor": users.get(executor) if executor else None})
            result[name] = cat
        return result

    def create_applicants(self):
        result = []
        for i, (fio, dep, pos, room) in enumerate(APPLICANTS, start=1):
            app, _ = Applicant.objects.get_or_create(
                full_name=fio, defaults={"department": dep, "position": pos, "room": room,
                                         "phone": f"+7 (495) 100-20-{i:02d}",
                                         "email": f"user{i}@college.local"})
            result.append(app)
        return result

    def create_tickets(self, users, categories, applicants):
        if Ticket.objects.exists():
            self.stdout.write("Обращения уже есть — пропускаю (используйте --clear).")
            return Ticket.objects.count()
        dispatcher = users["dispatcher"]
        now = timezone.now()
        for subject, descr, app_idx, cat, prio, channel, final, days_ago, hours in TICKETS:
            t = Ticket(subject=subject, description=descr, applicant=applicants[app_idx],
                       category=categories[cat], priority=prio, channel=channel,
                       created_by=dispatcher)
            t.save()
            executor = t.executor
            if final == "waiting":
                t.change_status("waiting", user=executor, comment="Запрошены уточнения у заявителя")
            if final in ("resolved", "closed"):
                t.change_status("resolved", user=executor, resolution="Проблема устранена, работа проверена")
            if final == "closed":
                t.change_status("closed", user=dispatcher, comment="Заявитель подтвердил решение")

            # «сдвигаем» даты в прошлое, чтобы отчёты выглядели реалистично
            created = now - timedelta(days=days_ago, hours=2)
            fields = {"created_at": created, "deadline": created + timedelta(hours=t.sla_hours)}
            if hours is not None:
                fields["resolved_at"] = created + timedelta(hours=hours)
                if final == "closed":
                    fields["closed_at"] = created + timedelta(hours=hours + 2)
            Ticket.objects.filter(pk=t.pk).update(**fields)
            last = fields.get("closed_at") or fields.get("resolved_at") or created + timedelta(minutes=30)
            for i, c in enumerate(t.comments.order_by("id")):
                moment = created if i == 0 else min(last, created + timedelta(minutes=15 * i))
                TicketComment.objects.filter(pk=c.pk).update(created_at=moment)
        return len(TICKETS)
