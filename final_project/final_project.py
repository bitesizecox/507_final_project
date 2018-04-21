import sqlite3
import csv
from bs4 import BeautifulSoup
import requests
import json
import locale
import secrets
import plotly.plotly as py
import plotly.graph_objs as go

locale.setlocale(locale.LC_ALL, 'en_US')

DBNAME = 'CollegeTuitionUSA.db'
TUITION = 'data/college_tuition.csv'
STATESINCOME = 'data/median_income.csv'
CITIES = 'data/us_postal_codes.csv'

CURRENT_SEARCH = None
CURRENT_SCHOOL = None
SEARCH_HISTORY = []
VIEW_HISTORY = []
CART = []

class JobOpps():
    def __init__(self, name, lat, lng):
        self.name = name
        self.lat = lat
        self.lng = lng

    def __str__(self):
        return self.name

class College():
    wage = 7.25
    latitude = None
    longitude = None
    def __init__(self, name, type_, status, tuition, motto=None, president=None,
                 colors=None, students=None, city=None, state=None, website=None, established=None, mascot=None):
        self.name = name
        self.type = type_
        self.status = status.lower()
        self.state = state
        self.tuition = int(tuition)
        self.motto = motto
        self.president = president
        self.colors = colors
        self.students = students
        self.city = city
        self.website = website
        self.established = established
        self.mascot = mascot
        self.latitude = None
        self.longitude = None

    def pay_tuition(self):
        total_hours = round(self.tuition / self.wage)
        return round(total_hours / 52)

    def about(self):
        print('\n')
        print('\033[1m'+self.name)
        # print('\033[0m'+'\n')
        if self.motto != None:
            print('\033[0m'+"{:<16} {}".format('Motto: ', self.motto))
        if self.city != None:
            print('\033[0m'+"{:<16} {}, {}".format('Location: ', self.city, self.state))
        else:
            print('\033[0m'+"{:<16} {}".format('Location: ',self.state))
        print("{:<16} {} {} college".format('Type: ', self.type, self.status))
        if self.established != None:
            print("{:<16} {}".format('Established: ', self.established))
        if self.students != None:
            print("{:<16} {}".format('# Students: ', self.students))
        print("{:<16} ${:,}".format('Annual Tuition: ', self.tuition))
        if self.president != None:
            print("{:<16} {}".format('President: ', self.president))
        if self.colors != None:
            print("{:<16} {}".format('School Colors: ', self.colors))
        if self.mascot != None:
            print("{:<16} {}".format('Mascot: ', self.mascot))
        if self.website != None:
            print("{:<16} {}".format('Website: ', self.website))
        if self.city == None:
            print('\n')
            print("Unfortunately, there was no additional information available on Wikipedia about this school.")
        print("\n")
        print("You would have to work about \033[1m{:,}\033[0m hours a week at the federal minimum wage (thats $7.25 an hour!) to pay your tuition out of pocket.".format(self.pay_tuition()))
        print("...and that's not including rent or food! Better start saving!")
        print("\n")

    def __str__(self):
        if self.city != None:
            return("{}: {} {} college; located in {}, {}; cost: ${:,} per year.".format(self.name, self.type, self.status, self.city, self.state, self.tuition))
        else:
            return("{}: {} {} college; located {}; cost: ${:,} per year.".format(self.name, self.type, self.status, self.state, self.tuition))


def init_tuition_db(database_name):
    conn = sqlite3.connect(database_name)
    cur = conn.cursor()

    statement = '''
        DROP TABLE IF EXISTS 'Colleges';
    '''
    cur.execute(statement)

    statement = '''
        DROP TABLE IF EXISTS 'StatesIncome';
    '''
    cur.execute(statement)

    statement = '''
        DROP TABLE IF EXISTS 'Cities';
    '''
    cur.execute(statement)
    conn.commit()

    statement = '''
        CREATE TABLE 'Colleges' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'Name' TEXT NOT NULL,
            'Type' TEXT,
            'Status' TEXT,
            'StateId' INTEGER,
            'StateAbbr' TEXT,
            'Tuition' INTEGER      
        );
    '''
    cur.execute(statement)

    statement = '''
        CREATE TABLE 'StatesIncome' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'StateName' TEXT,
            'StateAbbr' TEXT,
            'Median Income' INTEGER
        );
    '''
    cur.execute(statement)

    statement = '''
    CREATE TABLE 'Cities' (
            'Id' INTEGER PRIMARY KEY,
            'CityName' TEXT,
            'StateId' INTEGER,
            'State' TEXT,
            'Latitude' INTEGER,
            'Longitude' INTEGER
        );
    '''
    cur.execute(statement)
    conn.commit()
    conn.close()


