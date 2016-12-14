from collections import OrderedDict, namedtuple
from itertools import groupby
from queue import Queue
import re
import threading
import time
import sys

import musicbrainzngs as mb
from titlecase import titlecase

WORKERS = 5


def main():
    mb.set_useragent('mbutil', '0.1', 'https://github.com/Perlence/mbutil')
    try:
        cli(iter(sys.stdin), sys.stdout, sys.stderr)
    except KeyboardInterrupt:
        sys.exit(0)


def cli(it, out, err):
    lines = list(it)
    tracks = map(parse_foobar_clipboard, lines)
    by_artist_album = dict_groupby(tracks, lambda t: (t.artist, t.album), mapping=OrderedDict)

    q = Queue()
    threads = []
    for _ in range(WORKERS):
        th = quickthread(worker, q)
        threads.append(th)

    deferreds = []
    try:
        for (artist, album), tracks in by_artist_album.items():
            deferred = Queue(1)
            q.put((tracks, deferred))
            deferreds.append((artist, album, deferred))
            time.sleep(1)
    finally:
        for _ in range(WORKERS):
            q.put(None)

    for artist, album, deferred in deferreds:
        release, release_with_recordings, e = deferred.get()
        if e is not None:
            raise e
        if release is None:
            print('ERROR: nothing found for {} - {}'.format(artist, album), file=err)
            continue
        tags = release.get('tag-list', None)
        print('{} - {} {}'.format(release['artist-credit-phrase'], release['date'], release['title']),
              end='' if tags else None, file=err)
        if tags:
            print(': ' + '; '.join(titlecase(tag['name']) for tag in release['tag-list']), file=err)
        for medium in release_with_recordings['release']['medium-list']:
            for track in medium['track-list']:
                print(fix_quote(track['recording']['title']), file=out)

    for th in threads:
        th.join()


def parse_foobar_clipboard(line):
    mo = TRACK_RE.match(line)
    if mo is None:
        return
    artist = mo.group('artist')
    album = mo.group('album')
    discnumber = mo.group('discnumber')
    track = mo.group('track')
    title = mo.group('title')
    if discnumber is not None:
        discnumber = int(discnumber)
    if track is not None:
        track = int(track)
    return Track(artist, album, discnumber, track, title)


TRACK_RE = re.compile(r'(?P<artist>.+) - \['
                      r'(?P<album>.+?)'
                      r'(?: CD(?P<discnumber>\d+))?'
                      r'(?: \#(?P<track>\d+))?\]\s'
                      r'(?P<title>.+)')

Track = namedtuple('Track', 'artist, album, discnumber, track, title')


def dict_groupby(iterable, key, mapping=dict):
    result = mapping()
    for item in iterable:
        result.setdefault(key(item), []).append(item)
    return result


def quickthread(fn, *args, **kwargs):
    name = kwargs.pop('__name', None)
    th = threading.Thread(
        name=name,
        target=fn,
        args=args,
        kwargs=kwargs)
    th.daemon = True
    th.start()
    return th


def worker(q):
    while True:
        try:
            task = q.get()
            if task is None:
                break
            tracks, deferred = task
            release = pick_release(tracks)
            if release is None:
                deferred.put((None, None, None))
                continue
            release_with_recordings = mb.get_release_by_id(release['id'], includes=['recordings'])
            deferred.put((release, release_with_recordings, None))
        except Exception as e:
            deferred.put((None, None, e))


def pick_release(tracks):
    cdc = cd_count(tracks)
    tcs = track_counts(tracks)
    track = tracks[0]
    search_results = mb.search_releases(artist=track.artist, release=track.album, limit=10)
    for release in search_results['release-list']:
        # Number of CDs must match
        if release['medium-count'] != cdc:
            continue

        # Number of tracks in each CD must match
        if not all(medium['track-count'] == track_count
                   for medium, track_count in zip(release['medium-list'], tcs)):
            continue

        return release
    else:
        if search_results['release-list']:
            return search_results['release-list'][0]


def cd_count(tracks):
    return max(track.discnumber or 1 for track in tracks)


def track_counts(tracks):
    groups = groupby(tracks, lambda t: t.discnumber or 1)
    return tuple(len(list(ts)) for _, ts in groups)


def fix_quote(s):
    return s.replace("’", "'")


if __name__ == '__main__':
    main()
