from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from squac.permissions import IsAdminOwnerOrPublicReadOnly
from squac.filters import CharInFilter
from squac.mixins import SetUserMixin, PermissionsMixin
from .models import Network, Channel, Group
from nslc.serializers import NetworkSerializer, ChannelSerializer, \
    GroupSerializer, GroupDetailSerializer

"""Filter classes used for view filtering"""

''''
All query values are case insensitive.
perform 'in' query for network param
    /networks?network=uw,uo,cc
perform exact case for station
    /networks?station=rcm
perform regex SQL 'LIKE' for channel
    /networks?channel=ez
'''


class NetworkFilter(filters.FilterSet):
    network = CharInFilter(field_name='code', lookup_expr='in')
    channel = filters.CharFilter(field_name='channels__code')


class ChannelFilter(filters.FilterSet):
    network = CharInFilter(field_name='network__code')
    channel = filters.CharFilter(field_name='code', lookup_expr='iregex')
    station = filters.CharFilter(field_name='station_code')
    location = filters.CharFilter(field_name='loc')
    startafter = filters.CharFilter(field_name='starttime', lookup_expr='gte')
    startbefore = filters.CharFilter(field_name='starttime', lookup_expr='lte')
    endafter = filters.CharFilter(field_name='endtime', lookup_expr='gte')
    endbefore = filters.CharFilter(field_name='endtime', lookup_expr='lte')


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


class BaseNslcViewSet(SetUserMixin, PermissionsMixin, viewsets.ModelViewSet):
    pass


class NetworkViewSet(BaseNslcViewSet):
    serializer_class = NetworkSerializer
    q = Network.objects.all()
    filter_class = NetworkFilter
    queryset = serializer_class.setup_eager_loading(q)


class ChannelViewSet(BaseNslcViewSet):
    filter_class = ChannelFilter
    q = Channel.objects.all()
    serializer_class = ChannelSerializer
    queryset = serializer_class.setup_eager_loading(q)


class GroupViewSet(BaseNslcViewSet):
    serializer_class = GroupSerializer
    queryset = Group.objects.all()
    # commas act as 'ands'
    permission_classes = (
        IsAuthenticated, IsAdminOwnerOrPublicReadOnly)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GroupDetailSerializer
        return self.serializer_class

    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset
        '''view public and own resources'''
        return self.queryset.filter(user=self.request.user) | \
            self.queryset.filter(is_public=True)
