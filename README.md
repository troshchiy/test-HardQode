
# Тестовое задание Django/Backend

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray) ![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)

Проект представляет собой площадку для размещения онлайн-курсов с набором уроков. Доступ к урокам предоставляется после покупки курса (подписки). Внутри курса студенты автоматически распределяются по группам.

Перед тем, как приступить к выполнению задания, советуем изучить документацию, которая поможет в выполнении заданий:

1. https://docs.djangoproject.com/en/4.2/intro/tutorial01/
2. https://docs.djangoproject.com/en/4.2/topics/db/models/
3. https://docs.djangoproject.com/en/4.2/topics/db/queries/
4. https://docs.djangoproject.com/en/4.2/ref/models/querysets/
5. https://docs.djangoproject.com/en/4.2/topics/signals/
6. https://www.django-rest-framework.org/tutorial/quickstart/
7. https://www.django-rest-framework.org/api-guide/viewsets/
8. https://www.django-rest-framework.org/api-guide/serializers/

# Построение системы для обучения

Суть задания заключается в проверке знаний построения связей в БД и умении правильно строить запросы без ошибок N+1.

### Построение архитектуры(5 баллов)

В этом задании у нас есть 4 бизнес-задачи на хранение:

1. Создать сущность продукта. У продукта должен быть создатель этого продукта(автор/преподаватель). Название продукта, дата и время старта, стоимость. **(0,5 балла)**

`courses/models.py`:
```commandline
class Course(models.Model):
    """Модель продукта - курса."""

    author = models.CharField(
        max_length=250,
        verbose_name='Автор',
    )
    title = models.CharField(
        max_length=250,
        verbose_name='Название',
    )
    start_date = models.DateTimeField(
        auto_now=False,
        auto_now_add=False,
        verbose_name='Дата и время начала курса'
    )
    price = models.PositiveIntegerField(
        verbose_name='Стоимость'
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name='Доступен'
    )

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ('-id',)

    def __str__(self):
        return self.title
```
2. Определить, каким образом мы будем понимать, что у пользователя(клиент/студент) есть доступ к продукту. **(2 балла)**

`users/models.py`:
```commandline
class Subscription(models.Model):
    """Модель подписки пользователя на курс."""

    student = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Студент'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        verbose_name='Курс'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('-id',)
```
3. Создать сущность урока. Урок может принадлежать только одному продукту. В уроке должна быть базовая информация: название, ссылка на видео. **(0,5 балла)**

`courses/models.py`:
```commandline
class Lesson(models.Model):
    """Модель урока."""

    title = models.CharField(
        max_length=250,
        verbose_name='Название',
    )
    link = models.URLField(
        max_length=250,
        verbose_name='Ссылка',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Курс'
    )

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ('id',)

    def __str__(self):
        return self.title
```
4. Создать сущность баланса пользователя. Баланс пользователя не может быть ниже 0, баланс пользователя при создании пользователя равен 1000 бонусов. Бонусы могут начислять только через админку или посредством REST-апи с правами is_staff=True. **(2 балла)**

`users/models.py`:
```commandline
class Balance(models.Model):
    """Модель баланса пользователя."""

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name='Студент'
    )
    bonuses = models.PositiveIntegerField(
        default=1000,
        verbose_name='Бонусы'
    )

    class Meta:
        verbose_name = 'Баланс'
        verbose_name_plural = 'Балансы'
        ordering = ('-id',)
```

### Реализация базового сценария оплат (11 баллов)

В этом пункте потребуется использовать выполненную вами в прошлом задании архитектуру:

1. Реализовать API на список продуктов, доступных для покупки(доступных к покупке = они еще не куплены пользователем и у них есть флаг доступности), которое бы включало в себя основную информацию о продукте и количество уроков, которые принадлежат продукту. **(2 балла)**