def extract_tuition_data(csv_file):
    csvFile = open(csv_file)
    csvReader = csv.reader(csvFile)
    data = []
    for row in csvReader:
        data.append(row)
    csvFile.close()

    new_data = []
    for row in data[1:]:
        if 'PR' in row[5]:
            pass
        else:
            # print (row)
            sector = row[1].split(',')
            row[1] = sector[0]
            if 'public' in sector[1]:
                row.insert(2, 'Public')
            else:
                row.insert(2, 'Private')
            if ',' in row[7]:
                cost_split = row[7].split(",")
                fixed_cost = ""
                for n in cost_split:
                    fixed_cost += n
                row[7] = fixed_cost
            new_data.append(row)

    return new_data


def extract_state_data(csvfile):
    csvFile = open(csvfile)
    csvReader = csv.reader(csvFile)
    states = []
    data = []
    for r in csvReader:
        if r[2] in states:
            pass
        else:
            row = []
            states.append(r[2])
            row.append(r[2])
            row.append(r[3])
            data.append(row)
    csvFile.close()
    data = data[1:]
    data.sort()

    return data


def extract_income_data(csvfile):
    csvFile = open(csvfile)
    csvReader = csv.reader(csvFile)
    data = []
    for r in csvReader:
        row = []
        row.append(r[0])
        row.append(r[1])
        data.append(row)
    csvFile.close()

    return data[1:]


def extract_city_data(csv_file):
    csvFile = open(csv_file)
    csvReader = csv.reader(csvFile)
    data = []
    for row in csvReader:
        data.append(row)
    csvFile.close()

    return data


def create_colleges_table(csv_file, database_name):
    tuition_data = extract_tuition_data(csv_file)

    conn = sqlite3.connect(database_name)
    cur = conn.cursor()

    for r in tuition_data[1:]:
        insertion = (None, r[5],r[1],r[2],None,r[6],r[7])
        statement = 'INSERT INTO "Colleges" '
        statement += 'VALUES (?, ?, ?, ?, ?, ?, ?)'
        cur.execute(statement, insertion)

    conn.commit()
    conn.close


def create_statesIncome_table(file1, file2, database_name):
    states_data = extract_state_data(file1)
    income_data = extract_income_data(file2)
    statesIncome_data = []
    count = 0
    for s in states_data[1:]:
        d = []
        d.append(s[0])
        d.append(s[1])
        statesIncome_data.append(d)
    for i in income_data:
        statesIncome_data[count].insert(3, i[1])
        count+=1

    conn = sqlite3.connect(database_name)
    cur = conn.cursor()

    for r in statesIncome_data:
        insertion = (None, r[0], r[1], r[2])
        statement = 'INSERT INTO "StatesIncome" '
        statement += 'VALUES (?, ?, ?, ?)'
        cur.execute(statement, insertion)

    conn.commit()
    conn.close


def create_city_table(csv_file, database_name):
    city_data = extract_city_data(csv_file)

    conn = sqlite3.connect(database_name)
    cur = conn.cursor()

    for r in city_data[1:]:
        insertion = (r[0],r[1],None,r[2],r[5],r[6])
        statement = 'INSERT INTO "Cities" '
        statement += 'VALUES (?, ?, ?, ?, ?, ?)'
        cur.execute(statement, insertion)

    conn.commit()
    conn.close


