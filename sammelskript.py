# %%
from time import sleep

# package import
import requests
from tqdm.auto import tqdm
from datetime import datetime, timedelta
from sqlalchemy import Table, MetaData
from sqlalchemy.dialects.mysql import insert
from sqlalchemy import create_engine
import threading
import time
from datetime import datetime, timedelta
import pandas as pd
import json
import numpy as np
### Set your client key and secret from your dev account
client_key = "awrhcte67ofti445"  # set both variables to the given client key and client secret
client_secret = "Qsj5jPkCTNk6kwEAM7aJhS9xiFZr6zfI"
## api base_url
base_url = 'https://open.tiktokapis.com/v2/oauth/token/'  #URL where to get the Acess Token from
# set header and payload info for API request
headers = {'Content-Type': 'application/x-www-form-urlencoded',
           'Cache-Control': 'no-cache'}
payload = {"client_key": client_key,
           "client_secret": client_secret,
           "grant_type": "client_credentials"}

# request bearer auth token
response = requests.post(base_url, headers=headers, data=payload)  #method to send headers+payload to the URL

# save access token as a variable for further usage
access_token = response.json()[
    "access_token"]  # get data from the response, return of the AccessToken + safe as variable
print(response.status_code, response.json())  #checking wether correct token was given

# current time
jetzt = datetime.now()
# format it nicely
print("time:", jetzt.strftime("%d.%m.%Y %H:%M:%S"))
# add 2h until the token expires
neue_zeit = jetzt + timedelta(seconds=7200)
# show it pretty
print("expires:", neue_zeit.strftime("%d.%m.%Y %H:%M:%S"))
sleep(10)
#########################

engine = create_engine("mysql+pymysql://nbergma1:vi$yeiL4oroo@wdb2.hs-mittweida.de/nbergma1?charset=utf8mb4")

usernames1 = ["die.linke"] #Übergabe der Usernames nach denen abgefragt werden soll, einzen oder später über Iteration mögich
url = "https://open.tiktokapis.com/v2/research/video/query/?fields=id,video_description,create_time,region_code,share_count,view_count,like_count,comment_count,music_id,hashtag_names,username,effect_ids,playlist_id,voice_to_text,video_duration,hashtag_info_list,sticker_info_list,sticker_info_list,effect_info_list,video_mention_list,video_label,is_stem_verified,favorites_count,video_tag" #url der video

urlc = 'https://open.tiktokapis.com/v2/research/video/comment/list/?fields=id,like_count,create_time,text,video_id,parent_comment_id,reply_count' # URL der Comment_Query
urlu = "https://open.tiktokapis.com/v2/research/user/info/?fields=display_name, bio_description, avatar_url, is_verified, follower_count, following_count, likes_count, video_count,bio_url" #URL der UserInfo-Query
urlfing = "https://open.tiktokapis.com/v2/research/user/following/" #URL der Following-Quer
urlf = "https://open.tiktokapis.com/v2/research/user/followers/" #URL der Follower- Query
# alle URLs werden mit den fields übergeben die am Ende mit ausgegeben werden, das sind hier alle verfügbaren
headers = { #Angabe des Tokens, von TikTok vorgegeben
    "Authorization": f"Bearer {access_token}", #das erhaltene Token von oben
    "Content-Type": "application/json" # Angabe des Datentyps der Ursprungsressource
}
start_date = "20250721" #Zeitraum welcher abgefragt werden soll in: YYYYMMDD
end_date = "20250723" # inclusive
max_count = 100 #Maximalanzahl der Records, welche angefragt werden können
cursor = None # teilweise genutzt um besser iterieren zu können, teilweise nur ein Zeitstempel der Abfrage
has_more = True # hat die Anfrage noch mehr als die angefragten 100
data = [] #Dataframe für die Videos
datac = [] #Dataframe für die Kommentare
datau = [] #Dataframe für die User Infos
datafing = [] #Dataframe für Following
dataf = [] #Dataframe für Follower
# We add the search_id and cursor as input variables as well as to the query.
def scrape_videos_pagination(username, max_count, start_date, end_date, headers, search_id, cursor):
    query_params = { # Parameter über welche die Abfrage zusammen gebaut wird
                    "query": { #definition der Abfrage
                        "and": [ # mit UND verknüpfen
                            {"operation": "EQ", "field_name": "username", "field_values": [username]} #es sollen Ergebnisse zurück gegeben werden, welche vom angegeben Usernamen stammen, es wird also nach der kategorie "username" gefiltert und alle Ergebnisse geliefert welche mit dem oben definierten Usernamen übereinstimmen
                        ]
                    }, #hierhin besteht auch die Möglichkeit der Angabe der Fields welche gewünscht sind, statt es in der URL zu tun
                    "max_count": max_count,# optional: maximalzahl der records
                    "start_date": start_date, # pflicht: Startdatum von oben
                    "end_date": end_date, #pflicht: Enddatum von oben
                    "cursor": cursor, #optional: zählt wie viele ergebnisse schon gesammelt sind- je in 100er Schritten, da max_count = 100, gut für pagination
                    "search_id":search_id #string
                    }
    #Abfrage stellen und anschließend in eine JSON datei überführen
    response = requests.post(url, headers=headers, data=json.dumps(query_params))
    r = response.json()
    # return the response parsed as a JSON file
    return r #zurückgeben
