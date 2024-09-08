## Heatmaps

This example will show you how to generate various heatmaps and how to annotate
them using the plotly library.

### Datasets

This example makes use of two of the built-in datasets listed below

- `covid` - Protein expression data from a cohort of COVID-19 patients
- `ros-mito` - High content imaging features from an experiment.


```python
# Import
from hcitools import datasets, plot

# Load datasets
covid = datasets.load_dataset('covid')
ros = datasets.load_dataset('ros-mito')

# Plotly renderer
plot.set_renderer('notebook')  # Use this when running notebook
plot.set_renderer('iframe_connected')  # Use this when rendering docs
```

### Protein Expression Heatmaps

Here, we'll create a heatmap to look at the expression of proteins in the
patients' blood. We'll include colorbars for patient sex and mortality.
We'll also look at how you could add annotations to highlight certain regions
of the heatmap.


```python
# Prepare data frame
data = (covid.copy()
    .filter(regex='^B-', axis=1))  # Keep only blood markers
metadata =  covid[['Mortality', 'Sex']]
data.columns = [x[2:] for x in data.columns]

# Define groups for heatmap
row_groups = {
    k: list(v.values()) for k, v in metadata.to_dict(orient='index').items()
}
row_group_names = ['Mortality', 'Sex']
row_colors = {'Alive': '#38d652', 'Dead': '#d93e38',
              'Male': 'blue', 'Female': 'pink'}

# Create heatmap
fig = plot.heatmap(
    data=data,
    clust_rows=True,
    clust_cols=True,
    row_colors=row_colors,
    row_groups=row_groups,
    row_group_names=row_group_names
)

# Add a title and tweak the size
fig.update_layout(
    title='Blood Biomarkers',
    title_x=0.5,
    height=400,
    width=700
)

# Annotate highly expressed proteins
fig.add_shape(
    type='rect',
    x0='MCP-1', x1='EGF',
    y0=0, y1=88,
    row=1, col=3,
    line=dict(color='black')
)

fig.show()
```


<iframe
    scrolling="no"
    width="720px"
    height="420"
    src="assets/heatmaps_figure_2.html"
    frameborder="0"
    allowfullscreen
></iframe>



### Correlation Maps

Here, we'll generate a heatmap to visualize the correlation of blood proteins
with markers of clinical severity.


```python
# Prepare data frame
vars = ['APACHE1h', 'APACHE24h', 'CCI']
data = (covid.copy()
    .set_index(vars)
    .filter(regex='^B-')
    .reset_index()
    .corr()
    .loc[vars, :]
    .drop(vars, axis=1))
data.columns = [x[2:] for x in data.columns]

# Create heatmap
fig = plot.heatmap(
    data=data,
    clust_cols=True,
    clust_rows=True
)

fig.update_layout(
    title='Correlation with Clinical Severity',
    title_x=0.5,
    height=400,
    width=700
)

# Show ticks on the y axis (these are hidden by default)
fig.update_yaxes(
    showticklabels=True,
    tickfont_size=14
)


fig.show()
```


<iframe
    scrolling="no"
    width="720px"
    height="420"
    src="assets/heatmaps_figure_3.html"
    frameborder="0"
    allowfullscreen
></iframe>



### Plate Map

Next, we'll show how you can generate an interactive heatmap to view expression
across a 96 (or 384) well plate using high-content imaging data.


```python
fig = plot.plate_heatmap(
    data=ros,
    feature="Non-border cells - Number of Objects"
)
fig.update_layout(width=900, height=500)

fig.show()
```


<iframe
    scrolling="no"
    width="920px"
    height="520"
    src="assets/heatmaps_figure_4.html"
    frameborder="0"
    allowfullscreen
></iframe>