def update_tables(database_name):
    conn = sqlite3.connect(database_name)
    cur = conn.cursor()

    statement = '''
            UPDATE Colleges
            SET StateId = (
                SELECT StatesIncome.Id FROM StatesIncome
                WHERE StatesIncome.StateAbbr = Colleges.StateAbbr
                );
            '''
    cur.execute(statement)

    statement = '''
            UPDATE Cities
            SET StateId = (
                SELECT StatesIncome.Id FROM StatesIncome
                WHERE StatesIncome.StateName = Cities.State
                );
            '''
    cur.execute(statement)

    conn.commit()
    conn.close()

#database and tables created#

 # Implement Cache
CACHE_FNAME = 'wiki_cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()

except:
    CACHE_DICTION = {}


def params_unique_combination(base_url, params_dict):
    alphabetized_keys = sorted(params_dict.keys())
    res = []
    for k in alphabetized_keys:
        res.append("{}-{}".format(k, params_dict[k]))
    return base_url + "_".join(res)

def make_request_using_cache(base_url, params_dict=None):
    try:
        unique_ident = params_unique_combination(base_url,params_dict)
    except:
        unique_ident = base_url

    if unique_ident in CACHE_DICTION:
        # print("Getting cached data...")
        return CACHE_DICTION[unique_ident]
    else:
        print("Making a request for new data...")
        print("\n")
        resp = requests.get(base_url, params_dict)
        # print(resp.url)
        CACHE_DICTION[unique_ident] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close()
        return CACHE_DICTION[unique_ident]



state_info = extract_state_data(CITIES)
STATENAMES = []
STATEABBRS = []
for s in state_info[1:]:
    STATENAMES.append(s[0].upper())
    STATEABBRS.append(s[1].upper())

def format_string(string):
    if len(string)>=16:
        if "Less than" in string:
            string = "<2 yea" + ".."
        elif "District of" in string:
            string = "Washington D.C."
        else:
            string = string[:16] + "..."
        return string
    else:
        return string

def prettyprint(results):
    if results != []:
        header = "{:<24} {:<8} {:<8} {:<16} {:<15}"
        print_statement = "{:<20} {:<8} {:<8} {:<16} ${:,}"
        print_results = []
        for r in results:
            f = []
            for i in r[:-1]:
                f.append(format_string(i))
            f.append(r[-1])
            print_results.append(print_statement.format(*tuple(f)))

        numbered_results = enumerate(print_results, start=1)
        print("\n")
        print('\033[1m' + header.format("School Name", "Type", "Status", "Location", "An. Tuition"))
        for r in numbered_results:
            if len(print_results) < 10:
                print('\033[0m'+ "{:>1}. {}".format(*r))
            elif len(print_results) < 100:
                print('\033[0m'+ "{:>2}. {}".format(*r))
            else:
                print('\033[0m'+ "{:>3}. {}".format(*r))
        print("\n")
    else:
        print("That search didn't produce any results. Try again!")



def get_coordinates(college_instance):
    google_api = secrets.goog_secret

    base_url="https://maps.googleapis.com/maps/api/place/textsearch/json?"
    params_dict={}
    params_dict['query']=college_instance.name
    params_dict['type']='school'
    params_dict['key']=google_api
    try:
        results_json = make_request_using_cache(base_url, params_dict=params_dict)
        results = json.loads(results_json)
        lat = results['results'][0]["geometry"]["location"]["lat"]
        lng = results['results'][0]["geometry"]["location"]["lng"]
        college_instance.latitude = lat
        college_instance.longitude = lng
        return lat,lng
    except:
        return False

def compare_search(search=CURRENT_SEARCH):
    search_instances=[]
    for s in CURRENT_SEARCH:
        search_instances.append(college_info(s))
    x_vals = []
    y_vals = []
    text = []
    for i in search_instances:
        try:
            x_vals.append(i.name)
            y_vals.append(i.tuition)
            text.append(("{}<br>{};{}".format(i.name,i.type,i.status)))
        except:
            print("Location info unavailable for {}. Excluding {} from search.".format(i.name, i.name))

    trace0 = go.Bar(
        x=x_vals,
        y=y_vals,
        text=text,
        marker=dict(
            color='rgb(158,202,225)',
            line=dict(
                color='rgb(8,48,107)',
                width=1.5,
            )
        ),
        opacity=0.6
    )

    data = [trace0]
    layout = go.Layout(
        title='Search Comparison',
    )

    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='text-hover-bar')


