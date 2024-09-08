"""
This module contains functions for visualizing data and analysis results.
"""

# Imports
from rich import print

import plotly.graph_objects as go
import plotly.subplots as sp
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import textwrap
import math
import io


LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ONE_THIRD = 1.0 / 3.0
ONE_SIXTH = 1.0 / 6.0
TWO_THIRD = 2.0 / 3.0


def set_renderer(renderer):
    """
    Set the plotly default renderer
    """

    pio.renderers.default = renderer


class colormap:
    """
    Custom colormaps for plotly figures

    These colormaps assume the data has been scaled to between 0 and 1.

    Attributes
    ----------
    `OgBu` : list
        Seaborn diverging colorscale from blue (low) to orange (high)
    """

    OgBu = [
        [0.00, "#3F7F93"],
        [0.10, "#6296A6"],
        [0.20, "#85ADB9"],
        [0.30, "#A9C4CC"],
        [0.40, "#CDDBE0"],
        [0.50, "#F2F1F1"],
        [0.60, "#E9D2CD"],
        [0.70, "#DFB3A7"],
        [0.80, "#D69483"],
        [0.90, "#CC745D"],
        [1.00, "#C3553A"],
    ]

    # TODO: Write function for creating a custom color map


class LabelEncoder:
    """
    Encode target labels with values between 0 and n_classes-1

    Attributes
    ----------
    `encoder` : dict
        dictionary mapping target labels to encodings
    `decoder` : dict
        dictionary mapping encodings to target labels
    `dtype` : np.dtype
        dtype of original labels

    Methods
    -------
    `encode(labels)`
        Encode a list of target labels
    `decode(enc_labels)`
        Decode a list of encoded labels
    """

    def encode(self, labels):
        """
        Parameters
        ----------
        `labels` : array_like
            list of target labels

        Returns
        -------
        np.array
            Encoded labels

        Raises
        ------
        AssertionError
            If `enc_labels` is not 1-dimensional
        """

        labels = np.asarray(labels)
        assert labels.ndim == 1, "labels must be 1-dimensional"

        # Get unique classes
        classes = np.unique(labels)

        # Create and store maps
        self.encoder = {l: float(e) for e, l in enumerate(classes)}
        self.decoder = {float(e): l for e, l in enumerate(classes)}
        self.dtype = labels.dtype

        return np.fromiter(map(self.encoder.get, labels), dtype=float)

    def decode(self, enc_labels):
        """
        Parameters
        ----------
        `enc_labels` : array_like
            list of encoded lavels

        Returns
        -------
        np.array
            Decoded labels

        Raises
        ------
        AssertionError
            If `enc_labels` is not 1-dimensional
        """

        enc_labels = np.asarray(enc_labels)
        assert enc_labels.ndim == 1, "enc_labels must be 1-dimensional"

        return np.fromiter(map(self.decoder.get, enc_labels), dtype=self.dtype)


def _make_plate(data, feature, time_col="timepoint"):
    """
    Convert a feature data frame into a plate layout.

    This assumes `data` contains the following columns: `row`, `column` and
    `time_col`.

    Parameters
    ----------
    `data` : pd.DataFrame
        a data frame of features including certain metadata columns
    `feature` : str
        feature to populate plate with
    `time_col` : str, optional
        column that defines time points, by default 'timepoint'

    Returns
    -------
    np.array
        $(k \times r \times c)$ array where `k` = timepoint
    """

    assert feature in data.columns, "feature must be a column in data"
    assert time_col in data.columns, f"{time_col} must be a column in data"
    assert ("row" in data.columns) and (
        "column" in data.columns
    ), "'row' and 'column' must be columns in data"

    # Extract time points
    times = data[time_col].unique()

    # Define row and column names
    r = len(np.unique(data["row"]))
    c = len(np.unique(data["column"]))
    rows = {i: x for i, x in enumerate(LETTERS[:r], 1)}
    cols = [str(i) for i in range(1, c + 1)]

    # Create plate
    plate = []
    for T in times:
        plate.append(
            data.query(f"{time_col} == {T}")
            .loc[:, ["row", "column", feature]]
            .pivot(index="row", columns="column", values=feature)
            .rename(index=rows)
            .sort_index(ascending=False)
            .values
        )

    return np.array(plate), list(rows.values())[::-1], cols


