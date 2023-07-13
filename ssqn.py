#!/usr/bin/env python3

import os
import itertools
import argparse
import numpy as np
from lib.arcgis import *
from lib.constant import *
from lib.biomarkerQC import BiomarkerQC
from lib.surrogatevirusQC import SurrogatevirusQC
from lib.water_quality import WaterQuality
from lib.sewage_flow import SewageFlow
from lib.normalization import SewageNormalization
import lib.utils as utils
import lib.database as db


class SewageQuality:

    def __init__(self, output_folder, verbosity, quiet, rerun_all, interactive, biomarker_outlier_statistics,
                 min_biomarker_threshold, min_number_biomarkers_for_outlier_detection,
                 max_number_biomarkers_for_outlier_detection, report_number_of_biomarker_outlier, periode_month_surrogatevirus,
                 surrogatevirus_outlier_statistics, min_number_surrogatevirus_for_outlier_detection,
                 water_quality_number_of_last_month, min_number_of_last_measurements_for_water_qc, water_qc_outlier_statistics,
                 fraction_last_samples_for_dry_flow, min_num_samples_for_mean_dry_flow, heavy_precipitation_factor,
                 mean_sewage_flow_below_typo_factor, mean_sewage_flow_above_typo_factor, min_number_of_biomarkers_for_normalization,
                 base_reproduction_value_factor, max_number_of_flags_for_outlier
                  ):


        self.sewage_samples = None
        self.output_folder = output_folder
        self.verbosity = verbosity
        self.quiet = quiet
        self.rerun_all = rerun_all
        self.interactive = interactive
        # biomarker qc
        self.biomarker_outlier_statistics = biomarker_outlier_statistics
        self.min_biomarker_threshold = min_biomarker_threshold
        self.min_number_biomarkers_for_outlier_detection = min_number_biomarkers_for_outlier_detection
        self.max_number_biomarkers_for_outlier_detection = max_number_biomarkers_for_outlier_detection
        self.report_number_of_biomarker_outlier = report_number_of_biomarker_outlier
        # Surrogate virus
        self.periode_month_surrogatevirus = periode_month_surrogatevirus
        # Sewage flow
        self.fraction_last_samples_for_dry_flow = fraction_last_samples_for_dry_flow
        self.min_num_samples_for_mean_dry_flow = min_num_samples_for_mean_dry_flow
        self.heavy_precipitation_factor = heavy_precipitation_factor
        self.mean_sewage_flow_below_typo_factor = mean_sewage_flow_below_typo_factor
        self.mean_sewage_flow_above_typo_factor = mean_sewage_flow_above_typo_factor
        self.surrogatevirus_outlier_statistics = surrogatevirus_outlier_statistics
        self.min_number_surrogatevirus_for_outlier_detection = min_number_surrogatevirus_for_outlier_detection
        # Water quality
        self.water_quality_number_of_last_month = water_quality_number_of_last_month
        self.min_number_of_last_measurements_for_water_qc = min_number_of_last_measurements_for_water_qc
        self.water_qc_outlier_statistics = water_qc_outlier_statistics
        # biomarker normalization
        self.min_number_of_biomarkers_for_normalization = min_number_of_biomarkers_for_normalization
        self.base_reproduction_value_factor = base_reproduction_value_factor
        self.max_number_of_flags_for_outlier = max_number_of_flags_for_outlier

        self.logger = utils.SewageLogger(self.output_folder, verbosity=verbosity, quiet=quiet)
        self.__load_data()
        self.__setup()

    def __load_data(self):
        # arcgis = Arcgis(Config(self.config))
        # self.sewage_samples = arcgis.obtain_sewage_samples()
        # Todo: switch to real data import
        import pickle
        with open('data/sewageData.dat', 'rb') as f:
            self.sewage_samples = pickle.load(f)
        with open('data/sewagePlantData.dat', 'rb') as f:
            self.sewage_plants2trockenwetterabfluss = pickle.load(f)

    def __setup(self):
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        self.database = db.SewageDatabase(self.output_folder)
        self.biomarkerQC = BiomarkerQC(self.output_folder, self.interactive, self.biomarker_outlier_statistics, self.min_biomarker_threshold,
                                  self.min_number_biomarkers_for_outlier_detection,
                                  self.max_number_biomarkers_for_outlier_detection,
                                  self.report_number_of_biomarker_outlier)
        self.water_quality = WaterQuality(self.output_folder, self.interactive, self.water_quality_number_of_last_month,
                                          self.min_number_of_last_measurements_for_water_qc, self.water_qc_outlier_statistics)
        self.sewage_flow = SewageFlow(self.output_folder, self.interactive, self.sewage_plants2trockenwetterabfluss,
                                      self.fraction_last_samples_for_dry_flow, self.min_num_samples_for_mean_dry_flow,
                                      self.heavy_precipitation_factor, self.mean_sewage_flow_below_typo_factor, self.mean_sewage_flow_above_typo_factor)
        self.surrogateQC = SurrogatevirusQC(self.interactive, self.periode_month_surrogatevirus,
                                     self.min_number_surrogatevirus_for_outlier_detection,
                                     self.biomarker_outlier_statistics, self.output_folder)
        self.sewageNormalization = SewageNormalization(self.interactive, self.max_number_of_flags_for_outlier, self.min_number_of_biomarkers_for_normalization,
                                                       self.base_reproduction_value_factor, self.output_folder)

    def __initalize_flags(self, measurements: pd.DataFrame):
        for biomarker in Columns.get_biomarker_columns():
            measurements[CalculatedColumns.get_biomarker_flag(biomarker)] = 0
        for biomarker1, biomarker2 in itertools.combinations(Columns.get_biomarker_columns(), 2):
            measurements[CalculatedColumns.get_biomaker_ratio_flag(biomarker1, biomarker2)] = 0
        for sVirus in Columns.get_surrogatevirus_columns():
            measurements[CalculatedColumns.get_surrogate_flag(sVirus)] = 0
        for sVirus in Columns.get_surrogatevirus_columns():
            measurements[CalculatedColumns.get_surrogate_outlier_flag(sVirus)] = 0
        for c in CalculatedColumns:
            if not c.value in measurements:
                if c.type == bool:
                    measurements[c.value] = False
                elif c.type == str:
                    measurements[c.value] = ""
                else:
                    measurements[c.value] = 0
                measurements[c.value] = measurements[c.value].astype(c.type)

    def save_dataframe(self, sample_location, measurements: pd.DataFrame):
        result_folder = os.path.join(self.output_folder, "results")
        if not os.path.exists(result_folder):
            os.makedirs(result_folder)
        output_file = os.path.join(result_folder, "normalized_sewage_{}.xlsx".format(sample_location))
        measurements.to_excel(output_file, index=False)


    def run_quality_control(self):
        """
        Main method to run the quality checks and normalization
        """
        for idx, (sample_location, measurements) in enumerate(self.sewage_samples.items()):
            if idx < 5:
                continue   # skip first sewage location for testing  #Todo: remove before production
            self.logger.log.info("\n####################################################\n"
                             "\tSewage location: {} \n"
                             "####################################################".format(sample_location))

            measurements = utils.convert_sample_list2pandas(measurements)
            measurements = measurements.drop(columns=["flags"])   # artefact from stored data --> will be removed later
            measurements = measurements.fillna(value=np.nan)
            measurements[Columns.DATE.value] = pd.to_datetime(measurements[Columns.DATE.value],
                                                              format="%Y-%m-%d").dt.normalize()
            # Sort by collection date. Newest last.
            measurements.sort_values(by=Columns.DATE.value, ascending=True, inplace=True, ignore_index=True)

            self.__initalize_flags(measurements)
            self.database.needs_recalcuation(sample_location, measurements, self.rerun_all)

            self.logger.log.info("{}/{} new measurements to analyse".format(
                CalculatedColumns.get_num_of_unprocessed(measurements), measurements.shape[0]))

            # -----------------  BIOMARKER QC -----------------------
            # 1. check for comments. Flag samples that contain any commentary.
            self.biomarkerQC.check_comments(sample_location, measurements)
            self.biomarkerQC.check_mean_sewage_flow_present(sample_location, measurements)
            # 2. Mark biomarker values below threshold which are excluded from the analysis.
            self.biomarkerQC.biomarker_below_threshold_or_empty(sample_location, measurements)
            # 3. Calculate pairwise biomarker values if biomarkers were not marked to be below threshold.
            self.biomarkerQC.calculate_biomarker_ratios(sample_location, measurements)
            # 4. Detect outliers
            self.biomarkerQC.detect_outliers(sample_location, measurements)
            # 5. Assign biomarker outliers based on ratio outliers
            self.biomarkerQC.assign_biomarker_outliers_based_on_ratio_flags(sample_location, measurements)
            # Experimental: Final step explain flags
            measurements['flags_explained'] = SewageFlag.explain_flag_series(measurements[CalculatedColumns.FLAG.value])
            self.biomarkerQC.analyze_usable_biomarkers(sample_location, measurements)
            # 6. Create report in case the last two biomarkers were identified as outliers
            self.biomarkerQC.report_last_biomarkers_invalid(sample_location, measurements)

            # --------------------  SUROGATVIRUS QC -------------------
            self.surrogateQC.filter_dry_days_time_frame(sample_location, measurements)
            self.surrogateQC.is_surrogatevirus_outlier(sample_location, measurements)

            # --------------------  SEWAGE FLOW -------------------
            self.sewage_flow.sewage_flow_quality_control(sample_location, measurements)

            # --------------------  WATER QUALITY -------------------
            self.water_quality.check_water_quality(sample_location, measurements)

            # --------------------  NORMALIZATION -------------------
            self.sewageNormalization.normalize_biomarker_values(sample_location, measurements)

            # --------------------  MARK OUTLIERS FROM ALL STEPS -------------------
            self.sewageNormalization.decide_biomarker_usable_based_on_flags(sample_location, measurements)


            # Experimental: Final step explain flags
            measurements['flags_explained'] = SewageFlag.explain_flag_series(measurements[CalculatedColumns.FLAG.value])
            self.database.add_sewage_location2db(sample_location, measurements)
            self.save_dataframe(sample_location, measurements)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Sewage qPCR quality control",
        usage='use "python3  --help" for more information',
        epilog="author: Dr. Alexander Graf (graf@genzentrum.lmu.de)", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-o', '--output_folder', metavar="FOLDER", default="sewage_qc", type=str,
                        help="Specifiy output folder. (default folder: 'sewage_qc')",
                        required=False)
    parser.add_argument('-r', '--rerun_all', action="store_true", help="Rerun the analysis on all samples.")
    parser.add_argument('-i', '--interactive', action="store_true", help="Show plots interactively.")
    parser.add_argument('-v', '--verbosity', action="count", help="Increase output verbosity.")
    parser.add_argument('-q', '--quiet', action='store_true', help="Print litte output.")

    biomarker_qc_group = parser.add_argument_group("Biomarker quality control")
    biomarker_qc_group.add_argument('--biomarker_outlier_statistics', metavar="METHOD", default=['lof','rf','iqr'], nargs='+',
                        help=("Which outlier detection methods should be used? Multiple selections allowed. (default: 'lof','rf','iqr')\n"
                              "Possible choices are : [lof, rf, iqr, zscore, ci, all]\n"
                              "E.g. to select 'rf' and 'iqr' use: --biomarker_outlier_statistics rf iqr \n"
                              "\tlof = local outlier factor\n"
                              "\trf = random forest\n"
                              "\tiqr = interquartile range\n"
                              "\tzscore = modified z-score\n"
                              "\tci = 99%% confidence interval\n"
                              "\tall = use all methods\n") ,
                        choices=["lof", "rf", "iqr", "zscore", "ci", "all"],
                        required=False)
    biomarker_qc_group.add_argument('--biomarker_min_threshold', metavar="FLOAT", default=4, type=float,
                        help="Minimal biomarker threshold. (default: 4)",
                        required=False)
    biomarker_qc_group.add_argument('--min_number_biomarkers_for_outlier_detection', metavar="INT", default=9, type=int,
                        help="Minimal number of previous measurements required for outlier detection, otherwise this step is skipped. (default: 9)",
                        required=False)
    biomarker_qc_group.add_argument('--max_number_biomarkers_for_outlier_detection', metavar="INT", default=50, type=int,
                        help="Maximal number of previous measurements to use for outlier detection. (default: 50)",
                        required=False)
    biomarker_qc_group.add_argument('--report_number_of_biomarker_outliers', metavar="INT", default=2, type=int,
                        help="The number of outliers identified in the last N consecutive biomarker ratios that trigger a report. (default: 2)",
                        required=False)

    surrogatevirus_group = parser.add_argument_group("Surrogate virus quality control")
    surrogatevirus_group.add_argument('--periode_month_surrogatevirus', metavar="INT", default=4, type=int,
                        help="The periode of time (month) taken into account for surrogatevirus outliers. (default: 4)",
                        required=False)
    surrogatevirus_group.add_argument('--min_number_surrogatevirus_for_outlier_detection', metavar="FLOAT", default=2, type=float,
                        help="Minimal number of surrogatevirus measurements. (default: 2)",
                        required=False)
    surrogatevirus_group.add_argument('--surrogatevirus_outlier_statistics', metavar="METHOD", default=['lof','rf','iqr'], nargs='+',
                                    help=(
                                        "Which outlier detection methods should be used for surrogatevirus qc? Multiple selections allowed. (default: 'lof','rf','iqr')\n"
                                        "Possible choices are : [lof, rf, iqr, zscore, ci, all]\n"
                                        "E.g. to select 'rf' and 'iqr' use: --outlier_statistics rf iqr \n"
                                        "\tlof = local outlier factor\n"
                                        "\trf = random forest\n"
                                        "\tiqr = interquartile range\n"
                                        "\tzscore = modified z-score\n"
                                        "\tci = 99%% confidence interval\n"
                                        "\tall = use all methods\n"),
                                    choices=["lof", "rf", "iqr", "zscore", "ci", "all"],
                                    required=False)

    sewage_flow_group = parser.add_argument_group("Sewage flow quality control")
    sewage_flow_group.add_argument('--fraction_last_samples_for_dry_flow', metavar="FLOAT", default=0.1, type=float,
                                     help="If the dry flow of the sewage treatment plant is not known, "
                                          "the average dry flow rate is estimated from the previous flows rate of "
                                          "the lowest N percent of the samples. (default: 0.1)", choices=[round(x * 0.1, 1) for x in range(0, 10)],
                                     required=False)
    sewage_flow_group.add_argument('--min_num_samples_for_mean_dry_flow', metavar="INT", default=5, type=int,
                                   help="If the dry flow of the sewage treatment plant is not known, "
                                        "minimal N previous samples are required for the estimation of the dry flow rate. (default: 5)",
                                   required=False)
    sewage_flow_group.add_argument('--heavy_precipitation_factor', metavar="FLOAT", default=2.0, type=float,
                                   help="Factor above which the mean flow must be in comparison to the dry weather "
                                        "flow in order for the sample to be sorted out as a heavy rain event. (default: 2.0)",
                                   required=False)
    sewage_flow_group.add_argument('--mean_sewage_flow_below_typo_factor', metavar="FLOAT", default=1.5, type=float,
                                   help="Factor below which the mean flow must be in comparison to the dry weather "
                                        "flow in order to mark the value as a probable typo. (default: 1.5)",
                                   required=False)
    sewage_flow_group.add_argument('--mean_sewage_flow_above_typo_factor', metavar="FLOAT", default=9.0, type=float,
                                   help="Factor above which the mean flow must be in comparison to the dry weather "
                                        "flow in order to mark the value as a probable typo. (default: 9.0)",
                                   required=False)

    water_quality_group = parser.add_argument_group("Water quality control")
    water_quality_group.add_argument('--water_quality_number_of_last_month', metavar="INT", default=4, type=int,
                                      help="The number of last months to be used for water quality testing. (default: 4)",
                                      required=False)
    water_quality_group.add_argument('--min_number_of_last_measurements_for_water_qc', metavar="INT", default=9, type=int,
                                     help="The minimal number of last measurements required for water quality quality control. (default: 9)",
                                     required=False)
    water_quality_group.add_argument('--water_qc_outlier_statistics', metavar="METHOD", default=['lof','rf','iqr'], nargs='+',
                                    help=(
                                        "Which outlier detection methods should be used for water qc? Multiple selections allowed. (default: 'lof','rf','iqr')\n"
                                        "Possible choices are : [lof, rf, iqr, zscore, ci, all]\n"
                                        "E.g. to select 'rf' and 'iqr' use: --outlier_statistics rf iqr \n"
                                        "\tlof = local outlier factor\n"
                                        "\trf = random forest\n"
                                        "\tiqr = interquartile range\n"
                                        "\tzscore = modified z-score\n"
                                        "\tci = 99%% confidence interval\n"
                                        "\tall = use all methods\n"),
                                    choices=["lof", "rf", "iqr", "zscore", "ci", "all"],
                                    required=False)

    normalization_group = parser.add_argument_group("Biomarker normalization")
    normalization_group.add_argument('--max_number_of_flags_for_outlier', metavar="INT", default=2, type=int,
                                     help="Maximal number of accumulated flags from all quality controls. "
                                          "If the number is higher the sample will be marked as outlier. (default: 2)",
                                     required=False)
    normalization_group.add_argument('--min_number_of_biomarkers_for_normalization', metavar="INT", default=2, type=int,
                                     help="Minimal number of biomarkers used for normalization. (default: 2)",
                                     required=False)
    normalization_group.add_argument('--base_reproduction_value_factor', metavar="FLOAT", default=4.2, type=float,
                                   help="Factor below which the mean normalized biomarker value must be in comparison "
                                        "to the mean normalized biomarker value of the last 7 days. (default: 4.2)",
                                   required=False)

    args = parser.parse_args()
    sewageQuality = SewageQuality(args.output_folder, args.verbosity, args.quiet, args.rerun_all, args.interactive, args.biomarker_outlier_statistics, args.biomarker_min_threshold,
                                  args.min_number_biomarkers_for_outlier_detection,
                                  args.max_number_biomarkers_for_outlier_detection,
                                  args.report_number_of_biomarker_outliers, args.periode_month_surrogatevirus,
                                  args.surrogatevirus_outlier_statistics, args.min_number_surrogatevirus_for_outlier_detection,
                                  args.water_quality_number_of_last_month,
                                  args.min_number_of_last_measurements_for_water_qc, args.water_qc_outlier_statistics,
                                  args.fraction_last_samples_for_dry_flow, args.min_num_samples_for_mean_dry_flow,
                                  args.heavy_precipitation_factor, args.mean_sewage_flow_below_typo_factor,
                                  args.mean_sewage_flow_above_typo_factor, args.min_number_of_biomarkers_for_normalization,
                                  args.base_reproduction_value_factor, args.max_number_of_flags_for_outlier)

    sewageQuality.run_quality_control()