def compare_cart(cart=CART):
    try:
        if CART != []:
            x_vals = []
            y_vals=[]
            for item in cart:
                x_vals.append(item.name)
                y_vals.append(item.tuition)
            data = [go.Bar(
                    x=x_vals,
                    y=y_vals
            )]

            py.plot(data, filename='basic-bar')
        else:
            print("You haven't saved anything to your cart!")
    except:
        print("Having trouble...have you saved anything to your cart?")

def plot_schools(current_search):
    try:
        school_instances=[]
        lat_vals=[]
        lon_vals=[]
        text_vals=[]
        for s in current_search:
            school_instances.append(college_info(s))
        for s in school_instances:
            try:
                coord=get_coordinates(s)
                lat_vals.append(coord[0])
                lon_vals.append(coord[1])
                text_vals.append("{}<br>{}; {}<br>Tuition: ${:,}".format(s.name, s.type, s.status, s.tuition))
            except:
                print("Couldn't get coordinates for {}; continuing without.".format(s.name))
        data = [ dict(
                type = 'scattergeo',
                locationmode = 'USA-states',
                lon = lon_vals,
                lat = lat_vals,
                text = text_vals,
                mode = 'markers',
                marker = dict(
                    size = 16,
                    symbol = 'star',
                ))]

        min_lat = 10000
        max_lat = -10000
        min_lon = 10000
        max_lon = -10000

        for str_v in lat_vals:
            v = float(str_v)
            if v < min_lat:
                min_lat = v
            if v > max_lat:
                max_lat = v
        for str_v in lon_vals:
            v = float(str_v)
            if v < min_lon:
                min_lon = v
            if v > max_lon:
                max_lon = v


        max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
        padding = max_range * .50

        lat_axis = [min_lat, max_lat]
        lon_axis = [min_lon, max_lon]

        center_lat = (max_lat+min_lat) / 2
        center_lon = (max_lon+min_lon) / 2


        layout = dict(
                title = 'Schools in Current Search<br>(Hover for school names)',
                geo = dict(
                    scope='usa',
                    projection=dict( type='albers usa' ),
                    showland = True,
                    landcolor = "rgb(250, 250, 250)",
                    subunitcolor = "rgb(100, 217, 217)",
                    countrycolor = "rgb(217, 100, 217)",
                    lataxis = {'range': lat_axis},
                    lonaxis = {'range': lon_axis},
                    center= {'lat': center_lat, 'lon': center_lon },
                    countrywidth = 3,
                    subunitwidth = 3
                ),
            )

        fig = dict(data=data, layout=layout )
        py.plot( fig, validate=False, filename='schools_in_search' )
        return True
    
    except:
        print("Sorry, but we couldn't get that map for some reason.")
        print("Have you done a search?")
        return False


