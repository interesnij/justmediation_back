import uuid
import sys,os
import requests
from bs4 import BeautifulSoup
import json
project_dir = '../o/'

sys.path.append(project_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
import django
django.setup()

from apps.users.models.users import AppUser
from apps.users.models.attorneys import Attorney
from apps.users.models.extra import Jurisdiction, Speciality
from apps.users.models.attorney_links import AttorneyUniversity, AttorneyEducation
from cities_light.models import City, Country, Region


def get_json(url, page, perpage, total):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        'Content-Type': 'application/json',
        'Cookie': '_BEAMER_USER_ID_FmmRneJk26181=cefc1d23-64e8-4167-99a5-79d1ae5ffc46; _BEAMER_FIRST_VISIT_FmmRneJk26181=2024-10-17T13:35:24.828Z; intercom-device-id-gx0xej01=bf88fca1-d90e-4c67-82de-fc9e6c8d9262; _ga_Y14WDP0VKK=GS1.1.1729687059.1.0.1729687064.0.0.0; _gid=GA1.2.1814254535.1729852671; _lr_uf_-9oawpn=ac232e9c-0ad2-44c9-9cdc-d79b93a3dca7; _gat_gtag_UA_180493463_1=1; REMEMBERME=QXBwXEVudGl0eVxVc2VyOlltVmhkSEpwWTJWQVlYUjBiM0p1Wlhsd2JHRmpaVzFsYm5SemFXNTBMbU52YlE9PToxNzMyNTI2NDE1OjM4ZDBiZGFmZmJmYzE3MGRiNjI1Y2Y0NWE1YWE2MWJlMTlmOGIzNTY3MDJmMDUwMjE2YjczMmZjYWRiMmMyYWQ%3D; PHPSESSID=nhhnm8k2cgll516jd2hn2nh7if; _BEAMER_FILTER_BY_URL_FmmRneJk26181=false; _lr_tabs_-9oawpn%2Fengage-qkzza={%22sessionID%22:0%2C%22recordingID%22:%225-33651f05-c94b-485c-8d17-04a343f3fa8a%22%2C%22lastActivity%22:1729934416743%2C%22hasActivity%22:false}; _lr_hb_-9oawpn%2Fengage-qkzza={%22heartbeat%22:1729934416743}; _BEAMER_FILTER_BY_URL_FmmRneJk26181=false; intercom-session-gx0xej01=TXJ1dEhuN1RTKzJ2b2k2YnhZdHYrdy9BTE8ybzdZZFpLMU9MQ29kMGpRZmxWK2MwMTRCSlhaOFZLRkJkS1FGei0tbU5WNzJQUCtFaVpuWTFMbnh6alJjdz09--e571fd56c09123bdbd1f1581e66642b4d9a5e516; _ga_198VEWLTWK=GS1.1.1729934412.11.1.1729934422.0.0.0; _ga=GA1.1.1693193553.1729106339',
    }
    session = requests.session()
    data={"query": {"userlist": None,"matched_job": None,"matter": None,"attorney_connections": None,"firm_connections": None,"office_connections": None,"connection_notification": None,"keywords": {"phrase": "","search_within": {"profile": True,"matters": False,"notes": False,"education": False}},"keywords_excluded": {"phrase": "","search_within": {"profile": True,"matters": False,"notes": False,"education": False}},"full_name": "","firm_top200": {"enabled": False,"min": "","max": ""},"firm_top200_excluded": {"enabled": False,"min": "","max": ""},"firm_vault_rank": {"enabled": False,"min": "","max": ""},"firm_names": [],"firm_names_excluded": [],"prior_firms": {"items": []},"prior_firms_excluded": {"items": []},"firm_size": {"min": "","max": ""},"profits_per_partner": {"min": "","max": ""},"non_attorney": False,"active": True,"willing_to_mentor": False,"status": "","status_excluded": ["do_not_contact"],"created_at": {"min": "","max": ""},"titles": [],"law_schools": [],"llm_schools": [],"llm_year": {"min": "","max": "","without_year": False},"llm_specialty": [],"graduation_year": {"min": "","max": "","without_year": False},"undergraduates": [],"all_diversity": False,"bar_admissions": {"items": [],"condition": "or"},"bar_admissions_excluded": [],"honors": [],"clerkships": [],"languages": [],"countries": [],"advanced_degrees": [],"genders": [],"memberships": [],"acknowledgements": [],"regions": {"items": [],"condition": "or","use_second_location": True,"type": "location"},"regions_excluded": {"items": [],"condition": "or","use_second_location": True},"location_coords": {},"location_coords_excluded": {},"international": 0,"last_move_date_exclude": {"min": "","max": ""},"last_move_date": {"min": "","max": ""},"last_sent_date_exclude": {"min": "","max": ""},"sent_by_user_exclude": [],"practice_areas": {"items": [],"condition": "or"},"specialties": {"items": [],"condition": "or"},"practice_areas_excluded": [],"specialties_excluded": [],"titles_excluded": [],"entity_type": [],"inactive_entity_type": [],"source": 0,"tags": "null","practice_areas_with_specialties": {"items": [],"condition": "or"},"exclude_practice_areas_with_specialties": {"items": [],"condition": "or"},"claimed": False,"registered": False},"sort": {"field": "bestResults","sort": "desc"},"pagination": {"page": page,"perpage": perpage,"total": total},"uuid": None,"search_session_id": ""}
    session.headers.update(headers)
    print("pagination ", data['pagination'])
    data_as_json = json.dumps(data)
    results = session.post(url, json=data_as_json)
    return results.json()