def generate_date_range(start_date, end_date): #funktion zur Iteration über den Zeitraum, mit 1 Tagesabschnitten

    start = datetime.strptime(start_date, "%Y%m%d")
    end = datetime.strptime(end_date, "%Y%m%d")
    dates = []
    current_date = start
    while current_date <= end:
        next_date = current_date  # end date = same as start date for daily
        dates.append((
            current_date.strftime("%Y%m%d"),
            next_date.strftime("%Y%m%d")
        ))
        current_date += timedelta(days=1)
    return dates
def scrape_comments_pagination(video_id, max_count, headers, cursor): # Abfrage der Kommentare
    data = {
        "video_id": video_id, #pflicht
        "max_count": max_count,#optional # alle 3 verfügbaren Parameter angeben
        "cursor": cursor #optional
    }
    response = requests.post(urlc, headers=headers, data=json.dumps(data)) #übergeben
    comments_data = response.json() #als JSON parsen
    return comments_data
def scrape_user(username, headers): # Funktion für die userinformationen
    query_paramsu = {
        "username": username, #pflicht, keine optionalen, da keine iterationen
    }
    # Make the call and transform the response to a JSON file
    response = requests.post(urlu, headers=headers, data=json.dumps(query_paramsu)) #übergeben
    r = response.json()
    # return the response parsed as a JSON file
    return r
def scrape_following(username, max_count, headers, cursor=None): #following Anfrage
    query_params = {
        "username": username, #Pflicht
        "max_count": max_count #optional
    }
    if cursor:
        query_params["cursor"] = cursor #optional, hat teilweise gebuggt, deswegen hier in schleife

    response = requests.post(urlfing, headers=headers, data=json.dumps(query_params)) #übergeben
    return response.json() # als json parsen
def scrape_followers(username, max_count, headers): #selbes vorgehen wie bei den Following
    query_params = {
        "username": username,
        "max_count": max_count
    }
    response = requests.post(urlf, headers=headers, data=json.dumps(query_params))
    return response.json()
date_sections = generate_date_range(start_date, end_date) #Aufrufen der Datumsfunktion

def safe_json(val): # Funktion zur Behandlung der Dataframes für die Datenbank, für die Videos
    # 1. NA / None prüfen
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    # Listen und Dictionaries als JSON-String speichern
    if isinstance(val, (list, dict)):
        return json.dumps(val)
    # NumPy-Arrays zuerst in eine Liste umwandeln, dann als JSON-String speichern
    if isinstance(val, np.ndarray):
        return json.dumps(val.tolist())
   # Alle anderen Typen einfach in einen String konvertieren
    return str(val)

def json_to_videos_df(df_videos): #Funktion um die Dataframes für die DB vorzuverarbeiten
    """
    Wandelt df_videos (oder JSON-Liste) in ein sauberes DataFrame für MySQL um.
    Reihenfolge der Spalten/JSON-Einträge spielt keine Rolle.
    """
    all_videos = []
    # Alle Zeilen im DataFrame iterieren
    for idx, row in df_videos.iterrows(): #jeweils entsprechend dem Datentyp bearbeiten und in ein neues Dataframe einfügen
        video_dict = {}
        video_dict["id"] = row.get("id")
        video_dict["username"] = row.get("username")
        video_dict["video_description"] = row.get("video_description")
        video_dict["voice_to_text"] = row.get("voice_to_text")
        video_dict["type"] = row.get("type")
        video_dict["comment_count"] = pd.to_numeric(row.get("comment_count"), errors="coerce")
        video_dict["share_count"] = pd.to_numeric(row.get("share_count"), errors="coerce")
        video_dict["view_count"] = pd.to_numeric(row.get("view_count"), errors="coerce")
        video_dict["like_count"] = pd.to_numeric(row.get("like_count"), errors="coerce")
        video_dict["favorites_count"] = pd.to_numeric(row.get("favorites_count"), errors="coerce")
        video_dict["region_code"] = row.get("region_code")
        video_dict["playlist_id"] = row.get("playlist_id")
        video_dict["music_id"] = row.get("music_id")
        # create_time: nur konvertieren wenn es wirklich eine Zahl ist
        create_time = row.get("create_time")
        video_dict["create_time"] = (
            pd.to_datetime(create_time, unit="s", errors="coerce")
            if isinstance(create_time, (int, float, str))
            else None
        )
        video_dict["video_duration"] = pd.to_numeric(row.get("video_duration"), errors="coerce")
        video_dict["is_stem_verified"] = row.get("is_stem_verified")
        video_dict["video_label"] = json.dumps(row.get("video_label")) if row.get("video_label") else None
        video_dict["video_mention_list"] = safe_json(row.get("video_mention_list"))
        video_dict["effect_info_list"] = safe_json(row.get("effect_info_list"))
        video_dict["hashtag_info_list"] = safe_json(row.get("hashtag_info_list"))
        video_dict["sticker_info_list"] = safe_json(row.get("sticker_info_list"))
        video_dict["hashtag_names"] = safe_json(row.get("hashtag_names"))
        video_dict["video_tag"] = safe_json(row.get("video_tag"))
        all_videos.append(video_dict)
    df_videos_clean = pd.DataFrame(all_videos)
    return df_videos_clean