def plot_jobs(site_object):
    try:
        nearby_jobs = get_jobs(site_object)
        if nearby_jobs == []:
            return None
        else:
            site_name = [site_object.name + " " + site_object.type + site_object.status]
            coordinates = get_coordinates(site_object)
            site_lat = [coordinates[0]]
            site_lon = [coordinates[1]]

            places_names = []
            places_lat_vals = []
            places_lon_vals = []
            for s in nearby_jobs:
                places_names.append(s.name)
                places_lat_vals.append(s.lat)
                places_lon_vals.append(s.lng)

            trace1 = dict(
                    type = 'scattergeo',
                    locationmode = 'USA-states',
                    lon = site_lon,
                    lat = site_lat,
                    text = site_name,
                    mode = 'markers',
                    marker = dict(
                        size = 20,
                        symbol = 'star',
                        color = 'purple'
                    ))

            trace2 = dict(
                    type = 'scattergeo',
                    locationmode = 'USA-states',
                    lon = places_lon_vals,
                    lat = places_lat_vals,
                    text = places_names,
                    mode = 'markers',
                    marker = dict(
                        size = 10,
                        symbol = 'circle',
                        color = 'purple',
                        opacity = .5,
                    ))

            data = [trace1, trace2]

            min_lat = 10000
            max_lat = -10000
            min_lon = 10000
            max_lon = -10000

            for str_v in places_lat_vals:
                v = float(str_v)
                if v < min_lat:
                    min_lat = v
                if v > max_lat:
                    max_lat = v
            for str_v in places_lon_vals:
                v = float(str_v)
                if v < min_lon:
                    min_lon = v
                if v > max_lon:
                    max_lon = v

            center_lat = (max_lat+min_lat) / 2
            center_lon = (max_lon+min_lon) / 2
            
            max_range = max(abs(max_lat - min_lat), abs(max_lon - min_lon))
            padding = max_range * .10
            lat_axis = [min_lat - padding, max_lat + padding]
            lon_axis = [min_lon - padding, max_lon + padding]

            layout = dict(
                    title = 'Places near {} in {}<br>(Hover for site names)'.format(site_object.name, site_object.state),
                    geo = dict(
                        scope='usa',
                        projection=dict( type='albers usa' ),
                        showland = True,
                        showlakes = True,
                        showocean = True,
                        subunitcolor = "rgb(0,0,0)",
                        countrycolor = "rgb(217, 100, 217)",
                        lataxis = {'range': lat_axis},
                        lonaxis = {'range': lon_axis},
                        center= {'lat': center_lat, 'lon': center_lon },
                        countrywidth = 3,
                        subunitwidth = 3
                    )
                )

            fig = dict(data=data, layout=layout )
            py.plot( fig, validate=False, filename='nearby_jobs' )
            return True
    except:
        print("Sorry, but we couldn't get that map for some reason.")
        print("Have you viewed a school?")
        return False


def get_jobs(instance):
    google_api = secrets.goog_secret
    coordinates = get_coordinates(instance)
    if coordinates != False:
        try:
            base_url="https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={},{}".format(CURRENT_SCHOOL.latitude, CURRENT_SCHOOL.longitude)
            params_dict={}
            params_dict['radius']=4828
            # params_dict['type']='establishment'
            params_dict['key']=google_api

            results_json = make_request_using_cache(base_url, params_dict)
            results = json.loads(results_json)

            nearby_places_info = {}
            for r in results["results"]:
                place_name = r["name"]
                place_lat = r["geometry"]["location"]["lat"]
                place_lng = r["geometry"]["location"]["lng"]
                nearby_places_info[place_name] = {"lat":place_lat, "lng":place_lng}

            job_instances = []
            for k in nearby_places_info.keys():
                place = JobOpps(k,nearby_places_info[k]['lat'],nearby_places_info[k]['lng'])
                job_instances.append(place)
            return job_instances
        except:
            return False
    else:
        print("Sorry, but we can't seem to locate that for you right now")
        return False

def scrape_wiki(collegeName):
    try:
        base_url = "https://en.wikipedia.org/wiki/"
        split_name = collegeName.split()
        node = ""
        for w in split_name[:-1]:
            node += w + "_"
        node += split_name[-1]
        college_text = make_request_using_cache(base_url + node)
        college_soup = BeautifulSoup(college_text, "html.parser")

        info_table = college_soup.find(class_ = "infobox vcard")
        info_trs = info_table.find_all('tr')
        extracted_info = []
        for i in info_trs:
            extracted_info.append(i.text)

        semi_fixed_info = []
        for i in extracted_info:
            split = i.split('\n')
            for s in split:
                if s != '':
                    semi_fixed_info.append(s)

        fixed_info =[]
        for i in semi_fixed_info:
            if i[-3] == '[':
                if i[-6] == '[':
                    fixed_info.append(i[:-6])
                else:
                    fixed_info.append(i[:-3])
            elif i[-1] == ']':
                count = 0
                for c in i:
                    if c == '[':
                        break
                    else:
                        count+=1
                fixed_info.append(i[:count])
            else:
                fixed_info.append(i)

        return_info = {'motto':None, 'president':None, 'colors':None, 'students':None,
                        'city':None, 'website':None, 'established':None, 'mascot':None}
        count = 0
        for i in fixed_info:
            if i == "Motto":
                return_info['motto'] = fixed_info[count+1]
            elif i == "President":
                return_info['president'] = fixed_info[count+1]
            elif i == "Colors":
                colors = fixed_info[count+1]
                if u'\xa0' in colors:
                    new_colors = colors.split(u'\xa0')
                    final_colors =''
                    for n in new_colors:
                        if n != "":
                            final_colors += n
                    if final_colors != '':
                        return_info['colors'] = final_colors
                else:
                    return_info['colors'] = colors
            elif i == "Students":
                return_info['students'] = fixed_info[count+1]
            elif i == "Location":
                split_location = fixed_info[count+1].split(', ')
                return_info['city'] = split_location[0]
            elif i == "Website":
                return_info['website'] = fixed_info[count+1]
            elif i == "Established":
                return_info['established'] = fixed_info[count+1]
            elif i == "Mascot":
                return_info['mascot'] = fixed_info[count+1]
            else:
                pass
            count+=1
        return return_info
    except:
        pass


