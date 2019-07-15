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


def test_track_counts(metallica_tracks, kendrick_tracks):
    assert mbutil.track_counts(metallica_tracks) == (11, 16)
    assert mbutil.track_counts(kendrick_tracks) == (14,)

    shuffled_metallica_tracks = metallica_tracks[:]
    random.shuffle(shuffled_metallica_tracks)
    assert mbutil.track_counts(shuffled_metallica_tracks) == (11, 16), \
        'Track counts must be correct even if tracks are unordered'


def test_album_information():
    release = {
        'artist-credit-phrase': 'Yyrkoon',
        'title': 'Dying Sun',
    }
    assert mbutil.album_information(release) == 'Yyrkoon - Dying Sun'


def test_cli_tracks(set_useragent, metallica_raw_tracks, metallica_tracks, kendrick_raw_tracks, kendrick_tracks, custom_vcr):
    table = [
        (metallica_raw_tracks, metallica_tracks,
         'Metallica - 1998-11-24 Garage Inc.: Rock; Heavy Metal; Thrash Metal; Metal; Hard Rock'),
        (kendrick_raw_tracks, kendrick_tracks,
         'Kendrick Lamar - 2013-07-19 good kid, m.A.A.d city'),
    ]
    with custom_vcr.use_cassette('fixtures/musicbrainz.yaml'):
        for raw_tracks, tracks, artist_album in table:
            out = io.StringIO()
            err = io.StringIO()
            mbutil.cli([], iter(raw_tracks), out, err)
            assert err.getvalue().splitlines() == [artist_album]
            assert out.getvalue().splitlines() == list(track.title for track in tracks)

    raw_tracks = metallica_raw_tracks[1:] + kendrick_raw_tracks
    random.shuffle(raw_tracks)
    raw_tracks.insert(0, metallica_raw_tracks[0])
    out = io.StringIO()
    err = io.StringIO()
    with custom_vcr.use_cassette('fixtures/musicbrainz.yaml'):
        mbutil.cli([], iter(raw_tracks), out, err)
    assert err.getvalue().splitlines() == [artist_album for _, _, artist_album in table]
    assert out.getvalue().splitlines() == [mbutil.parse_foobar_clipboard(raw_track).title for raw_track in raw_tracks], \
        'Tracks must be listed in order of their appearance in stdin'

    out = io.StringIO()
    err = io.StringIO()
    with custom_vcr.use_cassette('fixtures/musicbrainz.yaml'):
        mbutil.cli([], iter(['sfaluijhfsdkjlhfs - [vnielwslcns] ierkjifdnhajk']), out, err)
    assert (err.getvalue().splitlines() == ['ERROR: nothing found for sfaluijhfsdkjlhfs - vnielwslcns']), \
        'Must print error message if no releases were found'


def test_cli_artists(set_useragent, kanye_raw_tracks, kanye_artists, custom_vcr):
    out = io.StringIO()
    err = io.StringIO()
    with custom_vcr.use_cassette('fixtures/musicbrainz.yaml'):
        mbutil.cli(['--artist'], iter(kanye_raw_tracks), out, err)
    assert out.getvalue().splitlines() == kanye_artists
    assert err.getvalue().splitlines() == ['Kanye West - 2005-09-21 The College Dropout']


def test_cli_missing(set_useragent, bityoq_raw_tracks, tool_raw_tracks, custom_vcr):
    bityoq_titles = [mbutil.parse_foobar_clipboard(track).title for track in bityoq_raw_tracks]
    tool_titles = [mbutil.parse_foobar_clipboard(track).title for track in tool_raw_tracks]
    it = iter([*bityoq_raw_tracks, *tool_raw_tracks])
    out = io.StringIO()
    err = io.StringIO()
    with custom_vcr.use_cassette('fixtures/musicbrainz.yaml'):
        mbutil.cli([], it, out, err)
    assert out.getvalue().splitlines() == [*bityoq_titles, *tool_titles]
    assert err.getvalue().splitlines() == [
        'ERROR: nothing found for Bityoq Casdwe - Teoid',
        'Tool - 2001 Lateralus',
    ]

    bityoq_artists = [mbutil.parse_foobar_clipboard(track).artist for track in bityoq_raw_tracks]
    tool_artists = [mbutil.parse_foobar_clipboard(track).artist for track in tool_raw_tracks]
    it = iter([*bityoq_raw_tracks, *tool_raw_tracks])
    out = io.StringIO()
    err = io.StringIO()
    with custom_vcr.use_cassette('fixtures/musicbrainz.yaml'):
        mbutil.cli(['--artist'], it, out, err)
    assert out.getvalue().splitlines() == [*bityoq_artists, *tool_artists]
    assert err.getvalue().splitlines() == [
        'ERROR: nothing found for Bityoq Casdwe - Teoid',
        'Tool - 2001 Lateralus',
    ]


