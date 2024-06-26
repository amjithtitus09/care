from rest_framework import status
from rest_framework.test import APITestCase

from care.facility.models import Bed
from care.facility.models.bed import AssetBed
from care.utils.assetintegration.asset_classes import AssetClasses
from care.utils.tests.test_utils import TestUtils


class BedViewSetTestCase(TestUtils, APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.state = cls.create_state()
        cls.district = cls.create_district(cls.state)
        cls.local_body = cls.create_local_body(cls.district)
        cls.super_user = cls.create_super_user("su", cls.district)
        cls.facility = cls.create_facility(cls.super_user, cls.district, cls.local_body)
        cls.asset_location = cls.create_asset_location(cls.facility)
        cls.user = cls.create_user("staff", cls.district, home_facility=cls.facility)
        cls.patient = cls.create_patient(
            cls.district, cls.facility, local_body=cls.local_body
        )

    def setUp(self) -> None:
        super().setUp()
        self.bed1 = Bed.objects.create(
            name="bed1", location=self.asset_location, facility=self.facility
        )
        self.bed2 = Bed.objects.create(
            name="bed2", location=self.asset_location, facility=self.facility
        )
        self.bed3 = Bed.objects.create(
            name="bed3", location=self.asset_location, facility=self.facility
        )

    def test_list_beds(self):
        # includes 3 queries for auth and 1 for pagination count
        with self.assertNumQueries(5):
            response = self.client.get("/api/v1/bed/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_non_occupied_beds(self):
        linked_bed = Bed.objects.create(
            name="linked_bed",
            location=self.asset_location,
            facility=self.facility,
        )
        asset = self.create_asset(
            self.asset_location, asset_class=AssetClasses.HL7MONITOR.name
        )
        AssetBed.objects.create(bed=linked_bed, asset=asset)

        # 4 beds 1 linked with HL7MONITOR and 3 created in setup

        response = self.client.get("/api/v1/bed/")

        # Assert list returns 4 beds
        self.assertEqual(response.json()["count"], 4)

        response_with_not_occupied_bed = self.client.get(
            "/api/v1/bed/",
            {"not_occupied_by_asset_type": "HL7MONITOR"},
        )

        # Assert count of unoccupied beds is 3
        self.assertEqual(response_with_not_occupied_bed.json()["count"], 3)