def df_from_index(df_userinfo): #darstellung der User Informationen vorbearbeiten, da die darstellung so nicht in die DB passt
    """
    Wandelt ein DataFrame mit Zeilen-Index als Keys in eine saubere
    User-Zeile für MySQL um.
    """
    # Zeilenindex in Spalten umwandeln
    df_clean = df_userinfo["data"].to_frame().T  # .T = Transpose → Index → Spalte
    # Datentypen casten
    int_cols = ["follower_count", "following_count", "likes_count", "video_count"]
    for col in int_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0).astype(int)
             # Verified-Flag → 1/0 Integer
    if "is_verified" in df_clean.columns:
        df_clean["verified"] = df_clean["is_verified"].apply(lambda x: 1 if x else 0)
        df_clean.drop(columns=["is_verified"], inplace=True)
    # Strings casten
    str_cols = ["avatar_url", "display_name", "bio_description", "bio_url"]
    for col in str_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str)
    return df_clean

def json_to_comments_df(df_comments): #kommentare vorverarbeiten
    """
    Wandelt df_comments in ein sauberes DataFrame für MySQL um.
    Reihenfolge der Spalten spielt keine Rolle.
    """
    all_comments = []
    for idx, row in df_comments.iterrows():
        comment_dict = {
            "id": pd.to_numeric(row.get("id"), errors="coerce"),
            "video_id": pd.to_numeric(row.get("video_id"), errors="coerce"),
            "parent_comment_id": pd.to_numeric(row.get("parent_comment_id"), errors="coerce")
                                 if row.get("parent_comment_id") else None,
            "text": row.get("text"),
            "like_count": pd.to_numeric(row.get("like_count"), errors="coerce"),
            "reply_count": pd.to_numeric(row.get("reply_count"), errors="coerce")
                           if "reply_count" in row else None,
            "create_time": pd.to_datetime(row.get("create_time"), unit="s", errors="coerce")
        }
        all_comments.append(comment_dict)

    df_comments_clean = pd.DataFrame(all_comments)
    return df_comments_clean
######VIDEOS####
for username in usernames1: # über alle usernamen in dem oben festgelegten dataframe
    for date_pair in tqdm(date_sections):
        #feste parameter
        start_date = date_pair[0]
        end_date = date_pair[1]
        print("Current date range:",date_pair)
        print("-"*20)
#parameter für die pagination
        cursor = 0
        has_more = True
        search_id = ""
        while has_more == True: #solange iterieren wie True zurückgegeben wird
            temp_data = scrape_videos_pagination(username, max_count, start_date, end_date, headers, search_id, cursor) #Aufruf der entsprechenden funktion
            # Ausgabe für Verfolfung
            print(username)
            print("error code and message:",temp_data["error"]["code"], temp_data["error"]["message"])

            #print("HTTP Status:", response.status_code) #error checl
            #print("Full Response:", response.text)  # ← das zeigt error.code, message, log_id
            #r = response.json() #error check
            #print("Parsed Error:", r.get("error", "No error field")) #error check

            print("cursor:",temp_data["data"]["cursor"])
            print("has_more:",temp_data["data"]["has_more"])
            # set cursor, has_more, and search_id based on previous request
            cursor = temp_data["data"]["cursor"]
            has_more = temp_data["data"]["has_more"]
            #search_id = temp_data["data"]["search_id"]

            # Collect retrieved data for each iteration directly as a data frame
            data.append(pd.DataFrame(temp_data["data"]["videos"]))

            print("Wait ...") #to avoid error thrown by API, unclear that this is the actual issue
            time.sleep(10)
            print("_"*10)

#videos in dataframe sammeln
df_videos = pd.concat(data, axis=0).reset_index(drop=True)
print(len(df_videos))#kontrolle
print(df_videos.head(5)) #kontrolle
if not df_videos.empty: #sofern das dataframe nicht leer ist
    df_videos['type'] = 'VIDEOS' # einen typ anfügen, für Alex ür SoNa

    df_videos_clean = json_to_videos_df(df_videos) #vorverarbeitung
#
#für die datenbank
#Nur neue Videos einfügen
    existing_video_ids = pd.read_sql("SELECT id FROM videos", con=engine)["id"].tolist()
    df_new_videos = df_videos_clean[~df_videos_clean["id"].isin(existing_video_ids)] #extrahieren der existiernden Inhalte der DB

#Einfügen in MySQL
    with engine.connect() as conn: #DB connecten
       df_new_videos.to_sql( #an die datenbank übergeben
           "videos",
           con=conn,
           if_exists="append",
           index=False,
           method='multi',
       )
       print(df_videos_clean)
