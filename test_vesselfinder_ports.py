#!/usr/bin/env python3
"""Unit tests for VesselFinder origin/destination extraction and merge logic."""
from bs4 import BeautifulSoup

from scraper import extract_from_vesselfinder, merge_voyage_ports


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


def test_extract_from_vesselfinder():
    soup = BeautifulSoup(VESSELFINDER_FIXTURE, 'html.parser')
    data = extract_from_vesselfinder(soup)
    assert data is not None
    assert data['location_text'] == 'Annacis Island, Canada'
    assert data['origin_city'] == 'Kawasaki, Japan'
    assert data['eta_text'] == 'Dec 2, 04:00'
    assert data['latitude'] == 35.0
    assert data['longitude'] == 141.0
    print("✓ VesselFinder fixture extracts current destination and last port")


def test_merge_overrides_stale_shipnext_ports():
    shipnext = {
        'location_text': 'Kawasaki, Japan',
        'origin_city': 'Gamagori, Japan',
        'latitude': 37.36,
        'longitude': 146.94,
    }
    vesselfinder = {
        'location_text': 'Annacis Island, Canada',
        'origin_city': 'Kawasaki, Japan',
        'latitude': 35.0,
        'longitude': 141.0,
        'eta_text': 'Dec 2, 04:00',
    }
    merged = merge_voyage_ports(shipnext, vesselfinder)
    assert merged['location_text'] == 'Annacis Island, Canada'
    assert merged['origin_city'] == 'Kawasaki, Japan'
    # Prefer precise ShipNext coordinates when present
    assert merged['latitude'] == 37.36
    assert merged['longitude'] == 146.94
    assert merged['eta_text'] == 'Dec 2, 04:00'
    print("✓ Merge overrides stale ShipNext ports and keeps ShipNext coordinates")


if __name__ == '__main__':
    test_extract_from_vesselfinder()
    test_merge_overrides_stale_shipnext_ports()
    print("ALL TESTS PASSED")