`api/v1/serializers/course_serializer.py`:
```commandline
class AvailableCoursesSerializer(serializers.ModelSerializer):
    """Список курсов, доступных для покупки."""

    lessons_count = serializers.SerializerMethodField(read_only=True)

    def get_lessons_count(self, obj):
        """Количество уроков в курсе."""
        return obj.lessons.count()

    class Meta:
        model = Course
        fields = (
            'id',
            'author',
            'title',
            'start_date',
            'price',
            'lessons_count',
        )
```
`api/v1/serializers/course_view.py`:
```
class AvailableCoursesViewSet(viewsets.ModelViewSet):
    """Курсы, доступные для покупки."""

    serializer_class = AvailableCoursesSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        # Список курсов, купленных пользователем
        bought_courses = Subscription.objects.filter(student=self.request.user).values_list('course')
        # Курсы, доступные к покупке = они еще не куплены пользователем и у них есть флаг доступности
        available_courses = Course.objects.exclude(id__in=bought_courses).filter(is_available=True)

        for course in available_courses.all():
            course_groups = Group.objects.filter(course=course)
            # Исключаем курсы, в которых не осталось свободных мест
            # т.е. в каждой из 10 групп курсы заполнены все 30 мест
            if course_groups.count() == 10 and not [group for group in course_groups if group.students_amount < 30]:
                available_courses = available_courses.exclude(pk=course.pk)

        return available_courses

    @action(
        methods=['post'],
        detail=True,
        permission_classes=(permissions.IsAuthenticated,)
    )
    def pay(self, request, pk):
        """Покупка доступа к курсу (подписка на курс)."""
        response = make_payment(request.user, pk)
        return response
```
2. Реализовать API оплаты продукты за бонусы. Назовем его …/pay/ **(3 балла)**

`api/v1/permissions.py`:
```commandline
def make_payment(request, pk):
    course = Course.objects.get(pk=pk)
    course_groups = Group.objects.filter(course=course)
    user_balance = Balance.objects.get(user=request.user)
    # Курс еще не куплен и у него есть флаг доступности
    if not Subscription.objects.filter(student=request.user, course=pk) and course.is_available:
        # Проверка, есть ли свободные места в потоке этого курса
        if course_groups.count() == 10 and not [group for group in course_groups if group.students_amount < 30]:
            return Response(
                data={'detail': 'There are no vacancies in the course groups'},
                status=status.HTTP_409_CONFLICT
            )

        if user_balance.bonuses >= course.price:
            user_balance.bonuses = user_balance.bonuses - course.price
            user_balance.save()
            subscription = Subscription(student=request.user, course=course)
            subscription.save()
            return Response(
                data={'detail': 'Subscription created successfully'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                data={'detail': 'There are not enough bonuses on the balance'},
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
    else:
        return Response(
            data={'detail': 'The course is already bought'},
            status=status.HTTP_409_CONFLICT
        )
```
3. По факту оплаты и списания бонусов с баланса пользователя должен быть открыт доступ к курсу. **(2 балла)**

`api/v1/permissions.py`:
```commandline
            ...
            user_balance.bonuses = user_balance.bonuses - course.price
            user_balance.save()
            subscription = Subscription(student=request.user, course=course)
            subscription.save()
            return Response(
                data={'detail': 'Subscription created successfully'},
                status=status.HTTP_201_CREATED
            )
            ...
```
4. После того, как доступ к курсу открыт, пользователя необходимо **равномерно** распределить в одну из 10 групп студентов. **(4 балла)**

'courses/signals.py':
```commandline
@receiver(post_save, sender=Subscription)
def post_save_subscription(sender, instance: Subscription, created, **kwargs):
    """Распределение нового студента в группу курса."""

    if created:
        user = CustomUser.objects.get(pk=instance.student.pk)
        groups = Group.objects.filter(course=instance.course).annotate(u_count=Count('users')).order_by('u_count')
        # Если создано меньше 10 групп, создаем новую группу для равномерного распределения
        if groups.count() < 10:
            new_group = Group(name=f'Group {groups.count()+1}', course=instance.course)
            new_group.save()
        else:    # Если созданы все 10 групп, добавляем пользователя в наименее заполненную
            user.groups.add(groups[0])
```

### Результат выполнения:

1. Выполненная архитектура на базе данных SQLite с использованием Django.
2. Реализованные API на базе готовой архитектуры.

### Мы ожидаем:

Ссылка на публичный репозиторий в GitHub с выполненным проектом.

** Нельзя форкать репозиторий. Используйте git clone. **



## Если вы все сделали, но хотите еще, то можете реализовать API для отображения статистики по продуктам. 
Необходимо отобразить список всех продуктов на платформе, к каждому продукту приложить информацию:

