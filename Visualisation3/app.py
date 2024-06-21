import pandas as pd
import numpy as np
import altair as alt
import geopandas as gpd
import json
import panel as pn

alt.data_transformers.enable('json')
pn.extension('vega')

# load data
names = pd.read_csv("../dpt2020.csv", sep=";")
names.drop(names[names.preusuel == '_PRENOMS_RARES'].index, inplace=True)
names.drop(names[names.dpt == 'XX'].index, inplace=True)
just_names = names

dpts = gpd.read_file('../departements-version-simplifiee.geojson')
plain_dpts = dpts

names = dpts.merge(names, how='right', left_on='code', right_on='dpt')
names.drop(columns=['code'], inplace=True)

just_names['annais'] = just_names['annais'].astype(int)



def plot_name_pyramid(names, min_year=1900, max_year=2020):
    year_slider = alt.binding_range(min=min_year, max=max_year, step=1, name='Year:')
    select_year = alt.selection_single(fields=['annais'], bind=year_slider)


    name_counts = just_names.groupby('preusuel')['nombre'].sum().reset_index()

    min_total_count = 2000
    filtered_names = name_counts[name_counts['nombre'] >= min_total_count]['preusuel'].tolist()

    name_stats = just_names.groupby(['preusuel', 'sexe'])['nombre'].sum().unstack(fill_value=0)

    name_stats['diff'] = abs(name_stats[1] - name_stats[2])

    sorted_names = name_stats[name_stats.index.isin(filtered_names)].sort_values(by='diff').index.tolist()

    selected_names = sorted_names[:20]
    print("Selected top mixed names:", selected_names)
    top_mixed_names = selected_names
    print("top mixed names", top_mixed_names)

    names = top_mixed_names

    filtered_names = just_names[(just_names['preusuel'].isin(names)) &
                                (just_names['annais'] >= min_year) &
                                (just_names['annais'] <= max_year)]
    
    all_names = pd.DataFrame([(name, sexe, year) for name in top_mixed_names
                                  for sexe in [1, 2]
                                  for year in range(min_year, max_year + 1)],
                                 columns=['preusuel', 'sexe', 'annais'])

    grouped_data = pd.merge(all_names, filtered_names, on=['preusuel', 'sexe', 'annais'], how='left').fillna(0)

    grouped_data = grouped_data.groupby(
        ['preusuel', 'sexe', 'annais'], as_index=False)['nombre'].sum()

    subset = grouped_data
    print(subset)

    gdf_json = json.loads(subset.to_json(orient='records'))
    features = gdf_json
    base = alt.Chart(alt.Data(values=features)).transform_calculate(
        gender=alt.expr.if_(alt.datum.sexe == 1, 'Male', 'Female')
    ).add_selection(
        select_year
    ).transform_filter(
        select_year
    ).properties(
        width=250
    )

    color_scale = alt.Scale(domain=['Male', 'Female'],
                            range=['#1f77b4', '#e377c2'])


    left = base.transform_filter(
        alt.datum.sexe == 2
    ).encode(
        alt.Y('preusuel:O').axis(None),
        alt.X('nombre:Q')
        .title('birth')
        .sort('descending'),
        alt.Color('gender:N')
        .scale(color_scale)
        .legend(None)
    ).mark_bar().properties(title='Female')

    middle = base.encode(
        alt.Y('preusuel:O').axis(None),
        alt.Text('preusuel:O'),
    ).mark_text().properties(width=20)

    right = base.transform_filter(
        alt.datum.sexe == 1
    ).encode(
        alt.Y('preusuel:O').axis(None),
        alt.X('nombre:Q').title('birth'),
        alt.Color('gender:N').scale(color_scale).legend(None)
    ).mark_bar().properties(title='Male')

    return (left | middle | right).configure_title(
        fontSize=20
    ).configure_axis(
        labelFontSize=15,
        titleFontSize=18
    ).configure_legend(
        labelFontSize=15,
        titleFontSize=18
    )

chart_pane = pn.pane.Vega(plot_name_pyramid([], 1900, 2020), width=1000, height=800)


app = pn.Row(
    chart_pane
)

app.servable()
