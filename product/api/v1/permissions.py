from rest_framework import status
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.response import Response
from users.models import Subscription, Balance
from courses.models import Course, Group


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


class IsStudentOrIsAdmin(BasePermission):
    def has_permission(self, request, view):
        # TODO
        pass

    def has_object_permission(self, request, view, obj):
        # TODO
        pass


class ReadOnlyOrIsAdmin(BasePermission):

    def has_permission(self, request, view):
        return request.user.is_staff or request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.method in SAFE_METHODS