def main():
    perpage = 20
    page = 2
    total = 237546
    count = 1
    while page < 15000:
        print("=========   ", page, "   =========")
        data = get_json("https://engage.firmprospects.com/attorneys/search", page, perpage, total)
        page += 1
        for i in data['data']:
            first_name = i['first_name']
            last_name = i['last_name']

            print("---   ", last_name, "   ---")
            continue
            try:
                firm_name = i['firm_office']['firm']['firm_name']
                email = i['email']
                if not email or email == "" or email == " " or email == "  ":
                    email = last_name + str(count) + "@justlaw.com"
            except:
                firm_name = 'empty '
                email = last_name + str(count) + "@justlaw.com"
            try:
                phone = i['phone_number']
            except:
                phone = ''
            try:
                bio = i['attorney_bio']
            except:
                bio = ''

            if AppUser.objects.filter(email=email).exists():
                print(" user exists!")
                continue

            password = str(uuid.uuid4())
            count += 2

            with open("part2.txt", "a") as myfile:
                myfile.write(first_name + " " + last_name + ", " + email + ", " + password)
                myfile.write("\n")
                myfile.write("\n")
                
            user = AppUser.objects.create_user(
                uuid = password,
                password = password,
                first_name = first_name,
                middle_name = None,
                last_name = last_name,
                email = email,
                phone = phone,
                onboarding = True,
                is_active = True,
            )

            user.set_password(password)
            user.is_active = True
            user.is_free_subscription = True
            user.save()

            new_user = Attorney.objects.create(
                user = user,
                license_info = "empty",
                firm_name = firm_name,
                verification_status = "approved",
                biography = bio,
            )

            specialities = i['attorneys_practice_areas']
            for m in specialities:
                if Speciality.objects.filter(title=m).exists():
                    spec = Speciality.objects.get(title=m.strip())
                else:
                    spec = Speciality.objects.create(title=m.strip())
                user.specialities.add(spec)
                
            try:
                law_school = i['law_school']
                if AttorneyUniversity.objects.filter(title=law_school).exists():
                    university = AttorneyUniversity.objects.get(
                        title = law_school,
                    )
                else:
                    university = AttorneyUniversity.objects.create(
                        title = law_school,
                    )
                AttorneyEducation.objects.create(
                    university = university,
                    attorney = new_user,
                    year = 0
                )
            except:
                pass



if __name__ == '__main__':
    main()