def college_info(college):
    info = {}
    info['name'] = college[0]
    info['type_'] = college[1]
    info['status'] = college[2]
    info['state'] = college[3]
    info['tuition'] = college[4]
    wiki_info = scrape_wiki(info['name'])
    try:
        for k in wiki_info.keys():
            info[k] = wiki_info[k]
    except:
        pass
    college_instance = College(**info)
    return college_instance


def colleges(dictionary):
    orderby = dictionary['orderby']
    sortby = dictionary['sortby']
    state = dictionary['state']
    college_name = dictionary['college_name']
    price_range = dictionary['price_range']
    price_low = dictionary['price_low']
    price_high = dictionary['price_high']
    price = dictionary['price']
    limit = dictionary['limit']

    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    statement = 'SELECT Colleges.Name, Colleges.Type, Colleges.Status, StatesIncome.StateName, Colleges.Tuition '
    statement += 'FROM Colleges '
    statement += 'JOIN StatesIncome ON Colleges.StateAbbr = StatesIncome.StateAbbr '

    if college_name == None:
        if sortby != None:
            if sortby.lower() == "public":
                statement += 'WHERE Status = "Public" '
            elif sortby.lower() == "private":
                statement += 'WHERE Status = "Private" '
            elif sortby.lower() == "4-year":
                statement += 'WHERE Type = "4-year" '
            elif sortby.lower() == "2-year":
                statement += 'WHERE Type = "2-year" '
            elif sortby.lower() == "other":
                statement += 'WHERE Type = "Less than 2-year" '
            elif sortby.lower() == "bottom":
                pass
            else:
                print("problem with sortby statement")
                return False
        if price_range != None:
            if sortby != None:
                if price_range.lower() == "between":
                    if price_low != None and type(price_low) == int:
                        if price_high != None and type(price_high) == int:
                            statement += 'AND Tuition BETWEEN {} AND {} '.format(price_low, price_high)
                        else:
                            print('problem with price_high')
                            return False
                    else:
                        print("problem with price_low")
                        return False
                elif price_range.lower() == "above":
                    if price != None and type(price) == int:
                        statement += 'AND Tuition > "{}" '.format(price)
                elif price_range.lower() == "below":
                    if price != None and type(price) == int:
                        statement += 'AND Tuition < "{}" '.format(price)
            else:
                if price_range.lower() == "between":
                    if price_low != None and type(price_low) == int:
                        if price_high != None and type(price_high) == int:
                            statement += 'WHERE Tuition BETWEEN {} AND {} '.format(price_low, price_high)
                        else:
                            print('problem with pricehigh')
                            return False
                    else:
                        print("problem with pricelow")
                        return False
                elif price_range.lower() == "above":
                    if price != None and type(price) == int:
                        statement += 'WHERE Tuition > "{}" '.format(price)
                elif price_range.lower() == "below":
                    if price != None and type(price) == int:
                        statement += 'WHERE Tuition < "{}" '.format(price)

        if state != None:
            if type(state) == str:
                if sortby != None or price_range != None:
                    if state.upper() in STATEABBRS:
                        statement += 'AND Colleges.StateAbbr = "{}" '.format(state.upper())
                    else:
                        print('not valid state- yes orderby')
                        return False
                else:
                    if state.upper() in STATEABBRS:
                        statement += 'WHERE Colleges.StateAbbr = "{}" '.format(state.upper())
                    else:
                        print('not valid state')
                        return False

            else:
                print('problem with state input')
                return False
    else:
        statement += 'WHERE Colleges.Name LIKE "{}%" '.format(college_name)

    if orderby.lower() == "top":
        statement += 'ORDER BY Tuition DESC '
    elif orderby.lower() == "bottom":
        statement += 'ORDER BY Tuition ASC '
    else:
        print('Problem with orderby')
        return False

    if limit != 10:
        statement += 'LIMIT {} '.format(limit)
    else:
        statement += 'LIMIT 10 '
    cur.execute(statement)
    results = []
    for row in cur:
        results.append(row)

    prettyprint(results)

    return results

