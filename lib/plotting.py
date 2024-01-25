# Created by alex at 28.06.23
import itertools
from dateutil.relativedelta import relativedelta
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from adjustText import adjust_text
from .constant import *


sns.set_style('darkgrid')
sns.set_context("talk")


def get_label_colors():
    colors = {'inlier': '#1f77b4',
              'not tested': '#505050',
              'outlier': '#d62728',
              'outlier recall': 'orange'
              }
    return colors


def get_date_outlier_labels_flags(plot_frame, filter_column, filter_value, outlier_column, sewageFlag: SewageFlag, select_column):
    labels = []
    plot_frame = plot_frame[plot_frame[filter_column] == filter_value]
    for index, current_row in plot_frame.iterrows():
        if SewageFlag.is_flag(current_row[outlier_column], sewageFlag):
            date = current_row['date'].strftime("%Y-%m-%d")
            t = (current_row['date'], current_row[select_column], date)
            labels.append(t)
    return labels


def get_date_outlier_labels_value(plot_frame, filter_column, filter_value, outlier_column, outlier_value, select_column):
    labels = []
    plot_frame = plot_frame[plot_frame[filter_column] == filter_value]
    for index, current_row in plot_frame.iterrows():
        if current_row[outlier_column] == outlier_value:
            date = current_row['date'].strftime("%Y-%m-%d")
            t = (current_row['date'], current_row[select_column], date)
            labels.append(t)
    return labels


def get_general_outlier_date_labels(plot_frame, outlier_col='outlier'):
    labels = []
    for index, current_row in plot_frame.iterrows():
        if current_row[outlier_col] != "":
            date = current_row['date'].strftime("%Y-%m-%d")
            t = plt.text(current_row['date'], current_row['value'], date, size='xx-small', color='black', horizontalalignment='right', rotation=0)
            labels.append(t)
    return labels

def get_date_outlier_labels_by_value(plot_frame, outlier_col='outlier', value='outlier'):
    labels = []
    for index, current_row in plot_frame.iterrows():
        if current_row[outlier_col] == value:
            date = current_row['date'].strftime("%Y-%m-%d")
            t = plt.text(current_row['date'], current_row['value'], date, size='xx-small', color='black', horizontalalignment='right', rotation=0)
            labels.append(t)
    return labels


def __add_outlier_date_labels2ax(g, labels_dict: dict):
    for biomarker_ratio, ax in g.axes_dict.items():
        texts = []
        for tuples in labels_dict[biomarker_ratio]:
            t = ax.text(tuples[0], tuples[1], tuples[2], size='xx-small', color='black', horizontalalignment='right', rotation=0)
            texts.append(t)
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='-', color='red'))

