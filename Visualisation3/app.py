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


panel_name_input = pn.widgets.TextInput(name='Name', placeholder='Enter names separated by a comma', value = "Dominique,Frédérique,Charlie,Camille,Pascal,Pascale")
year_slider = alt.binding_range(min=1900, max=2020, step=1, name='Year:')
select_year = alt.selection_single(fields=['annais'], bind=year_slider)

@pn.depends(panel_name_input, watch=True)
def plot_name_pyramid(names=[], min_year=1900, max_year=2020):
    names = names.upper().split(",")
    print(names)


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

    if len(names) == 0:
        names = top_mixed_names
    else:
        top_mixed_names = names
    print("names taken", names)

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
        width=250,
        height=round(33.5*len(names))
    )

    color_scale = alt.Scale(domain=['Male', 'Female'],
                            range=['#1f77b4', '#e377c2'])
    area_color_scale = alt.Scale(domain=['Male', 'Female'],
                            range=['#1f77b499', '#e377c299'])


    left = base.transform_filter(
        select_year
    ).transform_filter(
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

    middle = base.transform_filter(
        select_year
    ).encode(
        alt.Y('preusuel:O').axis(None),
        alt.Text('preusuel:O'),
    ).mark_text().properties(width=20)

    right = base.transform_filter(
        select_year
    ).transform_filter(
        alt.datum.sexe == 1
    ).encode(
        alt.Y('preusuel:O').axis(None),
        alt.X('nombre:Q').title('birth'),
        alt.Color('gender:N').scale(color_scale).legend(None)
    ).mark_bar().properties(title='Male')


    base_evol = alt.Chart(alt.Data(values=features)).transform_calculate(
        gender=alt.expr.if_(alt.datum.sexe == 1, 'Male', 'Female')
    ).properties(
        width=250,
        height=25
    )

    area_chart = base_evol.mark_area().encode(
        x=alt.X("annais:T", title=None),
        y=alt.Y("nombre:Q", title=None, scale=alt.Scale(zero=False)),
        color=alt.Color('gender:N').scale(area_color_scale)
    )

    vertical_bar = base_evol.mark_rule(
        color='red',
        size=2
    ).encode(
        x='annais:T'
    ).add_selection(
        select_year
    ).transform_filter(
        select_year
    )

    layered_chart = alt.layer(area_chart, vertical_bar)

    final_evol = layered_chart.facet(
        row=alt.Row("preusuel:O", title=None, header=None),
        spacing=0,
    ).properties(
        title='Evolution'
    ).resolve_scale(
        y='independent'
    )

    combined_chart = alt.concat(left, middle, right, spacing=5)

    final_chart = combined_chart.resolve_scale(
        x='shared'
    )

    return (final_chart | final_evol).configure_title(
        fontSize=20
    ).configure_axis(
        labelFontSize=15,
        titleFontSize=18
    ).configure_legend(
        labelFontSize=15,
        titleFontSize=18
    ).configure_axis(
        grid=False,
        domain=False,
        ticks=True,
        labels=True
    )

chart_pane = pn.pane.Vega(plot_name_pyramid, width=1000, height=800)
def on_name_button_click(*args, **kwargs):
    global chart_pane
    chart_pane = plot_name_pyramid(str(panel_name_input.value), 1900, 2020)
    return chart_pane


panel_name_button = pn.widgets.Button(name="Apply names")
panel_name_button.on_click(on_name_button_click)
app = pn.Row(
    chart_pane,
    pn.Column(
        panel_name_input,
        panel_name_button
    )
)

app.servable()
