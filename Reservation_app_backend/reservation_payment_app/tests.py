from django.test import TestCase
from rest_framework.test import APIClient

from accounts_app.models import CustomUser
from parking_info_app.tests import make_parking

from .models import ParkingPlace, Reservation


class ReservationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(username='driver', email='d@example.com', password='pw')
        self.parking = make_parking()
        self.place = ParkingPlace.objects.create(attributes='A1 · covered', parking=self.parking)

    def reserve(self, code='RES-001', place=None):
        return self.client.post('/reservations/addReservation/', {
            'user': self.user.id,
            'parking_place': (place or self.place).id,
            'entry_datetime': '2026-11-01 08:00',
            'exit_datetime': '2026-11-01 18:00',
            'reservation_code': code,
        }, format='json')

    def test_create_reservation(self):
        response = self.reserve()

        self.assertEqual(response.status_code, 201)
        reservation = Reservation.objects.get(reservation_code='RES-001')
        self.assertEqual(reservation.user, self.user)
        self.assertEqual(reservation.payment_status, 'pending')

    def test_reservation_code_must_be_unique(self):
        self.reserve()
        response = self.reserve()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_create_reservation_rejects_unknown_place(self):
        response = self.client.post('/reservations/addReservation/', {
            'user': self.user.id, 'parking_place': 9999,
            'entry_datetime': 'x', 'exit_datetime': 'y', 'reservation_code': 'R',
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_list_user_reservations(self):
        self.reserve('RES-001')
        self.reserve('RES-002')
        other = CustomUser.objects.create_user(username='other', email='o@example.com', password='pw')
        Reservation.objects.create(
            user=other, parking_place=self.place, entry_datetime='a', exit_datetime='b', reservation_code='RES-X'
        )

        data = self.client.get(f'/reservations/myReservations/{self.user.id}/').json()

        self.assertEqual(sorted(r['reservation_code'] for r in data), ['RES-001', 'RES-002'])
        self.assertEqual(data[0]['user']['username'], 'driver')
        self.assertEqual(data[0]['parking_place']['attributes'], 'A1 · covered')

    def test_list_reservations_unknown_user(self):
        self.assertEqual(self.client.get('/reservations/myReservations/9999/').status_code, 404)

    def test_available_places_excludes_taken_ones(self):
        ParkingPlace.objects.create(attributes='A2', parking=self.parking, available=False)

        data = self.client.get(f'/reservations/getAllParkingPlaces/{self.parking.id}/').json()

        self.assertEqual([p['attributes'] for p in data], ['A1 · covered'])
        self.assertEqual(data[0]['parking']['name'], 'Parking Didouche')

    def test_get_reservation_by_id(self):
        self.reserve()
        reservation = Reservation.objects.get()

        response = self.client.get(f'/reservations/getReservation/{reservation.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['reservation_code'], 'RES-001')
        self.assertEqual(self.client.get('/reservations/getReservation/9999/').status_code, 404)