else:
    print("keine Videos, nichts in die Datenbank")

if not df_videos.empty: #wenn Videos vorhanden sind werden kommentare gesamelt
    print(f"{len(df_videos)} Videos gefunden → Comments scrapen")
    spalte = df_videos['id'] #nutzen der id spalte der videos
    liste = spalte.tolist() # Als Liste weitergeben
    listemit = [f"{item}" for item in liste]
    commentslist = listemit #in Liste zusammenfügen für die Weiternutzung in den Kommentaren

####KOMMENTARE #####
    for comment in commentslist:# alle video_ids in der liste nutzen
        cursor = 0 #neu initialisieren
        has_more = True

        while has_more == True: #sofern true zurückkommt
            tempc_data = scrape_comments_pagination(comment, max_count, headers, cursor) #entsprechende funktion aufrufen
            #ausgeben für verfolgug
            print(comment)
            print("error code and message:",tempc_data["error"]["code"], tempc_data["error"]["message"])
            print("cursor:",tempc_data["data"]["cursor"])
            print("has_more:",tempc_data["data"]["has_more"])
            print("_"*10)
            # set cursor, has_more, and search_id based on previous request
            cursor = tempc_data["data"]["cursor"] #neuzuweisung
            has_more = tempc_data["data"]["has_more"] #neuzuweisung
            # Collect retrieved data for each iteration directly as a data frame
            datac.append(pd.DataFrame(tempc_data["data"]["comments"]))
            # Critical: The API throws errors if one waits no 10 seconds between repeated requests with a session id.

            time.sleep(10)
        df_comments = (pd.concat(datac, axis=0).reset_index #alles in einem dataframe sammeln
                    (drop=True))
        df_comments_clean = json_to_comments_df(df_comments) #vorverarbeiten
#
# Einfügen in die datenbank

# Nur neue Kommentare einfügen über die Selektierung der Existierenden
        existing_comment_ids = pd.read_sql("SELECT id FROM comments", con=engine)["id"].tolist()
        df_new_comments = df_comments_clean[~df_comments_clean["id"].isin(existing_comment_ids)] #nur neue einfügen

# Einfügen in MySQL
        with engine.connect() as conn: #einfügen
            df_new_comments.to_sql(
            "comments",
            con=conn,
            if_exists="append",
            index=False,
            method='multi',
        )
        print(len(df_comments)) #nachverfolgung

else: #falls keine kommentare
    print(f"Keine Videos für {username} am {date_pair[0]} → Comments übersprungen")

####USER INFOs####
for username in usernames1: #selbes Prinzip für die User
    # We call our scraping function, providing all the previously defined variables
    temp_datau = scrape_user(username, headers)
    # We print for each request some info so we understand better what is going on
    print(username)
    # error message/ ok message
    print("error code and message:", temp_datau["error"]["code"], temp_datau["error"]["message"])
    print("_" * 10)  # seperator
    # append each request's response to our data list
    datau.append(pd.DataFrame(temp_datau)) #Dataframe bauen
df_userinfo = pd.concat(datau, axis=0)

df_users_clean = df_from_index(df_userinfo) #vorverarbeitung
# Alle NaN in None umwandeln
df_users_clean_db = df_users_clean.where(pd.notnull(df_users_clean), None) #die hier
usernameInfo =usernames1[0]  #anfügen des usernames, der kommt nicht nochmal extra raus
df_users_clean_db['username'] = usernameInfo

print(df_users_clean_db)
from sqlalchemy.dialects.mysql import insert

# Beispiel: user_table = SQLAlchemy Table Objekt
from sqlalchemy import Table, MetaData #einfügen in die datenbank, über Aktualisierung
metadata = MetaData()
user_table = Table("user", metadata, autoload_with=engine)
with engine.begin() as conn:  # begin = Transaktion
    for i, row in df_users_clean_db.iterrows():
        stmt = insert(user_table).values(row.to_dict())
        stmt = stmt.on_duplicate_key_update(
            {col: stmt.inserted[col] for col in df_users_clean_db.columns if col != "username"}
        )
        conn.execute(stmt)

#####FOLLOWING ##
for username in usernames1: #über den Kanalnamen iterien
    cursor = None
    has_more = True #wieder alles neu vergeben
    max_count = 100
    while has_more == True:
        temp_datafing = scrape_following(username, max_count, headers, cursor) #funktion für Following
        print(username) #Nachverfolgung
        print("error code and message:",temp_datafing["error"]["code"], temp_datafing["error"]["message"]) #fehlerbehandlung falls das following privat ist/jegliche andere fehler
        if (temp_datafing["error"]["code"] != "ok" or
            "private" in temp_datafing["error"]["message"].lower() or
            not temp_datafing["data"]["user_following"]):
            print(f"{username}: Privat/Keine Daten → überspringe")
            break
        print("cursor:",temp_datafing["data"]["cursor"])
        print("has_more:",temp_datafing["data"]["has_more"])
        print("_"*10)
        cursor = temp_datafing["data"]["cursor"]  ##neuvergeben
        has_more = temp_datafing["data"]["has_more"]

        datafing.append(pd.DataFrame (temp_datafing["data"]["user_following"])) #dataframe bauen

        time.sleep(10)
