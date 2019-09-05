# Finding locations for cancer clinical trials

# pip install requests, googlemaps, geopy
import googlemaps
import requests
from geopy.distance import geodesic
from gmplot import gmplot

# download url
url = 'https://clinicaltrialsapi.cancer.gov/v1/clinical-trials?current_trial_status_date_gte=2016-08-25'
response = requests.get(url)
response.raise_for_status()
# print(response.status_code)

# convert response to JSON
trials = response.json()


def available_trial_info(cancer_type, p_geolocation):
    num_available_trials = 0
    api_geolocation = []
    site_avail = []
    for trial in trials['trials']:
        if cancer_type in trial['anatomic_sites'][0]:
            for site in trial['sites']:
                if site['recruitment_status'] == 'ACTIVE':
                    coordinate = site_geolocation(site)
                    if coordinate is None:                         # key ['org_coordinates'] is missing in API
                        location = site_location(site)             # get address location
                        if location:
                            coordinate = geolocation_conversion(location)    # convert address location into geolocation
                    api_geolocation.append(coordinate)
                    dist = nearby_locations(coordinate, p_geolocation, site)  # return a distance within 10.0 miles
                    if dist is not None:
                        num_available_trials += 1                  # calculate number of available trials
                        site_avail.append(coordinate)
    return api_geolocation, num_available_trials, site_avail


def site_geolocation(site):
    """ Obtain lat-lng coordinate of active trials in the Cancer NCI API"""

    try:
        latitude = site['org_coordinates']['lat']
        longitude = site['org_coordinates']['lon']
        lat_lng = tuple((latitude, longitude))
        return lat_lng
    except KeyError:    # key ['org_coordinates'] is missing
        return None


def site_location(site):
    """ Obtain address location of a trial site """

    try:
        address = site['org_address_line_1']
        city = site['org_city']
        state = site['org_state_or_province']
        postal_code = site['org_postal_code']
        location = ', '.join((address, city, state, postal_code))
        return location
    except TypeError:
        return None


def geolocation_conversion(location):
    """ Convert address location into geolocation as a coordinate """

    # place in a Google API key to call googlemaps module
    gglmaps = googlemaps.Client(key='XXXXXXXXXX')
    geo_result = gglmaps.geocode(location)
    lat_lng = geo_result[0]['geometry']['location']
    coord = tuple((lat_lng['lat'], lat_lng['lng']))
    return coord


def nearby_locations(site_coord, p_geo, site):
    """ Calculate the distance between patient_geolocation and site coordinate """

    distance_in_mile = geodesic(site_coord, p_geo).miles
    if float(distance_in_mile) <= 10.0:
        try:
            organization = site['org_name']
            address = site['org_address_line_1']
            city = site['org_city']
            state = site['org_state_or_province']
            postal_code = site['org_postal_code']
            trial_location = ', '.join((address, city, state, postal_code))
            print('Organization: ' + organization)
            print('Address: ' + trial_location)
            return distance_in_mile
        except TypeError:
            return None


def locations_on_map(avail_sites):
    """ Draw nearby geolocation coordinates on map """

    # place in a Google API key to call gmplot module
    gmap = gmplot.GoogleMapPlotter(37.766956, -122.438481, 13, apikey='XXXXXXXXXX')
    try:
        geo_lats, geo_lngs = zip(*avail_sites)
        gmap.scatter(geo_lats, geo_lngs, 'cornflowerblue', size=800, marker=False)     # Scatter pins
    except ValueError:
        print('Not enough locations to print on map')

    # Draw map
    gmap.draw('location_map.html')


if __name__ == '__main__':

    print('PROGRAM FINDING ACTIVE CANCER TRIALS NEAR YOUR HOME')
    patient_input = input('Please enter a cancer type (capitalized initial letter) or Multiple: ')
    zip_code = input('Please enter a 5-digit zip code: ')

    # convert patient's zip code into geolocation
    patient_geolocation = geolocation_conversion(zip_code)

    # return number of available trials and corresponding coordinate(s)
    list_of_geolocation, num_avail_trials, available_site_geo = available_trial_info(patient_input, patient_geolocation)

    print('The total number of active trials available in this area is ' + str(num_avail_trials) + ' trial(s)')

    # Place coordinates on map
    locations_on_map(available_site_geo)

    # print(available_site_geo)
    # print(len(available_site_geo))
    # print(list_of_geolocation)
    # print(len(list_of_geolocation))
