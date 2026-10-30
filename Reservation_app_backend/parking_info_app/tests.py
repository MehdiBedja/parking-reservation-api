from decimal import Decimal

from django.test import TestCase

from .models import Commune, Daira, Parking, Wilaya


def make_parking(name='Parking Didouche', commune_name='Sidi M\'Hamed'):
    wilaya = Wilaya.objects.create(name='Alger')
    daira = Daira.objects.create(name='Sidi M\'Hamed', wilaya=wilaya)
    commune = Commune.objects.create(name=commune_name, daira=daira)
    return Parking.objects.create(
        name=name, description='Underground, 200 places', image='image1.jpg',
        latitude=Decimal('36.763000'), longitude=Decimal('3.050000'), commune=commune,
    )


class ParkingApiTests(TestCase):
    def test_list_parkings(self):
        make_parking()

        response = self.client.get('/parkings/getParkings/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{
            'name': 'Parking Didouche',
            'description': 'Underground, 200 places',
            'commune_name': 'Sidi M\'Hamed',
            'image': 'image1.jpg',
        }])

    def test_list_parkings_with_ids_and_coordinates(self):
        parking = make_parking()

        data = self.client.get('/parkings/getParkingsId/').json()

        self.assertEqual(data[0]['id'], parking.id)
        self.assertEqual(data[0]['latitude'], '36.763000')
        self.assertEqual(data[0]['longitude'], '3.050000')

    def test_get_single_parking(self):
        parking = make_parking()

        response = self.client.get(f'/parkings/getParking/{parking.id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], 'Parking Didouche')

    def test_get_unknown_parking(self):
        response = self.client.get('/parkings/getParking/9999/')
        self.assertEqual(response.status_code, 404)