df_following = pd.concat(datafing, axis=0) if datafing else pd.DataFrame() #dataframe bauen
if not df_following.empty: #wenn Following vorhanden
    df_following['request_time'] = datetime.now() #zeit der Abfrage hinzufügen
    request_user =usernames1[0]
    df_following['request_username'] = request_user #den usernamen anfügen über dem abgefragt wurde

    #df_following = df_following.where(pd.notnull(df_follower), None)
    from sqlalchemy import Table, MetaData
    from sqlalchemy.dialects.mysql import insert
#In die Datenbank überführen, solange neu
    metadata = MetaData()
    following_table = Table("following", metadata, autoload_with=engine)
#
# # NaN → None
    df_following = df_following.where(pd.notnull(df_following), None)

    with engine.begin() as conn:
        for i, row in df_following.iterrows():
            stmt = insert(following_table).values(row.to_dict())
#     # Upsert: alles außer den Schlüsselspalten
            stmt = stmt.on_duplicate_key_update(
                {col: stmt.inserted[col]
                for col in df_following.columns
                if col not in ["username", "request_username"]}
            )
            conn.execute(stmt)
     print(df_following.head(25) if not df_following.empty else "Following ist leer, keine Daten")
#    # df_following.to_json(r"C:\Users\nbergma1\PyCharmMiscProject\Following.json", orient='records', indent=2, force_ascii=False) #notfallmäßige Speicherung in JSON, nur kurzzeitig nötig gewesen
 else:
     print("leere Following")



file_path_f = r"C:\Users\nbergma1\PyCharmMiscProject\Following.json"
file_path_fo = r"C:\Users\nbergma1\PyCharmMiscProject\Follower_linke.json"

def append_to_json(df, file_path): #für die Überführung inJSON für die follower, theoretisch hier sinnlos, weil da duplikate entstehen, aber kann man für andere sachen zweckentfremden
    df = df.copy()
    # Alle datetime-Spalten automatisch zu ISO-Strings machen
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
    new_records = df.to_dict(orient="records")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                existing_records = json.load(f)
            except json.JSONDecodeError:
                existing_records = []
        combined_records = existing_records + new_records
    else:
        combined_records = new_records

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(combined_records, f, indent=2, ensure_ascii=False)
###FOLLOWER###
for username in usernames1:
    runden = 0  # ← Neuer Zähler für 3 Runden
    max_count = 100
    cursor = None
    has_more = True
    while has_more == True and runden <= 550:  # selbes prinzip wie bei dem following, nur das nach 550 Runden beendet wird, damit das token nicht in der Abfrage abläuft
        print(f"Runde {runden} ")
        temp_dataf = scrape_followers(username, max_count, headers)
        print(username)
        print("error code and message:", temp_dataf["error"]["code"], temp_dataf["error"]["message"])
        print("cursor:", temp_dataf["data"]["cursor"])
        print("has_more:", temp_dataf["data"]["has_more"])
        print("_"*10)
        cursor = temp_dataf["data"]["cursor"]
        has_more = temp_dataf["data"]["has_more"]
        dataf.append(pd.DataFrame(temp_dataf["data"]["user_followers"]))
        runden += 1  # ← Zähler erhöhen
        time.sleep(10)
    df_follower = pd.concat(dataf, axis=0) if dataf else pd.DataFrame()
    df_follower['request_time'] = datetime.now()
    request_user =usernames1[0]
    df_follower['request_username'] = request_user

    print(df_follower.head(25) if not df_follower.empty else "Iteration abgebrochen")

    print(df_follower.head(25))
    print(len(df_follower))
    append_to_json(df_follower, file_path_fo) #in die JSON datei anfügen
    df_follower = df_follower.where(pd.notnull(df_follower), None)

#theoretisch in die Datenbank, statt
    # metadata1 = MetaData()
    # follower_table = Table("follower", metadata1, autoload_with=engine)
    # # NaN → None
    # df_follower = df_follower.where(pd.notnull(df_follower), None)
    #
    # with engine.begin() as conn:
    #     for i, row in df_follower.iterrows():
    #         stmt = insert(follower_table).values(row.to_dict())
    #     # Upsert: alles außer den Schlüsselspalten
    #         stmt = stmt.on_duplicate_key_update(
    #             {col: stmt.inserted[col]
    #             for col in df_follower.columns
    #             if col not in ["username", "request_username"]}
    #         )
    #         conn.execute(stmt)


#nach dem selben prinzip wie im Sammelskript werden die angepinnten, gelikten und reposteten videos abgefragt

