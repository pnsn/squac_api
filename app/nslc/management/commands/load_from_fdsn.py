"""
Command run without any options will give default URL
    http://service.iris.edu/irisws/fedcatalog/1/
        query?datacenter=IRISDMC,NCEDC,SCEDC
        &targetservice=station
        &level=channel
        &net=AZ,BC,BK,CC,CE,CI,CN,IU,NC,NN,NP,NV,OO,SN,UO,US,UW
        &sta=*
        &cha=?N?,?H?
        &loc=*
        &minlat=31.5
        &maxlat=50
        &minlon=-128.1
        &maxlon=-113.8930
        &endafter=YYYY-MM-DD (Current date)
        &format=text

load channels from fdsn webservice run in docker-compose like:
$:docker-compose run --rm app sh -c "LOADER_EMAIL=email@pnsn.org \
                    python manage.py load_from_fdsn
                    [optional args]
                    --path='.'
                    --datacenter='IRISDMC,...'
                    --sta='BEER,...'
                    --cha='HN?,ENN,...'
                    --loc=*
                    --minlat=31.5
                    --maxlat=50
                    --minlon=-128.1
                    --maxlon=-113.9
                    --endtime=[YYYY-mm-dd]"

 text response from fdsn has following schema:
 Network | Station | Location | Channel | Latitude | Longitude |
 Elevation | Depth | Azimuth | Dip | SensorDescription | Scale |
 ScaleFreq | ScaleUnits | SampleRate | StartTime | EndTime
"""
import csv
import requests
import sys
import os
from datetime import datetime
import pytz
import django
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from nslc.models import Network, Channel


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default='.',
            help="path to app root dir"
        )
        parser.add_argument(
            '--datacenter',
            default="IRISDMC,NCEDC,SCEDC",
            help="Comma seperated list of datacenters"
        )
        parser.add_argument(
            '--sta',
            default="*",
            help="Comma separated regex for stations, * default"
        )
        parser.add_argument(
            '--cha',
            default="?N?,?H?",
            help="Comma separated regex for channel code, ? wildcard, ?N?,?H?\
                default"
        )
        parser.add_argument(
            '--loc',
            default="*",
            help="Comma separated regex for locations, * default"
        )
        parser.add_argument(
            '--minlat',
            default=31.5,
            help="Lower latitude for search box, 31.5 default"
        )
        parser.add_argument(
            '--maxlat',
            default=50,
            help="Upper latitude for search box, 50 default"
        )
        parser.add_argument(
            '--minlon',
            default=-128.1,
            help="Left latitude for search box, -128.1 default"
        )
        parser.add_argument(
            '--maxlon',
            default=-113.893,
            help="Right latitude for search box, -113.893 default"
        )
        parser.add_argument(
            '--endafter',
            default=datetime.now().strftime("%Y-%m-%d"),
            help="filter for channels with offdates greater than datetime if\
                missing, defaults to datetime.now()"
        )

    def build_url(self, params, level):
        ''' create url based on params
            documentation at https://service.iris.edu/fdsnws/station/1/
        '''
        url = (
            f"http://service.iris.edu/irisws/fedcatalog/1/query?"
            f"datacenter={params['datacenter']}"
            f"&targetservice=station"
            f"&level={level}"
            f"&net={params['net']}"
            f"&endafter={params['endafter']}"
            "&format=text"
        )
        if (level != "network"):
            url += (
                f"&sta={params['sta']}"
                f"&cha={params['cha']}"
                f"&loc={params['loc']}"
                f"&minlat={params['minlat']}"
                f"&maxlat={params['maxlat']}"
                f"&minlon={params['minlon']}"
                f"&maxlon={params['maxlon']}"
            )
        return url

    def parse_datetime(self, datetime_str):
        ''' parse datetime from string of form
            # 2599-12-31T23:59:59
            return datetime
        '''
        year, month, day_time = datetime_str.split("-")
        day, time = day_time.split("T")
        hour, minute, sec = time.split(":")
        return datetime(int(year), int(month), int(day), int(hour),
                        int(minute), int(sec[:2]), tzinfo=pytz.UTC)

    '''Django command to check network and channel tables with FDSN service'''
    def handle(self, *args, **options):
        ALLOWED_NETWORKS = [
            "AZ", "BC", "BK", "CC", "CE", "CI", "CN", "IU", "NC", "NN", "NP",
            "NV", "OO", "SN", "UO", "US", "UW"
        ]
        options["net"] = ','.join(ALLOWED_NETWORKS)
        print('Getting data from FDSN...')
        LOADER_EMAIL = os.environ.get('LOADER_EMAIL')
        if not LOADER_EMAIL:
            print(
                "You must provide a valid email by setting the LOADER_EMAIL "
                "environmental variable."
            )
            sys.exit(1)
        project_path = options['path']
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'squac.settings')
        sys.path.append(project_path)
        django.setup()
        try:
            user = get_user_model().objects.get(email=LOADER_EMAIL)
        except ObjectDoesNotExist:
            print(
                f"Loader email {LOADER_EMAIL} does not exist.\n"
                "You must provide a valid email by setting the LOADER_EMAIL "
                "environmental variable."
            )
            sys.exit(1)

        network_url = self.build_url(options, "network")
        with requests.Session() as s:
            download = s.get(network_url)
            decoded_content = download.content.decode('utf-8')
            content = csv.reader(decoded_content.splitlines(), delimiter='|')
            row_list = list(content)
            # skip header rows in metadata
            for row in row_list[1:]:
                # extract data from row
                if len(row) > 1:
                    net_code = row[0]
                    net_name = row[1]

                    # Get or create the channel using data
                    Network.objects.get_or_create(
                        code=net_code.lower(),
                        defaults={
                            'name': net_name,
                            'user': user
                        }
                    )

        networks = {}
        for n in Network.objects.all():
            networks[n.code.lower()] = n

        station_url = self.build_url(options, 'station')
        stations = {}
        with requests.Session() as s:
            download = s.get(station_url)
            decoded_content = download.content.decode('utf-8')
            content = csv.reader(decoded_content.splitlines(), delimiter='|')
            row_list = list(content)
            # skip first two rows of metadata
            for row in row_list[1:]:
                if len(row) > 1:
                    sta_code = row[1].lower()
                    sta_name = row[5]
                    stations[sta_code] = sta_name

        channel_url = self.build_url(options, 'channel')
        try:
            with requests.Session() as s:
                download = s.get(channel_url)
                decoded_content = download.content.decode('utf-8')
                content = csv.reader(
                    decoded_content.splitlines(), delimiter='|')
                row_list = list(content)
                # skip header rows in metadata
                for row in row_list[1:]:
                    # extract data from row
                    if len(row) > 1:
                        net_code, sta, loc, cha, lat, lon, elev, *rem = row
                        depth, azimuth, dip, sensor_descr, scale, *rem = rem
                        freq, units, rate, start, end = rem
                        net = networks[net_code.lower()]

                        # Get or create the channel using data
                        Channel.objects.get_or_create(
                            network=net,
                            station_code=sta.lower(),
                            loc='--' if not loc else loc.lower(),
                            code=cha.lower(),
                            defaults={
                                'lat': float(lat),
                                'lon': float(lon),
                                'elev': float(elev),
                                'depth': float(depth),
                                'name': stations[sta_code.lower()],
                                'azimuth': 0.0 if not azimuth else float(
                                    azimuth),
                                'dip': 0.0 if not dip else float(dip),
                                'sensor_description': sensor_descr,
                                'scale': 0.0 if not scale else float(scale),
                                'scale_freq': 0.0 if not freq else float(freq),
                                'scale_units': units,
                                'sample_rate': 0.0 if not rate else float(
                                    rate),
                                'starttime': self.parse_datetime(start),
                                'endtime': self.parse_datetime(end),
                                'user': user,
                            }
                        )
        except KeyError:
            print('Key error occured')
        print('Loading finished')
