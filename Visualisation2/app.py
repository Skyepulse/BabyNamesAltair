import pandas as pd
import numpy as np
import altair as alt
import geopandas as gpd
import json
import panel as pn

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

names_secondary = names

just_names['annais'] = just_names['annais'].astype(int)
names_secondary['annais'] = names_secondary['annais'].astype(int)

different_possible_departments = just_names['dpt'].unique()
different_possible_departments_names = names_secondary['nom'].unique()
dictionnary_code_to_name = dict(zip(dpts['code'], dpts['nom']))

def get_most_common_names(year_min, year_max, num_names=10) -> list[str]:
    subset = just_names[(just_names['annais'] >= year_min) & (just_names['annais'] <= year_max)]
    subset = subset.groupby(['preusuel'], as_index=False).sum()
    subset = subset.sort_values(by='nombre', ascending=False)
    return subset['preusuel'].head(num_names).tolist()

def get_most_common_names_per_department(year_min, year_max, name, num_names=1) -> dict[list[str]]:
    name = name.upper()
    all_departments = {}
    special_name_ranking_per_department = {}
    #In the names dataframe, we want for each department the most common name in sum during time period
    for department in different_possible_departments:
        subset = just_names[(just_names['annais'] >= year_min) & (just_names['annais'] <= year_max) & (just_names['dpt'] == department)]
        subset = subset.groupby(['preusuel'], as_index=False).sum()
        subset = subset.sort_values(by='nombre', ascending=False).reset_index(drop=True)
        #We search the rank of the special name, if not found in this department, we write -1
        special_name_rank = -1
        for index, row in subset.iterrows():
            if row['preusuel'] == name:
                special_name_rank = index + 1
                break
        special_name_ranking_per_department[department] = special_name_rank
        all_departments[department] = subset['preusuel'].head(num_names).tolist()

    return all_departments, special_name_ranking_per_department

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
        width=800,
        height=600,
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
        width=50,
        height=400
    )


    return (chart | shadow_bar).configure_title(
        fontSize=10
    ).configure_axis(
        labelFontSize=7.5,
        titleFontSize=9
    ).configure_legend(
        labelFontSize=7.5,
        titleFontSize=9
    )

def plot_name_all_years(name, min_year=1900, max_year=2020):
    name = name.upper()
    if name not in just_names['preusuel'].values or min_year > max_year or min_year < 1900 or max_year > 2020:
        print('invalid')
        return load_plain_data(name), False
    
    filtered_names = just_names[(just_names['preusuel'] == name) & (just_names['annais'] >= min_year) & (just_names['annais'] <= max_year)]
    
    if filtered_names.empty:
        print('empty')
        return load_plain_data(name, min_year, max_year), False
    
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
        width=800,
        height=600,
        title=f'Nombre de naissances du prénom {name} par département entre {min_year} et {max_year}'
    ).add_params(
        selection
    ).project('mercator')

    total_births = grouped_data['nombre'].sum()

    shadow_bar = alt.Chart(alt.Data(values=features)).mark_bar(
        color='lightgrey'
    ).encode(
        x=alt.X('Cumulative Births:N', title=''),
        y=alt.Y('sum(properties.nombre):Q', title='nombre de naissances cumulées pour les départements sélectionnés')
    ).properties(
        width=50,
        height=400
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
        width=50,
        height=400,
        title='nombre de naissances cumulées pour les départements sélectionnés'
    )

    bar_chart = shadow_bar + selected_bar

    return (chart | bar_chart).configure_title(
        fontSize=10
    ).configure_axis(
        labelFontSize=7.5,
        titleFontSize=9
    ).configure_legend(
        labelFontSize=7.5,
        titleFontSize=9
    ), True


panel_name_input = pn.widgets.TextInput(name='Name', placeholder='Enter a name', value = 'Marie')
min_year_input = pn.widgets.IntInput(name='Min year', placeholder = 'enter min year', value=1900)
max_year_input = pn.widgets.IntInput(name='Max year', placeholder = 'enter max year', value=2020)
information_panel = pn.pane.Markdown('Suggested 10 most common names in time period:')
name_panels_column = pn.WidgetBox(height=300, scroll=True, sizing_mode='stretch_width')
mode_toggle = pn.widgets.Toggle(name='Switch to Per Department', value=False)


def on_name_button_click(stringname):
    panel_name_input.value = stringname
    update_plot(panel_name_input.value, min_year_input.value, max_year_input.value)

@pn.depends(panel_name_input, min_year_input, max_year_input, mode_toggle, watch=True)
def update_plot(name, min_year, max_year, mode):
    chart, valid = plot_name_all_years(name, min_year, max_year)
    if not valid:
        return chart
    name_panels_column.clear()
    if mode:
        most_common_names = get_most_common_names(min_year, max_year, 10)
        for common_name in most_common_names:
            button = pn.widgets.Button(name=common_name)
            button.on_click(lambda event, common_name=common_name: on_name_button_click(common_name))
            name_panels_column.append(button)
        mode_toggle.name = 'Switch to Per Department'
        information_panel.object = f'Suggested 10 most common names in time period overall:'
    else:
        most_common_names, special_name = get_most_common_names_per_department(min_year, max_year, name, 1)
        for dept, names in most_common_names.items():
            if(dept in dictionnary_code_to_name.keys()):
                for common_name in names:
                    button = pn.widgets.Button(name=f'{dictionnary_code_to_name[dept]}: {common_name} ({name}, rank: {special_name[dept]})')
                    button.on_click(lambda event, common_name=common_name: on_name_button_click(common_name))
                    name_panels_column.append(button)
        mode_toggle.name = 'Switch to Overall'
        information_panel.object = 'Most common names per department:'

    return chart

chart_pane = pn.pane.Vega(update_plot, width=1250, height=600)

app = pn.Row(
    chart_pane,
    pn.Column(
        panel_name_input,
        min_year_input,
        max_year_input,
        mode_toggle,
        information_panel,
        name_panels_column
    )
)

app.servable()