# url_pinned = "https://open.tiktokapis.com/v2/research/user/pinned_videos/?fields=id,create_time,username,region_code,video_description,music_id,like_count,comment_count,share_count,view_count,hashtag_names, is_stem_verified, favorites_count, video_duration,hashtag_info_list, sticker_info_list, effect_info_list, video_mention_list,video_label,video_tag"
# url_comments = 'https://open.tiktokapis.com/v2/research/video/comment/list/?fields=id,like_count,create_time,text,video_id,parent_comment_id'
#
# max_count = 100
# def scrape_pinned_vids(username, max_count, headers):
#     # We ask the API: Give us all videos uploaded between start_date and end_date whose uploader is in our username lists
#     query_params = {
#                    # "max_count": max_count,
#                     "username": username,
#                     }
#     # Make the call and transform the response to a JSON file
#     response = requests.post(url_pinned, headers=headers, data=json.dumps(query_params))
#     r = response.json()
#     # return the response parsed as a JSON file
#     return r
# def scrape_comments_pagination(video_id, max_count, headers, cursor):
#         data = {
#             "video_id": video_id,
#             "max_count": max_count,
#
#             "cursor": cursor
#         }
#         response = requests.post(url_comments, headers=headers, data=json.dumps(data))
#         comments_data = response.json()
#         return comments_data
# # init variable to add collected data to
# data_pinned = []
# for username in usernames1:
#     # We call our scraping function, providing all the previously defined variables
#     temp_data_pinned = scrape_pinned_vids(username, max_count, headers)
#     # We print for each request some info so we understand better what is going on
#     print(username)
#
#     if temp_data_pinned.get("error", {}).get("code") != "ok":
#         print("API-Fehler:", temp_data_pinned["error"])
#         continue
#     # index where data collection stopped
#    # print("cursor:",temp_data["data"]["cursor"])
#     # indicates if the requested sample has more entries than the cursor index
#     #print("has_more:",temp_data["data"]["has_more"])
#     # error message/ ok message
#     #print("error code and message:",temp_data["error"]["code"], temp_data["error"]["message"])
#     print("_"*10) # seperator
#     # append each request's response to our data list
#     data_pinned.append(pd.DataFrame(temp_data_pinned["data"]["pinned_videos_list"]))
#    # datalv.append(pd.DataFrame(temp_data))
# df_pinned = pd.concat(data_pinned, axis=0)
# df_pinned.head(4)
# print(df_pinned)
# df_pinned.to_json(r"C:\Users\Nelly\PyCharmMiscProject\BA\pinnedVideos.json", orient='records', indent=2, force_ascii=False)
# if not df_pinned.empty:
#     print(f"{len(df_pinned)} Videos gefunden → Comments scrapen")
#     spalte = df_pinned['id']
# # Als Liste weitergeben
#     liste = spalte.tolist()
#     liste10 = liste[0:10]
#     listemit = [f"{item}" for item in liste10]
# #commentslist = ["7574378968174890262"]
#     commentslist = listemit
#     max_count = 100
#     data_comments = []
#     for comment in commentslist:
#         # initial cursor and has_more
#         cursor = 0
#         has_more = True
#         while has_more == True:
#             temp1_data = scrape_comments_pagination(comment, max_count, headers, cursor)
#             # Again, print out to understand better what is happening in each iteration
#             print(comment)
#             print("error code and message:",temp1_data["error"]["code"], temp1_data["error"]["message"])
#             print("cursor:",temp1_data["data"]["cursor"])
#             print("has_more:",temp1_data["data"]["has_more"])
#             print("_"*10)
#             # set cursor, has_more, and search_id based on previous request
#             cursor = temp1_data["data"]["cursor"]
#             has_more = temp1_data["data"]["has_more"]
#             # Collect retrieved data for each iteration directly as a data frame
#             data_comments.append(pd.DataFrame(temp1_data["data"]["comments"]))
#             # Critical: The API throws errors if one waits no 10 seconds between repeated requests with a session id.
#             # However, they do not specify that this is the frequency of requests issue!
#             time.sleep(10)
#
#     df_comments= pd.concat(data_comments, axis=0).reset_index(drop=True)
#     print(len(df_comments))
#     df_comments.head(10)

# urllv = "https://open.tiktokapis.com/v2/research/user/liked_videos/?fields=id,create_time,username,region_code,video_description,music_id,like_count,comment_count,share_count,view_count,hashtag_names,is_stem_verified, video_duration,hashtag_info_list,sticker_info_list,effect_info_list,video_mention_list,video_label,video_tag"
#
# # With the header, we verify ourselves with our access token and indicate the format of the data we want to scrape
# headers = {
#     "Authorization": f"Bearer {access_token}",
#     "Content-Type": "application/json"
# }
# max_count = 100
# def scrape_liked_vids(username, max_count, headers):
#     # We ask the API: Give us all videos uploaded between start_date and end_date whose uploader is in our username lists
#     query_params = {
#                     "max_count": max_count,
#                     "username": username,
#                     }
#     # Make the call and transform the response to a JSON file
#     response = requests.post(urllv, headers=headers, data=json.dumps(query_params))
#     r = response.json()
#     # return the response parsed as a JSON file
#     return r
# datalv = []
# for username in usernames:
#
#     temp_data_liked = scrape_liked_vids(username, max_count, headers)
#     # We print for each request some info so we understand better what is going on
#     print(username)
#     if temp_data_liked.get("error", {}).get("code") != "ok":
#         print("API-Fehler:", temp_data["error"])
#         continue
#     # index where data collection stopped
#    # print("cursor:",temp_data["data"]["cursor"])
#     # indicates if the requested sample has more entries than the cursor index
#     #print("has_more:",temp_data["data"]["has_more"])
#     # error message/ ok message
#     print("error code and message:",temp_data_liked["error"]["code"], temp_data_liked["error"]["message"])
#     print("_"*10) # seperator
#     # append each request's response to our data list
#    # datalv.append(pd.DataFrame(temp_data["data"]["user_liked_videos"]))
#     datalv.append(pd.DataFrame(temp_data_liked))
# df_liked = pd.concat(datalv, axis=0)
# df_liked.head(4)

