from collections import OrderedDict, namedtuple, defaultdict
from itertools import groupby
import re
import sys

import musicbrainzngs as mb
from titlecase import titlecase

MIN_SCORE = 80


def main():
    mb.set_useragent('mbutil', '0.1', 'https://github.com/Perlence/mbutil')
    try:
        cli(iter(sys.stdin), sys.stdout, sys.stderr)
    except KeyboardInterrupt:
        sys.exit(0)


def cli(it, out, err):
    lines = list(it)
    parsed_tracks = list(map(parse_foobar_clipboard, lines))
    track_dict_by_artist_album = dict_groupby(parsed_tracks, lambda t: (t.artist, t.album), mapping=OrderedDict)
    tracks_by_artist_album = groupby(parsed_tracks, lambda t: (t.artist, t.album))
    indexed_tracks = defaultdict(dict)  # {(artist, album): {(discnumber, tracknumber): mbtrack}}
    for (artist, album), track_iter in tracks_by_artist_album:
        if (artist, album) not in indexed_tracks:
            release = pick_release(track_dict_by_artist_album[(artist, album)])
            if release is None:
                print('ERROR: nothing found for {} - {}'.format(artist, album), file=err)
                continue
            release_with_recordings = mb.get_release_by_id(release['id'], includes=['recordings'])

            print(album_information(release), file=err)

            # Index received tracks
            for discnumber, medium in enumerate(release_with_recordings['release']['medium-list'], start=1):
                for tracknumber, mbtrack in enumerate(medium['track-list'], start=1):
                    indexed_tracks[(artist, album)][(discnumber, tracknumber)] = mbtrack

        for track in track_iter:
            mbtrack = indexed_tracks[(artist, album)][(track.discnumber or 1, track.track)]
            print(fix_quote(mbtrack['recording']['title']), file=out)


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


def pick_release(tracks):
    tracks_on_cds = track_counts(tracks)
    cd_count = len(tracks_on_cds)
    track = tracks[0]
    search_results = mb.search_releases(artist=track.artist, release=track.album, limit=10)
    for release in search_results['release-list']:
        # Search score must be at least MIN_SCORE
        if int(release['ext:score']) < MIN_SCORE:
            break

        # Number of CDs must match
        if release['medium-count'] != cd_count:
            continue

        # Number of tracks in each CD must match
        if not tuple(m['track-count'] for m in release['medium-list']) == tracks_on_cds:
            continue

        return release


def track_counts(tracks):
    """Find out how many CDs and tracks on each CD in the given list of
    *tracks*."""
    key = lambda t: t.discnumber or 1  # noqa
    groups = groupby(sorted(tracks, key=key), key=key)
    return tuple(len(list(ts)) for _, ts in groups)


def album_information(release):
    """Format one-line album information."""
    tags = release.get('tag-list')
    result = '{artist-credit-phrase} - '.format(**release)
    if 'date' in release:
        result += '{date} '.format(**release)
    result += '{title}'.format(**release)
    if tags:
        result += ': ' + '; '.join(titlecase(tag['name']) for tag in release['tag-list'])
    return result


def fix_quote(s):
    return s.replace("’", "'")


if __name__ == '__main__':
    main()
