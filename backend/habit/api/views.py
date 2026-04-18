from logging import log
from urllib import request

from django.shortcuts import render

from rest_framework import viewsets
from .models import *
from .serializers import *

from rest_framework.permissions import IsAuthenticated

# Create your views here.

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

class HabitViewSet(viewsets.ModelViewSet):
    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        habit = self.get_object()
        today = timezone.now().date()

        log, created = HabitLog.objects.get_or_create(habit=habit, date=today)

        if not created:
            return Response({'message': 'Already completed today'})

        log.is_completed = True
        log.value = 1
        log.save()

        streak = 0
        current_day = today

        while HabitLog.objects.filter(
            habit=habit,
            date=current_day,
            is_completed=True
        ).exists():
            streak += 1
            current_day -= timedelta(days=1)

        return Response({
            'message': 'Habit completed',
            'streak': streak
        })
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        habit = self.get_object()
        
        logs = HabitLog.objects.filter(
            habit=habit,
            is_completed=True
        ).order_by('-date')    

        total_completed = logs.count()

        current_streak = 0
        today = timezone.now().date()
        day = today

        while HabitLog.objects.filter(
            habit=habit,
            date=day,
            is_completed=True
        ).exists():
            current_streak += 1
            day -= timedelta(days=1)

        longest_streak = 0
        temp_streak = 0
        prev_date = None

        logs_asc = logs.order_by('date')

        for log in logs_asc:
            if prev_date is None:
                temp_streak = 1
            elif (log.date - prev_date).days == 1:
                temp_streak += 1
            else:
                temp_streak = 1

            longest_streak = max(longest_streak, temp_streak)
            prev_date = log.date

        return Response({
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'total_completed': total_completed
        })
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        today = timezone.now().date()

        habits = self.get_queryset()

        data = []

        for habit in habits:
            completed = HabitLog.objects.filter(
                habit=habit,
                date=today,
                is_completed=True
            ).exists()

            data.append({
                "id": habit.id,
                "name": habit.name,
                "completed": completed
            })

        return Response(data)
                

from rest_framework.views import APIView
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth

class StatisticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start = request.GET.get('start')
        end = request.GET.get('end')
        group_by = request.GET.get('group_by', 'day')

        logs = HabitLog.objects.filter(
            habit__user=request.user,
            is_completed=True
        )

        if start:
            logs = logs.filter(date__gte=start)
        if end:
            logs = logs.filter(date__lte=end)

        if group_by == 'week':
            logs = logs.annotate(period=TruncWeek('date'))
        elif group_by == 'month':
            logs = logs.annotate(period=TruncMonth('date'))
        else:
            logs = logs.annotate(period=TruncDay('date'))

        habit_id = request.GET.get('habit')
        if habit_id:
            logs = logs.filter(habit_id=habit_id)

        data = logs.values('period').annotate(total=Count('id')).order_by('period')
        total_completed = logs.count()

        serializers = StatisticsSerializer(data, many=True)
        return Response({
            "data": serializers.data,
            "total_completed": total_completed
        })





class HabitLogViewSet(viewsets.ModelViewSet):
    queryset = HabitLog.objects.all()
    serializer_class = HabitLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return HabitLog.objects.filter(habit__user=self.request.user)