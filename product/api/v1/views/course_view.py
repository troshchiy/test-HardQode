from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions
from rest_framework.decorators import action

from api.v1.permissions import IsStudentOrIsAdmin, ReadOnlyOrIsAdmin, make_payment
from api.v1.serializers.course_serializer import (CourseSerializer,
                                                  CreateCourseSerializer,
                                                  AvailableCoursesSerializer,
                                                  CreateGroupSerializer,
                                                  CreateLessonSerializer,
                                                  GroupSerializer,
                                                  LessonSerializer)
from courses.models import Course, Group
from users.models import Subscription


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
        response = make_payment(request.user, pk)
        return response


class CourseViewSet(viewsets.ModelViewSet):
    """Курсы """

    queryset = Course.objects.all()
    permission_classes = (ReadOnlyOrIsAdmin,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return CourseSerializer
        return CreateCourseSerializer
