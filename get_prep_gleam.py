from gleam_client import *
import numpy as np
import os
import glob
from astropy.io import fits
import bdsf


def get_data(file_name):
    a = fits.open(file_name)
    adata = a[0].data
    a.close()
    del a[0].data
    return adata


def get_header(filename):
    a = fits.open(filename)
    hdr = fits.Header()
    hdr['SIMPLE'] = 'T'
    hdr['BITPIX'] = a[0].header['BITPIX']
    hdr['NAXIS'] = 3
    hdr['NAXIS1'] = a[0].header['NAXIS1']
    hdr['NAXIS2'] = a[0].header['NAXIS2']
    hdr['NAXIS3'] = 3
    hdr['EXTEND'] = 'T'
    hdr['EQUINOX'] = 2000.0
    hdr['MJD-OBS'] = a[0].header['MJD-OBS']
    hdr['CTYPE1'] = a[0].header['CTYPE1']
    hdr['CUNIT1'] = a[0].header['CUNIT1']
    hdr['CRVAL1'] = a[0].header['CRVAL1']
    hdr['CRPIX1'] = a[0].header['CRPIX1']
    hdr['CDELT1'] = a[0].header['CD1_1']
    hdr['CTYPE2'] = a[0].header['CTYPE2']
    hdr['CUNIT2'] = a[0].header['CUNIT2']
    hdr['CRVAL2'] = a[0].header['CRVAL2']
    hdr['CRPIX2'] = a[0].header['CRPIX2']
    hdr['CDELT2'] = a[0].header['CD2_2']
    hdr['CTYPE3'] = 'FREQ'
    hdr['CUNIT3'] = 'Hz'
    hdr['CRVAL3'] = 150395000.0
    hdr['CRPIX3'] = 1.0
    hdr['CDELT3'] = 7680000.0
    hdr['HISTORY'] = 'None'
    a.close()

    return hdr


def combine_freq(list_of_files, outname):
    adata = get_data(list_of_files[0])
    bdata = get_data(list_of_files[1])
    cdata = get_data(list_of_files[2])
    data = np.zeros(adata.shape[0] *
                    adata.shape[1] * 3).reshape(adata.shape[0],
                                                adata.shape[1], 3)
    data[:, :, 0] = adata
    data[:, :, 1] = bdata
    data[:, :, 2] = cdata
    hdr = get_header(list_of_files[0])
    fits.writeto(outname, data.transpose(), hdr)
    del adata
    del bdata
    del cdata
    del data
    del hdr
    pass


if __name__ == '__main__':
    final_dir = 'output'
    cat_dir = 'cat'
    mask_dir = 'mask'
    log_dir = 'logs'
    os.system('mkdir ' + final_dir)
    os.system('mkdir ' + cat_dir)
    os.system('mkdir ' + mask_dir)
    os.system('mkdir ' + log_dir)
    for dec in range(-50, -20, 2):
        for ra in range(0, 360, 2):
            ang_size = 2.0
            freq = ['147-154', '154-162', '162-170']
            projection = 'SIN'
            dl_dir = 'tmp'
            os.system('mkdir ' + dl_dir)

            # get images
            try:
                vo_get(ra, dec, ang_size, proj_opt=projection, freq=freq,
                       download_dir=dl_dir)

                files = glob.glob("{0}/{1}_{2}_{3}_*.fits".format(dl_dir,
                                                                  ra, dec,
                                                                  ang_size))
                outname = "{0}_{1}_cube.fits".format(ra, dec)
                combine_freq(files, outname)
                img = bdsf.process_image(outname, beam=(0.04707321897149086,
                                                        0.04345351085066795,
                                                        -1.452792048454285),
                                         thresh_isl=5.0, thresh_pix=7.0)
                img.write_catalog(outfile="{0}_{1}_cube.catalog".format(ra,
                                                                        dec),
                                  format='ascii')
                img.export_image(outfile="{0}_{1}_cube.image".format(ra, dec),
                                 img_type='island_mask', img_format='casa')
                os.system("mv {0}_{1}_cube.fits {2}".format(ra, dec,
                                                            final_dir))
                os.system("mv {0}_{1}_cube.catalog {2}".format(ra, dec,
                                                               cat_dir))
                os.system("mv {0}_{1}_cube.image {2}".format(ra, dec,
                                                             mask_dir))
                os.system("mv *.log {0}".format(log_dir))
                os.system("rm -r {0}".format(dl_dir))
            except:
                continue