#reposted vids

# urlrep = "https://open.tiktokapis.com/v2/research/user/reposted_videos/?fields=id,create_time,username, region_code, video_description, music_id, like_count, comment_count, share_count, view_count, hashtag_names, is_stem_verified, video_duration, hashtag_info_list, sticker_info_list, effect_info_list, video_mention_list, video_label,video_tag"
#
# # With the header, we verify ourselves with our access token and indicate the format of the data we want to scrape
# headers = {
#     "Authorization": f"Bearer {access_token}",
#     "Content-Type": "application/json"
# }
#
# max_count = 100
# #cursor = 1
# def scrape_reposted_vids(username, max_count,headers):
#     # We ask the API: Give us all videos uploaded between start_date and end_date whose uploader is in our username lists
#     query_params = {
#                     "max_count": max_count,
#                     "username" : username
#
#                     }
#     # Make the call and transform the response to a JSON file
#     response = requests.post(urlrep, headers=headers, data=json.dumps(query_params))
#     r = response.json()
#     # return the response parsed as a JSON file
#     return r
#
# # init variable to add collected data to
# data = []
# for username in usernames:
#     # We call our scraping function, providing all the previously defined variables
#     temp_data = scrape_reposted_vids(username, max_count, headers)
#     # We print for each request some info so we understand better what is going on
#     print(username)
#
#     if temp_data.get("error", {}).get("code") != "ok":
#         print("API-Fehler:", temp_data["error"])
#         continue
#     # index where data collection stopped
#     print("cursor:",temp_data["data"]["cursor"])
#     # indicates if the requested sample has more entries than the cursor index
#     print("has_more:",temp_data["data"]["has_more"])
#     # error message/ ok message
#     print("error code and message:",temp_data["error"]["code"], temp_data["error"]["message"])
#     print("_"*10) # seperator
#     # append each request's response to our data list
#     #if "user_reposted_videos" in temp_data["data"]:
#       #  data.append(pd.DataFrame(temp_data["data"]["reposted_videos"]))
#     #else:
#      #print(f"Keine reposteten Videos für {username} gefunden.")
#
#     data.append(pd.DataFrame(temp_data["data"]["reposted_videos"]))
#     #data.append(pd.DataFrame(temp_data))
# df = pd.concat(data, axis=0)
# df.head(10)

#playlist info