1. Количество учеников занимающихся на продукте.
2. На сколько % заполнены группы? (среднее значение по количеству участников в группах от максимального значения участников в группе, где максимальное = 30).
3. Процент приобретения продукта (рассчитывается исходя из количества полученных доступов к продукту деленное на общее количество пользователей на платформе).

`api/v1/serializers/course_serializer.py`:
```commandline
   class CourseSerializer(serializers.ModelSerializer):
    """Список курсов."""

    lessons = MiniLessonSerializer(many=True, read_only=True)
    students_count = serializers.SerializerMethodField(read_only=True)
    groups_filled_percent = serializers.SerializerMethodField(read_only=True)
    demand_course_percent = serializers.SerializerMethodField(read_only=True)


    def get_students_count(self, obj):
        """Общее количество студентов на курсе."""
        return Subscription.objects.filter(course=obj).count()

    def get_groups_filled_percent(self, obj):
        """Процент заполнения групп, если в группе максимум 30 чел."""
        groups = Group.objects.filter(course=obj)
        average = round(sum(g.users.count() for g in groups) / 30 * 100)
        return average

    def get_demand_course_percent(self, obj):
        """Процент приобретения курса."""
        course_subscribtions = Subscription.objects.filter(course=obj).count()
        total_users = CustomUser.objects.all().count()
        return round(course_subscribtions / total_users * 100)

    class Meta:
        model = Course
        fields = (
            'id',
            'author',
            'title',
            'start_date',
            'price',
            'lessons',
            'demand_course_percent',
            'students_count',
            'groups_filled_percent',
        )
```

`api/v1/views/course_view.py`:
```
class CourseViewSet(viewsets.ModelViewSet):
    """Курсы """

    queryset = Course.objects.all()
    permission_classes = (ReadOnlyOrIsAdmin,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CourseSerializer
        return CreateCourseSerializer
```

За это задание не ставится баллов, но при выборе между 2 кандидатами - оно нам поможет.


## __Установка на локальном компьютере__
1. Клонируйте репозиторий:
    ```
    git clone git@github.com:hqcamp/test-backend-3.git
    ```
2. Установите и активируйте виртуальное окружение:
    ```
    python -m venv venv
    source venv/Scripts/activate  - для Windows
    source venv/bin/activate - для Linux
    ```
3. Установите зависимости:
    ```
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    ```
4. Перейдите в папку product и выполните миграции:
    ```
    cd product
    python manage.py migrate
    ```
5. Создайте суперпользователя:
    ```
    python manage.py createsuperuser
    ```
6. Запустите проект:
    ```
    python manage.py runserver
    ```

### __OpenAPI документация__
* Swagger: http://127.0.0.1:8000/api/v1/swagger/
* ReDoc: http://127.0.0.1:8000/api/v1/redoc/


## Доп. задание
### __Реализуйте следующее API__

<details><summary> GET: http://127.0.0.1:8000/api/v1/courses/  - показать список всех курсов.</summary>

    200 OK:
    ```
    [
        {
            "id": 3,
            "author": "Михаил Потапов",
            "title": "Backend developer",
            "start_date": "2024-03-03T12:00:00Z",
            "price": "150000",
            "lessons_count": 0,
            "lessons": [],
            "demand_course_percent": 0,
            "students_count": 0,
            "groups_filled_percent": 0
        },
        {
            "id": 2,
            "author": "Михаил Потапов",
            "title": "Python developer",
            "start_date": "2024-03-03T12:00:00Z",
            "price": "120000",
            "lessons_count": 3,
            "lessons": [
                {
                    "title": "Урок №1"
                },
                {
                    "title": "Урок №2"
                },
                {
                    "title": "Урок №3"
                }
            ],
            "demand_course_percent": 84,
            "students_count": 10,
            "groups_filled_percent": 83
        },
        {
            "id": 1,
            "author": "Иван Петров",
            "title": "Онлайн курс",
            "start_date": "2024-03-03T12:00:00Z",
            "price": "56000",
            "lessons_count": 3,
            "lessons": [
                {
                    "title": "Урок №1"
                },
                {
                    "title": "Урок №2"
                },
                {
                    "title": "Урок №3"
                }
            ],
            "demand_course_percent": 7,
            "students_count": 1,
            "groups_filled_percent": 10
        }
    ]
    ```
</details>