def plot_biomarker_outlier_summary(pdf_plotter, measurements_df, sample_location, outlier_detection_methods):
    plot_frame = pd.DataFrame()
    labels_dict = dict()
    for biomarker1, biomarker2 in itertools.combinations(Columns.get_biomarker_columns(), 2):
        biomarker_ratio = biomarker1 + "/" + biomarker2
        length = len(measurements_df[biomarker_ratio].dropna())
        if length > 0:
            dat = pd.DataFrame()
            dat['date'] = measurements_df[Columns.DATE]
            dat['ratio/median ratio'] = measurements_df[biomarker_ratio]
            dat['biomarker_ratio'] = biomarker_ratio
            dat['outlier'] = measurements_df[CalculatedColumns.get_biomaker_ratio_flag(biomarker1, biomarker2)]
            plot_frame = pd.concat([plot_frame, dat])
            labels_dict[biomarker_ratio] = \
                get_date_outlier_labels_flags(plot_frame, 'biomarker_ratio', biomarker_ratio,
                                              'outlier', SewageFlag.BIOMARKER_RATIO_OUTLIER, 'ratio/median ratio')

    if plot_frame.shape[0] > 0:
        plot_frame['outlier'] = np.where(
            (SewageFlag.is_flag_set_for_series(plot_frame['outlier'], SewageFlag.NOT_ENOUGH_PREVIOUS_BIOMARKER_VALUES)),
            'not tested',
            np.where((SewageFlag.is_flag_set_for_series(plot_frame['outlier'], SewageFlag.BIOMARKER_RATIO_OUTLIER_REMOVED)), 'outlier recall',
                     np.where((SewageFlag.is_flag_set_for_series(plot_frame['outlier'], SewageFlag.BIOMARKER_RATIO_OUTLIER)), 'outlier', 'inlier')))

        g = sns.FacetGrid(plot_frame, col="biomarker_ratio", col_wrap=1, margin_titles=True, height=5, aspect=6, sharey=False, legend_out=True)
        min_date = plot_frame['date'].min() + relativedelta(days=-10)
        max_date = plot_frame['date'].max() + relativedelta(days=10)
        g.set(xlim=(min_date, max_date))
        g.set(yscale="log")
        g.map_dataframe(sns.scatterplot, x="date", y="ratio/median ratio", hue="outlier", palette=get_label_colors())
        # add outlier dates as text labels to each axis
        __add_outlier_date_labels2ax(g, labels_dict)
        color_dict = get_label_colors()
        legend_patches = []
        for label, color in color_dict.items():
            #legend_patches.append(matplotlib.patches.Patch(color=color, label=label))
            legend_patches.append(Line2D([0], [0], marker='o', markerfacecolor=color, color='white', linewidth=0, label=label, markersize=15))
        if any(labels_dict.values()):
            plt.legend(handles=legend_patches, loc="upper center", bbox_to_anchor=(.5, -0.2), ncol=3, title=None, frameon=True)
        g.set_titles(row_template='{row_name}', col_template='{col_name}')
        g.fig.subplots_adjust(top=0.9, bottom=0.1)
        g.fig.suptitle("Biomarker ratios for '{}' -  Outlier detection methods: {}".format(sample_location, outlier_detection_methods))
        pdf_plotter.savefig()
        plt.cla()
        plt.close()


def plot_surrogatvirus (pdf_plotter, measurements_df, sample_location, outlier_detection_methods):
    plot_frame = pd.DataFrame()
    labels_dict = dict()
    for sVirus in Columns.get_surrogatevirus_columns():
        dat = pd.DataFrame()
        dat['date'] = measurements_df[Columns.DATE]
        dat['value'] = measurements_df[sVirus]
        dat['type'] = sVirus
        dat['outlier'] = np.where(
            (SewageFlag.is_flag_set_for_series(measurements_df[CalculatedColumns.FLAG.value],
                                               SewageFlag.SURROGATEVIRUS_VALUE_NOT_USABLE)),
            'not tested', np.where((SewageFlag.is_flag_set_for_series(
                measurements_df[CalculatedColumns.FLAG.value], CalculatedColumns.get_surrogate_outlier_flag(sVirus))),
                'outlier', 'inlier'))
        plot_frame = pd.concat([plot_frame, dat])
        labels_dict[sVirus] = get_date_outlier_labels_value(plot_frame, 'type', sVirus, 'outlier', 'outlier', 'value')
    g = sns.FacetGrid(plot_frame, col="type", col_wrap=1, margin_titles=True, height=5, aspect=6, sharey=False, legend_out=True)
    min_date = plot_frame['date'].min() + relativedelta(days=-10)
    max_date = plot_frame['date'].max() + relativedelta(days=10)
    g.set(xlim=(min_date, max_date))
    g.map_dataframe(sns.scatterplot, x="date", y="value", hue="outlier", palette=get_label_colors())
    __add_outlier_date_labels2ax(g, labels_dict)
    if any(labels_dict.values()):
        plt.legend(loc="upper center", bbox_to_anchor=(.5, -0.2), ncol=3, title=None, frameon=True)
    g.set_titles(row_template='{row_name}', col_template='{col_name}')
    g.fig.subplots_adjust(top=0.9)
    g.fig.suptitle("Surrogatvirus quality control for '{}' -  Outlier detection methods: {}".format(sample_location, outlier_detection_methods))
    plt.tight_layout()
    pdf_plotter.savefig()
    plt.cla()
    plt.close()


