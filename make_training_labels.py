import pandas as pd
import glob
from astropy.io import fits
import numpy as np


def make_dataframe(file_name):
    raw_catalog = pd.read_csv(file_name, delimiter='\s+',
                              skipinitialspace=False, header=4)
    colnames = raw_catalog.columns
    new_colnames = colnames[1:]
    clean_catalog = pd.DataFrame(columns=new_colnames)
    for i in range(0, len(new_colnames)):
        clean_catalog[new_colnames[i]] = raw_catalog[colnames[i]]

    return clean_catalog


def get_pix_size(file_name):
    a = fits.open(file_name)
    deg_per_pix = np.abs(a[0].header['CDELT2'])
    imsize = a[0].header['NAXIS1']
    a.close()
    return deg_per_pix, imsize


def calc_box(df):
    df['x1'] = np.round(df['Xposn']) - df['length']
    df['x2'] = np.round(df['Xposn']) + df['length']
    df['y1'] = np.round(df['Yposn']) - df['length']
    df['y2'] = np.round(df['Yposn']) + df['length']

    pass


def fix_bounding_box(df, imsize):
    df.loc[df['x1'] < 0, 'x1'] = 0
    df.loc[df['y1'] < 0, 'y1'] = 0
    df.loc[df['x2'] > imsize, 'x2'] = imsize
    df.loc[df['y2'] > imsize, 'y2'] = imsize
    pass


def combine_multiple(df):
    islands = df.groupby('Isl_id').size()
    temp = pd.DataFrame(columns=['image', 'x1', 'y1', 'x2', 'y2',
                                 'S_Code'], index=islands.index)
    temp['image'] = df.loc[0]['image']
    for i in islands.index:
        temp.loc[i]['x1'] = np.min(df.loc[df['Isl_id'] == i]['x1'])
        temp.loc[i]['y1'] = np.min(df.loc[df['Isl_id'] == i]['y1'])
        temp.loc[i]['x2'] = np.max(df.loc[df['Isl_id'] == i]['x2'])
        temp.loc[i]['y2'] = np.max(df.loc[df['Isl_id'] == i]['y2'])
        if islands.loc[i] > 1:
            temp.loc[i]['S_Code'] = 'M'
        else:
            temp.loc[i]['S_Code'] = 'S'

    return temp


catalog_file_names = glob.glob('cat/*')
catalog_file_names.sort()
fits_file_names = glob.glob('output/*')
fits_file_names.sort()
training_labels = pd.DataFrame(columns=['image', 'x1', 'y1', 'x2', 'y2',
                                        'S_Code'])
for i in range(0, len(catalog_file_names)):
    pd_catalog = make_dataframe(catalog_file_names[i])
    name = 'output/' + catalog_file_names[i][4:-7] + 'fits'
    pd_catalog['image'] = name
    deg_per_pix, imsize = get_pix_size(name)
    pd_catalog['length'] = np.round(pd_catalog['Maj_img_plane'] / deg_per_pix)
    calc_box(pd_catalog)
    fix_bounding_box(pd_catalog, imsize)
    temp = combine_multiple(pd_catalog)
    training_labels = training_labels.append(temp[['image', 'x1', 'y1',
                                                   'x2', 'y2',
                                                   'S_Code']])

# fix_bounding_box(training_labels)
training_labels.to_csv('new_training_labels_right_box.csv', header=False, index=False)