def plate_heatmap(data, feature, time_col="timepoint", colorscale=colormap.OgBu):
    """
    Create an interactive plate heatmap; Including an animation for timelapses

    This function assumes that `data` contains the following columns: `row`,
    `column`, `time_col`, `compound`, `conc`.

    Parameters
    ----------
    `data` : pd.DataFrame
        a data frame of features including certain metadata columns
    `feature` : str
        feature to populate plate with
    `time_col` : str, optional
        column that defines time points, by default 'timepoint'
        This assumes the first time point is 1.
    `colorscale` : list, optional
        Plotly-compatible colormap, by default `colormap.OgBu`
        See `colormap.OgBu` for examples.

    Returns
    -------
    go.Figure
        Plotly figure
    """

    data.columns = [x.lower() for x in data.columns]
    feature = feature.lower()
    time_col = time_col.lower()

    assert feature in data.columns, "feature must be a column in data"
    assert time_col in data.columns, f"{time_col} must be a column in data"
    assert data[time_col].min() > 0, "the first time point must be 1 not 0"
    assert ("compound" in data.columns) and (
        "conc" in data.columns
    ), "'compound' and 'conc' must be columns in data"

    def platemap(x, y, z, cmpd, conc):
        """
        Wrapper for go.Heatmap
        """

        # Insert line breaks in the compound names
        cmpd = [
            [x.replace(" ", "<br>") if isinstance(x, str) else "" for x in sub]
            for sub in cmpd
        ]

        return go.Heatmap(
            x=x,
            y=y,
            z=z,
            colorscale=colorscale,
            text=cmpd,
            customdata=conc,
            hovertemplate=(
                "<b>Well:</b> %{y}%{x}<br>"
                + "<b>Compound:</b> %{text}"
                + "<b>Concentration:</b> %{customdata}<br>"
                + "<b>Value:</b> %{z:.2f}<extra></extra>"
            ),
            texttemplate="%{text}",
            # textfont_size=8.5
        )

    # Extract time points
    times = data[time_col].unique()

    # Reformat data as plate
    plate, rows, cols = _make_plate(data, feature, time_col)

    # Create data for tooltips
    cmpd = _make_plate(data, "compound", time_col)[0][0, ...]
    conc = _make_plate(data, "conc", time_col)[0][0, ...]

    # Create figure and fill in layout
    fig = {"data": [], "layout": {}, "frames": []}

    fig["layout"] = go.Layout(
        title=feature,
        title_x=0.5,
        xaxis={
            "showgrid": False,
            "showticklabels": True,
            "tickfont": {"size": 16, "color": "black"},
        },
        yaxis={
            "showgrid": False,
            "showticklabels": True,
            "tickfont": {"size": 16, "color": "black"},
        },
        hovermode="closest",
        updatemenus=[
            {
                "buttons": [
                    {
                        "args": [
                            None,
                            {
                                "frame": {"duration": 500, "redraw": True},
                                "fromcurrent": True,
                                "transition": {
                                    "duration": 300,
                                    "easing": "quadratic-in-out",
                                },
                            },
                        ],
                        "label": "Play",
                        "method": "animate",
                    },
                    {
                        "args": [
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": True},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                        "label": "Pause",
                        "method": "animate",
                    },
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 87},
                "showactive": False,
                "type": "buttons",
                "x": 0.1,
                "xanchor": "right",
                "y": 0,
                "yanchor": "top",
            }
        ]
        if len(times) > 1
        else None,
    )

    # Add Time 0 plate to data
    fig["data"].append(platemap(cols, rows, plate[0, ...], cmpd, conc))

    # Create frames & animations
    if len(times) > 1:
        # Create sliders
        sliders = {
            "active": 0,
            "yanchor": "top",
            "xanchor": "left",
            "currentvalue": {
                "font": {"size": 20},
                "prefix": "Timepoint:",
                "visible": True,
                "xanchor": "right",
            },
            "transition": {"duration": 300, "easing": "cubic-in-out"},
            "pad": {"b": 10, "t": 50},
            "len": 0.9,
            "x": 0.1,
            "y": 0,
            "steps": [],
        }

        # Create frames
        for time in data[time_col].unique().astype(str):
            # New frame
            fig["frames"].append(
                {
                    "data": platemap(cols, rows, plate[int(time) - 1, ...], cmpd, conc),
                    "name": str(time),
                }
            )

            # Corresponding slider step
            sliders["steps"].append(
                {
                    "args": [
                        [time],
                        {
                            "frame": {"duration": 300, "redraw": True},
                            "mode": "immediate",
                            "transition": {"duration": 300},
                        },
                    ],
                    "label": time,
                    "method": "animate",
                }
            )

        # Add sliders to figure layout
        fig["layout"]["sliders"] = [sliders]

    return go.Figure(fig)


def pca_comps(proj, exp_var, time_col="timepoint", n_comps=4):
    """
    Plot a scatter grid of PCA components

    This function is written to use the output from `process.dim_reduction`

    Parameters
    ----------
    `proj` : _pd.DataFrame
        Data frame with pca projections, from `process.dim_reduction`
    `exp_var` : array_like
        List of explained variances for each PCA component
    `time_col` : str, optional
        Column containing time points; must be in index; by default 'timepoint'
    `n_comps` : int, optional
        Number of pca components to plot, by default 4

    Returns
    -------
    go.Figure
        Plotly figure
    """

    # TODO: Improve plotting for pCA grid
    #   Use `plotly.graph_objects` instead of `plotly.express`
    #   Add better user controls for point colors & sizes

    proj.columns = [x.lower() for x in proj.columns]
    assert "variable" in proj.columns, "variable must be a column in proj"
    assert "compound" in proj.columns, f"compound must be a column in proj"
    assert time_col in proj.columns, f"{time_col} must be a column in proj"
    assert "conc" in proj.columns, "conc must be a column in proj"

    # Prepare matrix of components as well as variables for plotting
    comp_cols = [str(x + 1) for x in range(n_comps)]
    comps = proj.query("variable == 'PCA'").reset_index(drop=True)[
        ["compound", "conc", time_col, *comp_cols]
    ]
    compounds = comps["compound"]
    comps.drop(["compound", time_col, "conc"], axis=1, inplace=True)

    # Create labels
    labels = {str(i): f"PC {i+1} ({var:.2f}%)" for i, var in enumerate(exp_var)}

    # Create figure
    fig = px.scatter_matrix(
        comps.values,
        labels=labels,
        dimensions=range(n_comps),
        color=compounds,
        opacity=0.5,
        template="plotly_white",
    )
    fig.update_traces(diagonal_visible=False)
    fig.update_layout(paper_bgcolor="white", plot_bgcolor="white", height=500)

    return fig


def clusters(data, compound_a, compound_b, method, time_col="timepoint"):
    """
    Create clustering figures that compare 2 compounds.

    This function is written to use the output from `process.dim_reduction`

    Parameters
    ----------
    `data` : pd.DataFrame
        _description_
    `compound_a` : str
        Compound A (red points)
    `compound_b` : str
        Compound B (green points)
    `method` : str
        One of 'PCA', 'tSNE' or 'UMAP'
    `time_col` : str, optional
        Column containing time points, by default 'timepoint'

    Returns
    -------
    go.Figure
        Plotly figure
    """

    assert isinstance(data, pd.DataFrame), "data must be a data frame"
    assert "compound" in data.columns, "'compound' must be a column in data"
    assert (
        compound_a in data["compound"].tolist()
    ), "compound_a must be present in data['compound']"
    assert (
        compound_b in data["compound"].tolist()
    ), "compound_b must be present in data['compound']"
    method = method.lower()
    assert method in [
        "pca",
        "tsne",
        "umap",
    ], "method must be one of 'PCA', 'tSNE' or 'UMAP'"
    assert time_col in data.columns, f"{time_col} must be a column in proj"

    times = data[time_col].unique()
    method = method.upper()

    def create_traces(compound, colorscale, linecolor, cbar_pos):
        """
        Create traces for a particular compound
        """

        # Define colors for different time points
        if len(times) > 1:
            color_map = {
                tp: c
                for tp, c in zip(
                    times, sns.color_palette(colorscale, len(times)).as_hex()
                )
            }
            data["timecolor"] = data[time_col].replace(color_map)
        else:
            data["timecolor"] = colorscale

        # Subset data for compound
        cmpd = data.query(
            f"compound == '{compound}' & variable == '{method}'"
        ).reset_index(drop=True)

        # Encode different sizes for each concentration
        cmpd["conc"] = cmpd["conc"].astype(float)
        concs = sorted(cmpd["conc"].unique())
        if len(concs) > 1:
            conc_map = {c: s * 3 for c, s in zip(concs, range(1, len(concs) + 1))}
        else:
            conc_map = {concs[0]: 20}

        # Create traces
        traces = []

        for i, conc in enumerate(concs):
            # Create mask to subset data
            I = cmpd["conc"] == conc

            traces.append(
                go.Scatter(
                    x=cmpd.loc[I, "1"],
                    y=cmpd.loc[I, "2"],
                    mode="markers",
                    marker=dict(
                        color=cmpd.loc[I, time_col],
                        size=conc_map[conc],
                        opacity=0.5,
                        colorscale=colorscale,
                        colorbar=dict(
                            x=cbar_pos, thickness=20, yanchor="middle", len=0.7
                        )
                        if (i == 0) and (len(times) > 1)
                        else None,
                        line=dict(width=1.2, color=linecolor),
                    ),
                    name=str(conc),
                    legendgroup=compound.replace(" ", "").lower(),
                    legendgrouptitle_text=(compound if i == 0 else None),
                )
            )

        return traces

    # Create figure traces
    traces = [
        *create_traces(compound_a, "Reds", "red", -0.25),
        *create_traces(compound_b, "Greens", "green", -0.35),
    ]

    # Create layout
    layout = go.Layout(
        legend=dict(tracegroupgap=20, groupclick="toggleitem"),
        template="plotly_white",
        margin=dict(l=20, r=20, t=70, b=40),
        height=500,
        title=f"{compound_a} vs {compound_b}<br>({method} Clusters)",
        title_x=0.5,
        xaxis_title=f"{method} 1",
        yaxis_title=f"{method} 2",
    )

    # Create figure
    fig = go.Figure(data=traces, layout=layout)
    fig.update_yaxes(scaleanchor="x", scaleratio=1)

    # Annotate the colorbars
    if len(times) > 1:
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=-0.33,
            y=0.92,
            text="Time Point",
            font_size=14,
            showarrow=False,
        )

    return fig


