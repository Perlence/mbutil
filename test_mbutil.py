import io
import random

import musicbrainzngs as mb
import vcr
import pytest

import mbutil


def test_parse_foobar_clipboard(metallica_raw_tracks, kendrick_raw_tracks):
    assert (mbutil.parse_foobar_clipboard(metallica_raw_tracks[2]) ==
            mbutil.Track('Metallica', 'Garage Inc.', 1, 3, 'Sabbra Cadabra'))
    assert (mbutil.parse_foobar_clipboard(metallica_raw_tracks[19]) ==
            mbutil.Track('Metallica', 'Garage Inc.', 2, 9, 'The Prince'))
    assert (mbutil.parse_foobar_clipboard(kendrick_raw_tracks[5]) ==
            mbutil.Track('Kendrick Lamar', 'good kid, m.A.A.d city', None, 6, 'Poetic Justice'))


def test_dict_groupby():
    assert mbutil.dict_groupby(range(10), lambda x: x % 2) == {0: [0, 2, 4, 6, 8], 1: [1, 3, 5, 7, 9]}


def test_cd_count(metallica_tracks, kendrick_tracks):
    assert mbutil.cd_count(metallica_tracks) == 2
    assert mbutil.cd_count(kendrick_tracks) == 1


def test_track_counts(metallica_tracks, kendrick_tracks):
    assert mbutil.track_counts(metallica_tracks) == (11, 16)
    assert mbutil.track_counts(kendrick_tracks) == (14,)


def test_cli(set_useragent, metallica_raw_tracks, metallica_tracks, kendrick_raw_tracks, kendrick_tracks):
    table = [
        (metallica_raw_tracks, metallica_tracks,
         'Metallica - 1998-11-24 Garage Inc.: Rock; Heavy Metal; Thrash Metal; Metal; Hard Rock'),
        (kendrick_raw_tracks, kendrick_tracks,
         'Kendrick Lamar - 2013-07-19 good kid, m.A.A.d city'),
    ]
    with vcr.use_cassette('fixtures/musicbrainz.yaml', record_mode='once'):
        for raw_tracks, tracks, artist_album in table:
            out = io.StringIO()
            err = io.StringIO()
            mbutil.cli(iter(raw_tracks), out, err)
            assert artist_album in err.getvalue().splitlines()
            assert out.getvalue().splitlines() == list(track.title for track in tracks)

    raw_tracks = metallica_raw_tracks[1:] + kendrick_raw_tracks
    random.shuffle(raw_tracks)
    raw_tracks.insert(0, metallica_raw_tracks[0])
    out = io.StringIO()
    err = io.StringIO()
    with vcr.use_cassette('fixtures/musicbrainz.yaml', record_mode='once'):
        mbutil.cli(iter(raw_tracks), out, err)
    for _, _, artist_album in table:
        assert artist_album in err.getvalue().splitlines()
    assert (out.getvalue().splitlines() ==
            list(track.title for track in metallica_tracks + kendrick_tracks)), \
        'Tracks must be listed on order of album appearence in stdin'


@pytest.fixture
def set_useragent():
    mb.set_useragent('mbutil', '0.1', 'https://github.com/Perlence/mbutil')


@pytest.fixture
def metallica_tracks(metallica_raw_tracks):
    return list(map(mbutil.parse_foobar_clipboard, metallica_raw_tracks))


@pytest.fixture
def kendrick_tracks(kendrick_raw_tracks):
    return list(map(mbutil.parse_foobar_clipboard, kendrick_raw_tracks))


@pytest.fixture
def metallica_raw_tracks():
    return """\
Metallica - [Garage Inc. CD1 #01] Free Speech for the Dumb
Metallica - [Garage Inc. CD1 #02] It's Electric
Metallica - [Garage Inc. CD1 #03] Sabbra Cadabra
Metallica - [Garage Inc. CD1 #04] Turn the Page
Metallica - [Garage Inc. CD1 #05] Die, Die My Darling
Metallica - [Garage Inc. CD1 #06] Loverman
Metallica - [Garage Inc. CD1 #07] Mercyful Fate: Satan's Fall / Curse of the Pharaohs / A Corpse Without Soul / Into the Coven / Evil
Metallica - [Garage Inc. CD1 #08] Astronomy
Metallica - [Garage Inc. CD1 #09] Whiskey in the Jar
Metallica - [Garage Inc. CD1 #10] Tuesday's Gone
Metallica - [Garage Inc. CD1 #11] The More I See
Metallica - [Garage Inc. CD2 #01] Helpless
Metallica - [Garage Inc. CD2 #02] The Small Hours
Metallica - [Garage Inc. CD2 #03] The Wait
Metallica - [Garage Inc. CD2 #04] Crash Course in Brain Surgery
Metallica - [Garage Inc. CD2 #05] Last Caress / Green Hell
Metallica - [Garage Inc. CD2 #06] Am I Evil?
Metallica - [Garage Inc. CD2 #07] Blitzkrieg
Metallica - [Garage Inc. CD2 #08] Breadfan
Metallica - [Garage Inc. CD2 #09] The Prince
Metallica - [Garage Inc. CD2 #10] Stone Cold Crazy
Metallica - [Garage Inc. CD2 #11] So What
Metallica - [Garage Inc. CD2 #12] Killing Time
Metallica - [Garage Inc. CD2 #13] Overkill
Metallica - [Garage Inc. CD2 #14] Damage Case
Metallica - [Garage Inc. CD2 #15] Stone Dead Forever
Metallica - [Garage Inc. CD2 #16] Too Late Too Late
""".splitlines()


@pytest.fixture
def kendrick_raw_tracks():
    return """\
Kendrick Lamar - [good kid, m.A.A.d city #01] Sherane a.k.a. Master Splinter's Daughter
Kendrick Lamar - [good kid, m.A.A.d city #02] Bitch, Don't Kill My Vibe
Kendrick Lamar - [good kid, m.A.A.d city #03] Backseat Freestyle
Kendrick Lamar - [good kid, m.A.A.d city #04] The Art of Peer Pressure
Kendrick Lamar - [good kid, m.A.A.d city #05] Money Trees
Kendrick Lamar - [good kid, m.A.A.d city #06] Poetic Justice
Kendrick Lamar - [good kid, m.A.A.d city #07] good kid
Kendrick Lamar - [good kid, m.A.A.d city #08] m.A.A.d city
Kendrick Lamar - [good kid, m.A.A.d city #09] Swimming Pools (Drank) (extended version)
Kendrick Lamar - [good kid, m.A.A.d city #10] Sing About Me, I'm Dying of Thirst
Kendrick Lamar - [good kid, m.A.A.d city #11] Real
Kendrick Lamar - [good kid, m.A.A.d city #12] Compton
Kendrick Lamar - [good kid, m.A.A.d city #13] Bitch, Don't Kill My Vibe (remix)
Kendrick Lamar - [good kid, m.A.A.d city #14] Bitch, Don't Kill My Vibe (International remix)
""".splitlines()
