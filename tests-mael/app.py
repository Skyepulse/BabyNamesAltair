import pandas as pd
import numpy as np
import altair as alt
import geopandas as gpd
import json
import panel as pn
import param

alt.data_transformers.enable('json')
pn.extension('vega')

#load data
names = pd.read_csv("../dpt2020.csv", sep=";")
names.drop(names[names.preusuel == '_PRENOMS_RARES'].index, inplace=True)
names.drop(names[names.dpt == 'XX'].index, inplace=True)
just_names = names

dpts = gpd.read_file('../departements-version-simplifiee.geojson')
plain_dpts = dpts

names = dpts.merge(names, how = 'right', left_on='code', right_on='dpt')
names.drop(columns=['code'], inplace=True)

just_names['annais'] = just_names['annais'].astype(int)


def load_plain_data(name, min_year=1900, max_year=2020):
    print('hello')
    gdf_json = json.loads(plain_dpts.to_json())
    
    features = gdf_json['features']

    selection = alt.selection_point(fields=['properties.nom'], empty=True, on='click')

    chart = alt.Chart(alt.Data(values=features)).mark_geoshape(
        fill='lightgray',
        stroke='black'
    ).encode(
        opacity=alt.condition(selection, alt.value(1), alt.value(1)),
        tooltip=[
            alt.Tooltip('properties.code:N', title='Code'),
            alt.Tooltip('properties.nom:N', title='Name')
        ]
    ).properties(
        width=1600,
        height=1200,
        title=f'Aucune naissance avec le nom: {name} entre {min_year} et {max_year} en France'
    ).add_params(
        selection
    ).project('mercator')

    shadow_bar = alt.Chart(pd.DataFrame({'Cumulative Births': ['Total'], 'nombre': [0]})).mark_bar(
        color='lightgrey'
    ).encode(
        x=alt.X('Cumulative Births:N', title=''),
        y=alt.Y('nombre:Q', title='nombre de naissances cumulées pour les départements sélectionnés')
    ).properties(
        width=100,
        height=800
    )


    return (chart | shadow_bar).configure_title(
        fontSize=20
    ).configure_axis(
        labelFontSize=15,
        titleFontSize=18
    ).configure_legend(
        labelFontSize=15,
        titleFontSize=18
    )

def plot_name_all_years(name, min_year=1900, max_year=2020):
    name = name.upper()
    if name not in just_names['preusuel'].values or min_year > max_year or min_year < 1900 or max_year > 2020:
        print('invalid')
        return load_plain_data(name)
    
    filtered_names = just_names[(just_names['preusuel'] == name) & (just_names['annais'] >= min_year) & (just_names['annais'] <= max_year)]
    
    if filtered_names.empty:
        print('empty')
        return load_plain_data(name, min_year, max_year)
    
    grouped_data = filtered_names.groupby(['dpt'], as_index=False).sum()

    subset = dpts.merge(grouped_data, how='right', left_on='code', right_on='dpt')
    subset.drop(columns=['dpt'], inplace=True)
    gdf_json = json.loads(subset.to_json())
    features = gdf_json['features']

    selection = alt.selection_point(fields=['properties.nom'], empty=True, on='click')

    chart = alt.Chart(alt.Data(values=features)).mark_geoshape(
        stroke='black'
    ).encode(
        color= alt.Color('properties.nombre:Q', title='Nombre', scale=alt.Scale(scheme='oranges')),
        tooltip=[
            alt.Tooltip('properties.code:N', title='Code'),
            alt.Tooltip('properties.nom:N', title='Name'),
            alt.Tooltip('properties.nombre:Q', title='Nombre')
        ],
        opacity=alt.condition(selection, alt.value(1), alt.value(0.4))
    ).properties(
        width=1600,
        height=1200,
        title=f'Nombre de naissances du prénom {name} par département entre {min_year} et {max_year}'
    ).add_params(
        selection
    ).project('mercator')

    total_births = grouped_data['nombre'].sum()

    shadow_bar = alt.Chart(pd.DataFrame({'Cumulative Births': ['Total'], 'nombre': [total_births]})).mark_bar(
        color='lightgrey'
    ).encode(
        x=alt.X('Cumulative Births:N', title=''),
        y=alt.Y('nombre:Q', title='nombre de naissances cumulées pour les départements sélectionnés')
    ).properties(
        width=100,
        height=800
    )

    selected_bar = alt.Chart(alt.Data(values=features)).mark_bar().encode(
        x=alt.X('Cumulative Births:N', title=''),
        y=alt.Y('sum(properties.nombre):Q'),
        tooltip=[
            alt.Tooltip('sum(properties.nombre):Q', title='nombre de naissances cumulées')
        ]
    ).transform_filter(
        selection
    ).properties(
        width=100,
        height=800,
        title='nombre de naissances cumulées pour les départements sélectionnés'
    )

    bar_chart = shadow_bar + selected_bar

    return (chart | bar_chart).configure_title(
        fontSize=20
    ).configure_axis(
        labelFontSize=15,
        titleFontSize=18
    ).configure_legend(
        labelFontSize=15,
        titleFontSize=18
    )


panel_name_input = pn.widgets.TextInput(name='Name', placeholder='Enter a name', value = 'Marie')
min_year_input = pn.widgets.IntInput(name='Min year', placeholder = 'enter min year', value=1900)
max_year_input = pn.widgets.IntInput(name='Max year', placeholder = 'enter max year', value=2020)

@pn.depends(panel_name_input, min_year_input, max_year_input, watch=True)
def update_plot(name, min_year, max_year):
    print('trying with', name, min_year, max_year)
    chart = plot_name_all_years(name, min_year, max_year)
    print(chart)
    return chart

chart_pane = pn.pane.Vega(update_plot, width=2500, height=1200)

app = pn.Row(
    chart_pane,
    pn.Column(
        panel_name_input,
        min_year_input,
        max_year_input
    )
)

app.servable()