def _make_grid(items, col_wrap=2):
    """
    Split a list of items into a grid for subplots

    Parameters
    ----------
    `items` : list
        List of items for each subplot (e.g., tiles)
    `col_wrap` : int, optional
        Number of columns allowed in layout, by default 2

    Returns
    -------
    go.Figure
        Plotly figure
    """

    def grid_dims(n, col_wrap):
        """
        Determine grid dimensions
        """

        nrows = math.ceil(n / col_wrap)
        ncols = col_wrap if n > col_wrap else n

        return nrows, ncols

    nrows, ncols = grid_dims(len(items), col_wrap)
    positions = {
        x: {"x": (i // col_wrap) + 1, "y": (i % col_wrap) + 1}
        for i, x in enumerate(items)
    }

    return nrows, ncols, positions


def _v(m1, m2, hue):
    hue = hue % 1.0
    if hue < ONE_SIXTH:
        return m1 + (m2 - m1) * hue * 6.0
    if hue < 0.5:
        return m2
    if hue < TWO_THIRD:
        return m1 + (m2 - m1) * (TWO_THIRD - hue) * 6.0
    return m1


def _hls_to_rgb(h, l, s):
    """
    Convert HLS (Hue, Luminance, Saturation) to RGB
    """

    if s == 0.0:
        return l, l, l
    if l <= 0.5:
        m2 = l * (1.0 + s)
    else:
        m2 = l + s - (l * s)
    m1 = 2.0 * l - m2
    return (_v(m1, m2, h + ONE_THIRD), _v(m1, m2, h), _v(m1, m2, h - ONE_THIRD))


def _get_colors(n):
    """
    Generate n visually distinct colors.

    This is taken from [this](https://stackoverflow.com/a/9701141) stack
    overflow post.
    """

    colors = []
    for i in np.arange(0.0, 360.0, 360.0 / n):
        hue = i / 360.0
        lightness = (50 + np.random.rand() * 10) / 100
        saturation = (90 + np.random.rand() * 10) / 100

        r, g, b = _hls_to_rgb(hue, lightness, saturation)
        colors.append("#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255)))

    return colors


def distplot(
    data, features, group_col, tooltips=None, kind="box", col_wrap=2, title_len=30
):
    """
    Create boxplots showing the distibution of features for different groups.

    This generates a figure with as many subplots as there are features

    Parameters
    ----------
    `data` : pd.DataFrame
        Data frame to plot
    `features` : list
        List of features to visualize
    `group_col` : str
        `data` column that contains groups of interest
    `tooltips` : dict, optional
        Dictionary that defines annotation tooltips, by default None
        Keys = Tooltip Name;
        Values = Corresponding column in `data`
    `kind` : str, optional
        Type of plot to generate; one of 'box', 'bar', by default 'box'
    `col_wrap` : int, optional
        Number of columns allowed in layout, by default 3
    `title_len` : int, optional
        Wrap length for subplot titles, by default 30

    Returns
    -------
    go.Figure
        Plotly figure

    Raises
    ------
    NotImplementedError
        When `kind != 'box'`
    """

    assert isinstance(data, pd.DataFrame), "data must be a data frame"
    assert kind in ["box", "bar"], "kind must be one of 'box', 'bar'."
    assert group_col in data.columns, "group_col must be a column in data"
    for f in features:
        assert f in data.columns, "features must contain columns from data"
    if tooltips is not None:
        for col in tooltips.values():
            assert col in data.columns, "Values of tooltips must be columns of data"

    # Determine grid dimensions & positions
    nrows, ncols, positions = _make_grid(features, col_wrap=col_wrap)

    # Wrap text for subplot titles
    titles = ["<br>".join(textwrap.wrap(x, title_len)) for x in features]

    # Get list of groups & colors
    groups = data[group_col].unique()
    colors = _get_colors(len(groups))

    # Create figure
    fig = sp.make_subplots(rows=nrows, cols=ncols, subplot_titles=titles)

    # Add traces
    if kind == "box":
        for feature, pos in positions.items():
            for grp, color in zip(groups, colors):
                # Prepare data for annotations
                _data = data.query(f"{group_col} == '{grp}'")
                text = "well: " + data["well"] + "<br>"
                if tooltips is not None:
                    for name, col in tooltips.items():
                        text += f"{name}: " + data[col].astype(str) + "<br>"

                fig.add_trace(
                    go.Box(
                        y=_data[feature],
                        name=grp,
                        text=text.tolist(),
                        hovertemplate="%{text}",
                        legendgroup=grp,
                        marker_color=color,
                        showlegend=True if pos["x"] == pos["y"] == 1 else False,
                    ),
                    row=pos["x"],
                    col=pos["y"],
                )
    elif kind == "bar":
        raise NotImplementedError("Can't do that yet. Working on it.")
    else:
        raise NotImplementedError("Can't do that yet.")

    fig.update_xaxes(showticklabels=False)
    fig.update_layout(template="plotly_white")
    fig.update_annotations(font=dict(family="Helvetica", size=14))

    return fig


def textplot(text):
    """
    Create a blank figure to display some text. Serves as placeholder for
    actual figure.

    Parameters
    ----------
    `text` : str
        Message to display in figure

    Return
    ------
    go.Figure
        Plotly figure
    """

    fig = go.Figure(
        go.Scatter(
            x=[0],
            y=[0],
            text=[text],
            textposition="top center",
            textfont_size=16,
            mode="text",
            hoverinfo="skip",
        )
    )
    fig.update_layout(template="simple_white", height=300)
    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True)

    return fig


def gifify(fig, file, frame_title="Frame", fps=30) -> None:
    """
    Export a plotly animation as a gif

    Parameters
    ----------
    `fig` : go.Figure
        Plotly figure
    `file` : str
        Path to file where figure gif will be stored
    `frame_title` : str, optional
        Title that describes each frame, by default 'Frame'
    `fps` : int, optional
        Frame rate, by default 30
    """

    assert isinstance(fig, go.Figure), "This only works for plotly figures"
    assert file.endswith(".gif"), "file must be a .gif"

    import moviepy.editor as mpy
    from PIL import Image

    def fig2array(fig):
        """
        Convert a plotly figure to a numpy array
        """

        bytes = fig.to_image(format="jpg", engine="kaleido")
        buffer = io.BytesIO(bytes)
        img = Image.open(buffer)

        return img

    # Remove sliders and buttons from figure layout
    exclude = ["updatemenus", "sliders"]
    layout = fig.to_dict()["layout"]
    layout = {k: v for k, v in layout.items() if not k in exclude}

    # Create list to store frames (as images)
    frames = []
    for i, frame in enumerate(fig["frames"]):
        _fig = go.Figure(data=frame["data"], layout=layout)
        _fig.update_layout(title=f"{frame_title} {i+1}", title_x=0.5)
        frames.append(fig2array(_fig))

    # Create animation
    make_frame = lambda t: frames[int(t)]
    anim = mpy.VideoClip(make_frame, duration=len(frames))
    anim.write_gif(file, fps=fps, logger=None)
    print("Done :thumbsup:")


def heatmap(
    data,
    col_groups=None,
    col_colors=None,
    col_group_names=None,
    row_groups=None,
    row_colors=None,
    row_group_names=None,
    clust_cols=True,
    clust_rows=True,
    cluster_kws=dict(),
):
    """
    Construct an interactive heatmap

    Parameters
    ----------
    data : pd.DataFrame
        Data to plota
    {row, col}_groups : dict
        Dictionary assigning groups to rows or columns.
        Keys should be the index or columns of data.
        Values should be a list of groups.
    {row, col}_group_names : list
        Names for each of the row/col groups
        Should be the same length as the lists in {row, col}_groups
    {row, col}_colors : dict
        Dictionary defining colors for each group.
        Keys = groups;  Values = colors;
    clust_{rows, cols} : bool
        Should row and/or column clustering be performed
    cluster_kws : dict
        kwargs for sns.clustermap
    """

    # TODO: plot.heatmap: Improve Usability
    #   Make the function easier to use, or write a wrapper similar to `seaborn.heatmap`
    #   Also add input checking

    from sklearn.preprocessing import LabelEncoder

    # Check inputs

    ## col_groups and row_groups: each value should be of the same length
    if col_group_names is None:
        col_group_names = []
    if row_group_names is None:
        row_group_names = []

    # Determine the size of the subplot grid
    n_col_grps = len(col_group_names)
    n_row_grps = len(row_group_names)
    I, J = n_col_grps + 1, n_row_grps + 1

    # Define column widths and row heights
    col_widths = [0.03 for _ in range(J - 1)] + [1 - (J - 1) * 0.03]
    row_heights = [0.07 for _ in range(I - 1)] + [1 - (I - 1) * 0.07]

    # Create subplot grid
    fig = sp.make_subplots(
        rows=I,
        cols=J,
        column_widths=col_widths,
        row_heights=row_heights,
        vertical_spacing=0.01,
        horizontal_spacing=0.01,
        shared_xaxes=True,
        shared_yaxes=True,
    )

    # Perform clustering and extract clustered data frame from seaborn clustermap
    if clust_cols or clust_rows:
        data = sns.clustermap(
            data, row_cluster=clust_rows, col_cluster=clust_cols, **cluster_kws
        ).data2d
        plt.close()

    # Plot the heatmap and adjust axes
    fig.append_trace(
        go.Heatmap(
            z=data,
            x=data.columns,
            y=data.index.astype(str),
            colorscale="RdBu_r",
            hovertemplate="<b>Sample:</b> %{y}<br>"
            + "<b>Feature:</b> %{x}<br>"
            + "<b>Value:</b>%{z}"
            "<extra></extra>",
        ),
        row=I,
        col=J,
    )
    fig.update_yaxes(row=I, col=J, showticklabels=False, autorange="reversed")
    fig.update_xaxes(row=I, col=J, showticklabels=True, tickangle=270)
    fig.update_traces(row=I, col=J, colorbar_len=0.7)

    # Add row colors
    if row_groups is not None:
        for j, grp in enumerate(row_group_names):
            # Create row data
            row_data = [row_groups[r][j] for r in data.index]

            # Encode row data numerically so that heatmap can be plotted
            le = LabelEncoder().fit(row_data)
            Z = le.transform(row_data)

            # Define colorscale
            znorm = np.unique((Z - Z.min()) / (Z.max() - Z.min()))
            zmax = Z.max()
            colorscale = [
                [z, row_colors[le.inverse_transform([int(z * zmax)])[0]]] for z in znorm
            ]

            fig.append_trace(
                go.Heatmap(
                    z=pd.DataFrame(Z),
                    y=data.index.astype(str),
                    x=[grp],
                    text=pd.DataFrame(row_data),
                    colorscale=colorscale,
                    hovertemplate="<b>Sample:<b> %{y}<br>"
                    + f"<b>{grp}:</b>: %{{text}}"
                    + "<extra></extra>",
                    showscale=False,
                ),
                row=I,
                col=j + 1,
            )
            fig.update_yaxes(
                row=I, col=j + 1, showticklabels=False, autorange="reversed"
            )
            fig.update_xaxes(
                row=I,
                col=j + 1,
                showticklabels=True,
                tickangle=270,
                tickfont={"size": 15, "family": "Arial"},
            )

    # Add column colors
    if col_groups is not None:
        for i, grp in enumerate(col_group_names):
            # Create column data
            col_data = [col_groups[r][i] for r in data.columns]

            # Encode col data numerically so that heatmap can be plotted
            le = LabelEncoder().fit(col_data)
            Z = le.transform(col_data)

            # Define colorscale
            znorm = np.unique((Z - Z.min()) / (Z.max() - Z.min()))
            zmax = Z.max()
            colorscale = [
                [z, col_colors[le.inverse_transform([int(z * zmax)])[0]]] for z in znorm
            ]

            fig.append_trace(
                go.Heatmap(
                    z=pd.DataFrame(Z).T,
                    y=[grp],
                    x=data.columns,
                    text=pd.DataFrame(col_data).T,
                    colorscale=colorscale,
                    hovertemplate="<b>Feature:</b> %{x}<br>"
                    + f"<b>{grp}:</b>: %{{text}}"
                    + "<extra></extra>",
                    showscale=False,
                ),
                row=i + 1,
                col=J,
            )
            fig.update_yaxes(
                row=i + 1,
                col=J,
                showticklabels=True,
                autorange="reversed",
                side="right",
                tickfont={"size": 15, "family": "Arial"},
            )
            fig.update_xaxes(row=i + 1, col=J, showticklabels=False)

    # TODO: plot.heatmap: Add legends to empty subplots i figure grid

    # FIXME: plot.heatmap: Clustering rows makes some data disappear

    return fig