def plot_water_quality(pdf_plotter, measurements_df, sample_location,  outlier_detection_methods):
    plot_frame = pd.DataFrame()
    labels_dict = dict()
    for qual_type, outlier_flag, not_enough_flag in zip([Columns.AMMONIUM, Columns.CONDUCTIVITY],
                                                        [SewageFlag.AMMONIUM_OUTLIER, SewageFlag.CONDUCTIVITY_OUTLIER],
                                                        [SewageFlag.NOT_ENOUGH_AMMONIUM_VALUES, SewageFlag.NOT_ENOUGH_CONDUCTIVITY_VALUES]):
        dat = pd.DataFrame()
        dat['date'] = measurements_df[Columns.DATE]
        dat['value'] = measurements_df[qual_type]
        dat['type'] = qual_type
        dat['outlier'] = measurements_df[CalculatedColumns.FLAG.value]
        dat['outlier'] = np.where((SewageFlag.is_flag_set_for_series(measurements_df[CalculatedColumns.FLAG.value], not_enough_flag)), 'not tested',
                                     np.where((SewageFlag.is_flag_set_for_series(measurements_df[CalculatedColumns.FLAG.value], outlier_flag)), 'outlier', 'inlier'))
        plot_frame = pd.concat([plot_frame, dat])
        labels_dict[qual_type] = get_date_outlier_labels_value(plot_frame, 'type', qual_type, 'outlier', 'outlier', 'value')

    g = sns.FacetGrid(plot_frame, col="type", col_wrap=1, margin_titles=True, height=5, aspect=6, sharey=False, legend_out=True)
    min_date = plot_frame['date'].min() + relativedelta(days=-10)
    max_date = plot_frame['date'].max() + relativedelta(days=10)
    g.set(xlim=(min_date, max_date))
    g.map_dataframe(sns.scatterplot, x="date", y="value", hue="outlier", palette=get_label_colors(), legend="full")
    __add_outlier_date_labels2ax(g, labels_dict)
    if any(labels_dict.values()):
        plt.legend(loc="upper center", bbox_to_anchor=(.5, -0.2), ncol=3, title=None, frameon=True)
    g.set_titles(row_template='{row_name}', col_template='{col_name}')
    g.fig.subplots_adjust(top=0.9)
    g.fig.suptitle("Water quality control for '{}' -  Outlier detection methods: {}".format(sample_location, outlier_detection_methods))
    plt.tight_layout()
    pdf_plotter.savefig()
    plt.cla()
    plt.close()


def plot_sewage_flow(pdf_plotter, measurements_df, sample_location):
    plot_frame = pd.DataFrame()
    plot_frame['date'] = measurements_df[Columns.DATE]
    plot_frame['value'] = measurements_df[Columns.MEAN_SEWAGE_FLOW]
    plot_frame['outlier'] = np.where(
        (SewageFlag.is_flag_set_for_series(measurements_df[CalculatedColumns.FLAG.value], SewageFlag.SEWAGE_FLOW_HEAVY_PRECIPITATION)) |
        (SewageFlag.is_flag_set_for_series(measurements_df[CalculatedColumns.FLAG.value], SewageFlag.SEWAGE_FLOW_PROBABLE_TYPO)),
        'outlier', np.where((SewageFlag.is_flag_set_for_series(measurements_df[CalculatedColumns.FLAG.value], SewageFlag.SEWAGE_FLOW_NOT_ENOUGH_PREVIOUS_VALUES)),
        'not tested', 'inlier'))
    plt.figure(figsize=(30, 8))
    g = sns.scatterplot(data=plot_frame, x="date", y="value", hue="outlier", palette=get_label_colors())
    min_date = plot_frame['date'].min() + relativedelta(days=-10)
    max_date = plot_frame['date'].max() + relativedelta(days=10)
    g.set(xlim=(min_date, max_date))
    # if dry_weather_flow:
    #    g.axhline(dry_weather_flow, label="Dry weather flow", linestyle='dashed', c='black')
    #    plt.title("Mean sewage flow for '{}' - Dry weather flow: '{}'".format(sample_location, round(dry_weather_flow,1)))
    # plt.legend(bbox_to_anchor=(1.01, 0.5), loc='center left', borderaxespad=0)
    labels = get_date_outlier_labels_by_value(plot_frame, 'outlier', 'outlier')
    adjust_text(labels)
    sns.move_legend(
        g, loc="upper center",
        bbox_to_anchor=(.5, -0.1), ncol=3, title=None, frameon=True
    )
    plt.title("Mean sewage flow for '{}'".format(sample_location), fontsize=22)
    plt.ylabel('Mean sewage flow')
    plt.tight_layout()
    pdf_plotter.savefig()
    plt.cla()
    plt.close()


