import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import pytz

# Making a GET request
URL = 'https://www.republika.co.id/'
r = requests.get(URL)

# Parsing the HTML
soup = BeautifulSoup(r.content, 'html.parser')
contents = soup.find_all('li', class_='list-group-item list-border conten1')

# Mendapatkan nama bulan berdasarkan angkanya
def get_bulan(bulan):
    nama_bulan = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    return nama_bulan[int(bulan)]

# Fungsi untuk mendapatkan waktu terbit dari berita
def get_publish_time(jeda_publish):
    jeda_publish = jeda_publish.text.split('-')[-1].strip().split()[0:2]
    waktu_jakarta = pytz.timezone('Asia/Jakarta')
    if jeda_publish[1] in ['detik', 'seconds']:
        publish_time = datetime.now(waktu_jakarta) - timedelta(seconds=int(jeda_publish[0]))
        scrap_time = datetime.now(waktu_jakarta)
    elif jeda_publish[1] in ['menit', 'minutes']:
        publish_time = datetime.now(waktu_jakarta) - timedelta(minutes=int(jeda_publish[0]))
        scrap_time = datetime.now(waktu_jakarta)
    elif jeda_publish[1] in ['jam', 'hours']:
        publish_time = datetime.now(waktu_jakarta) - timedelta(hours=int(jeda_publish[0]))
        scrap_time = datetime.now(waktu_jakarta)
    return (f"{publish_time.day} {get_bulan(publish_time.month)} {publish_time.year} {publish_time.strftime('%H:%M:%S')}", 
            f"{scrap_time.day} {get_bulan(scrap_time.month)} {scrap_time.year} {scrap_time.strftime('%H:%M:%S')}")

# Fungsi untuk mendapatkan nama penulis dari suatu berita
def get_writer(link_berita, kategori):
    # Mendapatkan subdomain dari berita
    subdomain = link_berita.split('/')[2].split('.')[0]
    # Melakukan request untuk mendapatkan html
    berita = requests.get(link_berita)
    if berita.status_code == 403: return '-'
    while berita.status_code == 429:
        berita = requests.get(link_berita)
    # Melakukan parsing HTML
    soup_berita = BeautifulSoup(berita.content, 'html.parser')
    # Mencari nama penulis (dengan informasi tertentu)
    if subdomain == 'ramadhan':
        try: return soup_berita.find('div', class_='read-title').find('h2').find('span').find('span').find('span').text.strip()
        except AttributeError: return soup_berita.find('div', class_='read-title').find('h2').find('span').text.strip()
    elif subdomain == 'visual':
        return soup_berita.find('div', class_='max-card__title vsl').find('div').text.split(':')[-1].strip()
    elif subdomain == 'tv':
        return soup_berita.find('div', class_='by').find('p').text.split(':')[-1].strip()
    elif kategori == 'Network':
        try: 
            penulis = soup_berita.find('div', class_='profile-name profile-name-list').find('a').text.strip()
            return penulis if penulis else '-'
        except AttributeError: pass
    # Mencari nama penulis (default)
    search_penulis = soup_berita.find_all('a')
    for a in search_penulis:
        try:
            if any(keyword in a.get('href') for keyword in ['penulis', 'writer', 'author']):
                if 'FOLLOW' in a.text:
                    return '-'
                return a.text if (a.text.strip() != None) else '-'
        except TypeError:
            pass
    return '-'

# Menambahkan elemen berita baru ke list_berita
list_berita = []
for content in contents:
    # Mendapatkan judul berita
    title = content.find('span', class_=False).text.strip()
    # Mendapatkan kategori berita
    category = content.find('span', class_='kanal-info').text.strip()
    # Mendapatkan waktu terbit berita
    publish_time = content.find('div', class_='date')
    publish_time, scrap_time = get_publish_time(publish_time)
    # Mendapatkan nama penulis berita
    link = content.find('a').get('href')
    penulis = get_writer(link, category).title()
    # Menambahkan informasi berita baru ke list
    list_berita.append({'Judul': title,
                        'Link': link,
                        'Kategori': category,
                        'Waktu Terbit': publish_time,
                        'Waktu Scrapping': scrap_time,
                        'Penulis': penulis})

# Mengkonversi dictionary menjadi file .json
with open("daftar_berita.json", "w") as outfile:
    json.dump(list_berita, outfile, indent=4)
