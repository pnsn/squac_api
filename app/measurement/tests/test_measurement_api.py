from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from measurement.models import DataSource, Metric, MetricGroup, Threshold,\
                               Alarm

from rest_framework.test import APIClient
from rest_framework import status

'''Tests for all measurement models:
    *

to run only these tests:
    ./mg.sh "test measurement && flake8"
'''


def sample_user(email='test@pnsn.org', password="secret"):
    '''create a sample user for testing'''
    return get_user_model().objects.create_user(email, password)


class PublicMeasurementApiTests(TestCase):
    '''Test the measurement api (public)'''

    def setUp(self):
        self.user = sample_user()
        self.client = APIClient()
        # unauthenticate all public tests
        self.client.force_authenticate(user=None)
        self.datasrc = DataSource.objects.create(
            name='Data source test',
            user=self.user
        )
        self.metric = Metric.objects.create(
            name='Metric test',
            unit='meter',
            datasource=self.datasrc,
            user=self.user
        )
        self.metricgroup = MetricGroup.objects.create(
            name="Metric group test",
            description='Some stuff',
            is_public=True,
            metric=self.metric,
            user=self.user
        )
        self.threshold = Threshold.objects.create(
            name="Threshold test",
            min=2.1,
            max=3.5,
            metricgroup=self.metricgroup,
            user=self.user
        )
        self.alarm = Alarm.objects.create(
            name='Alarm test',
            period=2,
            num_period=3,
            threshold=self.threshold,
            user=self.user
        )

    def test_datasource_res_and_str(self):
        url = reverse(
            'measurement:datasource-detail',
            kwargs={'pk': self.datasrc.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # self.assertEqual(res.data['name'], "Data source test")
        self.assertEqual(str(self.datasrc), "Data source test")

    def test_datasource_post_unauth(self):
        url = reverse('measurement:datasource-list')
        payload = {'name': 'Test'}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_metric_res_and_str(self):
        url = reverse(
            'measurement:metric-detail',
            kwargs={'pk': self.metric.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Metric test')
        self.assertEqual(str(self.metric), 'Metric test')

    def test_metric_post_unauth(self):
        url = reverse('measurement:metric-list')
        payload = {
            'name': 'Test',
            'unit': 'meter',
            'datasource': self.datasrc.id
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_metricgroup_res_and_str(self):
        url = reverse(
            'measurement:metricgroup-detail',
            kwargs={'pk': self.metricgroup.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Metric group test')
        self.assertEqual(str(self.metricgroup), 'Metric group test')

    def test_metricgroup_post_unauth(self):
        url = reverse('measurement:metricgroup-list')
        payload = {
            'name': 'Test',
            'description': 'This is a test',
            'is_public': True,
            'metric': self.metric.id
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_threshold_res_and_str(self):
        url = reverse(
            'measurement:threshold-detail',
            kwargs={'pk': self.threshold.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Threshold test')
        self.assertEqual(str(self.threshold), 'Threshold test')

    def test_threshold_post_unauth(self):
        url = reverse('measurement:threshold-list')
        payload = {
            'name': 'Test',
            'min': 2.1,
            'max': 2.2,
            'metricgroup': self.metricgroup.id
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_alarm_res_and_str(self):
        url = reverse(
            'measurement:alarm-detail',
            kwargs={'pk': self.alarm.id}
        )
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Alarm test')
        self.assertEqual(str(self.alarm), 'Alarm test')

    def test_alarm_post_unauth(self):
        url = reverse('measurement:alarm-list')
        payload = {
            'name': 'Alarm test',
            'period': 2,
            'num_period': 3,
            'threshold': self.threshold
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateMeasurementAPITests(TestCase):
    '''For authenticated tests in measuremnt API'''

    def setUp(self):
        self.client = APIClient()
        self.user = sample_user()
        self.client.force_authenticate(self.user)
        self.datasrc = DataSource.objects.create(
            name='Sample data source',
            user=self.user
        )
        self.metric = Metric.objects.create(
            name='Sample metric',
            unit='furlong',
            datasource=self.datasrc,
            user=self.user
        )
        self.metricgroup = MetricGroup.objects.create(
            name='Sample metric group',
            is_public=True,
            metric=self.metric,
            user=self.user
        )
        self.threshold = Threshold.objects.create(
            name="Sample threshold",
            min=2.1,
            max=3.5,
            metricgroup=self.metricgroup,
            user=self.user
        )

    def test_create_datasource(self):
        url = reverse('measurement:datasource-list')
        payload = {'name': 'Data source test', 'user': self.user}
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        datasource = DataSource.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(datasource, key))

    def test_create_metric(self):
        url = reverse('measurement:metric-list')
        payload = {
            'name': 'Metric test',
            'description': 'Test description',
            'unit': 'meter',
            'datasource': self.datasrc.id,
            'user': self.user
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        metric = Metric.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'datasource':
                self.assertEqual(payload[key], metric.datasource.id)
            else:
                self.assertEqual(payload[key], getattr(metric, key))

    def test_create_metricgroup(self):
        url = reverse('measurement:metricgroup-list')
        payload = {
            'name': 'Group test',
            'description': 'This is a test',
            'is_public': True,
            'metric': self.metric.id
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        metricgroup = MetricGroup.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'metric':
                self.assertEqual(payload[key], metricgroup.metric.id)
            else:
                self.assertEqual(payload[key], getattr(metricgroup, key))

    def test_create_threshold(self):
        url = reverse('measurement:threshold-list')
        payload = {
            'name': 'Test',
            'min': 2.1,
            'max': 2.2,
            'metricgroup': self.metricgroup.id
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        threshold = Threshold.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'metricgroup':
                self.assertEqual(payload[key], threshold.metricgroup.id)
            else:
                self.assertEqual(payload[key], getattr(threshold, key))

    def test_create_alarm(self):
        url = reverse('measurement:alarm-list')
        payload = {
            'name': 'Alarm test',
            'period': 2,
            'num_period': 3,
            'threshold': self.threshold.id
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        alarm = Alarm.objects.get(id=res.data['id'])
        for key in payload.keys():
            if key == 'threshold':
                self.assertEqual(payload[key], alarm.threshold.id)
            else:
                self.assertEqual(payload[key], getattr(alarm, key))
