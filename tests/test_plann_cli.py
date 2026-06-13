## Check https://click.palletsprojects.com/en/8.1.x/testing/

## TODO!  add some tests

import json
from unittest.mock import patch

from click.testing import CliRunner

from plann.cli import cli


class FakeCalendar:
    def __init__(self, ident):
        self.ident = ident
        self.url = f"http://example.com/cal/{ident}/"

    def get_display_name(self):
        return f"calendar {self.ident}"


def fake_find_calendars(args, raise_errors):
    """
    Mimics the relevant bits of plann.lib.find_calendars: only "connects"
    if some caldav_* connection info is given, and honors calendar_url /
    calendar_name if given - otherwise returns "all" calendars.
    """
    if not args.get('caldav_url'):
        return []
    if args.get('calendar_url'):
        return [FakeCalendar(x) for x in args['calendar_url']]
    if args.get('calendar_name'):
        return [FakeCalendar(x) for x in args['calendar_name']]
    return [FakeCalendar(i) for i in range(6)]


@patch("plann.cli.find_calendars", side_effect=fake_find_calendars)
def test_calendar_url_overrides_config(mock_find_calendars, tmp_path):
    """
    --calendar-url given on the command line should narrow down the
    calendar selection even when the caldav connection details come from
    the config file, rather than being silently ignored.
    """
    config_file = tmp_path / "calendar.conf"
    config_file.write_text(json.dumps({
        "default": {
            "caldav_url": "https://dav.example.com/",
            "caldav_user": "someuser",
            "caldav_pass": "somepass",
        }
    }))

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--calendar-url=http://example.com/cal/the-one/',
        '-c', str(config_file),
        'list-calendars',
    ])

    assert result.exit_code == 0
    assert 'calendar http://example.com/cal/the-one/' in result.output
    ## without the fix, all 6 calendars from the config's "default" section
    ## would be returned, ignoring --calendar-url
    for i in range(6):
        assert f'calendar {i} ' not in result.output


@patch("plann.cli.find_calendars", side_effect=fake_find_calendars)
def test_calendar_name_overrides_config(mock_find_calendars, tmp_path):
    """
    --calendar-name should override the config file's calendar selection,
    same as --calendar-url.
    """
    config_file = tmp_path / "calendar.conf"
    config_file.write_text(json.dumps({
        "default": {
            "caldav_url": "https://dav.example.com/",
            "caldav_user": "someuser",
            "caldav_pass": "somepass",
        }
    }))

    runner = CliRunner()
    result = runner.invoke(cli, [
        '--calendar-name=birthdays',
        '-c', str(config_file),
        'list-calendars',
    ])

    assert result.exit_code == 0
    assert 'calendar birthdays' in result.output
    for i in range(6):
        assert f'calendar {i} ' not in result.output
