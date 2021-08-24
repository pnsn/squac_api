from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response
from django_filters import rest_framework as filters
from squac.filters import CharInFilter, NumberInFilter
from measurement.aggregates.percentile import Percentile
from django.db.models import (Avg, StdDev, Min, Max, Count, FloatField,
                              Subquery)
from django.db.models.functions import (Coalesce, Abs, Least, Greatest)
from squac.mixins import (SetUserMixin, DefaultPermissionsMixin,
                          AdminOrOwnerPermissionMixin)
from .exceptions import MissingParameterException
from .models import (Metric, Measurement, Threshold,
                     Alert, ArchiveDay, ArchiveWeek, ArchiveMonth,
                     ArchiveHour, Monitor, Trigger)
from measurement import serializers
from silk.profiling.profiler import silk_profile


def check_measurement_params(params):
    '''ensure that each request for measurements/archives and aggs has:
        * channel or group
        * metric
        * starttime
        * endtime
    '''
    if 'channel' not in params and 'group' not in params or \
            (not all([p in params
                      for p in ("metric", "starttime", "endtime")])):
        raise MissingParameterException


'''Filters'''


class MetricFilter(filters.FilterSet):
    # CharInFilter is custom filter see imports
    name = CharInFilter(lookup_expr='in')


class ThresholdFilter(filters.FilterSet):
    class Meta:
        model = Threshold
        fields = ('metric', 'widget')


class MeasurementFilter(filters.FilterSet):
    """filters measurment by metric, channel, starttime,
        and endtime (starttime)"""
    starttime = filters.CharFilter(field_name='starttime', lookup_expr='gte')

    ''' Note although param is called endtime, it uses starttime, which is
        the the only field with an index
    '''
    endtime = filters.CharFilter(field_name='starttime', lookup_expr='lt')
    metric = NumberInFilter(field_name='metric')
    channel = NumberInFilter(field_name='channel')
    group = NumberInFilter(field_name='channel__group')


class MonitorFilter(filters.FilterSet):
    class Meta:
        model = Monitor
        fields = ('channel_group', 'metric')


class TriggerFilter(filters.FilterSet):
    class Meta:
        model = Trigger
        fields = ('monitor',)


class AlertFilter(filters.FilterSet):
    class Meta:
        model = Alert
        fields = ('trigger', 'in_alarm')


'''Base Viewsets'''


class MeasurementBaseViewSet(SetUserMixin, DefaultPermissionsMixin,
                             viewsets.ModelViewSet):
    pass


class MonitorBaseViewSet(SetUserMixin, AdminOrOwnerPermissionMixin,
                         viewsets.ModelViewSet):
    '''only owner can see monitors and alert'''
    pass


class ArchiveBaseViewSet(DefaultPermissionsMixin,
                         viewsets.ReadOnlyModelViewSet):
    """Viewset that provides access to Archive data

        since there is not a user set on archive, all permissions will be
        model
    """
    filter_class = MeasurementFilter

    def list(self, request, *args, **kwargs):
        check_measurement_params(request.query_params)
        return super().list(self, request, *args, **kwargs)


'''Viewsets'''