# url = "https://open.tiktokapis.com/v2/research/video/query/?fields=id,video_description,create_time,region_code,share_count,view_count,like_count,comment_count,music_id,hashtag_names,username,effect_ids,playlist_id,voice_to_text,video_duration,hashtag_info_list,sticker_info_list,sticker_info_list,effect_info_list,video_mention_list,video_label,is_stem_verified,favorites_count,video_tag"
#
# # With the header, we verify ourselves with our access token and indicate the format of the data we want to scrape
# headers = {
#     "Authorization": f"Bearer {access_token}",
#     "Content-Type": "application/json"
# }
# # We also need to set additional query parameters:
# # First, the start and end date on which the videos have been uploaded
# # "YYYYMMDD" format as string, both are meant inclusive, no more than 30 days time frame possible
# # We will look at a workaround to the 30-day rule in a minute.
# start_date = "20251201" #start und endatum zum suchen, anpassen exlusive des end_dates
# end_date = "20251209"
# # The default number of items returned by a request is 20.
# # We set it to a maximum of 100 entries.
# max_count = 100
# def scrape_videos_userbased(username, max_count, start_date, end_date, headers):
#     # We ask the API: Give us all videos uploaded between start_date and end_date whose uploader is in our username lists
#     query_params = {"query": { "and": [ {"operation": "EQ", "field_name": "username", "field_values": [username]} ] },
#                     "max_count": max_count,
#                     "start_date": start_date,
#                     "end_date": end_date
#                     }
#     # Make the call and transform the response to a JSON file
#     response = requests.post(url, headers=headers, data=json.dumps(query_params))
#     r = response.json()
#     # return the response parsed as a JSON file
#     return r
#
# # init variable to add collected data to
# data = []
# for username in usernames:
#     # We call our scraping function, providing all the previously defined variables
#     temp_data = scrape_videos_userbased(username, max_count, start_date, end_date, headers)
#     # We print for each request some info so we understand better what is going on
#     print(username)
#     # index where data collection stopped
#     print("cursor:",temp_data["data"]["cursor"])
#     # indicates if the requested sample has more entries than the cursor index
#     print("has_more:",temp_data["data"]["has_more"])
#     # error message/ ok message
#     print("error code and message:",temp_data["error"]["code"], temp_data["error"]["message"])
#     print("_"*10) # seperator
#     # append each request's response to our data list
#     data.append(pd.DataFrame(temp_data["data"]["videos"]))
#
# df = pd.concat(data, axis=0)
# df.head(4)
#
#
# #spalte = df["playlist_id"] # geht nicht ohne Playlist ID und die hab ich momentan nicht
# #print(df["playlist_id"].dtype)
#
# # playlist_id als echte ganze Zahl (int64) speichern
# #df["playlist_id"] = df["playlist_id"].astype("int64")
# df["playlist_id"] = pd.to_numeric(df["playlist_id"], errors='coerce').astype('Int64')
# #print(df["playlist_id"].dtype)  # sollte 'Int64' sein
# #print(df["playlist_id"].head())
#
# spalte = df["playlist_id"]
#
# # Als Liste weitergeben
# liste = spalte.tolist()
# liste10 = liste[0:10]
# listemit = [f"{item}" for item in liste10]
#
# #usernames = ["afdfraktionimbundestag","tagesschau", "zeitimbild","20minuten"]
# #usernames = str(df["playlist_id"].iloc[0])
# usernames = str(7470435077793516544) #playlist  id
# #usernames = listemit
# #print(listemit)
#Playlistinfo #stand 26.11.2025
# urlplaylist = "https://open.tiktokapis.com/v2/research/playlist/info/"
# def scrape_playlist_ID(username, max_count, headers):
#     # We ask the API: Give us all videos uploaded between start_date and end_date whose uploader is in our username lists
#     query_params = {
#                     "username": username,
#                     "max_count": max_count
#
#                     }
#     # Make the call and transform the response to a JSON file
#     response = requests.post(urlplaylist, headers=headers, data=json.dumps(query_params))
#     r = response.json()
#     # return the response parsed as a JSON file
#     return r
#
# # init variable to add collected data to
# dataf = []
# for username in usernames:
#     # We call our scraping function, providing all the previously defined variables
#     temp_dataf = scrape_playlist_ID(username, max_count, headers)
#     # We print for each request some info so we understand better what is going on
#     print(username)
#     if temp_dataf.get("error", {}).get("code") != "ok":
#         print("API-Fehler:", temp_dataf["error"])
#         continue
#     # index where data collection stopped
#    # print("cursor:",temp_dataf["data"]["cursor"])
#     # indicates if the requested sample has more entries than the cursor index
#     #print("has_more:",temp_dataf["data"]["has_more"])
#     # error message/ ok message
#     #print("error code and message:",temp_dataf["error"]["code"], temp_dataf["error"]["message"])
#     print("_"*10) # seperator
#     # append each request's response to our data list
#     dataf.append(pd.DataFrame(temp_dataf["data"]["playlist_id"]))
#
# df = pd.concat(dataf, axis=0)
# df.head(4)

# shop info

# urlshop = "https://open.tiktokapis.com/v2/research/tts/shop/?fields=shop_name,shop_rating,shop_review_count,item_sold_count,shop_id"
#
# # With the header, we verify ourselves with our access token and indicate the format of the data we want to scrape
# headers = {
#     "Authorization": f"Bearer {access_token}",
#     "Content-Type": "application/json"
# }
#
# limit = 5
#
# def scrape_shop_info(username,limit, headers):
#     # We ask the API: Give us all videos uploaded between start_date and end_date whose uploader is in our username lists
#     query_params = {
#                     "username": username,
#                     "limit": limit
#
#                     }
#     # Make the call and transform the response to a JSON file
#     response = requests.post(urlshop, headers=headers, data=json.dumps(query_params))
#     r = response.json()
#     # return the response parsed as a JSON file
#     return r
#
# # init variable to add collected data to
# dataf = []
# for username in usernames:
#     # We call our scraping function, providing all the previously defined variables
#     temp_dataf = scrape_shop_info(username, max_count, headers)
#     # We print for each request some info so we understand better what is going on
#     print(username)
#     if temp_dataf.get("error", {}).get("code") != "ok":
#         print("API-Fehler:", temp_dataf["error"])
#         continue
#     # index where data collection stopped
#    # print("cursor:",temp_dataf["data"]["cursor"])
#     # indicates if the requested sample has more entries than the cursor index
#    # print("has_more:",temp_dataf["data"]["has_more"])
#     # error message/ ok message
#     print("error code and message:",temp_dataf["error"]["code"], temp_dataf["error"]["message"])
#     print("_"*10) # seperator
#     # append each request's response to our data list
#     #dataf.append(pd.DataFrame(temp_dataf["data"]["shop_name"]))
#     print("test", temp_dataf["data"]["shop_name"])
# df = pd.concat(dataf, axis=0)
# df.head(4)