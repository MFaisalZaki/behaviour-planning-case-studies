

import os
from pyrosm import OSM

def plot_state(plan_id, state):

    # Set colors for each landuse type and sort legend alphabetically
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    import matplotlib.pyplot as plt

    landuse_to_cat = {
        "forest": 4.0,               # green space
        "recreation_ground": 4.0,    # green space
        "farmyard": 4.0,             # green/agricultural
        "plant_nursery": 4.0,        # green/agricultural
        "brownfield": 2.0,           # development/commercial/industrial reuse
        "farmland": 4.0,             # green/agricultural
        "grass": 4.0,                # green space
        "meadow": 4.0,               # green space
        "residential": 0.0,          # residential zone
        "apiary": 4.0,               # green/agricultural
        "industrial": 2.0,           # economic/production -> commercial bucket
        "orchard": 4.0,              # green/agricultural
        "garages": 3.0,              # facility/parking
        "retail": 2.0,               # commercial zone
        "cemetery": 3.0,             # community facility
        "construction": 2.0,         # development/commercial by default
        "allotments": 4.0,           # community green space
        "free space": -1.0,
    }

    landuse_to_string = {
        "forest": "green space zone",               # green space
        "recreation_ground": "green space zone",    # green space
        "farmyard": "green space zone",      # green/agricultural
        "plant_nursery": "green space zone", # green/agricultural
        "brownfield": "commercial zone",
        "farmland": "green space zone",      # green/agricultural
        "grass": "green space zone",                # green space
        "meadow": "green space zone",               # green space
        "residential": "residential zone",          # residential zone
        "apiary": "green space zone",               # green/agricultural
        "industrial": "commercial zone",
        "orchard": "green space zone",              # green/agricultural
        "garages": "facility zone",                # facility/parking
        "retail": "commercial zone",                  # commercial zone
        "cemetery": "facility zone",             # community facility
        "construction": "commercial zone",
        "allotments": "green space zone",
        "free space": "empty space zone",
    }

    index_to_cat = {v: landuse_to_string[k] for k, v in landuse_to_cat.items()}

    current_dir = os.path.dirname(os.path.abspath(__file__))
    scotland_osm_file = os.path.join(current_dir, "auxfiles", "scotland-latest.osm.pbf")
    osm = OSM(scotland_osm_file, [-2.84134, 56.32577, -2.76541, 56.34756])

    landuse_net = osm.get_landuse()
    # Compress landuse categories
    landuse_net['landuse'] = landuse_net['landuse'].map(landuse_to_string)

    for n in state.urban_graph.nodes:
        for i in landuse_net.index[landuse_net['id'] == n].tolist():
            landuse_net.loc[i, 'landuse'] = index_to_cat[state.urban_graph.nodes[n]['landuse_type']]

    color_map = {
        'green space zone':[ '#2ca02c'],  # blue
        'commercial zone':[ '#d62728'],  # red,
        'residential zone':[ '#1f77b4'],  # green
        'facility zone':[ '#9467bd'],  # purple
        'empty space zone':[ '#ffffff'],  # white
    }

    unique_landuses = sorted(landuse_net['landuse'].unique())
    cmap = ListedColormap([color_map.get(lu, ['#cccccc'])[0] for lu in unique_landuses])

    # Plot with custom color map
    ax = landuse_net.plot(column='landuse', legend=False, figsize=(10,6), cmap=cmap)

    # Custom legend sorted alphabetically
    legend_patches = [Patch(facecolor=color_map.get(lu, ['#cccccc'])[0], label=lu) for lu in unique_landuses]
    ax.legend(handles=legend_patches, title='Landuse', loc='best')
    # Remove x and y axes
    ax.set_axis_off()

    # Save as PNG with transparent background
    dump_dir = os.path.join(os.path.dirname(__file__), '..', 'sandbox-dump-default', 'dump_figures')
    os.makedirs(dump_dir, exist_ok=True)

    plt.savefig(os.path.join(dump_dir,f'landuse_map_plan_{plan_id}_dscore_{state.diversity_score}_sscore_{state.sustainability_score}.png'), bbox_inches='tight', pad_inches=0.1, transparent=True, dpi=300)
    plt.savefig(os.path.join(dump_dir,f'landuse_map_plan_{plan_id}_dscore_{state.diversity_score}_sscore_{state.sustainability_score}.pdf'), bbox_inches='tight', pad_inches=0.1, transparent=True, dpi=300)

    pass