@pytest.fixture
def set_useragent():
    mb.set_useragent('mbutil', '0.1', 'https://github.com/Perlence/mbutil')


@pytest.fixture
def custom_vcr():
    def unordered_query(r1, r2):
        return dict(r1.query) == dict(r2.query)
    v = vcr.VCR()
    # v = vcr.VCR(record_mode='new_episodes')
    v.register_matcher('unordered_query', unordered_query)
    v.match_on = ['method', 'scheme', 'host', 'port', 'path', 'unordered_query']
    return v


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


@pytest.fixture
def tool_raw_tracks():
    return """\
Tool - [Lateralus #1] The Grudge
Tool - [Lateralus #2] Eon Blue Apocalypse
Tool - [Lateralus #3] The Patient
Tool - [Lateralus #4] Mantra
Tool - [Lateralus #5] Schism
Tool - [Lateralus #6] Parabol
Tool - [Lateralus #7] Parabola
Tool - [Lateralus #8] Ticks & Leeches
Tool - [Lateralus #9] Lateralus
Tool - [Lateralus #10] Disposition
Tool - [Lateralus #11] Reflection
Tool - [Lateralus #12] Triad
Tool - [Lateralus #13] Faaip de Oiad
""".splitlines()


@pytest.fixture
def kanye_raw_tracks():
    return """\
Kanye West - [The College Dropout #01] Intro
Kanye West - [The College Dropout #02] We Don't Care
Kanye West - [The College Dropout #03] Graduation Day
Kanye West - [The College Dropout #04] All Falls Down
Kanye West - [The College Dropout #05] I'll Fly Away
Kanye West - [The College Dropout #06] Spaceship
Kanye West - [The College Dropout #07] Jesus Walks
Kanye West - [The College Dropout #08] Never Let Me Down
Kanye West - [The College Dropout #09] Get Em High
Kanye West - [The College Dropout #10] Workout Plan
Kanye West - [The College Dropout #11] The New Workout Plan
Kanye West - [The College Dropout #12] Slow Jamz
Kanye West - [The College Dropout #13] Breathe In Breathe Out
Kanye West - [The College Dropout #14] School Spirit (skit 1)
Kanye West - [The College Dropout #15] School Spirit
Kanye West - [The College Dropout #16] School Spirit (skit 2)
Kanye West - [The College Dropout #17] Lil Jimmy (skit)
Kanye West - [The College Dropout #18] Two Words
Kanye West - [The College Dropout #19] Through the Wire
Kanye West - [The College Dropout #20] Family Business
Kanye West - [The College Dropout #21] Last Call
Kanye West - [The College Dropout #22] Heavy Hitters
""".splitlines()


@pytest.fixture
def kanye_artists():
    return """\
Kanye West
Kanye West
Kanye West
Kanye West; Syleena Johnson
Kanye West
Kanye West; GLC; Consequence
Kanye West
Kanye West; JAY-Z; J. Ivy
Kanye West; Talib Kweli; Common
Kanye West
Kanye West
Kanye West; Twista; Jamie Foxx
Kanye West; Ludacris
Kanye West
Kanye West
Kanye West
Kanye West
Kanye West; Mos Def; Freeway; The Boys Choir of Harlem
Kanye West
Kanye West
Kanye West
Kanye West; GLC
""".splitlines()


@pytest.fixture
def bityoq_raw_tracks():
    return """\
Bityoq Casdwe - [Teoid #01] No. 1
Bityoq Casdwe - [Teoid #02] No. 2
Bityoq Casdwe - [Teoid #03] No. 3
Bityoq Casdwe - [Teoid #04] No. 4
Bityoq Casdwe - [Teoid #05] No. 5
Bityoq Casdwe - [Teoid #06] No. 6
Bityoq Casdwe - [Teoid #07] No. 7
Bityoq Casdwe - [Teoid #08] No. 8
Bityoq Casdwe - [Teoid #09] No. 9
""".splitlines()
