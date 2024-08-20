from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from sqlparse.engine.grouping import group

from api.v1.permissions import IsStudentOrIsAdmin, ReadOnlyOrIsAdmin
from api.v1.serializers.course_serializer import (CourseSerializer,
                                                  CreateCourseSerializer,
                                                  AvailableCoursesSerializer,
                                                  CreateGroupSerializer,
                                                  CreateLessonSerializer,
                                                  GroupSerializer,
                                                  LessonSerializer)
from api.v1.serializers.user_serializer import SubscriptionSerializer
from courses.models import Course, Group
from users.models import Subscription, Balance


class LessonViewSet(viewsets.ModelViewSet):
    """Уроки."""

    permission_classes = (IsStudentOrIsAdmin,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return LessonSerializer
        return CreateLessonSerializer

    def perform_create(self, serializer):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer.save(course=course)

    def get_queryset(self):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        return course.lessons.all()


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
                user_balance.bonuses=user_balance.bonuses - course.price
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


class CourseViewSet(viewsets.ModelViewSet):
    """Курсы """

    queryset = Course.objects.all()
    permission_classes = (ReadOnlyOrIsAdmin,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CourseSerializer
        return CreateCourseSerializer
