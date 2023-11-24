import numpy as np
import pandas as pd
from requests import get
from PIL import Image
from io import BytesIO
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from .credentials import lib_url, aud_url, usr_url, spot_url


def collect_song_info(access_token, anniversary):
    global fav_ids_string

    fav_ids_string = ''
    fav_uri_list = []
    info = []

    def save_song_info(n):
        global fav_ids_string
        for i in range(n):
            if response_json[i]['added_at'][5:10] == anniversary:
                details_dict = {}
                fav_ids_string += f'{response_json[i]["track"]["id"]},'
                fav_uri_list.append(response_json[i]['track']['uri'])
                details_dict['artwork']=response_json[i]['track']['album']['images'][0]['url']
                details_dict['track']=response_json[i]['track']['name']
                details_dict['url_track']=response_json[i]['track']['external_urls']['spotify']
                details_dict['url_embed']=f'https://open.spotify.com/embed/track/{response_json[i]["track"]["id"]}?utm_source=generator&theme=0'
                details_dict['album']=response_json[i]['track']['album']['name']
                details_dict['url_album']=response_json[i]['track']['album']['external_urls']['spotify']
                artists_list = []
                for j, val in enumerate(response_json[i]['track']['artists']):
                    artist_info = {}
                    artist_info[response_json[i]['track']['artists'][j]['name']] = response_json[i]['track']['artists'][j]['external_urls']['spotify']
                    artists_list.append(artist_info)
                details_dict['artists']=artists_list
                details_dict['year']=response_json[i]['added_at'][:4]
                info.append(details_dict)

    header = {
        'Authorization':f'Bearer {access_token}',
        'Content-Type':'application/json'
    }

    response = get(lib_url, {'offset':'0', 'limit':'50'}, headers=header)
    song_count = response.json()['total']
    response_json = response.json()['items']
    if song_count > 50:
        save_song_info(50)
        count = response.json()['total']
        remainder = count%50
        quotient = count-remainder
        max_year = int(response.json()['items'][0]['added_at'][:4])

        for j in range(50, quotient, 50):
            response = get(lib_url, {'offset':j, 'limit':'50'}, headers=header)
            response_json = response.json()['items']
            save_song_info(50)
        min_year = int(response_json[49]['added_at'][:4])

        if remainder > 0:
            response = get(lib_url, {'offset':quotient, 'limit':remainder}, headers=header)
            response_json = response.json()['items']
            save_song_info(remainder)
            min_year = int(response_json[remainder-1]['added_at'][:4])
    else:
        save_song_info(song_count)
        min_year = int(response_json[song_count-1]['added_at'][:4])
        max_year = int(response.json()['items'][0]['added_at'][:4])

    available_years = sorted([int(i['year']) for i in info], reverse=True) # List of year for each song

    all_years = {}                                                          
    for i, val in enumerate(available_years):                               # For each element in available_years                                                     
        if available_years[i] != available_years[i-1]:                      # if the value is different to previous element
            all_years[available_years[i]] = i                               # item added to all_years dict in format year:position in list

    for i in range(min_year, max_year+1):
        if i not in all_years:
            all_years[i] = -1

    all_years = dict(sorted(all_years.items(), reverse=True))

    if len(available_years) == 1 or (len(available_years) > 1 and max(available_years) == min(available_years)):
        all_years[available_years[0]] = 0

    colours = []
    for i, val in enumerate(info):
        try:
            img = info[i]['artwork']
            response = get(img)
            arr = np.array(Image.open(BytesIO(response.content)))
            arr_mean = np.mean(arr, axis=(0,1))
            R = round(arr_mean[0])
            G = round(arr_mean[1])
            B = round(arr_mean[2])
            colours.append(f'{R}, {G}, {B}')
        except:
            colours.append('0, 0, 0')

    return access_token, info, fav_ids_string, fav_uri_list, available_years, all_years, colours


def user(access_token):
    header = {
        'Authorization':f'Bearer {access_token}',
        'Content-Type':'application/json'
    }

    response = get(usr_url, {}, headers=header)
    response_json = response.json()
    user_id = response_json['id']
    
    return user_id


