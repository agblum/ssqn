# Created by alex at 10.07.23
import os
import itertools
import hashlib
import pyarrow as pa
import pyarrow.parquet as pq
from .utils import *


class SewageDatabase:

    def __init__(self, output_folder):
        self.output_folder = os.path.join(output_folder, ".db")
        self.database_file = os.path.join(self.output_folder, ".sewage_db.gzip")
        self.measurements_dict = dict()
        self.__create_folder()

    def __create_folder(self):
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def __load_db_for_location(self, sample_location):
        sample_location = self.__get_sample_location_escaped(sample_location)
        #database_file = os.path.join(self.output_folder, ".{}_sewage_db.gzip".format(sample_location))
        database_file = os.path.join(self.output_folder, ".{}_sewage_db.parquet".format(sample_location))
        if os.path.exists(database_file):
            table2 = pq.read_table(database_file)
            loaded_df = table2.to_pandas()
            #loaded_df = pd.read_pickle(database_file, compression="gzip")
            return loaded_df, True
        return None, False

    def __get_sample_location_escaped(self, sample_location: str):
        sample_location_escaped = sample_location.replace(" ", "_").replace("/", "_")
        return sample_location_escaped

    def add_sewage_location2db(self, sample_location, measurements_df: pd.DataFrame):
        sample_location = self.__get_sample_location_escaped(sample_location)
        if CalculatedColumns.NEEDS_PROCESSING.value in measurements_df:
            df2save = measurements_df.drop(columns=[CalculatedColumns.NEEDS_PROCESSING.value])

        table = pa.Table.from_pandas(df2save)
        pq.write_table(table, os.path.join(self.output_folder, ".{}_sewage_db.parquet".format(sample_location)))
    #    database_file = os.path.join(self.output_folder, ".{}_sewage_db.gzip".format(sample_location))
    #    df2save.to_pickle(database_file, compression="gzip")

    def __get_checksum_for_row(self, row):
        used_columns = [c.value for c in Columns]
        used_row = row[used_columns]
        merged = ','.join([str(i) for i in used_row.to_list()])
        return hashlib.md5(merged.encode('utf-8')).hexdigest()

    def __set_dtypes(self, new_measurements):
        for c in CalculatedColumns:
            if c.value in new_measurements:
                new_measurements[c.value] = new_measurements[c.value].astype(c.type)
        for column in CalculatedColumns.get_biomarker_flag_columns():
            if column in new_measurements:
                new_measurements[column] = new_measurements[column].astype(np.int)
        for biomarker1, biomarker2 in itertools.combinations(Columns.get_biomarker_columns(), 2):
            column = CalculatedColumns.get_biomaker_ratio_flag(biomarker1, biomarker2)
            if column in new_measurements:
                new_measurements[column] = new_measurements[column].astype(np.int)
        for column in Columns.get_surrogatevirus_columns():
            column_flag = CalculatedColumns.get_surrogate_outlier_flag(column)
            if column_flag in new_measurements:
                new_measurements[column_flag] = new_measurements[column_flag].astype(np.int)
            column_flag = CalculatedColumns.get_surrogate_flag(column)
            if column_flag in new_measurements:
                new_measurements[column_flag] = new_measurements[column_flag].astype(np.int)



    def needs_recalcuation(self, sample_location, new_measurements: pd.DataFrame, rerun_all: bool):
        if rerun_all:
            new_measurements[CalculatedColumns.NEEDS_PROCESSING.value] = True
        else:
            db_measurements, is_loaded = self.__load_db_for_location(sample_location)
            if is_loaded:
                indices = []
                for index, row in new_measurements.iterrows():
                    needs_recalculation = True
                    db_row = db_measurements[db_measurements[Columns.DATE.value] == row[Columns.DATE.value]]
                    if db_row.shape[0] > 0:
                        stored_checksum = self.__get_checksum_for_row(db_row.squeeze())
                        new_checksum = self.__get_checksum_for_row(row)
                        if stored_checksum == new_checksum and index != 3:
                            needs_recalculation = False
                            indices.append(db_row.index.tolist()[0])
                    new_measurements.at[index, CalculatedColumns.NEEDS_PROCESSING.value] = needs_recalculation
                update_df = db_measurements.iloc[indices]
                new_measurements.set_index(Columns.DATE.value, inplace=True)
                new_measurements.update(update_df.set_index(Columns.DATE.value))
                new_measurements.reset_index(inplace=True)
                self.__set_dtypes(new_measurements)
            else:
                new_measurements[CalculatedColumns.NEEDS_PROCESSING.value] = True



