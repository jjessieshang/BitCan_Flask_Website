from tokenize import String
from flask import Flask, redirect, url_for, render_template, request, abort
import pandas as pd
import numpy as np
import folium
from math import radians, cos, sin, asin, sqrt
from folium.plugins import Fullscreen

app = Flask(__name__)

@app.route("/")
def home(): #home page
    return render_template("index.html")

@app.route("/form/", methods=["POST","GET"])
def form():
    return render_template("uwiForm.html")

#mapping page
@app.route('/form/mapping/')
def mapping(): 
    lsd = request.args.get('lsd')
    sc  = request.args.get('sc')
    rg  = request.args.get('rg')
    twp  = request.args.get('twp')
    md  = request.args.get('md')

    UWI_number = [int(md),int(rg),int(twp),int(sc),int(lsd)]

    #IMPORT DATAFRAMES
    ATS = pd.read_csv('~/Desktop/OneDrive - BitCan/Mapping Program/ATS.csv', sep =',')
    ATS = ATS.drop('Unnamed: 3',axis = 1)

    directory = pd.read_csv('~/Desktop/OneDrive - BitCan/Mapping Program/ATS_directory.csv', sep =',')
    directory = directory.drop('Unnamed: 10',axis = 1)
    directory = directory.drop('Unnamed: 11',axis = 1)
    directory = directory.drop('Unnamed: 12',axis = 1)
    directory = directory.drop('Unnamed: 13',axis = 1)
    directory = directory.drop('Unnamed: 14',axis = 1)
    directory = directory.drop('Unnamed: 15',axis = 1)
    directory = directory.drop('Unnamed: 16',axis = 1)
    directory = directory.drop('Unnamed: 17',axis = 1)
    directory = directory.drop(index = 28)
    directory = directory.drop(index = 29)

    arr = np.arange(1,37)
    arr = np.sort(arr)[::-1]
    arr = arr.reshape(6,6)
    df = pd.DataFrame(arr)
    df.iloc[0::2,:] = df.iloc[0::2,::-1]

    array = df.to_numpy()

    #SOME FUNCTIONS FOR UWI STRING MANIPULATION
    def lsdToQuarter(UWI):
        """ Associate the legal subdivision to the adjacent quarter section corner. If position 
            is bottom left, print the section.
        """
        
        # sort subdivision
        lsd = UWI[4]

        if (lsd == 2 or lsd == 3 or lsd == 6):
            UWI[4] = 'S4'
        elif (lsd == 10 or lsd == 11 or lsd == 13 or lsd == 14 or lsd == 15):
            UWI[4] = 'N4'
        elif (lsd == 1 or lsd == 7 or lsd == 8 or lsd == 9):
            UWI[4] = 'E4'
        elif (lsd == 4 or lsd == 5 or lsd == 12):
            UWI[4] = 'W4'
        elif (lsd == 16):
            UWI[4] = 'NE'
            
        #sort section
        sc = UWI[4]
        
        if (sc == 'S4'):
            result = np.where(array == UWI[3])
        elif (sc == 'W4'):
            result = np.where(array == UWI[3])
        else:
            result = 100
            
        return UWI, result

    def new_coordinate(coord, UWI_):
        """ a function to rename the section of a location based input index applied to matrix of 36 sections
        """
        tp = UWI_[4]
        if coord == 100:
            y1 = 100
            x1 = 100
            
        else:
            x1 = int(coord[0])
            y1 = int(coord[1])
        
            if tp == 'S4':
                if x1 == 5:
                    tp = 'E4'
                else:
                    x1 += 1
                    tp = 'N4'

        
            elif tp == 'W4':
                if y1 == 0:
                    tp = 'N4'
            
                else:
                    y1 = y1 - 1
                    tp = 'E4'
        
        UWI_[4] = tp
        x = x1
        y = y1
        
        return UWI_, x, y

    def ListToString(list_form):
        """ A function to convert from list to string
        """
        median = str(list_form[0])

        range_str = str(list_form[1])
        UWIrg = range_str.zfill(2)
        
        township_str = str(list_form[2])
        township = township_str.zfill(3)
        
        section_str = str(list_form[3])
        section = section_str.zfill(2)
        
        qs = str(list_form[4])
        
        wellID = median + UWIrg + township + section + qs
        
        return(wellID)

    def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance in kilometers between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
        return c * r

    # #MAIN TERMINAL CODE
    UWI_list = UWI_number

    UWI, co = lsdToQuarter(UWI_list)

    UWI, x, y = new_coordinate(co, UWI)

    # call on the matrix and output the number at that index, assign as new section
    if x == 100:
        pass

    else:
        new_sc = array[x,y]
        UWI[3] = new_sc
        
    UWI_ID = ListToString(UWI)

    ATS.loc[ATS['UWI'] == UWI_ID]

    input_coord = ATS.loc[ATS['UWI'] == UWI_ID]
    lati1 = float(input_coord.iloc[0]['Latitude'])
    long1 = float(input_coord.iloc[0]['Longitude'])

    for index, row in directory.iterrows():
        directory.loc[index, "Distance (km)"] = haversine(long1, lati1, row['Longitude'], row['Latitude'])
        
    # sort the distance values in ascending order, closest well site to furthest well site
    directory.sort_values(by = ['Distance (km)'],
                        axis = 0,
                        ascending = True)

    #FOLIUM MAP
    m = folium.Map(location=[55,-115], tiles =None,
                    zoom_start=5)

    borderStyle={
        'fillOpacity': 0.1,
        'weight': 1,
        'color': 'black'
    }
    # #Injecting html for back button
    # m.get_root().html.add_child(folium.Element("""
    #         <button style="width: 45px;
    #         height: 45px;
    #         position: fixed;
    #         z-index: 900;
    #         outline: none;
    #         background-color: #acadb2;
    #         outline: none;
    #         top: 20px;
    #         border: none;
    #         left: 50px;
    #         border-radius: 50%;
    #         font-size: xx-large;
    #         cursor: pointer;"><a href="/form" style="text-decoration: none;
    #                 color: #f8f8f9;
    #                 position: fixed;
    #                 top: 17px;
    #                 left: 62px;">
    #         <
    #         </a></button>
    # """))
    # m.save("output.html")

    folium.GeoJson("alberta.geojson", 
                    name="Alberta",
                    style_function=lambda x:borderStyle).add_to(m)
    folium.TileLayer("https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png", 
                 name = 'Light Map',
                 attr= 'Stadia Maps').add_to(m)
    folium.TileLayer('https://api.maptiler.com/maps/outdoor/{z}/{x}/{y}.png?key=D1R440GkNxYWsQt9rTf3', 
                 name = 'Topography',
                 attr= 'OpenTopo').add_to(m)
    folium.TileLayer('https://api.maptiler.com/maps/hybrid/256/{z}/{x}/{y}.jpg?key=D1R440GkNxYWsQt9rTf3', 
                 name = 'Satellite',
                 attr= 'Esri_WorldImagery').add_to(m)
    folium.LayerControl().add_to(m)

    #df column with rounded numbers and units
    directory['Print Distance']=directory['Distance (km)']
    directory['Print Distance']=directory['Print Distance'].round(decimals=2)
    directory['Print Distance']='<strong>Distance: </strong>' + directory['Print Distance'].astype(str) + ' km'
    directory

    df_well_locations = directory.copy()
    df_well_locations['Longitude']*= -1
    df_well_locations = df_well_locations.drop(columns=['Directory', 'LSD','SC','TWP','RG','W','M','adjusted_UWI','Distance (km)','Print Distance'])
    # df_well_locations
    well_location_list = df_well_locations.values.tolist()
    well_location_list_size = len(well_location_list)

    #MARKERS
    for point in range(0, well_location_list_size):
        folium.Marker(well_location_list[point],
                    icon=folium.Icon(icon='glyphicon-star', icon_color='white', color='green'),
                    tooltip=directory.iloc[point]['Directory'],
                    popup=folium.Popup(directory.iloc[point]['Print Distance'], max_width=500)
                    ).add_to(m)

    inputLong =long1*-1

    #markers for location of interest
    folium.Circle(
        radius=50000,
        location=[lati1,inputLong],
        tooltip="50km radius",
        color="cadetblue",
        fill=True,
    ).add_to(m)

    folium.Marker(location=[lati1,inputLong],
                    tooltip=UWI_ID,
                    icon=folium.Icon(icon='glyphicon-star', color='cadetblue'),
                    ).add_to(m)


    fs = Fullscreen()
    m.add_child(fs)  # adding fullscreen button to map

    return m._repr_html_()
    


if __name__ == "__main__":
    app.run(debug=True)