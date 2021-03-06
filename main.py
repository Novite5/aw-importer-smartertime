import csv
from datetime import datetime, timedelta, timezone
import secrets
import json

from tabulate import tabulate

from aw_core.models import Event


def parse(filepath):
    events = []
    with open(filepath, 'r') as f:
        c = csv.DictReader(f)
        for r in c:
            # print(r)
            dt = datetime.fromtimestamp(float(r['Timestamp']) / 1000)
            tz_h, tz_m = map(int, r['Time'].split("GMT+")[1].split()[0].split(":"))
            dt = dt.replace(tzinfo=timezone(timedelta(hours=tz_h, minutes=tz_m)))
            td = timedelta(milliseconds=float(r['Duration ms']))
            e = Event(timestamp=dt, duration=td, data={
                'activity': r['Activity'],
                'device': r['Device'],
                'place': r['Place'],
                'room': r['Room'],
            })
            events.append(e)
    return events


def import_as_bucket(filepath):
    events = parse(filepath)
    end = max(e.timestamp + e.duration for e in events)
    bucket = {
        'id': f'smartertime_export_{end.date()}_{secrets.token_hex(4)}',
        'events': events,
        'data': {
            'readonly': True,
        }
    }
    return bucket


def print_info(bucket):
    events = bucket['events']
    print(bucket['id'])
    print(bucket['data'])
    rows = []
    for a in ['Messenger', 'Plex', 'YouTube', 'Firefox', 'reddit', 'call:']:
        rows.append([a, sum((e.duration for e in events if a in e.data['activity']), timedelta(0))])
    print(tabulate(rows, ['title', 'time']))


def default(o):
    if hasattr(o, 'isoformat'):
        return o.isoformat()
    elif hasattr(o, 'total_seconds'):
        return o.total_seconds()
    else:
        raise NotImplementedError


def save_bucket(bucket):
    with open(bucket['id'] + ".awbucket.json", 'w') as f:
        json.dump(bucket, f, indent=True, default=default)


if __name__ == '__main__':
    bucket = import_as_bucket('timeslots.csv')
    save_bucket(bucket)
    print_info(bucket)
