#!/usr/bin/env python3
"""Unit tests for VesselFinder origin/destination/ETA extraction and merge logic."""
from datetime import date
from bs4 import BeautifulSoup

from scraper import (
    extract_from_vesselfinder,
    extract_shipnext_eta_and_transit,
    merge_voyage_ports,
    parse_eta_relative,
    parse_eta_text_to_iso,
)


VESSELFINDER_FIXTURE = """
<html><body>
  <div class="vi__r1 vi__sbt">
    <div class="vilabel">Destination</div>
    <a class="_npNa" href="/ports/CAANI001">Annacis Island, Canada</a>
    <div class="_value">
      <span class="_mcol12ext">ETA: Dec 2, 04:00</span>
      <span class="_arrTde">(in 13 days)</span>
    </div>
  </div>
  <div class="vi__r1 vi__stp">
    <div class="vilabel">Last Port</div>
    <a class="_npNa" href="/ports/JPKWS001">Kawasaki, Japan</a>
    <div class="_value">
      ATD: Nov 17, 07:19 UTC
      <span class="_arrTde">(2 days ago)</span>
    </div>
  </div>
  <div id="djson" data-json='{"ship_lat":35,"ship_lon":141}'></div>
</body></html>
"""

SHIPNEXT_TRANSIT_FIXTURE = (
    "According to the latest AIS and Satellite data, the ship is currently "
    "on route to Kawasaki, Japan. Estimated time of arrival at Kawasaki, "
    "Japan is 16-11-2026 at 20:20. Ship's current position is 037° 32' 23\" N."
)


def test_extract_from_vesselfinder():
    soup = BeautifulSoup(VESSELFINDER_FIXTURE, 'html.parser')
    data = extract_from_vesselfinder(soup)
    assert data is not None
    assert data['location_text'] == 'Annacis Island, Canada'
    assert data['origin_city'] == 'Kawasaki, Japan'
    assert data['eta_text'] == 'Dec 2, 04:00'
    assert data['eta_days'] == 13
    assert data['in_transit'] is True
    assert data['eta'] is not None
    assert data['latitude'] == 35.0
    assert data['longitude'] == 141.0
    print("✓ VesselFinder fixture extracts destination, last port, and ETA countdown")


def test_merge_overrides_stale_shipnext_ports():
    shipnext = {
        'location_text': 'Kawasaki, Japan',
        'origin_city': 'Gamagori, Japan',
        'latitude': 37.36,
        'longitude': 146.94,
        'eta_text': '16-11-2026 20:20',
        'eta': '2026-11-16',
        'eta_days': -3,
        'in_transit': True,
    }
    vesselfinder = {
        'location_text': 'Annacis Island, Canada',
        'origin_city': 'Kawasaki, Japan',
        'latitude': 35.0,
        'longitude': 141.0,
        'eta_text': 'Dec 2, 04:00',
        'eta': '2026-12-02',
        'eta_days': 13,
        'in_transit': True,
    }
    merged = merge_voyage_ports(shipnext, vesselfinder)
    assert merged['location_text'] == 'Annacis Island, Canada'
    assert merged['origin_city'] == 'Kawasaki, Japan'
    # Prefer precise ShipNext coordinates when present
    assert merged['latitude'] == 37.36
    assert merged['longitude'] == 146.94
    assert merged['eta_text'] == 'Dec 2, 04:00'
    assert merged['eta'] == '2026-12-02'
    assert merged['eta_days'] == 13
    assert merged['in_transit'] is True
    print("✓ Merge overrides stale ShipNext ports/ETA and keeps ShipNext coordinates")


def test_parse_eta_relative():
    assert parse_eta_relative('(in 13 days)') == 13
    assert parse_eta_relative('(in 1 day)') == 1
    assert parse_eta_relative('(in 5 hours)') == 0
    assert parse_eta_relative('(2 days ago)') == -2
    assert parse_eta_relative('(arrived)') == -1
    assert parse_eta_relative('(today)') == 0
    assert parse_eta_relative('nonsense') is None
    print("✓ Relative ETA strings parse to day offsets")


def test_parse_eta_text_to_iso():
    assert parse_eta_text_to_iso('Dec 2, 04:00', reference_date=date(2026, 11, 19)) == '2026-12-02'
    # Year omitted and date appears past -> roll to next year
    assert parse_eta_text_to_iso('Jan 5, 04:00', reference_date=date(2026, 11, 19)) == '2027-01-05'
    assert parse_eta_text_to_iso('16-11-2026') == '2026-11-16'
    print("✓ ETA text parses to ISO dates with year inference")


def test_extract_shipnext_eta_and_transit():
    data = extract_shipnext_eta_and_transit(SHIPNEXT_TRANSIT_FIXTURE)
    assert data['in_transit'] is True
    assert data['eta_text'] == '16-11-2026 20:20'
    assert data['eta'] == '2026-11-16'
    print("✓ ShipNext voyage prose yields ETA date and in-transit flag")


if __name__ == '__main__':
    test_extract_from_vesselfinder()
    test_merge_overrides_stale_shipnext_ports()
    test_parse_eta_relative()
    test_parse_eta_text_to_iso()
    test_extract_shipnext_eta_and_transit()
    print("ALL TESTS PASSED")
