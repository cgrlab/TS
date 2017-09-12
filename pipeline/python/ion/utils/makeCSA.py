#!/usr/bin/env python
# Copyright (C) 2016 Ion Torrent Systems, Inc. All Rights Reserved
import os
import zipfile
import fnmatch
result_patterns = [
    'ion_params_00.json',
    'alignment.log',
    'report.pdf',
    'backupPDF.pdf',
    '*-full.pdf',
    'DefaultTFs.conf',
    'drmaa_stderr_block.txt',
    'drmaa_stdout.txt',
    'drmaa_stdout_block.txt',
    'ReportLog.html',
    'sysinfo.txt',
    'uploadStatus',
    'version.txt',
    #Signal processing files
    '*bfmask.stats',
    'avgNukeTrace_*.txt',
    'dcOffset*',
    'NucStep*',
    'processParameters.txt',
    'separator.bftraces.txt',
    'separator.trace.txt',
    'sigproc.log',
    'BkgModelFilterData.h5',
    'pinsPerFlow.txt',
    # Basecaller files
    '*ionstats_alignment.json',
    '*ionstats_basecaller.json',
    'alignmentQC_out.txt',
    'alignmentQC_out_*.txt',
    'alignStats_err.json',
    'BaseCaller.json',
    'basecaller.log',
    'datasets_basecaller.json',
    'datasets_pipeline.json',
    'datasets_tf.json',
    '*ionstats_tf.json',
    'TFStats.json',
    '*.sparkline.png'
]
rawdata_patterns = [
    'explog_final.txt',
    'InitLog.txt',
    'InitLog1.txt',
    'InitLog2.txt',
    'RawInit.txt',
    'RawInit.jpg',
    'InitValsW3.txt',
    'InitValsW2.txt',
    'Controller',
    'debug',
    'Controller_1',
    'debug_1',
    'chipCalImage.bmp.bz2',
]


def match_files(walk, pattern):
    for root, _, files in walk:
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


def get_file_list(directory, patterns, block_list=[]):
    mylist = []
    walk = list(os.walk(directory, followlinks=True))
    for pattern in patterns:
        for filename in match_files(walk, pattern):
            blockthis = False
            for blocker in block_list:
                if blocker in filename:
                    blockthis = True
            if not blockthis:
                mylist.append(filename)

    return mylist


def get_list_from_results(directory):
    return get_file_list(directory, result_patterns, block_list=["plugin_out"])


def get_list_from_rawdata(directory):
    return get_file_list(directory, rawdata_patterns)


def writeZip(fullnamepath, filelist, dirtrim="", openmode="w"):
    '''Add files to zip archive.  dirtrim is a string which will be deleted
    from each file entry.  Used to strip leading directory from filename.'''
    # Open a zip archive file
    csa = zipfile.ZipFile(fullnamepath, mode=openmode,
                          compression=zipfile.ZIP_DEFLATED, allowZip64=True)

    # Add each file to the zip archive file
    for item in filelist:
        if os.path.exists(item):
            arcname = item.replace(dirtrim, '')
            csa.write(item, arcname)

    # Close zip archive file
    csa.close()

def migrateZip(logzipname, fullnamepath, openmode="w"):

    # Open a zip archive file
    csa = zipfile.ZipFile(fullnamepath, mode=openmode,
                      compression=zipfile.ZIP_DEFLATED, allowZip64=True)
    csa_files = sorted(csa.namelist())

    # Include files from pgm_logs.zip found in reportDir
    if not zipfile.is_zipfile(logzipname):
        csa.writestr("missing_instrument_logs.log", "Could not find raw data directory\npgm_logs.zip also missing.")
    else:
        # Add contents of pgm_logs.zip
        # This file generated by TLScript.py (src in pipeline/python/ion/reports)
        # list of files included in zip should match list above
        pgmlogzip = zipfile.ZipFile(logzipname, mode="r")
        for item in pgmlogzip.namelist():
            if not item in csa_files:
                contents = pgmlogzip.read(item)
                csa.writestr(item, contents)
        pgmlogzip.close()

    csa.close()
    return


def makeCSA(reportDir, rawDataDir, csa_file_name=None):

    # reportDir must exist
    if not os.path.exists(reportDir):
        raise IOError("%s: Does not exist" % reportDir)

    # Define output file name
    if not csa_file_name:
        csa_file_name = "%s.support.zip" % os.path.basename(reportDir)
    csaFullPath = os.path.join(reportDir, csa_file_name)

    # Generate a list of files from report dir to write to the archive
    zipList = get_list_from_results(reportDir)
    writeZip(csaFullPath, zipList, dirtrim=reportDir, openmode="w")

    # Generate a list of files from rawdata dir to append to the archive
    zipList = get_list_from_rawdata(rawDataDir)
    writeZip(csaFullPath, zipList, dirtrim=rawDataDir, openmode="a")

    # Append contents of pgm_logs.zip file in case rawdata contents has been deleted
    migrateZip(os.path.join(reportDir, "pgm_logs.zip"), csaFullPath, openmode="a")

    return csaFullPath
