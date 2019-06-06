from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.authentication import TokenAuthentication, \
    SessionAuthentication

from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Network, Station, Location, Channel
from nslc.serializers import NetworkSerializer, StationSerializer, \
    LocationSerializer, ChannelSerializer
import django_filters as filters

"""Common methods for filtering classes to share"""


def in_sql(queryset, name, value):
    """perform generic 'in' SQL statement exp

    select * from networks where code in ('uw', 'uo')
    """

    if name is not None:
        values = value.lower().split(",")
        name_in = '__'.join([name, 'in'])
        queryset = queryset.filter(**{name_in: values})
    return queryset


def regex_sql(queryset, name, value):
    """perform python regex searches on field"""
    if name is not None:
        name_regex = '__'.join([name, 'iregex'])
        queryset = queryset.filter(**{name_regex: value})
    return queryset


"""Filter classes used for view filtering"""


class NetworkFilter(filters.FilterSet):
    network = filters.CharFilter(
        field_name='code', method=in_sql)
    station = filters.CharFilter(
        field_name='stations__code', lookup_expr='iexact')
    location = filters.CharFilter(
        field_name='station__locations__code', lookup_expr='iexact')
    channel = filters.CharFilter(
        field_name='stations__locations__channels__code', method=regex_sql)


class StationFilter(filters.FilterSet):
    network = filters.CharFilter(
        field_name='network__code', method=in_sql)
    station = filters.CharFilter(
        field_name='code', lookup_expr='iexact')
    location = filters.CharFilter(
        field_name='locations__code', lookup_expr='iexact')
    channel = filters.CharFilter(
        field_name='locations__channels__code', method=regex_sql)


class LocationFilter(filters.FilterSet):
    network = filters.CharFilter(
        field_name='station__network__code', method=in_sql)
    station = filters.CharFilter(
        field_name='station__code', lookup_expr='iexact')
    location = filters.CharFilter(
        field_name='code', lookup_expr='iexact')
    channel = filters.CharFilter(
        field_name='channel_code', method=regex_sql)


class ChannelFilter(filters.FilterSet):
    network = filters.CharFilter(
        field_name='location__station__network__code', method=in_sql)
    station = filters.CharFilter(
        field_name='location__station__code', lookup_expr='iexact')
    location = filters.CharFilter(
        field_name='location__code', lookup_expr='iexact')
    channel = filters.CharFilter(
        field_name='code', method=regex_sql)


@api_view(['GET'])
def api_root(request, format=None):
    '''api root'''
    return Response({
        'nets': reverse('network-list', request=request, format=format),
    })


"""model viewset include all CRUD methods:
    retrieve
    list
    update
    partial_update
    destory
"""


class ObjPermissionOrReadOnly(BasePermission):
    """Object-level permission on scarey methods, read only on safe methods """

    def has_permission(self, request, view):
        '''http permission?'''

        if request.method in SAFE_METHODS:
            return True
        # user must be authenticated
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        '''object level permissions, set by adding user to group

        Read permissions are allowed to any request,
        so we'll always allow GET, HEAD or OPTIONS requests.
        '''
        if request.method in SAFE_METHODS:
            return True

        # user must have permission
        return self.check_object_permissions(request, obj)


class BaseNslcViewSet(viewsets.ModelViewSet):
    '''base class for all nslc viewsets:

     Permissions are IsAuthticatedOrReadOnly
        This allows auth user to fully crud but unathorized user to view
        all data
     '''
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (ObjPermissionOrReadOnly, )
    # permisssion_classes = (IsAuthenticatedOrReadOnly, )

    # all models have require an auth user, set on create
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NetworkViewSet(BaseNslcViewSet):
    serializer_class = NetworkSerializer
    filter_class = NetworkFilter
    q = Network.objects.all()
    queryset = serializer_class.setup_eager_loading(q)


class StationViewSet(BaseNslcViewSet):
    serializer_class = StationSerializer
    filter_class = StationFilter
    q = Station.objects.all()
    queryset = serializer_class.setup_eager_loading(q)


class LocationViewSet(BaseNslcViewSet):
    serializer_class = LocationSerializer
    filter_class = LocationFilter
    q = Location.objects.all()
    queryset = serializer_class.setup_eager_loading(q)


class ChannelViewSet(BaseNslcViewSet):
    serializer_class = ChannelSerializer
    filter_class = ChannelFilter
    q = Channel.objects.all()
    queryset = serializer_class.setup_eager_loading(q)