class MetricViewSet(MeasurementBaseViewSet):
    serializer_class = serializers.MetricSerializer
    filter_class = MetricFilter

    def get_queryset(self):
        return Metric.objects.all()

    @silk_profile(name='Dispatch metrics')
    @method_decorator(cache_page(60 * 10))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class MeasurementViewSet(MeasurementBaseViewSet):
    '''end point for using channel filter'''
    serializer_class = serializers.MeasurementSerializer
    filter_class = MeasurementFilter

    def get_queryset(self):
        q = Measurement.objects.all()
        return self.serializer_class.setup_eager_loading(q)
        # return

    @silk_profile(name='GET Measurements')
    def list(self, request, *args, **kwargs):
        '''We want to be careful about large queries so require params'''
        check_measurement_params(request.query_params)
        return super().list(self, request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        '''Create single or bulk measurements'''
        many = isinstance(request.data, list)
        serializer = self.get_serializer(data=request.data, many=many)
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED,
                            headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ThresholdViewSet(MonitorBaseViewSet):
    serializer_class = serializers.ThresholdSerializer
    filter_class = ThresholdFilter

    def get_queryset(self):
        return Threshold.objects.all()


class MonitorViewSet(MonitorBaseViewSet):
    serializer_class = serializers.MonitorSerializer
    filter_class = MonitorFilter

    def get_queryset(self):
        queryset = Monitor.objects.all()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return serializers.MonitorDetailSerializer
        return self.serializer_class


class TriggerViewSet(MonitorBaseViewSet):
    serializer_class = serializers.TriggerSerializer
    filter_class = TriggerFilter

    def get_queryset(self):
        queryset = Trigger.objects.all()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)


class AlertViewSet(MonitorBaseViewSet):
    serializer_class = serializers.AlertSerializer
    filter_class = AlertFilter

    def get_queryset(self):
        queryset = Alert.objects.all().order_by('-timestamp')
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return serializers.AlertDetailSerializer
        return self.serializer_class


class ArchiveHourViewSet(ArchiveBaseViewSet):
    serializer_class = serializers.ArchiveHourSerializer

    def get_queryset(self):
        return ArchiveHour.objects.all()


class ArchiveDayViewSet(ArchiveBaseViewSet):
    serializer_class = serializers.ArchiveDaySerializer

    def get_queryset(self):
        return ArchiveDay.objects.all()


class ArchiveWeekViewSet(ArchiveBaseViewSet):
    serializer_class = serializers.ArchiveWeekSerializer

    def get_queryset(self):
        return ArchiveWeek.objects.all()


class ArchiveMonthViewSet(ArchiveBaseViewSet):
    serializer_class = serializers.ArchiveMonthSerializer

    def get_queryset(self):
        return ArchiveMonth.objects.all()


class AggregatedViewSet(IsAuthenticated, viewsets.ViewSet):
    ''' calculate aggregates from raw data
        this is NOT a model viewset so filter_class and serializer_class
        cannot be used
    '''

    def list(self, request):
        params = request.query_params
        check_measurement_params(params)
        measurements = Measurement.objects.all()
        # determine if this is a list of channels or list of channel groups
        try:
            channels = [int(x) for x in params['channel'].split(',')]
            measurements = measurements.filter(channel__in=channels)
        except KeyError:
            '''list of channel groups'''
            groups = [int(x) for x in params['group'].split(',')]
            measurements = measurements.filter(
                channel__group__in=groups)

        metrics = [int(x) for x in params['metric'].split(',')]
        measurements = measurements.filter(metric__in=metrics)
        measurements = measurements.filter(
            starttime__gte=params['starttime']).filter(
            starttime__lt=params['endtime']).order_by('-starttime')
        aggs = measurements.values(
            'channel', 'metric').annotate(
                mean=Avg('value'),
                median=Percentile('value', percentile=0.5),
                min=Min('value'),
                max=Max('value'),
                minabs=Least(Abs(Min('value')), Abs(Max('value'))),
                maxabs=Greatest(Abs(Min('value')), Abs(Max('value'))),
                stdev=Coalesce(StdDev('value', sample=True), 0,
                               output_field=FloatField()),
                p05=Percentile('value', percentile=0.05),
                p10=Percentile('value', percentile=0.10),
                p90=Percentile('value', percentile=0.90),
                p95=Percentile('value', percentile=0.95),
                num_samps=Count('value'),
                starttime=Min('starttime'),
                endtime=Max('endtime'),
                latest=Subquery(measurements.values('value')[:1])

        )
        serializer = serializers.AggregatedSerializer(
            instance=aggs, many=True)
        return Response(serializer.data)