def update_current(college_search):
    CURRENT = college_search

def view_cart():
    for i in CART:
        print(i)


def view_history(input):
    if input == 'school':
        if len(VIEW_HISTORY) != 0:
            for h in enumerate(VIEW_HISTORY, 1):
                if len(VIEW_HISTORY) < 10:
                    print('\033[1m{:>1}. \033[0m{}'.format(*h))
                elif len(VIEW_HISTORY) < 100:
                    print('\033[1m{:>2}. \033[0m{}'.format(*h))
                else:
                    print('\033[1m{:>3}. \033[0m{}'.format(*h))

        else:
            print("No current view history.")
    elif input == 'search':
        if len(SEARCH_HISTORY) != 0:
            count = 1
            for h in SEARCH_HISTORY:
                print('\033[1m'+"Search: {}".format(count))
                for k in h.keys():
                    if h[k] != None:
                        print('\033[0m'+'{:<14}: {}'.format(k, h[k]))
                count+=1
        else:
            print("No current search history")
    else:
        print("Sorry, but that's not a valid command.")


def process_command(command):
    if command.lower() != 'exit':
        non_college_commands = ['view_school', 'job_opps', 'cart', 'view_history', 'clear_history', 'see_map', 'get_graph']
        integer_params = ['price_low', 'price_high', 'price', 'limit']
        params_dict = {'orderby':'top', 'limit':'10', 'sortby':None, 'price_range':None,
                        'price':None,'price_low':None, 'price_high':None, 'state':None, 
                        'college_name':None, 'view_school':None, 'job_opps':None,'cart':None, 
                        'view_history':None, 'clear_history':None, 'see_map':None, 'get_graph':None}
        colleges_search_dict = {}
        if 'college_name' in command:
            count = 0
            for c in command:
                if c == "=":
                    count += 1
            if count == 1:
                split_command = command.split('=')
                params_dict['college_name'] = split_command[1]
            else:
                print("Thats not a valid college search")
                print("Remeber, your input should look something like:")
                print("college_name=university of michigan")
                return False

        else:
            split_command = command.lower().split()
            user_commands = []
            for s in split_command:
                user_commands.append(s.split('='))
            for c in user_commands:
                if c[0] in params_dict.keys():
                    params_dict[c[0]] = c[1]
                elif c[0] == "view_job_opps":
                    params_dict['job_opps']=True
                else:
                    print('Problem with command'.format(c[0]))
                    return False
        if params_dict['get_graph'] == None:
            if params_dict['see_map'] == None:
                if params_dict['clear_history'] == None:
                    if params_dict['view_history'] == None:
                        if params_dict['cart'] == None:
                            if params_dict['job_opps'] == None:
                                if params_dict['view_school'] == None:
                                    for k in params_dict.keys():
                                        if k in non_college_commands:
                                            pass
                                        else:
                                            if k in integer_params and params_dict[k]!=None:
                                                try:
                                                    params_dict[k] = int(params_dict[k])
                                                    colleges_search_dict[k] = params_dict[k]
                                                except:
                                                    print("Problem with {}".format(k))
                                            else:
                                                colleges_search_dict[k] = params_dict[k]
                                    global SEARCH_HISTORY
                                    SEARCH_HISTORY.append(colleges_search_dict)
                                    user_search = colleges(colleges_search_dict)
                                    global CURRENT_SEARCH
                                    CURRENT_SEARCH = user_search
                                    # print(user_search)
                                    return user_search
                                else:
                                    try:
                                        view_school_input = int(params_dict['view_school'])-1
                                        school_search = CURRENT_SEARCH[view_school_input]
                                        view_school = college_info(school_search)
                                        global VIEW_HISTORY
                                        VIEW_HISTORY.append(view_school)
                                        global CURRENT_SCHOOL
                                        CURRENT_SCHOOL = view_school
                                        view_school.about()
                                        print('\n')
                                        print("This school has been saved to your search history.")
                                        print("Would you like to add it to your cart so you can compare it to other schools?")
                                        print("Type cart=add, or enter a new command.")
                                        print('\n')
                                    except:
                                        print("Sorry, but that option isn't available based on your last search. Try again.")

                            else:
                                if CURRENT_SCHOOL != None:
                                    if CURRENT_SCHOOL.city != None:
                                        get_coordinates(CURRENT_SCHOOL)
                                        jobs = get_jobs(CURRENT_SCHOOL)
                                        if jobs != False:
                                            print('\033[1m'+"Jobs within 3 miles of {}:".format(CURRENT_SCHOOL.name))
                                            print('\033[0m')
                                            for j in jobs:
                                                print(j)
                                        else:
                                            print("Looks like theres no where to work.")
                                            print("This school is in the middle of nowhere. Don't go here!")
                                    else:
                                        print("I'm sorry, but we don't have enough information on {} to do that search.".format(view_school.name))
                                        return False
                                else:
                                    print("You haven't viewed any schools yet.")
                                    return False
                        else:
                            if params_dict['cart'] == "add":
                                global CART
                                CART.append(CURRENT_SCHOOL)
                                print("{} added to cart.".format(CURRENT_SCHOOL.name))
                                print("\n")
                            elif params_dict['cart'] == "view":
                                if CART != []:
                                    view_cart()
                                else:
                                    print("Your cart is empty!")
                                    return False
                            elif params_dict['cart'] == "empty":
                                if CART != []:
                                    CART = []
                                    print("POOF. (thats magic talk for your cart is empty)")
                                    return True
                                else:
                                    print("Your cart is already empty!")
                                    return False
                            else:
                                print("Sorry, that's not a valid command")
                                return False

                    else:
                        view_history(params_dict['view_history'])

                else:
                    if params_dict['clear_history'] == "school":
                        VIEW_HISTORY = []
                        print("School view history has been successfully erased")
                        return True
                    elif params_dict['clear_history'] == "search":
                        SEARCH_HISTORY = []
                        print("Search history has been successfully erased")
                        return True
                    elif params_dict['clear_history'] == "all":
                        VIEW_HISTORY = []
                        SEARCH_HISTORY = []
                        print("All search history has been successfully erased")
                        return True
                    else:
                        print("Sorry, but that's not a valid command.")
                        return False
            else:
                if params_dict['see_map'] == 'jobs':
                    plot_jobs(CURRENT_SCHOOL)
                elif params_dict['see_map'] == 'current_search':
                    plot_schools(CURRENT_SEARCH)
                else:
                    print("That's not a valid entry.")
                    return False
        else:
            if params_dict['get_graph'] == 'cart':
                print("Getting graph...")
                compare_cart()
            elif params_dict['get_graph'] == 'current_search':
                print("Getting graph...")
                compare_search()
            else:
                print("That's not a valid entry.")
                return False
    else:
        return 'exit'



def load_help_text():
    with open('help.txt') as f:
        return f.read()


def interactive_prompt():
    help_text = load_help_text()
    response = ''
    while response != 'exit':
        response = input('Enter a command: ')
        try:
            process_command(response)
        except:
            print("can't process command")
            pass
        if response == 'help':
            print(help_text)
            continue


if __name__=="__main__":
    # extract_tuition_data(TUITION)
    init_tuition_db(DBNAME)
    create_colleges_table(TUITION, DBNAME)
    create_statesIncome_table(CITIES, STATESINCOME, DBNAME)
    create_city_table(CITIES,DBNAME)
    update_tables(DBNAME)
    interactive_prompt()








