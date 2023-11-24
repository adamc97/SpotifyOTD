import calendar
import datetime
import pandas as pd
from datetime import date, timedelta
from django.shortcuts import render
from pymongo import MongoClient
from requests import post, Request
from .credentials import redirect_uri, client_id, client_secret, auth_url, token_url, connection_string
from .utils import collect_song_info, user, fav_audio_properties, collect_spotify_songs, spot_audio_properties, enhance_playlist
import certifi



def home(request):

    today = datetime.datetime.today()
    anniversary = str(today)[5:10] 

    day = int(anniversary[3:5])
    month_no = int(anniversary[0:2])
    month_name = calendar.month_name[month_no]
    if day == 1 or day == 21 or day == 31:
        day_suffix = 'st'
    elif day == 2 or day == 22:
        day_suffix = 'nd'
    elif day == 3 or day == 23:
        day_suffix = 'rd'
    else:
        day_suffix = 'th'

    global db_user_tokens

    mg_client = MongoClient(connection_string, tlsCAFile=certifi.where())
    dbs = mg_client.list_database_names()
    auth_db = mg_client.on_this_day_spot
    db_user_tokens = auth_db.user_tokens

    scope = 'user-library-read playlist-modify-private'

    url = Request('GET', auth_url, params={
        'scope':scope,
        'response_type':'code',
        'redirect_uri':redirect_uri,
        'client_id':client_id
    }).prepare().url

    today_day = date.today().strftime("%A")
    today_month = datetime.datetime.today().strftime('%B')
    today_day_no = datetime.date.today().day
    today_year = datetime.date.today().year
    today = f'{today_day}, {today_month} {today_day_no}{day_suffix} {today_year}'

    data = {
        'url':url, 
        'today':today
    }

    return render(request, 'main_app/home.html', data)


def callback(request):

    today = datetime.datetime.today()
    anniversary = str(today)[5:10] 
    day = int(anniversary[3:5])
    month_no = int(anniversary[0:2])
    month_name = calendar.month_name[month_no]
    if day == 1 or day == 21 or day == 31:
        day_suffix = 'st'
    elif day == 2 or day == 22:
        day_suffix = 'nd'
    elif day == 3 or day == 23:
        day_suffix = 'rd'
    else:
        day_suffix = 'th'

    code = request.GET.get('code')
    error = request.GET.get('error')

    try:
        response = post(token_url, data={
            'client_id':client_id,
            'client_secret':client_secret,
            'grant_type':'authorization_code',
            'code':code, 
            'redirect_uri':redirect_uri
        }).json()
        access_token = response.get('access_token')
        token_type = response.get('token_type')
        refresh_token = response.get('refresh_token')
        expires_in = int(response.get('expires_in'))
        expires = datetime.datetime.now() + timedelta(seconds=expires_in)
        error = response.get('error')
        db_doc = {
            'code':code,
            'access_token':access_token,
            'token_type':token_type,
            'refresh_token':refresh_token,
            'expires':expires,
            'error':error
        }
        db_user_tokens.insert_one(db_doc)
    except:
        access_token = db_user_tokens.find_one({'code':code})['access_token']

    db_user_tokens.delete_many({'expires': {'$lt':datetime.datetime.now()}})

    access_token, info, fav_ids_string, fav_uri_list, available_years, all_years, colours = collect_song_info(access_token, anniversary)
    user_id = user(access_token)
    spot_ids_string, spot_uri_list = collect_spotify_songs(access_token)
    fav_df = fav_audio_properties(access_token, fav_uri_list, fav_ids_string)
    spot_df = spot_audio_properties(access_token, spot_uri_list, spot_ids_string)
    df = pd.concat([fav_df, spot_df])

    try:
        uri_list_enhanced = enhance_playlist(df, fav_uri_list, spot_uri_list)
    except:
        uri_list_enhanced = fav_uri_list
    
    data = {
        'access_token': access_token,
        'info':info,
        'available_years': available_years,
        'all_years':all_years,
        'colours':colours,
        'user_id': user_id,
        'playlist_name': f'OnThisDay: {month_name} {day}{day_suffix}',
        'uri_list': fav_uri_list,
        'uri_list_enhanced':uri_list_enhanced
    }

    if len(fav_uri_list) > 0:
        return render(request, 'main_app/onthisday.html', data)
    else:
        return render(request, 'main_app/no_songs.html')