`api/v1/serializers/course_serializer.py`:
```commandline
   class CourseSerializer(serializers.ModelSerializer):
    """Список курсов."""

    lessons = MiniLessonSerializer(many=True, read_only=True)
    students_count = serializers.SerializerMethodField(read_only=True)
    groups_filled_percent = serializers.SerializerMethodField(read_only=True)
    demand_course_percent = serializers.SerializerMethodField(read_only=True)


    def get_students_count(self, obj):
        """Общее количество студентов на курсе."""
        return Subscription.objects.filter(course=obj).count()

    def get_groups_filled_percent(self, obj):
        """Процент заполнения групп, если в группе максимум 30 чел."""
        groups = Group.objects.filter(course=obj)
        average = round(sum(g.users.count() for g in groups) / 30 * 100)
        return average

    def get_demand_course_percent(self, obj):
        """Процент приобретения курса."""
        course_subscribtions = Subscription.objects.filter(course=obj).count()
        total_users = CustomUser.objects.all().count()
        return round(course_subscribtions / total_users * 100)

    class Meta:
        model = Course
        fields = (
            'id',
            'author',
            'title',
            'start_date',
            'price',
            'lessons',
            'demand_course_percent',
            'students_count',
            'groups_filled_percent',
        )
```

`api/v1/views/course_view.py`:
```
class CourseViewSet(viewsets.ModelViewSet):
    """Курсы """

    queryset = Course.objects.all()
    permission_classes = (ReadOnlyOrIsAdmin,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CourseSerializer
        return CreateCourseSerializer
```

<details><summary> GET: http://127.0.0.1:8000/api/v1/courses/2/groups/  - показать список групп определенного курса.</summary> 

    200 OK:
    ```
    [
        {
            "title": "Группа №3",
            "course": "Python developer",
            "students": [
                {
                    "first_name": "Иван",
                    "last_name": "Грозный",
                    "email": "user9@user.com"
                },
                {
                    "first_name": "Корней",
                    "last_name": "Чуковский",
                    "email": "user8@user.com"
                },
                {
                    "first_name": "Максим",
                    "last_name": "Горький",
                    "email": "user7@user.com"
                }
            ]
        },
        {
            "title": "Группа №2",
            "course": "Python developer",
            "students": [
                {
                    "first_name": "Ольга",
                    "last_name": "Иванова",
                    "email": "user6@user.com"
                },
                {
                    "first_name": "Саша",
                    "last_name": "Иванов",
                    "email": "user5@user.com"
                },
                {
                    "first_name": "Дмитрий",
                    "last_name": "Иванов",
                    "email": "user4@user.com"
                }
            ]
        },
        {
            "title": "Группа №1",
            "course": "Python developer",
            "students": [
                {
                    "first_name": "Андрей",
                    "last_name": "Петров",
                    "email": "user10@user.com"
                },
                {
                    "first_name": "Олег",
                    "last_name": "Петров",
                    "email": "user3@user.com"
                },
                {
                    "first_name": "Сергей",
                    "last_name": "Петров",
                    "email": "user2@user.com"
                },
                {
                    "first_name": "Иван",
                    "last_name": "Петров",
                    "email": "user@user.com"
                }
            ]
        }
    ]
    ```
</details>

`api/v1/serializers/course_serializer.py`:
```commandline
class StudentSerializer(serializers.ModelSerializer):
    """Студенты курса."""

    class Meta:
        model = CustomUser
        fields = (
            'first_name',
            'last_name',
            'email',
        )


class GroupSerializer(serializers.ModelSerializer):
    """Список групп."""

    students = StudentSerializer(many=True, read_only=True, source='users')

    class Meta:
        model = Group
        fields = (
            'title',
            'course',
            'students',
        )
```

`api/v1/views/course_view.py`:
```commandline
class GroupViewSet(viewsets.ModelViewSet):
    """Группы."""

    permission_classes = (permissions.IsAdminUser,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return GroupSerializer
        return CreateGroupSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        return course.groups.all()
```

### __Технологии__
* [Python 3.10.12](https://www.python.org/doc/)
* [Django 4.2.10](https://docs.djangoproject.com/en/4.2/)
* [Django REST Framework  3.14.0](https://www.django-rest-framework.org/)
* [Djoser  2.2.0](https://djoser.readthedocs.io/en/latest/getting_started.html)