def plot_biomarker_normalization(pdf_plotter, measurements_df, sample_location):
    plot_frame = pd.DataFrame()
    labels_dict = dict()
    for column_type in [CalculatedColumns.NORMALIZED_MEAN_BIOMARKERS.value, CalculatedColumns.BASE_REPRODUCTION_FACTOR.value]:
        dat = pd.DataFrame()
        dat['date'] = measurements_df[Columns.DATE]
        dat['value'] = measurements_df[column_type]
        dat['type'] = column_type
        dat['outlier'] = np.where(
            (SewageFlag.is_flag_set_for_series(measurements_df[CalculatedColumns.FLAG.value], SewageFlag.REPRODUCTION_NUMBER_OUTLIER)),
            'outlier', np.where((SewageFlag.is_flag_set_for_series(measurements_df[CalculatedColumns.FLAG.value], SewageFlag.REPRODUCTION_NUMBER_OUTLIER_SKIPPED)),
                                'not tested', 'inlier'))
        plot_frame = pd.concat([plot_frame, dat])
        labels_dict[column_type] = get_date_outlier_labels_value(plot_frame, 'type', column_type, 'outlier', 'outlier', 'value')
    g = sns.FacetGrid(plot_frame, col="type", col_wrap=1, margin_titles=True, height=5, aspect=6, sharey=False, legend_out=True)
    min_date = plot_frame['date'].min() + relativedelta(days=-2)
    max_date = plot_frame['date'].max() + relativedelta(days=2)
    g.set(xlim=(min_date, max_date))
    g.map_dataframe(sns.scatterplot, x="date", y="value", hue="outlier", palette=get_label_colors())
    __add_outlier_date_labels2ax(g, labels_dict)
    plt.legend(loc="upper center", bbox_to_anchor=(.5, -0.2), ncol=3, title=None, frameon=True)
    g.set_titles(row_template='{row_name}', col_template='{col_name}')
    g.fig.subplots_adjust(top=0.9)
    g.fig.suptitle("Biomarker normalization for '{}'".format(sample_location))
    g.fig.axes[1].set_yscale("symlog", base=2)
    plt.tight_layout()
    pdf_plotter.savefig()
    plt.cla()
    plt.close()


def plot_general_outliers(pdf_plotter, measurements_df, sample_location):
    plot_frame = pd.DataFrame()
    plot_frame['date'] = measurements_df[Columns.DATE]
    plot_frame['value'] = measurements_df[CalculatedColumns.NORMALIZED_MEAN_BIOMARKERS.value]
    plot_frame['outlier'] = measurements_df[CalculatedColumns.OUTLIER_REASON.value]
    plt.figure(figsize=(30, 10))
    g = sns.scatterplot(data=plot_frame, x="date", y="value", hue="outlier")
    min_date = plot_frame['date'].min() + relativedelta(days=-10)
    max_date = plot_frame['date'].max() + relativedelta(days=10)
    g.set(xlim=(min_date, max_date))
    labels = get_general_outlier_date_labels(plot_frame, 'outlier')
    adjust_text(labels)
    if len(labels) > 0:
        sns.move_legend(
            g, loc="upper center",
            bbox_to_anchor=(.5, -0.1), ncol=2, title=None, frameon=True
        )
    plt.title("Outliers - Normalized mean biomarkers for '{}'".format(sample_location), fontsize=22)
    plt.tight_layout()
    pdf_plotter.savefig()
    plt.cla()
    plt.close()