def fav_audio_properties(access_token, fav_uri_list, fav_ids_string):
    
    danceability = []
    energy = []
    key = []
    loudness = []
    mode = []
    speechiness = []
    acousticness = []
    instrumentalness = []
    liveness = []
    valence = []
    tempo = []
    fav = []

    header = {
        'Authorization':f'Bearer {access_token}',
        'Content-Type':'application/json'
    }
    response = get(aud_url, {'ids':fav_ids_string}, headers=header)
    response_json = response.json()

    for i, val in enumerate(fav_uri_list):
        danceability.append(response_json['audio_features'][i]['danceability'])
        energy.append(response_json['audio_features'][i]['energy'])
        key.append(response_json['audio_features'][i]['key'])
        loudness.append(response_json['audio_features'][i]['loudness'])
        mode.append(response_json['audio_features'][i]['mode'])
        speechiness.append(response_json['audio_features'][i]['speechiness'])
        acousticness.append(response_json['audio_features'][i]['acousticness'])
        instrumentalness.append(response_json['audio_features'][i]['instrumentalness'])
        liveness.append(response_json['audio_features'][i]['liveness'])
        valence.append(response_json['audio_features'][i]['valence'])
        tempo.append(response_json['audio_features'][i]['tempo'])
        fav.append(1)

    fav_df = pd.DataFrame({
        'uri':fav_uri_list,
        'danceability':danceability,
        'energy':energy,
        'key':key,
        'loudness':loudness,
        'mode':mode,
        'speechiness':speechiness,
        'acousticness':acousticness,
        'instrumentalness':instrumentalness,
        'liveness':liveness,
        'valence':valence,
        'tempo':tempo,
        'fav':fav
    })

    return fav_df
    

def collect_spotify_songs(access_token):

    header = {
        'Authorization':f'Bearer {access_token}',
        'Content-Type':'application/json'
    }
    response = get(spot_url, {}, headers=header)
    response_json = response.json()

    spotify_playlists = [response_json['items'][i]['id'] for i in range(len(response_json['items']))]

    spot_ids_string = []
    spot_uri_list = []

    for i, val in enumerate(spotify_playlists):

        strings = ''
        uris = []

        tracks_url = f'https://api.spotify.com/v1/playlists/{val}/tracks'
        response = get(tracks_url, {}, headers=header)
        response_json = response.json()

        print(response_json['items'])

        song_count = len(response_json['items'])

        for i in range(song_count):
            try:
                id_ = response_json['items'][i]['track']['id']
                strings += f'{id_},'
                uris.append(f'spotify:track:{id_}')
                zz+=1
            except:
                pass
        
        spot_ids_string.append(strings)
        spot_uri_list.append(uris)

    return spot_ids_string, spot_uri_list


def spot_audio_properties(access_token, spot_uri_list, spot_ids_string):
    
    uris = []
    danceability = []
    energy = []
    key = []
    loudness = []
    mode = []
    speechiness = []
    acousticness = []
    instrumentalness = []
    liveness = []
    valence = []
    tempo = []
    fav = []

    header = {
        'Authorization':f'Bearer {access_token}',
        'Content-Type':'application/json'
    }

    for i, val in enumerate(spot_ids_string):
        response = get(aud_url, {'ids':val}, headers=header)
        response_json = response.json()

        for i_, val_ in enumerate(spot_uri_list[i]):
            try:   
                danceability.append(response_json['audio_features'][i_]['danceability'])
                energy.append(response_json['audio_features'][i_]['energy'])
                key.append(response_json['audio_features'][i_]['key'])
                loudness.append(response_json['audio_features'][i_]['loudness'])
                mode.append(response_json['audio_features'][i_]['mode'])
                speechiness.append(response_json['audio_features'][i_]['speechiness'])
                acousticness.append(response_json['audio_features'][i_]['acousticness'])
                instrumentalness.append(response_json['audio_features'][i_]['instrumentalness'])
                liveness.append(response_json['audio_features'][i_]['liveness'])
                valence.append(response_json['audio_features'][i_]['valence'])
                tempo.append(response_json['audio_features'][i_]['tempo'])
                fav.append(0)
                uris.append(spot_uri_list[i][i_])
            except:
                pass

    spot_df = pd.DataFrame({
        'uri':uris,
        'danceability':danceability,
        'energy':energy,
        'key':key,
        'loudness':loudness,
        'mode':mode,
        'speechiness':speechiness,
        'acousticness':acousticness,
        'instrumentalness':instrumentalness,
        'liveness':liveness,
        'valence':valence,
        'tempo':tempo,
        'fav':fav
    })   

    return spot_df


def enhance_playlist(df, fav_uri_list, spot_uri_list):

    shuffle_df = df.sample(frac=1)

    train_size = int(0.7 * len(df))
    train_set = shuffle_df[:train_size]
    test_set = shuffle_df[train_size:]

    X = train_set.drop(columns=['fav', 'uri'])
    y = train_set.fav

    X_test = test_set.drop(columns=['fav', 'uri'])
    y_test = test_set.fav

    k_n = sum(y) - 1

    X_train, y_train = SMOTE(k_neighbors=k_n).fit_resample(X, y)

    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    y_predicted = model.predict(X_test)

    enhanced_uri_list = fav_uri_list.copy()

    for i in (y_predicted > 0).nonzero():
        for j in i:
            enhanced_uri_list.append(test_set['uri'].iloc[j])
            
    return enhanced_uri_list