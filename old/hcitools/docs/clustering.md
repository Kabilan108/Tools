## Clustering

This example will show you how to perform dimensionality reduction and visualize
any resulting clusters. We will also show how certain preprocessing steps can
be done using `preprocess.clean_data`.

### Datasets

This example makes use of the `ros-mito` data set which contains features
extracted from high-content images.


```python
# Imports
from hcitools import datasets, plot, analysis, preprocess

# Load dataset
ros = datasets.load_dataset('ros-mito')

# Plotly renderer
plot.set_renderer('notebook')  # Use this when running notebook
plot.set_renderer('iframe_connected')  # Use this when rendering docs
```


```python
# Preprocessing
meta = ['Well', 'Row', 'Column', 'Timepoint', 'Compound', 'Conc']
df, dropped, LOG = preprocess.clean_data(
    data=ros,
    metacols=meta,
    dropna=True,
    drop_low_var=0.0,
    corr_thresh=0.9,
    verbose=True
)
df = df.set_index(meta)

# Generate clusters with default arguments
proj, expvar = analysis.dim_reduction(data=df, method=['pca', 'tsne'])
```


```python
# Plot PCA components
fig = plot.pca_comps(proj, expvar, n_comps=3)
fig.update_layout(width=700, height=400)

fig.show()
```


<iframe
    scrolling="no"
    width="720px"
    height="420"
    src="assets/clustering_figure_3.html"
    frameborder="0"
    allowfullscreen
></iframe>




```python
# Compare 2 compounds
fig = plot.clusters(proj, 'Sorafenib Tosylate', 'Imatinib mesylate', 'tsne')
fig.update_layout(width=750, height=450)

fig.show()
```


<iframe
    scrolling="no"
    width="770px"
    height="470"
    src="assets/clustering_figure_4.html"
    frameborder="0"
    allowfullscreen
></iframe>
